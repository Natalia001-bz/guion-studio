"""Lectura del guion en Markdown.

Formato (el mismo que usa el teleprompter):

    # Título del video            (opcional)
    ## 1. Apertura                 cada `##` abre un bloque = un clip
    > Nota para quien graba         no se lee en voz alta
    [Pantalla: …]                  indicación de producción; no se lee
    Una línea = una respiración.
                                   línea en blanco = pausa corta
    ···                            pausa larga (también vale `---`)
    **énfasis** y [[pronunciación]] (la pronunciación no se lee)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_BLOQUE = re.compile(r"^##\s+(?:(\d+)[.)]?\s*)?(.*)$")
_PAUSA_LARGA = {"···", "...", "---", "—"}


@dataclass
class Bloque:
    numero: int
    titulo: str
    lineas: list[str] = field(default_factory=list)   # tal como se escriben (con marcas)

    @property
    def texto_hablado(self) -> str:
        """Solo lo que se pronuncia: sin notas, marcas ni pronunciaciones."""
        partes = []
        for l in self.lineas:
            if l.strip() in _PAUSA_LARGA or not l.strip():
                continue
            partes.append(limpiar(l))
        return " ".join(p for p in partes if p)

    @property
    def palabras(self) -> int:
        return len(self.texto_hablado.split())


def limpiar(linea: str) -> str:
    linea = re.sub(r"\[\[.*?\]\]", "", linea)
    linea = linea.replace("**", "")
    return re.sub(r"\s+", " ", linea).strip()


def leer_guion(ruta: str | Path) -> list[Bloque]:
    texto = Path(ruta).read_text(encoding="utf-8")
    return analizar(texto)


def analizar(texto: str) -> list[Bloque]:
    bloques: list[Bloque] = []
    actual: Bloque | None = None
    for crudo in texto.splitlines():
        linea = crudo.rstrip()
        m = _BLOQUE.match(linea)
        if m:
            numero = int(m.group(1)) if m.group(1) else len(bloques) + 1
            actual = Bloque(numero, m.group(2).strip())
            bloques.append(actual)
            continue
        if actual is None:
            continue                                   # texto antes del primer bloque
        s = linea.strip()
        if s.startswith(">") or (s.startswith("[") and not s.startswith("[[")):
            continue                                   # notas e indicaciones de producción
        actual.lineas.append(s)
    for b in bloques:                                  # quita líneas en blanco sobrantes
        while b.lineas and not b.lineas[0]:
            b.lineas.pop(0)
        while b.lineas and not b.lineas[-1]:
            b.lineas.pop()
    return bloques


def posicion_frase(bloque: Bloque, frase: str) -> float | None:
    """Fracción (0-1) del bloque en que empieza la frase, medida en palabras habladas.

    La búsqueda ignora mayúsculas, signos y marcas, para que la frase de la
    diapositiva no tenga que copiarse con la puntuación exacta del guion.
    """
    norm = lambda s: re.sub(r"[^\wáéíóúüñ]+", " ", s.lower()).split()
    palabras = norm(bloque.texto_hablado)
    buscada = norm(frase)
    if not buscada or not palabras:
        return None
    n = len(buscada)
    for i in range(len(palabras) - n + 1):
        if palabras[i:i + n] == buscada:
            return i / len(palabras)
    return None
