import shutil
from pathlib import Path

from guion_studio.config import Proyecto
from guion_studio.diapositivas import cargar, generar

PLANTILLA = Path(__file__).parents[1] / "guion_studio" / "plantilla"


def proyecto(tmp_path):
    shutil.copytree(PLANTILLA, tmp_path, dirs_exist_ok=True)
    cfg = tmp_path / "proyecto.toml"
    cfg.write_text(cfg.read_text(encoding="utf-8").replace("[montaje]", "[montaje]\nancho = 960\nalto = 540"),
                   encoding="utf-8")
    return Proyecto(tmp_path)


def test_pasos_por_diapositiva(tmp_path):
    proy = proyecto(tmp_path)
    dias = {d.id: d for d in cargar(proy)}
    assert dias["metodo"].pasos == 4          # p0 + 3 ítems animados
    assert dias["pregunta"].pasos == 2
    assert "referencias_1" in dias and dias["referencias_1"].bloque is None


def test_genera_imagenes_del_tamano_configurado_sin_desbordes(tmp_path):
    from PIL import Image
    proy = proyecto(tmp_path)
    carpeta, desborde = generar(proy)
    imgs = sorted(carpeta.glob("*.png"))
    assert len(imgs) == sum(d.pasos for d in cargar(proy))
    assert Image.open(imgs[0]).size == (960, 540)
    assert desborde == []


def test_paso_cero_y_final_son_distintos(tmp_path):
    from PIL import ImageChops, Image
    proy = proyecto(tmp_path)
    carpeta, _ = generar(proy)
    p0 = Image.open(carpeta / "metodo_p0.png").convert("RGB")
    p3 = Image.open(carpeta / "metodo_p3.png").convert("RGB")
    assert ImageChops.difference(p0, p3).getbbox() is not None


TODOS = '''
[[diapositiva]]
id = "a"
bloque = 1
tipo = "cita"
titulo = "Cita"
texto = "Una frase memorable."
autor = "Autora"
[[diapositiva]]
id = "b"
bloque = 1
tipo = "vinetas"
titulo = "Viñetas"
subtitulo = "Subtítulo"
items = [{ texto = "Uno", frase = "x" }, { texto = "Conclusión", estilo = "destacado", frase = "y" }]
[[diapositiva]]
id = "c"
bloque = 1
tipo = "linea_tiempo"
titulo = "Línea"
items = [{ fecha = "2020", texto = "Hecho", frase = "x" }, { fecha = "2021", texto = "Otro", frase = "y" }]
[[diapositiva]]
id = "d"
bloque = 1
tipo = "tabla"
titulo = "Columnas"
cabecera = ["", "A", "B"]
filas = [["Fila", "1", "2"]]
columnas_frases = ["", "x", "y"]
[[diapositiva]]
id = "e"
tipo = "referencias"
lineas = ["Autora, A. (2020). *Obra*. Editorial."]
'''


def test_dibuja_todos_los_tipos(tmp_path):
    proy = proyecto(tmp_path)
    (tmp_path / "diapositivas.toml").write_text(TODOS, encoding="utf-8")
    carpeta, desborde = generar(proy)
    dias = {d.id: d for d in cargar(proy)}
    assert dias["d"].pasos == 3               # columna 0 fija + 2 columnas animadas
    assert dias["b"].pasos == 3
    assert (carpeta / "e_1_p0.png").exists()
    assert desborde == []
