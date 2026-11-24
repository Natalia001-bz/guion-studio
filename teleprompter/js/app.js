/* Teleprompter: lectura con desplazamiento por palabras por minuto, bloques y grabación. */
(function () {
  "use strict";

  const $ = id => document.getElementById(id);
  const texto = $("texto"), guia = $("guia");

  // Preferencias por persona (solo comodidad: si el navegador no guarda, todo funciona igual)
  const leer = (k, d) => { try { const v = localStorage.getItem("gs_" + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } };
  const guardar = (k, v) => { try { localStorage.setItem("gs_" + k, JSON.stringify(v)); } catch (e) { /* sin almacenamiento */ } };

  const est = {
    fuente: leer("guion", window.GUION_EJEMPLO || ""),
    bloque: leer("bloque", 0),
    ppm: leer("ppm", 135),
    tam: leer("tam", 44),
    espejo: leer("espejo", false),
    franja: leer("franja", 0.22),
    grabar: leer("grabar", false),
  };
  let guion = Guion.analizar(est.fuente);
  let y = 0, corriendo = false, ultimo = 0, velocidad = 0, palabras = 1, cuentaActiva = false, tomas = {};

  function cambiar(k, v) { est[k] = v; guardar(k, v); }
  const bloqueActual = () => guion.bloques[est.bloque] || guion.bloques[0];

  /* ---------- dibujo del texto ---------- */
  function esc(s) { return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function formato(l) {
    return esc(l).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\[\[(.+?)\]\]/g, '<span class="pronunciacion">[$1]</span>');
  }

  function llenarBloques() {
    const s = $("s-bloque");
    s.innerHTML = "";
    guion.bloques.forEach((b, i) => {
      const o = document.createElement("option");
      o.value = i;
      o.textContent = `${b.numero}. ${b.titulo}`;
      s.appendChild(o);
    });
    if (est.bloque >= guion.bloques.length) cambiar("bloque", 0);
    s.value = est.bloque;
  }

  function render() {
    const b = bloqueActual();
    if (!b) {
      texto.innerHTML = '<p class="parrafo">El guion no tiene bloques. Abre <b>Guion</b> y empieza cada bloque con <code>## </code>.</p>';
      return;
    }
    palabras = Math.max(1, Guion.palabras(b));
    let html = `<div class="bloque-titulo">Bloque ${b.numero} · ${esc(b.titulo)}</div>`;
    for (const n of b.notas) html += `<p class="nota">${esc(n)}</p>`;
    for (const p of Guion.estructura(b)) {
      html += p.tipo === "pausa"
        ? '<span class="pausa">· · ·</span>'
        : `<div class="parrafo">${p.lineas.map(l => `<span class="linea">${formato(l)}</span>`).join("")}</div>`;
    }
    html += '<div class="fin" id="fin">— Fin del bloque. Un segundo de silencio. —</div><div style="height:80vh"></div>';
    texto.innerHTML = html;
    document.documentElement.style.setProperty("--ancho", Math.round(est.tam * 19) + "px");
    texto.style.fontSize = est.tam + "px";
    guia.style.fontSize = est.tam + "px";
    colocarFranja();
    document.body.classList.toggle("espejo", est.espejo);
    $("b-espejo").classList.toggle("boton--activo", est.espejo);
    $("b-grabar").classList.toggle("boton--activo", est.grabar);
    $("s-bloque").value = est.bloque;
    reiniciar();
  }

  function colocarFranja() { guia.style.top = `calc(${est.franja * 100}vh - 1.1em)`; }

  /* ---------- desplazamiento ---------- */
  function calcularVelocidad() {
    const alto = texto.scrollHeight - window.innerHeight * 0.8;   // sin el relleno final
    velocidad = alto / (palabras / est.ppm * 60);                  // píxeles por segundo
  }
  function pintar() {
    texto.style.top = (window.innerHeight * est.franja - 10 - y) + "px";
    actualizarEstado();
  }
  function actualizarEstado() {
    const seg = Math.round(palabras / est.ppm * 60);
    $("ppm").textContent = est.ppm + " ppm";
    const rec = Grabadora.grabando() ? "● grabando · " : "";
    $("estado").textContent = `${rec}${palabras} palabras · ≈ ${Math.floor(seg / 60)}:${String(seg % 60).padStart(2, "0")}` +
      (corriendo ? "" : " · en pausa");
  }
  function llegoAlFinal() {
    const fin = $("fin");
    return fin && fin.getBoundingClientRect().top < window.innerHeight * est.franja;
  }
  function paso(t) {
    if (!corriendo) return;
    if (ultimo) y += velocidad * (t - ultimo) / 1000;
    ultimo = t;
    pintar();
    if (Grabadora.grabando() && llegoAlFinal()) {
      corriendo = false;
      document.body.classList.remove("corriendo");
      setTimeout(detenerGrabacion, 1500);      // un segundo y medio de silencio final
      return;
    }
    requestAnimationFrame(paso);
  }

  async function iniciar() {
    if (cuentaActiva) return;
    if (corriendo) { corriendo = false; document.body.classList.remove("corriendo"); actualizarEstado(); return; }
    const arrancar = () => {
      calcularVelocidad();
      corriendo = true; ultimo = 0;
      document.body.classList.add("corriendo");
      requestAnimationFrame(paso);
    };
    if (y > 0) return arrancar();
    if (est.grabar) {
      try {
        await encenderCamara();
        Grabadora.iniciar();                    // empieza antes de la cuenta: el silencio inicial se recorta luego
        $("camara").classList.add("camara--grabando");
      } catch (e) { avisar(e.message); return; }
    }
    const c = $("cuenta");
    let n = 3;
    cuentaActiva = true;
    c.classList.add("cuenta--visible");
    c.textContent = n;
    const tic = setInterval(() => {
      n--;
      if (n === 0) { clearInterval(tic); c.classList.remove("cuenta--visible"); cuentaActiva = false; arrancar(); }
      else c.textContent = n;
    }, 800);
  }

  async function detenerGrabacion() {
    if (!Grabadora.grabando()) return;
    const b = bloqueActual();
    const k = (tomas[b.numero] = (tomas[b.numero] || 0) + 1);
    const r = await Grabadora.detener(k === 1 ? `bloque${b.numero}` : `bloque${b.numero}_toma${k}`);
    $("camara").classList.remove("camara--grabando");
    if (r) avisar(`Guardado ${r.nombre} (${r.mb.toFixed(1)} MB). Muévelo a la carpeta clips/ del proyecto.`);
    actualizarEstado();
  }

  function reiniciar() {
    corriendo = false;
    document.body.classList.remove("corriendo");
    y = 0;
    pintar();
  }

  /* ---------- cámara ---------- */
  function avisar(msg) { $("aviso-camara").textContent = msg; $("estado").textContent = msg; }
  async function encenderCamara() {
    $("camara").hidden = false;
    $("b-camara").classList.add("boton--activo");
    await Grabadora.encender($("video"), $("nivel"), m => { $("aviso-camara").textContent = m; });
  }
  async function alternarCamara() {
    if ($("camara").hidden) {
      try { await encenderCamara(); } catch (e) { avisar("No se pudo abrir la cámara: " + e.message); }
    } else {
      if (Grabadora.grabando()) await detenerGrabacion();
      Grabadora.apagar();
      $("camara").hidden = true;
      $("b-camara").classList.remove("boton--activo");
    }
  }

  /* ---------- guion ---------- */
  function usarGuion(md) {
    est.fuente = md; guardar("guion", md);
    guion = Guion.analizar(md);
    cambiar("bloque", 0);
    llenarBloques();
    if (guion.titulo) document.title = `${guion.titulo} · Teleprompter`;
    render();
  }
  function abrirEditor() { $("editor").value = est.fuente; $("d-guion").showModal(); }
  function leerArchivo(archivo) {
    const r = new FileReader();
    r.onload = () => { $("editor").value = r.result; usarGuion(r.result); };
    r.readAsText(archivo, "utf-8");
  }

  /* ---------- controles ---------- */
  function moverFranja(d) {
    cambiar("franja", Math.round(Math.min(0.6, Math.max(0.05, est.franja + d)) * 100) / 100);
    colocarFranja(); pintar();
  }
  const acciones = {
    lento: () => { cambiar("ppm", Math.max(80, est.ppm - 5)); calcularVelocidad(); actualizarEstado(); },
    rapido: () => { cambiar("ppm", Math.min(220, est.ppm + 5)); calcularVelocidad(); actualizarEstado(); },
    menos: () => { cambiar("tam", Math.max(24, est.tam - 4)); render(); },
    mas: () => { cambiar("tam", Math.min(110, est.tam + 4)); render(); },
    espejo: () => { cambiar("espejo", !est.espejo); render(); },
    grabar: () => { cambiar("grabar", !est.grabar); $("b-grabar").classList.toggle("boton--activo", est.grabar); },
    completa: () => {
      if (document.fullscreenElement) document.exitFullscreen();
      else document.documentElement.requestFullscreen().catch(() => {});
    },
  };

  $("b-iniciar").onclick = iniciar;
  $("b-reiniciar").onclick = reiniciar;
  $("b-lento").onclick = acciones.lento;
  $("b-rapido").onclick = acciones.rapido;
  $("b-menos").onclick = acciones.menos;
  $("b-mas").onclick = acciones.mas;
  $("b-espejo").onclick = acciones.espejo;
  $("b-completa").onclick = acciones.completa;
  $("b-subir").onclick = () => moverFranja(-0.02);
  $("b-bajar").onclick = () => moverFranja(0.02);
  $("b-camara").onclick = alternarCamara;
  $("b-grabar").onclick = acciones.grabar;
  $("b-ayuda").onclick = () => $("d-ayuda").showModal();
  $("b-entendido").onclick = () => $("d-ayuda").close();
  $("b-guion").onclick = abrirEditor;
  $("b-usar").onclick = () => { usarGuion($("editor").value); $("d-guion").close(); };
  $("b-ejemplo").onclick = () => { $("editor").value = window.GUION_EJEMPLO || ""; };
  $("b-descargar-guion").onclick = () => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([$("editor").value], { type: "text/markdown" }));
    a.download = "guion.md"; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  };
  $("archivo").onchange = e => { if (e.target.files[0]) leerArchivo(e.target.files[0]); };
  $("s-bloque").onchange = e => { cambiar("bloque", Number(e.target.value)); render(); };

  document.addEventListener("fullscreenchange", () => {
    const on = !!document.fullscreenElement;
    document.body.classList.toggle("completa", on);
    $("b-completa").classList.toggle("boton--activo", on);
    calcularVelocidad(); pintar();
  });

  // Arrastrar y soltar un .md en cualquier parte
  ["dragenter", "dragover"].forEach(ev => document.addEventListener(ev, e => { e.preventDefault(); document.body.classList.add("soltar"); }));
  ["dragleave", "drop"].forEach(ev => document.addEventListener(ev, e => { e.preventDefault(); document.body.classList.remove("soltar"); }));
  document.addEventListener("drop", e => { const f = e.dataTransfer.files[0]; if (f) leerArchivo(f); });

  document.addEventListener("keydown", e => {
    if (e.target.closest("textarea, input, select") || document.querySelector("dialog[open]")) return;
    const k = e.key;
    if (e.code === "Space") { e.preventDefault(); iniciar(); }
    else if (k === "ArrowUp") { e.preventDefault(); acciones.rapido(); }
    else if (k === "ArrowDown") { e.preventDefault(); acciones.lento(); }
    else if (k === "ArrowLeft") { y = Math.max(0, y - est.tam * 2.5); pintar(); }
    else if (k === "ArrowRight") { y += est.tam * 2.5; pintar(); }
    else if (k === "+" || k === "=") acciones.mas();
    else if (k === "-") acciones.menos();
    else if (k === "PageUp") { e.preventDefault(); moverFranja(-0.02); }
    else if (k === "PageDown") { e.preventDefault(); moverFranja(0.02); }
    else if (/^[1-9]$/.test(k) && Number(k) <= guion.bloques.length) { cambiar("bloque", Number(k) - 1); render(); }
    else if (k === "?") $("d-ayuda").showModal();
    else switch (k.toLowerCase()) {
      case "r": reiniciar(); break;
      case "m": acciones.espejo(); break;
      case "f": acciones.completa(); break;
      case "c": alternarCamara(); break;
      case "x": acciones.grabar(); break;
      case "g": abrirEditor(); break;
      case "s": if (Grabadora.grabando()) { corriendo = false; document.body.classList.remove("corriendo"); detenerGrabacion(); } break;
    }
  });
  window.addEventListener("resize", () => { calcularVelocidad(); pintar(); });

  llenarBloques();
  if (guion.titulo) document.title = `${guion.titulo} · Teleprompter`;
  render();
  if (!leer("visto", false) && location.hash !== "#leer") { $("d-ayuda").showModal(); guardar("visto", true); }
})();
