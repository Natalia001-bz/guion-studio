"""Paso 1: preparar cada clip antes del montaje.

- Corta el silencio del inicio y del final (el momento en que se ve que la persona
  inicia o detiene la grabación).
- Acorta las pausas internas largas sin tocar las naturales.
- Corrige la imagen con suavidad (cara a contraluz) y limpia el audio.
- Acelera levemente (1,05×) sin cambiar el tono de la voz.

Lecciones de uso real que fijan los valores por defecto:
- Subir mucho el contraste y la saturación quita la "niebla", pero se ve artificial.
- La reducción de ruido (afftdn) en una voz ya limpia deja un sonido metálico.
- rubberband conserva mejor la voz que atempo al cambiar la velocidad.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import Proyecto
from .medios import buscar_clip, duracion, ejecutar, silencios

IMAGEN = {
    "suave": ("curves=master='0/0 0.25/0.29 0.55/0.6 1/1',eq=contrast=1.04:saturation=1.05,"
              "unsharp=5:5:0.35:5:5:0"),
    "ninguna": "null",
}
AUDIO = {
    "limpio": "highpass=f=70,acompressor=threshold=-22dB:ratio=2:attack=15:release=250",
    "ninguno": "anull",
}


@dataclass
class Plan:
    numero: int
    origen: Path
    duracion: float
    tramos: list[tuple[float, float]]
    velocidad: float

    @property
    def neto(self) -> float:
        return sum(b - a for a, b in self.tramos) / self.velocidad


def calcular_tramos(dur: float, sil: list[tuple[float, float]], p: dict) -> list[tuple[float, float]]:
    """Intervalos que se conservan. Función pura: se prueba sin FFmpeg."""
    unidos: list[list[float]] = []
    for a, b in sil:
        b = min(b, dur)
        if unidos and a - unidos[-1][1] < p["unir"]:
            unidos[-1][1] = b
        else:
            unidos.append([a, b])
    inicio, fin = 0.0, dur
    if unidos and unidos[0][0] < 0.2:
        inicio = max(0.0, unidos[0][1] - p["margen_inicio"])
        unidos = unidos[1:]
    if unidos and unidos[-1][1] > dur - 0.2:
        fin = min(dur, unidos[-1][0] + p["margen_fin"])
        unidos = unidos[:-1]
    keep, cur, mitad = [], inicio, p["pausa_queda"] / 2
    for a, b in unidos:
        if b - a > p["pausa_larga"]:
            keep.append((cur, a + mitad))
            cur = b - mitad
    keep.append((cur, fin))
    return [(round(a, 3), round(b, 3)) for a, b in keep if b - a > 0.05]


def planear(proy: Proyecto, numeros: list[int]) -> list[Plan]:
    p = proy["preparar"]
    planes = []
    for n in numeros:
        src = buscar_clip(proy.ruta("clips"), n)
        if src is None:
            raise FileNotFoundError(f"Falta el clip del bloque {n} en {proy.ruta('clips')}")
        dur = duracion(src)
        tramos = calcular_tramos(dur, silencios(src, p["umbral_db"], p["silencio_min"]), p)
        planes.append(Plan(n, src, dur, tramos, p["velocidad"]))
    return planes


def procesar(proy: Proyecto, plan: Plan) -> Path:
    p = proy["preparar"]
    salida = proy.ruta("preparados")
    salida.mkdir(parents=True, exist_ok=True)
    imagen = IMAGEN.get(p["imagen"], p["imagen"])
    audio = AUDIO.get(p["audio"], p["audio"])
    vel, fps = p["velocidad"], p["fps"]
    expr = "+".join(f"between(t,{a},{b})" for a, b in plan.tramos)
    v = (f"[0:v]fps={fps},select='{expr}',setpts=N/FRAME_RATE/TB,{imagen},"
         f"setpts=PTS/{vel},fps={fps},format=yuv420p[v]")
    tempo = f"rubberband=tempo={vel}:window=standard," if abs(vel - 1) > 1e-3 else ""
    a = (f"[0:a]aselect='{expr}',asetpts=N/SR/TB,{audio},{tempo}"
         f"loudnorm=I={p['volumen_lufs']}:TP=-1.5:LRA=9,aresample=48000[a]")
    out = salida / f"bloque{plan.numero}.mp4"
    ejecutar(["ffmpeg", "-y", "-v", "error", "-i", str(plan.origen), "-filter_complex", f"{v};{a}",
              "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", str(p["crf"]),
              "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)])
    return out
