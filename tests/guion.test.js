// Pruebas del lector del guion del teleprompter: node --test tests/
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const Guion = require("../teleprompter/js/guion.js");

const md = `# Título
## 1. Apertura
> Nota para quien graba
[Pantalla: portada]
Hola, **bienvenidos**.

Soy Nohlen [[nólen]].
···
Fin del bloque.
## Desarrollo
Primero.`;

test("separa bloques, título y notas", () => {
  const g = Guion.analizar(md);
  assert.strictEqual(g.titulo, "Título");
  assert.deepStrictEqual(g.bloques.map(b => b.numero), [1, 2]);
  assert.deepStrictEqual(g.bloques[0].notas, ["Nota para quien graba"]);
});

test("cuenta solo las palabras habladas (igual que la versión en Python)", () => {
  assert.strictEqual(Guion.palabras(Guion.analizar(md).bloques[0]), 8);
});

test("estructura en párrafos y pausas largas", () => {
  const partes = Guion.estructura(Guion.analizar(md).bloques[0]);
  assert.deepStrictEqual(partes.map(p => p.tipo), ["parrafo", "parrafo", "pausa", "parrafo"]);
});

test("el guion de ejemplo tiene tres bloques", () => {
  const texto = fs.readFileSync(path.join(__dirname, "../guion_studio/plantilla/guion.md"), "utf8");
  assert.strictEqual(Guion.analizar(texto).bloques.length, 3);
});
