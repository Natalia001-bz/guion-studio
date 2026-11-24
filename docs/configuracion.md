# Configuración (`proyecto.toml`)

Solo hace falta escribir lo que cambia; el resto toma estos valores por defecto, que funcionaron en un video real grabado con webcam.

## `[proyecto]`

| Clave | Por defecto | Uso |
|---|---|---|
| `guion` | `guion.md` | Guion en Markdown. |
| `diapositivas` | `diapositivas.toml` | Diapositivas como datos. |
| `clips` | `clips` | Clips originales: `bloque1.webm`, `bloque02.mp4` o `1.webm`. |
| `preparados` | `preparados` | Salida de `preparar`; `montar` los usa si existen. |
| `salida` | `salida/video.mp4` | Video final. |
| `ajustes` | `ajustes.toml` | Correcciones manuales de tiempos. |

## `[preparar]`

| Clave | Por defecto | Uso |
|---|---|---|
| `umbral_db` | `-38` | Por debajo de este nivel se considera silencio. Súbelo (−35) si hay ruido de fondo. |
| `silencio_min` | `0.4` | Duración mínima para detectar un silencio. |
| `unir` | `0.3` | Dos silencios separados por menos de esto (un clic, una respiración) cuentan como uno. |
| `margen_inicio` / `margen_fin` | `0.25` / `0.4` | Silencio que se conserva al inicio y al final del clip. |
| `pausa_larga` / `pausa_queda` | `0.7` / `0.35` | Las pausas internas más largas que `pausa_larga` quedan en `pausa_queda`. |
| `velocidad` | `1.05` | 1,05 no se nota; desde 1,10 suena apurado. 1 = sin cambio. |
| `imagen` | `suave` | `suave` (aclara tonos medios, nitidez leve), `ninguna` o una cadena de filtros FFmpeg propia. |
| `audio` | `limpio` | `limpio` (filtro de graves y compresión suave), `ninguno` o filtros FFmpeg propios. |
| `volumen_lufs` | `-16` | Volumen integrado de salida (estándar para web). |
| `fps`, `crf` | `30`, `18` | Cuadros por segundo y calidad H.264 (menor = mejor). |

## `[montaje]`

| Clave | Por defecto | Uso |
|---|---|---|
| `ancho`, `alto` | `1920`, `1080` | Resolución del video y de las diapositivas. |
| `camara` | `true` | Cámara en la esquina. Con `false`, solo diapositivas y voz. |
| `camara_ancho`, `camara_margen` | `464`, `48` | Tamaño y margen del recuadro (en escala 1080p). |
| `intro_camara` | `6.0` | Segundos de cámara completa al inicio, con el rótulo. |
| `rotulo_nombre`, `rotulo_detalle` | vacíos | Rótulo inferior durante la introducción. |
| `transicion` | `0.5` | Fundido entre diapositivas y aparición de ítems. |
| `fundido_bloque` | `0.4` | Fundido de entrada y salida de cada bloque. |
| `seg_referencia` | `6.0` | Segundos por página de referencias. |
| `ajustar_a_frases`, `ventana_ajuste` | `true`, `2.5` | Ajuste de los tiempos al inicio de frase más cercano. |

## `[tema]`

| Clave | Uso |
|---|---|
| `cabecera` | Texto de la banda superior (vacío = sin banda, salvo que la diapositiva tenga `etiqueta`). |
| `fondo`, `tinta`, `primario`, `acento`, `tenue`, `linea`, `claro`, `blanco`, `cabecera_texto` | Colores en hexadecimal. |
| `fuente_titulo`, `fuente_titulo_negrita`, `fuente_texto`, `fuente_texto_negrita`, `fuente_texto_cursiva` | Rutas a archivos `.ttf`. Vacías = fuentes del sistema. |
