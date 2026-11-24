# Formato del guion

El guion es un archivo Markdown. Lo leen tanto el teleprompter (para mostrarlo) como la herramienta de línea de comandos (para estimar duraciones y sincronizar las diapositivas), con las mismas reglas.

```markdown
# Título del video

Todo lo que va antes del primer bloque es para ti; no se lee.

## 1. Apertura

> Nota para quien graba: se ve tenue en el teleprompter y no se cuenta.
[Pantalla: portada]

Hola, y bienvenidos.

Hoy les cuento cómo preparar una exposición
**sin perder horas editando**.
···
Gracias a Dieter Nohlen [[nólen]] por la idea.
```

| Marca | Significado |
|---|---|
| `## 1. Título` | Abre un bloque. Cada bloque se graba como un clip (`bloque1.webm`). El número es opcional. |
| Una línea | Una respiración. Corta donde va la coma o el punto, para no tropezar con la puntuación. |
| Línea en blanco | Pausa corta. |
| `···`, `...` o `---` | Pausa larga: un momento para mirar a la cámara. |
| `**texto**` | Énfasis (se ve en dorado). |
| `[[texto]]` | Ayuda de pronunciación. Se ve en gris y no se lee ni se cuenta. |
| `> nota` | Nota para quien graba. |
| `[Pantalla: …]` | Indicación de producción. No aparece en el teleprompter. |

## Consejos de escritura para la voz

- **Frases de 8 a 15 palabras.** Las oraciones largas se cortan en varias líneas, cada una con sentido propio.
- **Cifras como se dicen.** «Cero coma ochenta», «ochenta y cuatro por ciento». Evita leer «0,80» en voz alta.
- **Nombres difíciles con su pronunciación**: `Mainwaring [[méinuering]]`.
- **Ritmo:** 135 palabras por minuto es un ritmo natural de exposición. `guion-studio guion` calcula la duración de cada bloque.
- **Bloques de 30 segundos a 3 minutos.** Si te equivocas, repites solo ese bloque.
