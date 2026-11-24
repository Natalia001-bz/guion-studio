# Cambios

## Próximo

- Pendiente: la grabación automática se detiene 1,5 s después de que el final del texto cruza la franja; si se lee por encima de la franja, se cortan las últimas palabras. Se hará que se detenga por silencio del micrófono, con un aviso cancelable y una espera configurable.

## 0.1.0 · 2026-11-24

Primera versión pública, construida a partir de la producción de un video universitario real.

- Teleprompter web: guion en Markdown, ritmo en palabras por minuto, franja de lectura, espejo, pantalla completa, cámara con medidor de micrófono y grabación por bloque (`bloqueN.webm`).
- CLI `guion-studio`: `iniciar`, `guion`, `preparar`, `diapositivas`, `plan`, `montar` y `revisar`.
- Nueve tipos de diapositiva generados desde TOML, con aparición de ítems sincronizada con la voz.
- Probado con FFmpeg 6.1 (Ubuntu 24.04) y 8.0 (Ubuntu 26.04, integración continua).
- Pruebas: 15 en Python (incluido un montaje de extremo a extremo con clips sintéticos) y 4 en Node.
