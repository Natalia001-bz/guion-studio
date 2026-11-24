"""Copia el guion de la plantilla al teleprompter (js/ejemplo.js) para la demo."""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
md = (RAIZ / "guion_studio" / "plantilla" / "guion.md").read_text(encoding="utf-8")
(RAIZ / "teleprompter" / "js" / "ejemplo.js").write_text(
    "/* Generado por scripts/sincronizar_ejemplo.py a partir de guion_studio/plantilla/guion.md. No editar a mano. */\n"
    f"window.GUION_EJEMPLO = {json.dumps(md, ensure_ascii=False)};\n", encoding="utf-8")
print("teleprompter/js/ejemplo.js actualizado")
