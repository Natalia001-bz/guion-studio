"""Paso 4: verificar el resultado sin tener que verlo entero.

- Hoja de fotogramas: una imagen con N cuadros repartidos por el video.
- Volumen integrado (LUFS) y duración.
- Diferencia entre pistas de imagen y audio (desfase al final).
"""
from __future__ import annotations

from pathlib import Path

from .medios import duracion, duraciones_pistas, ejecutar, volumen_integrado


def hoja_fotogramas(video: Path, salida: Path, cuadros: int = 12, columnas: int = 4) -> Path:
    dur = duracion(video)
    filas = -(-cuadros // columnas)
    fps = cuadros / dur
    ejecutar(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vf",
              f"fps={fps:.6f},scale=480:-2,drawtext=text='%{{pts\\:hms}}':x=8:y=8:fontsize=20:"
              f"fontcolor=yellow:box=1:boxcolor=black@0.5,tile={columnas}x{filas}",
              "-frames:v", "1", str(salida)])
    return salida


def informe(video: Path, limite_min: float | None = None) -> dict:
    dur = duracion(video)
    pistas = duraciones_pistas(video)
    lufs = volumen_integrado(video)
    res = {
        "archivo": str(video),
        "duracion": f"{int(dur // 60)}:{int(dur % 60):02d}",
        "segundos": round(dur, 1),
        "tamano_mb": round(video.stat().st_size / 1e6, 1),
        "volumen_lufs": lufs,
        "desfase_final_s": round(abs(pistas.get("video", dur) - pistas.get("audio", dur)), 2),
        "alertas": [],
    }
    if limite_min and dur > limite_min * 60:
        res["alertas"].append(f"Dura más de {limite_min} min.")
    if lufs is not None and not (-18 <= lufs <= -13):
        res["alertas"].append(f"Volumen {lufs} LUFS fuera del rango web (−18 a −13).")
    if res["desfase_final_s"] > 0.5:
        res["alertas"].append("Imagen y audio difieren más de 0,5 s al final.")
    return res
