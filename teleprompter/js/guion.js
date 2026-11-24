/* Lector del guion en Markdown (mismas reglas que guion_studio/guion.py).
   ## N. Título  → bloque        > nota / [Pantalla: …] → no se lee
   línea = respiración · línea en blanco = pausa corta · ··· o --- = pausa larga
   **énfasis** · [[pronunciación]] (no se lee)
   Funciona en el navegador (window.Guion) y en Node (module.exports) para las pruebas. */
(function (raiz) {
  "use strict";

  const BLOQUE = /^##\s+(?:(\d+)[.)]?\s*)?(.*)$/;
  const PAUSA_LARGA = new Set(["···", "...", "---", "—"]);

  function analizar(texto) {
    const bloques = [];
    let actual = null;
    let titulo = "";
    for (const crudo of String(texto).split(/\r?\n/)) {
      const linea = crudo.trimEnd();
      const m = linea.match(BLOQUE);
      if (m) {
        actual = { numero: m[1] ? Number(m[1]) : bloques.length + 1, titulo: m[2].trim(), lineas: [], notas: [] };
        bloques.push(actual);
        continue;
      }
      const s = linea.trim();
      if (!actual) {
        if (!titulo && s.startsWith("# ")) titulo = s.slice(2).trim();
        continue;
      }
      if (s.startsWith(">")) { actual.notas.push(s.replace(/^>\s*/, "")); continue; }
      if (s.startsWith("[") && !s.startsWith("[[")) continue;
      actual.lineas.push(s);
    }
    for (const b of bloques) {
      while (b.lineas.length && !b.lineas[0]) b.lineas.shift();
      while (b.lineas.length && !b.lineas[b.lineas.length - 1]) b.lineas.pop();
    }
    return { titulo, bloques };
  }

  function limpiar(linea) {
    return linea.replace(/\[\[.*?\]\]/g, "").replace(/\*\*/g, "").replace(/\s+/g, " ").trim();
  }

  function palabras(bloque) {
    return bloque.lineas
      .filter(l => l && !PAUSA_LARGA.has(l))
      .map(limpiar).join(" ").split(/\s+/).filter(Boolean).length;
  }

  /* Agrupa las líneas en párrafos (separados por línea en blanco) y pausas largas. */
  function estructura(bloque) {
    const partes = [];
    let grupo = [];
    const cerrar = () => { if (grupo.length) { partes.push({ tipo: "parrafo", lineas: grupo }); grupo = []; } };
    for (const l of bloque.lineas) {
      if (!l) cerrar();
      else if (PAUSA_LARGA.has(l)) { cerrar(); partes.push({ tipo: "pausa" }); }
      else grupo.push(l);
    }
    cerrar();
    return partes;
  }

  const api = { analizar, limpiar, palabras, estructura };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else raiz.Guion = api;
})(typeof window !== "undefined" ? window : globalThis);
