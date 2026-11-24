# Diapositivas

Las diapositivas se describen como datos en `diapositivas.toml` y se dibujan con Pillow. Como cada diapositiva sabe dibujarse con un número dado de ítems visibles, la animación sale sola: `id_p0.png` muestra solo el título, `id_p1.png` el primer ítem, y así sucesivamente. En el montaje, cada paso entra con un fundido de 0,5 s.

## Campos comunes

```toml
[[diapositiva]]
id = "cifras"                  # nombre único (se usa en ajustes.toml)
bloque = 2                     # bloque del guion; sin bloque = referencias al final
entra = "Los números ayudan"   # frase con que entra (la primera del bloque entra al inicio)
tipo = "datos"
etiqueta = "Bloque 2 · Método" # texto a la derecha de la cabecera
titulo = "Cifras para planear"
fuente = "Autor (2024)."       # pie de fuente en cursiva (opcional)
items = [ { cifra = "135", rotulo = "palabras por minuto", frase = "135 palabras" } ]
```

Un ítem con `frase` aparece cuando se dice esa frase; sin `frase`, aparece junto con la diapositiva. Las frases se buscan sin importar mayúsculas ni signos de puntuación (las tildes sí cuentan), pero deben ser palabras consecutivas del guion. `guion-studio guion` avisa si alguna no se encuentra.

## Tipos

| Tipo | Campos propios | Ítems |
|---|---|---|
| `pregunta` | `texto` (grande, con tipografía de título) | `texto` |
| `cita` | `texto`, `autor` | `texto` (viñetas debajo) |
| `vinetas` | `subtitulo`, `tamano` | `texto`, `estilo = "destacado"` para una conclusión en negrita |
| `numerada` | — | `titulo`, `texto` (círculos numerados) |
| `datos` | `subtitulo`, `por_fila` (3) | `cifra`, `rotulo` (la cifra se reduce si no cabe) |
| `linea_tiempo` | — | `fecha`, `texto` |
| `comparacion` | — | `titulo`, `texto` (paneles lado a lado; 2 o 3) |
| `tabla` | `cabecera`, `tamano`; para revelar por columnas: `filas` y `columnas_frases` | `celdas` (revela por filas) |
| `referencias` | `archivo` (una referencia por línea; `*cursiva*`) o `lineas` | — (se pagina sola, 12 por página, sin cámara) |

### Tabla que se revela por columnas

Útil cuando la explicación recorre las columnas (por ejemplo, un sistema por columna):

```toml
[[diapositiva]]
id = "sistemas"
bloque = 2
tipo = "tabla"
titulo = "Cómo distribuye el poder cada sistema"
cabecera = ["", "Presidencial", "Semipresidencial", "Parlamentario"]
filas = [["Origen", "Voto popular", "Mixto", "Mayoría del parlamento"]]
columnas_frases = ["", "En el presidencial", "El semipresidencial", "En el parlamentario"]
```

## Zona de la cámara

Con `camara = true` (por defecto), el contenido se dibuja a la izquierda del recuadro de la cámara, que ocupa la esquina inferior derecha. Si un contenido se sale de su zona, `diapositivas` y `montar` lo avisan: revisa la imagen en `salida/diapositivas/` y acorta el texto o baja `tamano`.

## Tema

Los colores y las fuentes salen de la sección `[tema]` de `proyecto.toml` (ver [configuración](configuracion.md)). Sin fuentes configuradas se usan DejaVu Serif y DejaVu Sans, presentes en casi todos los sistemas Linux; en Windows se buscan Georgia y Segoe UI.

## Sincronización

1. La posición de la frase dentro del bloque (en palabras habladas) da un tiempo estimado: si la frase empieza en la palabra 40 de 100 y el clip dura 60 s, se estima el segundo 24.
2. Ese tiempo se lleva al **comienzo de frase más cercano** del audio (el final de una pausa), dentro de ±2,5 s, para que el ítem aparezca cuando empiezas a decirlo y no a mitad.
3. Entre dos pasos quedan al menos 0,8 s, y ningún ítem aparece después de que entra la diapositiva siguiente.
4. Lo que quede corrido se fija a mano en `ajustes.toml`.

La estimación por proporción funciona bien si se lee el guion con el teleprompter. Si se improvisa mucho, conviene revisar `guion-studio plan` y ajustar.
