"""Prueba de extremo a extremo con clips sintéticos (requiere FFmpeg con rubberband)."""
import shutil
import subprocess
from pathlib import Path

import pytest

from guion_studio.config import Proyecto
from guion_studio.medios import duracion, duraciones_pistas
from guion_studio.montar import montar, planear as planear_montaje
from guion_studio.preparar import planear, procesar
from guion_studio.revisar import informe

PLANTILLA = Path(__file__).parents[1] / "guion_studio" / "plantilla"
pytestmark = [pytest.mark.lento,
              pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg no está instalado")]


def clip_sintetico(ruta: Path, segundos: float):
    """Video de prueba + "voz" (tono) con 1 s de silencio al inicio, 2 s al final y una pausa larga."""
    voz = f"sin(2*PI*220*t)*0.3*between(t,1,{segundos - 2})*not(between(t,4,5.5))"
    subprocess.run(["ffmpeg", "-y", "-v", "error",
                    "-f", "lavfi", "-i", f"testsrc2=size=640x360:rate=30:duration={segundos}",
                    "-f", "lavfi", "-i", f"aevalsrc='{voz}':s=48000:d={segundos}",
                    "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "libopus", "-shortest", str(ruta)],
                   check=True)


@pytest.fixture(scope="module")
def proy(tmp_path_factory):
    carpeta = tmp_path_factory.mktemp("proyecto")
    shutil.copytree(PLANTILLA, carpeta, dirs_exist_ok=True)
    texto = (carpeta / "proyecto.toml").read_text(encoding="utf-8")
    (carpeta / "proyecto.toml").write_text(texto.replace("intro_camara = 6.0", "intro_camara = 2.0").replace("[montaje]", "[montaje]\nancho = 640\nalto = 360"),
                                           encoding="utf-8")
    (carpeta / "clips").mkdir()
    for n, seg in ((1, 9), (2, 12), (3, 10)):
        clip_sintetico(carpeta / "clips" / f"{n}.mkv", seg)
    return Proyecto(carpeta)


def test_preparar_recorta_silencios(proy):
    planes = planear(proy, [1, 2, 3])
    p = planes[1]                                   # 12 s con 1 s inicial, 2 s finales y pausa de 1,5 s
    assert p.tramos[0][0] > 0.6                     # cortó el silencio inicial
    assert p.tramos[-1][1] < 10.6                   # cortó el silencio final
    assert len(p.tramos) == 2                       # acortó la pausa larga
    for pl in planes:
        out = procesar(proy, pl)
        assert abs(duracion(out) - pl.neto) < 0.3


def test_plan_ubica_eventos_en_orden(proy):
    plan, refs, avisos = planear_montaje(proy)
    assert not [a for a in avisos if "no encontré" in a]
    for _, _, dur, eventos in plan:
        tiempos = [e.t for e in eventos]
        assert tiempos == sorted(tiempos)
        assert all(0 <= t < dur for t in tiempos)
    assert len(refs) == 1


def test_montaje_final(proy):
    salida = montar(proy, avisar=lambda *_: None)
    assert salida.exists()
    pistas = duraciones_pistas(salida)
    esperado = sum(duracion(proy.ruta("preparados") / f"bloque{n}.mp4") for n in (1, 2, 3)) + 6.0
    assert abs(pistas["video"] - esperado) < 1.0
    r = informe(salida)
    assert r["desfase_final_s"] < 0.5
