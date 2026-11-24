"""Utilidades de FFmpeg compartidas."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

EXT_VIDEO = (".webm", ".mp4", ".mov", ".mkv", ".m4v")


class ErrorFFmpeg(RuntimeError):
    pass


def verificar_ffmpeg() -> None:
    for prog in ("ffmpeg", "ffprobe"):
        if shutil.which(prog) is None:
            raise ErrorFFmpeg(f"No encontré «{prog}». Instálalo (Ubuntu: sudo apt install ffmpeg).")


def ejecutar(cmd: list[str]) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        pista = ""
        if r.returncode in (-9, 137):
            pista = "\nEl sistema detuvo FFmpeg por falta de memoria."
        raise ErrorFFmpeg(f"FFmpeg falló (código {r.returncode}).{pista}\n{r.stderr[-2500:]}")
    return r


def duracion(ruta: Path) -> float:
    r = ejecutar(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                  "-of", "csv=p=0", str(ruta)])
    return float(r.stdout.strip())


def duraciones_pistas(ruta: Path) -> dict[str, float]:
    r = ejecutar(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration",
                  "-of", "csv=p=0", str(ruta)])
    res = {}
    for linea in r.stdout.split():
        tipo, _, d = linea.partition(",")
        if d and d != "N/A":
            res[tipo] = float(d)
    return res


def silencios(ruta: Path, umbral_db: float = -38, minimo: float = 0.4) -> list[tuple[float, float]]:
    """Intervalos de silencio (inicio, fin) detectados en el audio."""
    err = ejecutar(["ffmpeg", "-hide_banner", "-nostats", "-i", str(ruta), "-af",
                    f"silencedetect=noise={umbral_db}dB:d={minimo}", "-f", "null", "-"]).stderr
    ini = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    fin = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    if len(fin) < len(ini):
        fin.append(duracion(ruta))
    return [(max(a, 0.0), b) for a, b in zip(ini, fin)]


def inicios_de_frase(ruta: Path, umbral_db: float = -38) -> list[float]:
    """Momentos en que la voz retoma tras una pausa breve."""
    return [b for _, b in silencios(ruta, umbral_db, 0.25)]


def buscar_clip(carpeta: Path, numero: int) -> Path | None:
    """Acepta bloque3.webm, bloque03.mp4 o 3.webm."""
    for p in sorted(carpeta.glob("*")):
        if p.suffix.lower() not in EXT_VIDEO:
            continue
        m = re.fullmatch(r"(?:bloque)?0*(\d+)", p.stem, re.IGNORECASE)
        if m and int(m.group(1)) == numero:
            return p
    return None


def volumen_integrado(ruta: Path) -> float | None:
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(ruta), "-af", "ebur128",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    resumen = err.rsplit("Summary:", 1)[-1] if "Summary:" in err else ""
    m = re.search(r"I:\s+(-?[\d.]+) LUFS", resumen)
    return float(m.group(1)) if m else None
