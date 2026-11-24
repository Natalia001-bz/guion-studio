"""Línea de comandos: guion-studio <comando> [carpeta del proyecto]."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from . import __version__
from .config import Proyecto
from .medios import ErrorFFmpeg, verificar_ffmpeg

EJEMPLO = Path(__file__).parent / "plantilla"


def cmd_iniciar(a):
    destino = Path(a.carpeta)
    if destino.exists() and any(destino.iterdir()):
        sys.exit(f"La carpeta {destino} ya tiene archivos; elige una vacía.")
    shutil.copytree(EJEMPLO, destino, dirs_exist_ok=True)
    (destino / "clips").mkdir(exist_ok=True)
    print(f"Proyecto creado en {destino}.\nEdita guion.md y diapositivas.toml; graba con el teleprompter "
          "y guarda los clips en clips/ (bloque1.webm, bloque2.webm…).")


def cmd_guion(a):
    from .guion import leer_guion
    from .diapositivas import cargar
    from .guion import posicion_frase
    proy = Proyecto(a.carpeta)
    bloques = leer_guion(proy.ruta("guion"))
    total = 0
    ppm = a.ppm
    for b in bloques:
        seg = b.palabras / ppm * 60
        total += seg
        print(f"Bloque {b.numero} · {b.titulo}: {b.palabras} palabras ≈ {int(seg // 60)}:{int(seg % 60):02d}")
    print(f"Total ≈ {int(total // 60)}:{int(total % 60):02d} a {ppm} palabras por minuto")
    if proy.ruta("diapositivas").exists():
        por_num = {b.numero: b for b in bloques}
        faltan = 0
        for d in cargar(proy):
            if d.bloque is None:
                continue
            b = por_num.get(d.bloque)
            frases = ([d.entra] if d.entra else []) + [it["frase"] for it in d.animados]
            for fr in frases:
                if b is None or posicion_frase(b, fr) is None:
                    print(f"  ✗ «{fr}» ({d.id}) no está en el bloque {d.bloque}")
                    faltan += 1
        print("Frases de las diapositivas: " + ("todas encontradas ✓" if not faltan else f"{faltan} sin encontrar"))


def cmd_preparar(a):
    from .preparar import planear, procesar
    from .guion import leer_guion
    proy = Proyecto(a.carpeta)
    numeros = a.bloques or [b.numero for b in leer_guion(proy.ruta("guion"))]
    total = 0
    for p in planear(proy, numeros):
        total += p.neto
        print(f"Bloque {p.numero}: {p.duracion:6.1f} s → {p.neto:6.1f} s "
              f"(conserva {p.tramos[0][0]:.2f}–{p.tramos[-1][1]:.2f}; {len(p.tramos) - 1} pausas acortadas)")
        if not a.plan:
            out = procesar(proy, p)
            print(f"          listo: {out.relative_to(proy.carpeta)}")
    print(f"Total: {int(total // 60)}:{int(total % 60):02d}")


def cmd_diapositivas(a):
    from .diapositivas import generar
    proy = Proyecto(a.carpeta)
    carpeta, desborde = generar(proy)
    print(f"Diapositivas en {carpeta}")
    for d in desborde:
        print(f"Aviso: «{d}» se sale de su zona.")


def cmd_plan(a):
    from .montar import planear
    proy = Proyecto(a.carpeta)
    plan, refs, avisos = planear(proy)
    total = 0
    for b, clip, dur, eventos in plan:
        total += dur
        print(f"Bloque {b.numero} ({dur:.1f} s): " + ", ".join(f"{e.clave}@{e.t:.1f}" for e in eventos))
    total += len(refs) * proy["montaje"]["seg_referencia"]
    print(f"Duración estimada: {int(total // 60)}:{int(total % 60):02d}")
    for x in avisos:
        print("Aviso: " + x)


def cmd_montar(a):
    from .montar import montar
    proy = Proyecto(a.carpeta)
    salida = montar(proy)
    print(f"Video listo: {salida}")
    if not a.sin_revisar:
        a.video = str(salida)
        cmd_revisar(a)


def cmd_revisar(a):
    from .revisar import hoja_fotogramas, informe
    proy = Proyecto(a.carpeta)
    video = Path(a.video) if getattr(a, "video", None) else proy.ruta("salida")
    r = informe(video, a.limite)
    hoja = hoja_fotogramas(video, video.with_name(video.stem + "_fotogramas.jpg"))
    print(f"{r['duracion']} · {r['tamano_mb']} MB · {r['volumen_lufs']} LUFS · desfase final {r['desfase_final_s']} s")
    print(f"Hoja de fotogramas: {hoja}")
    for x in r["alertas"]:
        print("Alerta: " + x)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="guion-studio", description="Del guion al video: teleprompter, clips, diapositivas animadas y montaje.")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def nuevo(nombre, func, ayuda):
        p = sub.add_parser(nombre, help=ayuda)
        p.add_argument("carpeta", nargs="?", default=".", help="carpeta del proyecto (por defecto, la actual)")
        p.set_defaults(func=func)
        return p

    nuevo("iniciar", cmd_iniciar, "crea un proyecto nuevo a partir de la plantilla")
    nuevo("guion", cmd_guion, "duración estimada por bloque y frases de las diapositivas").add_argument("--ppm", type=int, default=135)
    p = nuevo("preparar", cmd_preparar, "corta silencios, corrige imagen y audio, ajusta la velocidad")
    p.add_argument("--plan", action="store_true", help="solo muestra los cortes")
    p.add_argument("--bloques", type=int, nargs="*", help="solo estos bloques")
    nuevo("diapositivas", cmd_diapositivas, "dibuja las diapositivas y sus pasos")
    nuevo("plan", cmd_plan, "muestra en qué segundo entra cada diapositiva e ítem")
    p = nuevo("montar", cmd_montar, "arma el video final")
    p.add_argument("--sin-revisar", action="store_true")
    p.add_argument("--limite", type=float, default=None, help="duración máxima en minutos")
    p = nuevo("revisar", cmd_revisar, "hoja de fotogramas, volumen y desfase")
    p.add_argument("--video", default=None)
    p.add_argument("--limite", type=float, default=None)

    a = ap.parse_args(argv)
    try:
        if a.cmd != "iniciar" and a.cmd != "guion" and a.cmd != "diapositivas":
            verificar_ffmpeg()
        a.func(a)
    except (ErrorFFmpeg, FileNotFoundError) as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
