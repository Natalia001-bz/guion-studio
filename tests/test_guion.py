from guion_studio.guion import analizar, posicion_frase

GUION = """# Título
Texto previo que no es parte de ningún bloque.

## 1. Apertura
> Nota para quien graba
[Pantalla: portada]
Hola, **bienvenidos**.

Soy Nohlen [[nólen]].
···
Fin del bloque.

## Desarrollo
Primero, el guion.
Segundo, la grabación.
"""


def test_bloques_y_numeracion():
    b = analizar(GUION)
    assert [x.numero for x in b] == [1, 2]
    assert b[0].titulo == "Apertura"
    assert b[1].titulo == "Desarrollo"


def test_texto_hablado_sin_notas_ni_marcas():
    b = analizar(GUION)[0]
    assert b.texto_hablado == "Hola, bienvenidos. Soy Nohlen . Fin del bloque."
    assert "Pantalla" not in b.texto_hablado
    assert b.palabras == 8


def test_posicion_frase_ignora_signos_y_mayusculas():
    b = analizar(GUION)[1]
    assert posicion_frase(b, "primero el guion") == 0.0
    assert posicion_frase(b, "SEGUNDO, LA GRABACIÓN") == 0.5
    assert posicion_frase(b, "tercero") is None


def test_ejemplo_del_teleprompter_sincronizado():
    """teleprompter/js/ejemplo.js debe ser copia de la plantilla (scripts/sincronizar_ejemplo.py)."""
    import json
    from pathlib import Path
    raiz = Path(__file__).parents[1]
    js = (raiz / "teleprompter" / "js" / "ejemplo.js").read_text(encoding="utf-8")
    md = (raiz / "guion_studio" / "plantilla" / "guion.md").read_text(encoding="utf-8")
    assert json.loads(js.split("=", 1)[1].strip().rstrip(";")) == md
