# Decisiones técnicas

Registro de las decisiones importantes y de por qué se tomaron. Cada una se puede revisar si cambian las condiciones.

## D1 · FFmpeg directo, sin editores ni skills de terceros

**Contexto.** Antes de construir se revisaron opciones existentes (noviembre de 2026): Remotion y sus *agent skills*, *Claude Code Video Toolkit*, *ffmpeg-skill* y la skill *video-edit* de HeyGen.

**Decisión.** Usar FFmpeg directamente desde Python.

**Por qué.**
- Las skills de video revisadas son, en el fondo, envoltorios de FFmpeg: no aportaban una capacidad nueva y exigían auditar código ajeno antes de instalarlo.
- Remotion genera video desde componentes de React. Es potente para animación hecha con código, pero excesivo para un video de cámara con diapositivas, y tiene una licencia propia que habría que revisar para cada uso.
- FFmpeg está en los repositorios oficiales de cada sistema, es estable y cubre todo lo necesario: detección de silencios, filtros de imagen, normalización EBU R128, cambio de tempo con rubberband y fundidos (`xfade`).

## D2 · Diapositivas desde datos, no desde imágenes

**Primera versión.** Las diapositivas se dibujaban terminadas y, para animarlas, se tapaban las regiones de los ítems aún no dichos.

**Problema.** Había que calcular coordenadas a mano o detectarlas por color, y cualquier cambio de diseño rompía las regiones.

**Decisión.** Cada tipo de diapositiva se dibuja con N ítems visibles. Los pasos de la animación salen del mismo código que dibuja la diapositiva.

## D3 · Pista de diapositivas tramo por tramo

**Problema.** Un único filtro `xfade` con 33 imágenes de 1920 × 1080 agotó la memoria de un equipo con 3,8 GB y el sistema detuvo FFmpeg.

**Decisión.** Cada tramo se codifica por separado con solo dos imágenes (la anterior, para el fundido, y la actual) y luego se concatenan sin recodificar. La memoria usada ya no depende de cuántas diapositivas tenga el video.

## D4 · Corrección de imagen suave

**Problema.** Con una cortina clara detrás, la webcam oscurece la cara. Una curva fuerte con más contraste y saturación quitaba la "niebla", pero el resultado se veía artificial.

**Decisión.** Por defecto solo se aclaran los tonos medios (`curves` 0,25 → 0,29 y 0,55 → 0,60), con un contraste de +4 %, una saturación de +5 % y una nitidez leve. La mejor solución sigue siendo grabar con la luz de frente.

## D5 · Sin reducción de ruido por defecto

**Problema.** `afftdn` sobre una voz ya limpia (ruido de fondo de −56 dB) dejaba un sonido metálico.

**Decisión.** El preset `limpio` usa solo un filtro de graves (70 Hz) y una compresión suave. El teleprompter graba con la supresión de ruido del navegador desactivada por la misma razón.

## D6 · Velocidad con rubberband a 1,05×

`atempo` (WSOLA) funciona, pero `rubberband` conserva mejor el timbre de la voz. A 1,05× el cambio no se percibe; desde 1,10× la exposición empieza a sonar apurada.

## D7 · Sincronización por proporción + ajuste al audio

**Situación actual.** Sin transcripción, el momento de cada frase se estima por su posición en el guion y se ajusta al comienzo de frase más cercano detectado en el audio. Funciona bien si se lee con el teleprompter.

**Siguiente paso.** Una transcripción local con marcas de tiempo por palabra (por ejemplo, Whisper) daría el segundo exacto de cada frase. Queda para una versión posterior, después de auditar la dependencia (tamaño del modelo, licencia y si funciona sin conexión).

## D8 · Teleprompter sin compilación

HTML, CSS y JavaScript sin módulos ni dependencias, para que funcione con doble clic (`file://`) y en GitHub Pages. El lector del guion es el mismo archivo en el navegador y en las pruebas de Node, y el guion de ejemplo del navegador se genera desde la plantilla (`scripts/sincronizar_ejemplo.py`); una prueba comprueba que no se desincronicen.
