"""Configuración del proyecto (proyecto.toml) con valores por defecto probados."""
from __future__ import annotations

import copy
import tomllib
from pathlib import Path

# Valores que funcionaron en un video real (webcam a contraluz, voz limpia, 9 min).
POR_DEFECTO = {
    "proyecto": {
        "titulo": "Mi video",
        "guion": "guion.md",
        "diapositivas": "diapositivas.toml",
        "clips": "clips",              # bloque1.webm, bloque2.mp4… (o 1.webm, 2.webm…)
        "preparados": "preparados",
        "salida": "salida/video.mp4",
        "ajustes": "ajustes.toml",     # correcciones manuales de tiempos (opcional)
    },
    "preparar": {
        "umbral_db": -38,              # por debajo, silencio
        "silencio_min": 0.4,
        "unir": 0.3,                   # silencios separados por menos de esto cuentan como uno
        "margen_inicio": 0.25,
        "margen_fin": 0.4,
        "pausa_larga": 0.7,            # pausas internas más largas se acortan…
        "pausa_queda": 0.35,           # …a esta duración
        "velocidad": 1.05,             # 1,05 no se nota; desde 1,10 suena apurado
        "imagen": "suave",             # suave | ninguna | <cadena de filtros FFmpeg>
        "audio": "limpio",             # limpio | ninguno | <cadena de filtros FFmpeg>
        "volumen_lufs": -16,
        "fps": 30,
        "crf": 18,
    },
    "montaje": {
        "ancho": 1920,
        "alto": 1080,
        "camara": True,
        "camara_ancho": 464,           # recuadro en la esquina inferior derecha
        "camara_margen": 48,
        "intro_camara": 6.0,           # segundos de cámara completa al inicio
        "rotulo_nombre": "",
        "rotulo_detalle": "",
        "transicion": 0.5,             # fundido entre diapositivas y aparición de ítems
        "fundido_bloque": 0.4,
        "seg_referencia": 6.0,
        "ajustar_a_frases": True,      # lleva cada cambio al inicio de frase más cercano
        "ventana_ajuste": 2.5,
    },
    "tema": {
        "cabecera": "",
        "fondo": "#F5F2EC",
        "tinta": "#1E2A38",
        "primario": "#1F3A5F",
        "acento": "#B5502F",
        "tenue": "#5B6573",
        "linea": "#D6D0C4",
        "claro": "#E9E3D7",
        "blanco": "#FFFFFF",
        "cabecera_texto": "#C9D3E0",
        # Rutas a .ttf; vacías = se buscan fuentes del sistema (DejaVu como respaldo)
        "fuente_titulo": "",
        "fuente_titulo_negrita": "",
        "fuente_texto": "",
        "fuente_texto_negrita": "",
        "fuente_texto_cursiva": "",
    },
}


def _fusionar(base: dict, extra: dict) -> dict:
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _fusionar(base[k], v)
        else:
            base[k] = v
    return base


class Proyecto:
    """Configuración + rutas resueltas respecto de la carpeta del proyecto."""

    def __init__(self, carpeta: str | Path = ".", archivo: str = "proyecto.toml"):
        self.carpeta = Path(carpeta).resolve()
        self.cfg = copy.deepcopy(POR_DEFECTO)
        ruta = self.carpeta / archivo
        if ruta.exists():
            with open(ruta, "rb") as f:
                _fusionar(self.cfg, tomllib.load(f))

    def __getitem__(self, seccion: str) -> dict:
        return self.cfg[seccion]

    def ruta(self, clave: str) -> Path:
        return self.carpeta / self.cfg["proyecto"][clave]

    def ajustes(self) -> dict:
        r = self.ruta("ajustes")
        if not r.exists():
            return {}
        with open(r, "rb") as f:
            return tomllib.load(f).get("tiempos", {})
