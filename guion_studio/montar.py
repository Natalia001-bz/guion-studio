"""Paso 3: montaje final.

Por cada bloque: pista de diapositivas (con fundidos y aparición de ítems) +
cámara en la esquina + audio del clip. Al final, las referencias.

Sincronización: el momento de cada diapositiva o ítem se estima por la posición
de su frase en el guion (proporción de palabras) y luego se lleva al comienzo
de frase más cercano en el audio (cuando la voz retoma tras una pausa).
Si algo queda corrido, se corrige en ajustes.toml:

    [tiempos]
    "postura" = 24.0       # segundo del bloque en que entra la diapositiva
    "postura#2" = 33.1     # segundo en que aparece su 2.º ítem animado

La pista de diapositivas se arma tramo por tramo (dos imágenes por vez): con
un único filtro xfade de decenas de entradas FFmpeg se queda sin memoria.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import Proyecto
from .diapositivas import Diapositiva, cargar, generar
from .guion import Bloque, leer_guion, posicion_frase
from .medios import buscar_clip, duracion, ejecutar, inicios_de_frase


@dataclass
class Evento:
    imagen: str          # nombre del PNG del paso
    t: float             # segundo dentro del bloque
    clave: str           # id o id#k (para ajustes y reportes)


def _ajustar(t: float, inicios: list[float], ventana: float) -> float:
    cerca = [i for i in inicios if abs(i - t) <= ventana]
    return (min(cerca, key=lambda i: abs(i - t)) - 0.1) if cerca else t


def calcular_eventos(bloque: Bloque, dias: list[Diapositiva], dur: float, inicios: list[float],
                     ajustes: dict, m: dict, avisos: list[str]) -> list[Evento]:
    inicio_bloque = m["intro_camara"] if bloque.numero == 1 and m["camara"] else 0.0
    ventana = m["ventana_ajuste"] if m["ajustar_a_frases"] else 0

    def momento(frase: str, ref: str) -> float | None:
        pos = posicion_frase(bloque, frase)
        if pos is None:
            avisos.append(f"Bloque {bloque.numero}: no encontré «{frase}» ({ref}) en el guion.")
            return None
        return _ajustar(pos * dur, inicios, ventana)

    # 1) entrada de cada diapositiva
    entradas = []
    for i, dia in enumerate(dias):
        if dia.id in ajustes:
            t = float(ajustes[dia.id])
        elif i == 0 or not dia.entra:
            t = inicio_bloque if i == 0 else None
        else:
            t = momento(dia.entra, dia.id)
        if t is None:      # sin frase: reparte el tiempo entre las vecinas
            t = entradas[-1] + 1.0 if entradas else inicio_bloque
        entradas.append(max(t, inicio_bloque))
    for i in range(1, len(entradas)):
        entradas[i] = max(entradas[i], entradas[i - 1] + 1.0)

    # 2) pasos de cada diapositiva
    eventos: list[Evento] = []
    for i, dia in enumerate(dias):
        t0 = entradas[i]
        limite = entradas[i + 1] if i + 1 < len(dias) else dur
        eventos.append(Evento(f"{dia.id}_p0.png", round(t0, 2), dia.id))
        previo = t0
        for k, it in enumerate(dia.animados, 1):
            clave = f"{dia.id}#{k}"
            tk = float(ajustes[clave]) if clave in ajustes else momento(it["frase"], clave)
            if tk is None:
                tk = previo + 1.0
            tk = min(max(tk, previo + 0.8), limite - 0.8)
            eventos.append(Evento(f"{dia.id}_p{k}.png", round(tk, 2), clave))
            previo = tk
    return eventos


def pista_diapositivas(eventos: list[Evento], dur: float, imgs: Path, tmp: Path, m: dict, fps: int) -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(fps)]
    trans = m["transicion"]
    lista = []
    for i, ev in enumerate(eventos):
        fin = eventos[i + 1].t if i + 1 < len(eventos) else dur
        largo = max(fin - ev.t, 0.2)
        seg = tmp / f"t{i:03d}.mp4"
        img = ["-loop", "1", "-framerate", str(fps), "-t", f"{largo:.3f}", "-i", str(imgs / ev.imagen)]
        if i == 0 or trans <= 0:
            ejecutar(["ffmpeg", "-y", "-v", "error", *img, "-vf", "format=yuv420p,setsar=1", *enc, str(seg)])
        else:
            prev = ["-loop", "1", "-framerate", str(fps), "-t", f"{trans:.3f}", "-i", str(imgs / eventos[i - 1].imagen)]
            ejecutar(["ffmpeg", "-y", "-v", "error", *prev, *img, "-filter_complex",
                      "[0:v]format=yuv420p,setsar=1[a];[1:v]format=yuv420p,setsar=1[b];"
                      f"[a][b]xfade=transition=fade:duration={min(trans, largo - 0.05):.3f}:offset=0[v]",
                      "-map", "[v]", *enc, str(seg)])
        lista.append(seg)
    txt = tmp / "lista.txt"
    txt.write_text("".join(f"file '{p.name}'\n" for p in lista), encoding="utf-8")
    out = tmp.with_suffix(".mp4")
    ejecutar(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(txt), "-c", "copy", str(out)])
    return out


def _escapar(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def montar_bloque(proy: Proyecto, bloque: Bloque, clip: Path, eventos: list[Evento], dur: float,
                  imgs: Path, tmp: Path) -> Path:
    m, t = proy["montaje"], proy["tema"]
    W, H, fps = m["ancho"], m["alto"], proy["preparar"]["fps"]
    from .diapositivas import Lienzo
    lz = Lienzo(proy)
    cx, cy, cw, ch = lz.cam
    pista = pista_diapositivas(eventos, dur, imgs, tmp / f"pista{bloque.numero}", m, fps)
    f = [f"[0:v]fps={fps},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,split=2[full][c2]",
         f"[c2]scale={cw}:{ch},pad={cw + 8}:{ch + 8}:4:4:color={t['primario'].replace('#', '0x')}[mini]",
         f"[1:v]fps={fps},format=yuv420p,setsar=1[s0]"]
    intro = m["intro_camara"] if bloque.numero == 1 and m["camara"] else 0
    if intro:
        f.append(f"color=c={t['fondo'].replace('#', '0x')}:s={W}x{H}:r={fps}:d={eventos[0].t}[pre]")
        f.append("[pre][s0]concat=n=2:v=1:a=0[s]")
    else:
        f.append("[s0]null[s]")
    if m["camara"]:
        f.append(f"[s][mini]overlay={cx - 4}:{cy - 4}:shortest=1[comp]")
    else:
        f.append("[s]null[comp]")
    if intro:
        rot = []
        if m["rotulo_nombre"]:
            fn = lz._buscar("texto_negrita") if not t["fuente_texto_negrita"] else t["fuente_texto_negrita"]
            fd = lz._buscar("texto") if not t["fuente_texto"] else t["fuente_texto"]
            y0 = int(H * 0.76)
            rot.append(f"drawbox=x=0:y={y0}:w={int(W * 0.57)}:h={int(H * 0.14)}:color={t['primario'].replace('#', '0x')}@0.92:t=fill")
            rot.append(f"drawtext=fontfile='{fn}':text='{_escapar(m['rotulo_nombre'])}':fontsize={int(H * 0.052)}:"
                       f"fontcolor=white:x={int(W * 0.042)}:y={y0 + int(H * 0.018)}")
            if m["rotulo_detalle"]:
                rot.append(f"drawtext=fontfile='{fd}':text='{_escapar(m['rotulo_detalle'])}':fontsize={int(H * 0.033)}:"
                           f"fontcolor={t['cabecera_texto'].replace('#', '0x')}:x={int(W * 0.042)}:y={y0 + int(H * 0.085)}")
        f.append(f"[full]{','.join(rot) if rot else 'null'}[fr]")
        f.append(f"[comp][fr]overlay=0:0:enable='lt(t,{intro})'[v0]")
    else:
        f.append("[full]nullsink")
        f.append("[comp]null[v0]")
    fb = m["fundido_bloque"]
    f.append(f"[v0]fade=t=in:st=0:d={fb},fade=t=out:st={dur - fb:.3f}:d={fb}[v]")
    f.append(f"[0:a]aresample=48000,afade=t=in:st=0:d={fb},afade=t=out:st={dur - fb:.3f}:d={fb}[a]")
    out = tmp / f"b{bloque.numero}.mp4"
    ejecutar(["ffmpeg", "-y", "-v", "error", "-i", str(clip), "-i", str(pista), "-filter_complex", ";".join(f),
              "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "medium",
              "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", str(out)])
    return out


def montar_referencias(proy: Proyecto, refs: list[Diapositiva], imgs: Path, tmp: Path) -> Path | None:
    if not refs:
        return None
    m, fps = proy["montaje"], proy["preparar"]["fps"]
    seg = m["seg_referencia"]
    eventos = [Evento(f"{d.id}_p0.png", i * seg, d.id) for i, d in enumerate(refs)]
    total = seg * len(refs)
    pista = pista_diapositivas(eventos, total, imgs, tmp / "pista_ref", m, fps)
    out = tmp / "referencias.mp4"
    ejecutar(["ffmpeg", "-y", "-v", "error", "-i", str(pista), "-f", "lavfi", "-t", f"{total}", "-i",
              "anullsrc=r=48000:cl=stereo", "-vf", f"fade=t=in:st=0:d={m['fundido_bloque']}",
              "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
              "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-shortest", str(out)])
    return out


def planear(proy: Proyecto, solo_plan: bool = False):
    """Devuelve [(bloque, clip, dur, eventos)], referencias y avisos."""
    bloques = leer_guion(proy.ruta("guion"))
    dias = cargar(proy)
    origen = proy.ruta("preparados") if proy.ruta("preparados").exists() else proy.ruta("clips")
    ajustes = proy.ajustes()
    avisos: list[str] = []
    plan = []
    for b in bloques:
        clip = buscar_clip(origen, b.numero)
        if clip is None:
            raise FileNotFoundError(f"Falta el clip del bloque {b.numero} en {origen}")
        dur = duracion(clip)
        propias = [d for d in dias if d.bloque == b.numero]
        if not propias:
            avisos.append(f"Bloque {b.numero} no tiene diapositivas: se verá solo la cámara.")
        inicios = inicios_de_frase(clip, proy["preparar"]["umbral_db"]) if proy["montaje"]["ajustar_a_frases"] else []
        eventos = calcular_eventos(b, propias, dur, inicios, ajustes, proy["montaje"], avisos) if propias else []
        plan.append((b, clip, dur, eventos))
    refs = [d for d in dias if d.bloque is None]
    return plan, refs, avisos


def montar(proy: Proyecto, avisar=print) -> Path:
    plan, refs, avisos = planear(proy)
    for a in avisos:
        avisar("Aviso: " + a)
    imgs, desborde = generar(proy)
    for d in desborde:
        avisar(f"Aviso: la diapositiva «{d}» se sale de su zona; revisa la imagen.")
    tmp = proy.carpeta / "salida" / "_temporal"
    tmp.mkdir(parents=True, exist_ok=True)
    partes = []
    for b, clip, dur, eventos in plan:
        if not eventos:   # bloque sin diapositivas: solo cámara a pantalla completa
            m = proy["montaje"]
            out = tmp / f"b{b.numero}.mp4"
            fb = m["fundido_bloque"]
            ejecutar(["ffmpeg", "-y", "-v", "error", "-i", str(clip), "-vf",
                      f"fps={proy['preparar']['fps']},scale={m['ancho']}:{m['alto']}:force_original_aspect_ratio=increase,"
                      f"crop={m['ancho']}:{m['alto']},setsar=1,fade=t=in:st=0:d={fb},fade=t=out:st={dur - fb:.3f}:d={fb}",
                      "-af", f"aresample=48000,afade=t=in:st=0:d={fb},afade=t=out:st={dur - fb:.3f}:d={fb}",
                      "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", str(out)])
            partes.append(out)
        else:
            partes.append(montar_bloque(proy, b, clip, eventos, dur, imgs, tmp))
        avisar(f"Bloque {b.numero} listo ({dur:.1f} s)")
    r = montar_referencias(proy, refs, imgs, tmp)
    if r:
        partes.append(r)
    lista = tmp / "lista.txt"
    lista.write_text("".join(f"file '{p.name}'\n" for p in partes), encoding="utf-8")
    salida = proy.ruta("salida")
    salida.parent.mkdir(parents=True, exist_ok=True)
    ejecutar(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
              "-c", "copy", "-movflags", "+faststart", str(salida)])
    return salida
