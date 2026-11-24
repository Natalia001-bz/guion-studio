"""Paso 2: diapositivas generadas desde datos (diapositivas.toml).

Cada diapositiva se dibuja con N ítems visibles. Así salen los "pasos" de la
animación (p0 = solo título; p1 = primer ítem; …) sin recortar ni tapar
imágenes. Un ítem sin `frase` aparece junto con la diapositiva.

Tipos: pregunta · vinetas · numerada · datos · linea_tiempo · comparacion ·
tabla · cita · referencias. Ver docs/diapositivas.md.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .config import Proyecto

# --------------------------------------------------------------------- datos

@dataclass
class Diapositiva:
    id: str
    tipo: str
    bloque: int | None                 # None = referencias (van al final)
    titulo: str = ""
    entra: str | None = None           # frase del guion con que entra
    datos: dict = field(default_factory=dict)
    items: list[dict] = field(default_factory=list)

    @property
    def animados(self) -> list[dict]:
        return [it for it in self.items if it.get("frase")]

    @property
    def pasos(self) -> int:
        """Cantidad de imágenes (p0…pN)."""
        return len(self.animados) + 1


def leer_diapositivas(ruta: Path) -> list[Diapositiva]:
    with open(ruta, "rb") as f:
        datos = tomllib.load(f)
    res = []
    for i, d in enumerate(datos.get("diapositiva", []), 1):
        d = dict(d)
        items = d.pop("items", [])
        if d.get("tipo") == "tabla" and d.get("columnas_frases"):
            # Revelado por columnas: cada columna es un "ítem" animado
            items = [{"columna": j, "frase": fr} for j, fr in enumerate(d["columnas_frases"]) if fr]
        items = [it if isinstance(it, dict) else {"texto": str(it)} for it in items]
        res.append(Diapositiva(
            id=d.pop("id", f"d{i:02d}"), tipo=d.pop("tipo", "vinetas"), bloque=d.pop("bloque", None),
            titulo=d.pop("titulo", ""), entra=d.pop("entra", None), datos=d, items=items))
    return res


# ------------------------------------------------------------------- dibujo

_RESPALDO = {
    "titulo": ["DejaVuSerif.ttf", "georgia.ttf", "Georgia.ttf"],
    "titulo_negrita": ["DejaVuSerif-Bold.ttf", "georgiab.ttf", "Georgia Bold.ttf"],
    "texto": ["DejaVuSans.ttf", "segoeui.ttf", "arial.ttf", "Arial.ttf"],
    "texto_negrita": ["DejaVuSans-Bold.ttf", "segoeuib.ttf", "arialbd.ttf", "Arial Bold.ttf"],
    "texto_cursiva": ["DejaVuSans-Oblique.ttf", "segoeuii.ttf", "ariali.ttf", "Arial Italic.ttf"],
}
_CARPETAS = [Path("/usr/share/fonts/truetype/dejavu"), Path("/usr/share/fonts/TTF"),
             Path("/usr/share/fonts/dejavu"), Path("/mnt/c/Windows/Fonts"), Path("C:/Windows/Fonts"),
             Path("/Library/Fonts"), Path("/System/Library/Fonts/Supplemental")]


class Lienzo:
    """Dibuja diapositivas con el tema y la escala del proyecto."""

    def __init__(self, proy: Proyecto):
        self.t = proy["tema"]
        m = proy["montaje"]
        self.W, self.H = m["ancho"], m["alto"]
        self.s = self.H / 1080
        self.camara = m["camara"]
        cw = int(m["camara_ancho"] * self.s * (self.W / self.H) / (16 / 9))
        ch = int(cw * 9 / 16)
        mg = int(m["camara_margen"] * self.s)
        self.cam = (self.W - mg - cw, self.H - mg - ch, cw, ch)    # x, y, ancho, alto
        self._cache: dict = {}
        self.desborde: list[str] = []

    # utilidades -------------------------------------------------------
    def px(self, v: float) -> int:
        return int(round(v * self.s))

    def fuente(self, rol: str, tam: float) -> ImageFont.FreeTypeFont:
        clave = (rol, tam)
        if clave not in self._cache:
            ruta = self.t.get(f"fuente_{rol}") or self._buscar(rol)
            try:
                self._cache[clave] = ImageFont.truetype(str(ruta), self.px(tam)) if ruta else None
            except OSError:
                self._cache[clave] = None
            if self._cache[clave] is None:
                self._cache[clave] = ImageFont.load_default(self.px(tam))
        return self._cache[clave]

    @staticmethod
    def _buscar(rol: str) -> Path | None:
        for nombre in _RESPALDO[rol]:
            for c in _CARPETAS:
                if (c / nombre).exists():
                    return c / nombre
        return None

    def envolver(self, d, texto, fnt, ancho):
        lineas, actual = [], ""
        for palabra in str(texto).split():
            prueba = (actual + " " + palabra).strip()
            if d.textlength(prueba, font=fnt) <= ancho or not actual:
                actual = prueba
            else:
                lineas.append(actual)
                actual = palabra
        if actual:
            lineas.append(actual)
        return lineas

    def parrafo(self, d, xy, texto, fnt, ancho, color, interlinea=1.3):
        x, y = xy
        for linea in self.envolver(d, texto, fnt, ancho):
            d.text((x, y), linea, font=fnt, fill=color)
            y += int(fnt.size * interlinea)
        return y

    def alto_parrafo(self, d, texto, fnt, ancho, interlinea=1.3):
        return len(self.envolver(d, texto, fnt, ancho)) * int(fnt.size * interlinea)

    # zonas ------------------------------------------------------------
    def zona(self, con_camara=True):
        x0, y0 = self.px(100), self.px(250)
        x1 = (self.cam[0] - self.px(40)) if (self.camara and con_camara) else self.W - self.px(100)
        return x0, y0, x1, self.H - self.px(90)

    def base(self, dia: Diapositiva, con_camara=True):
        t = self.t
        im = Image.new("RGB", (self.W, self.H), t["fondo"])
        d = ImageDraw.Draw(im)
        if t["cabecera"] or dia.datos.get("etiqueta"):
            d.rectangle([0, 0, self.W, self.px(96)], fill=t["primario"])
            d.text((self.px(80), self.px(26)), t["cabecera"], font=self.fuente("texto_negrita", 30), fill=t["blanco"])
            et = dia.datos.get("etiqueta", "")
            if et:
                fb = self.fuente("texto", 30)
                d.text((self.W - self.px(80) - d.textlength(et, font=fb), self.px(26)), et, font=fb,
                       fill=t["cabecera_texto"])
        if dia.titulo:
            d.rectangle([self.px(80), self.px(140), self.px(92), self.px(210)], fill=t["acento"])
            d.text((self.px(118), self.px(132)), dia.titulo, font=self.fuente("titulo_negrita", 60), fill=t["primario"])
        fuente_cita = dia.datos.get("fuente")
        if fuente_cita:
            x0, _, x1, _ = self.zona(con_camara)
            self.parrafo(d, (self.px(80), self.H - self.px(78)), "Fuente: " + fuente_cita,
                         self.fuente("texto_cursiva", 22), x1 - self.px(80), t["tenue"], 1.2)
        if self.camara and con_camara:
            x, y, w, h = self.cam
            d.rounded_rectangle([x - self.px(6), y - self.px(6), x + w + self.px(6), y + h + self.px(6)],
                                self.px(14), outline=t["linea"], width=max(2, self.px(3)))
        return im, d

    def revisar_desborde(self, dia, y, limite):
        if y > limite and dia.id not in self.desborde:
            self.desborde.append(dia.id)

    # render -----------------------------------------------------------
    def dibujar(self, dia: Diapositiva, visibles: int) -> Image.Image:
        """Imagen con los `visibles` primeros ítems animados (los fijos siempre)."""
        n = 0
        mostrar = []
        for it in dia.items:
            if it.get("frase"):
                n += 1
                mostrar.append(n <= visibles)
            else:
                mostrar.append(True)
        con_camara = dia.tipo != "referencias"
        im, d = self.base(dia, con_camara)
        getattr(self, "_" + dia.tipo, self._vinetas)(dia, d, mostrar)
        return im

    def _pregunta(self, dia, d, mostrar):
        t, (x0, y0, x1, y1) = self.t, self.zona()
        ancho = self.W - self.px(200)
        y = self.parrafo(d, (self.px(118), self.px(300)), dia.datos.get("texto", ""),
                         self.fuente("titulo", 70), ancho, t["tinta"], 1.25) + self.px(40)
        for it, ver in zip(dia.items, mostrar):
            if ver:
                self.parrafo(d, (self.px(118), y), it.get("texto", ""), self.fuente("texto", 40), x1 - self.px(118), t["tenue"])
            y += self.alto_parrafo(d, it.get("texto", ""), self.fuente("texto", 40), x1 - self.px(118)) + self.px(16)
        self.revisar_desborde(dia, y, y1)

    def _cita(self, dia, d, mostrar):
        t, (x0, y0, x1, y1) = self.t, self.zona()
        y = self.parrafo(d, (self.px(118), self.px(300)), "«" + dia.datos.get("texto", "") + "»",
                         self.fuente("titulo", 60), x1 - self.px(118), t["tinta"], 1.25)
        if dia.datos.get("autor"):
            d.text((self.px(118), y + self.px(30)), "— " + dia.datos["autor"], font=self.fuente("texto_negrita", 38), fill=t["acento"])
        self._vinetas(dia, d, mostrar, y + self.px(110))

    def _vinetas(self, dia, d, mostrar, y=None):
        t, (x0, y0, x1, y1) = self.t, self.zona()
        y = y if y is not None else y0
        if dia.datos.get("subtitulo"):
            y = self.parrafo(d, (x0, y), dia.datos["subtitulo"], self.fuente("titulo_negrita", 52), x1 - x0,
                             t["acento"]) + self.px(24)
        tam = dia.datos.get("tamano", 42)
        fv, fd = self.fuente("texto", tam), self.fuente("texto_negrita", tam - 2)
        for it, ver in zip(dia.items, mostrar):
            txt = it.get("texto", "")
            if it.get("estilo") == "destacado":
                y += self.px(30)
                if ver:
                    self.parrafo(d, (x0, y), txt, fd, x1 - x0, t["primario"])
                y += self.alto_parrafo(d, txt, fd, x1 - x0) + self.px(18)
                continue
            if ver:
                r = self.px(8)
                cy = y + int(fv.size * 0.62)
                d.ellipse([x0, cy - r, x0 + 2 * r, cy + r], fill=t["acento"])
                self.parrafo(d, (x0 + self.px(40), y), txt, fv, x1 - x0 - self.px(40), t["tinta"])
            y += self.alto_parrafo(d, txt, fv, x1 - x0 - self.px(40)) + self.px(22)
        self.revisar_desborde(dia, y, y1)

    def _numerada(self, dia, d, mostrar):
        t, (x0, y0, x1, y1) = self.t, self.zona()
        y = y0
        ft, fx = self.fuente("texto_negrita", 40), self.fuente("texto", 34)
        for k, (it, ver) in enumerate(zip(dia.items, mostrar), 1):
            alto = self.px(56) + self.alto_parrafo(d, it.get("texto", ""), fx, x1 - x0 - self.px(100))
            if ver:
                c = self.px(70)
                d.ellipse([x0, y, x0 + c, y + c], fill=t["acento"])
                fn = self.fuente("texto_negrita", 42)
                num = str(it.get("numero", k))
                d.text((x0 + (c - d.textlength(num, font=fn)) / 2, y + self.px(6)), num, font=fn, fill=t["blanco"])
                d.text((x0 + self.px(100), y), it.get("titulo", ""), font=ft, fill=t["primario"])
                self.parrafo(d, (x0 + self.px(100), y + self.px(56)), it.get("texto", ""), fx, x1 - x0 - self.px(100), t["tinta"])
            y += max(alto, self.px(80)) + self.px(30)
        self.revisar_desborde(dia, y, y1)

    def _datos(self, dia, d, mostrar):
        t, (x0, y0, x1, y1) = self.t, self.zona()
        y = y0
        if dia.datos.get("subtitulo"):
            d.text((x0, y), dia.datos["subtitulo"], font=self.fuente("texto_negrita", 38), fill=t["primario"])
            y += self.px(70)
        por_fila = dia.datos.get("por_fila", 3)
        ancho = (x1 - x0) // por_fila
        fc, fr = self.fuente("titulo_negrita", 96), self.fuente("texto", 30)
        alto_fila = 0
        for k, (it, ver) in enumerate(zip(dia.items, mostrar)):
            col = k % por_fila
            if col == 0 and k:
                y += alto_fila + self.px(40)
                alto_fila = 0
            x = x0 + col * ancho
            alto = self.px(118) + self.alto_parrafo(d, it.get("rotulo", ""), fr, ancho - self.px(40), 1.2)
            alto_fila = max(alto_fila, alto)
            if ver:
                cifra, tam = str(it.get("cifra", "")), 96
                fnt = fc
                while tam > 40 and d.textlength(cifra, font=fnt) > ancho - self.px(40):
                    tam -= 6
                    fnt = self.fuente("titulo_negrita", tam)
                d.text((x, y + (fc.size - fnt.size)), cifra, font=fnt, fill=t["acento"])
                self.parrafo(d, (x, y + self.px(118)), it.get("rotulo", ""), fr, ancho - self.px(40), t["tenue"], 1.2)
        self.revisar_desborde(dia, y + alto_fila, y1)

    def _linea_tiempo(self, dia, d, mostrar):
        t, (x0, y0, x1, y1) = self.t, self.zona()
        y = y0
        ff, ft = self.fuente("texto_negrita", 36), self.fuente("texto", 36)
        col = self.px(240)
        for it, ver in zip(dia.items, mostrar):
            alto = self.alto_parrafo(d, it.get("texto", ""), ft, x1 - x0 - col)
            if ver:
                d.text((x0, y), str(it.get("fecha", "")), font=ff, fill=t["acento"])
                self.parrafo(d, (x0 + col, y), it.get("texto", ""), ft, x1 - x0 - col, t["tinta"])
            y += alto + self.px(30)
        self.revisar_desborde(dia, y, y1)

    def _comparacion(self, dia, d, mostrar):
        t, (x0, y0, x1, y1) = self.t, self.zona()
        n = max(1, len(dia.items))
        gap = self.px(40)
        ancho = (x1 - x0 - gap * (n - 1)) // n
        fti, ftx = self.fuente("titulo_negrita", 52), self.fuente("texto", 38)
        altos = [self.px(120) + self.alto_parrafo(d, it.get("texto", ""), ftx, ancho - self.px(60)) for it in dia.items]
        alto = max(altos + [self.px(300)])
        y = y0 + self.px(10)
        colores = [t["primario"], t["acento"], t["tinta"]]
        for k, (it, ver) in enumerate(zip(dia.items, mostrar)):
            x = x0 + k * (ancho + gap)
            if ver:
                d.rounded_rectangle([x, y, x + ancho, y + alto], self.px(16), fill=t["claro"])
                d.text((x + self.px(30), y + self.px(28)), it.get("titulo", ""), font=fti, fill=colores[k % 3])
                self.parrafo(d, (x + self.px(30), y + self.px(110)), it.get("texto", ""), ftx, ancho - self.px(60), t["tinta"])
        self.revisar_desborde(dia, y + alto, y1)

    def _tabla(self, dia, d, mostrar):
        t, (x0, y0, x1, y1) = self.t, self.zona()
        cab = dia.datos.get("cabecera", [])
        por_columnas = bool(dia.datos.get("columnas_frases"))
        filas = dia.datos.get("filas") if por_columnas else [it.get("celdas", []) for it in dia.items]
        ncol = max([len(cab)] + [len(f) for f in filas] + [1])
        tam = dia.datos.get("tamano", 28)
        # anchos proporcionales al texto más largo de cada columna (mínimo 12 %)
        largo = [max([len(str(cab[j])) if j < len(cab) else 0] + [len(str(f[j])) if j < len(f) else 0 for f in filas] + [4])
                 for j in range(ncol)]
        total = x1 - x0
        pesos = [max(l / sum(largo), 0.12) for l in largo]
        anchos = [int(total * p / sum(pesos)) for p in pesos]
        if por_columnas:
            visibles_col = {0} | {it["columna"] for it, ver in zip(dia.items, mostrar) if ver}
            filas_ver = [True] * len(filas)
        else:
            visibles_col = set(range(ncol))
            filas_ver = mostrar
        y = y0
        todas = ([cab] if cab else []) + filas
        ver_filas = ([True] if cab else []) + list(filas_ver)
        for i, (fila, ver) in enumerate(zip(todas, ver_filas)):
            es_cab = bool(cab) and i == 0
            celdas, alto = [], 0
            for j in range(ncol):
                txt = str(fila[j]) if j < len(fila) else ""
                fnt = self.fuente("texto_negrita" if es_cab or j == 0 else "texto", tam)
                ls = self.envolver(d, txt, fnt, anchos[j] - self.px(36))
                celdas.append((ls, fnt))
                alto = max(alto, len(ls) * int(fnt.size * 1.3) + self.px(32))
            fondo = t["primario"] if es_cab else (t["claro"] if i % 2 == 0 else t["fondo"])
            if ver:
                d.rectangle([x0, y, x0 + sum(anchos), y + alto], fill=fondo)
                x = x0
                for j, (ls, fnt) in enumerate(celdas):
                    if j in visibles_col:
                        yy = y + self.px(16)
                        for l in ls:
                            d.text((x + self.px(18), yy), l, font=fnt, fill=t["blanco"] if es_cab else t["tinta"])
                            yy += int(fnt.size * 1.3)
                    x += anchos[j]
            y += alto
        self.revisar_desborde(dia, y, y1)

    def _referencias(self, dia, d, mostrar):
        t = self.t
        x0, y = self.px(80), self.px(250)
        fn, fi = self.fuente("texto", 21), self.fuente("texto_cursiva", 21)
        for ref in dia.datos.get("lineas", []):
            y = self._ref(d, x0, y, ref, self.W - 2 * x0, fn, fi) + self.px(8)
        self.revisar_desborde(dia, y, self.H - self.px(40))

    def _ref(self, d, x, y, texto, ancho, fn, fi):
        """Referencia con sangría francesa; *texto* va en cursiva."""
        cx, cur, alto = x, False, int(fn.size * 1.35)
        for palabra in texto.split(" "):
            if not palabra:
                continue
            trozos = []
            for k, seg in enumerate(palabra.split("*")):
                if k:
                    cur = not cur
                if seg:
                    trozos.append((seg, cur))
            ancho_p = sum(d.textlength(sg, font=fi if c else fn) for sg, c in trozos)
            if cx + ancho_p > x + ancho:
                y += alto
                cx = x + self.px(40)
            for sg, c in trozos:
                fnt = fi if c else fn
                d.text((cx, y), sg, font=fnt, fill=self.t["tinta"])
                cx += d.textlength(sg, font=fnt)
            cx += d.textlength(" ", font=fn)
        return y + alto


# ---------------------------------------------------------------- generación

def paginar_referencias(proy: Proyecto, dias: list[Diapositiva], por_pagina: int = 12) -> list[Diapositiva]:
    """Una diapositiva `referencias` con `archivo` o `lineas` se divide en páginas."""
    res = []
    for dia in dias:
        if dia.tipo != "referencias":
            res.append(dia)
            continue
        lineas = list(dia.datos.get("lineas", []))
        if dia.datos.get("archivo"):
            lineas += [l.strip() for l in (proy.carpeta / dia.datos["archivo"]).read_text(encoding="utf-8").splitlines() if l.strip()]
        paginas = [lineas[i:i + por_pagina] for i in range(0, len(lineas), por_pagina)] or [[]]
        for k, pag in enumerate(paginas, 1):
            datos = {kk: v for kk, v in dia.datos.items() if kk not in ("archivo", "lineas")}
            datos["lineas"] = pag
            titulo = dia.titulo or "Referencias"
            if len(paginas) > 1:
                titulo += f" ({k} de {len(paginas)})"
            res.append(Diapositiva(f"{dia.id}_{k}", "referencias", None, titulo, None, datos, []))
    return res


def cargar(proy: Proyecto) -> list[Diapositiva]:
    return paginar_referencias(proy, leer_diapositivas(proy.ruta("diapositivas")))


def generar(proy: Proyecto, carpeta: Path | None = None) -> tuple[Path, list[str]]:
    """Dibuja todos los pasos. Devuelve la carpeta y las diapositivas que se desbordan."""
    carpeta = carpeta or proy.carpeta / "salida" / "diapositivas"
    carpeta.mkdir(parents=True, exist_ok=True)
    lz = Lienzo(proy)
    for dia in cargar(proy):
        for k in range(dia.pasos):
            lz.dibujar(dia, k).save(carpeta / f"{dia.id}_p{k}.png")
    return carpeta, lz.desborde
