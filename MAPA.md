# Mapa del repositorio

Para orientarse sin leer todo el código.

```
guion-studio/
├── teleprompter/              Aplicación web (sin compilación; GitHub Pages publica esta carpeta)
│   ├── index.html             Estructura: barra, visor, cámara, diálogos de guion y ayuda
│   ├── css/base.css           Tokens (colores, tipografía, espaciado) y estilos de etiquetas
│   ├── css/layout.css         Zonas: barra, visor, cámara; adaptación a pantallas angostas
│   ├── css/components.css     Botones, franja, texto del guion, medidor, diálogos
│   ├── js/guion.js            Lector del guion (navegador y Node; mismas reglas que guion.py)
│   ├── js/ejemplo.js          Guion de demostración (generado; no editar a mano)
│   ├── js/grabadora.js        Cámara, medidor de micrófono y MediaRecorder
│   └── js/app.js              Lectura, controles, teclado, grabación por bloque
├── guion_studio/              Paquete de Python (CLI `guion-studio`)
│   ├── cli.py                 Comandos: iniciar, guion, preparar, diapositivas, plan, montar, revisar
│   ├── config.py              proyecto.toml con valores por defecto probados
│   ├── guion.py               Lector del guion y búsqueda de frases
│   ├── medios.py              FFmpeg: duración, silencios, inicios de frase, volumen
│   ├── preparar.py            Recorte de silencios, imagen, audio y velocidad
│   ├── diapositivas.py        Nueve tipos de diapositiva y sus pasos de animación (Pillow)
│   ├── montar.py              Tiempos, pista de diapositivas por tramos y montaje final
│   ├── revisar.py             Hoja de fotogramas, LUFS y desfase
│   └── plantilla/             Proyecto de ejemplo que copia `guion-studio iniciar`
├── tests/                     pytest (Python) y node --test (lector del teleprompter)
├── scripts/sincronizar_ejemplo.py   Copia la plantilla al guion de ejemplo del teleprompter
├── docs/                      Formato del guion, diapositivas, configuración, decisiones
└── .github/workflows/         Pruebas en cada cambio y publicación del teleprompter
```

## Flujo de datos

`guion.md` → teleprompter → `clips/` → `preparar` → `preparados/` → `montar` (+ `diapositivas.toml` → `salida/diapositivas/`) → `salida/video.mp4` → `revisar`.

## Dónde tocar

| Quiero… | Archivo |
|---|---|
| Un tipo de diapositiva nuevo | `diapositivas.py`: método `_<tipo>` en `Lienzo` + fila en `docs/diapositivas.md` |
| Cambiar los valores por defecto | `config.py` (`POR_DEFECTO`) + `docs/configuracion.md` |
| Una marca nueva en el guion | `guion.py` **y** `teleprompter/js/guion.js` (+ pruebas de ambos) |
| Un atajo de teclado | `teleprompter/js/app.js` (bloque `keydown`) + diálogo de ayuda en `index.html` |
