/* Cámara, medidor de micrófono y grabación por bloque (MediaRecorder).
   Todo queda en el navegador; el archivo se descarga al detener. */
(function () {
  "use strict";

  const TIPOS = [
    "video/webm;codecs=h264,opus",   // H.264: menos uso de CPU y FFmpeg lo procesa rápido
    "video/webm;codecs=vp9,opus",
    "video/webm;codecs=vp8,opus",
    "video/webm",
    "video/mp4",
  ];

  let flujo = null, grabador = null, trozos = [], tipo = "", contexto = null, analizador = null, alAvisar = () => {};

  function tipoCompatible() {
    if (typeof MediaRecorder === "undefined") return "";
    return TIPOS.find(t => MediaRecorder.isTypeSupported(t)) || "";
  }

  async function encender(video, nivel, avisar) {
    alAvisar = avisar || alAvisar;
    if (flujo) return flujo;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error("Este navegador no permite usar la cámara. Prueba con Chrome, Edge o Firefox actualizados.");
    }
    flujo = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1920 }, height: { ideal: 1080 }, frameRate: { ideal: 30 } },
      // Sin procesar: la supresión de ruido del navegador puede dejar la voz "metálica".
      audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false, channelCount: 1 },
    });
    video.srcObject = flujo;
    medir(nivel);
    const v = flujo.getVideoTracks()[0].getSettings();
    alAvisar(`${v.width || "?"}×${v.height || "?"} · ${tipoCompatible().split(";")[0] || "sin grabación"}`);
    return flujo;
  }

  function medir(nivel) {
    try {
      contexto = new (window.AudioContext || window.webkitAudioContext)();
      analizador = contexto.createAnalyser();
      analizador.fftSize = 1024;
      contexto.createMediaStreamSource(flujo).connect(analizador);
      const datos = new Float32Array(analizador.fftSize);
      const ciclo = () => {
        if (!analizador) return;
        analizador.getFloatTimeDomainData(datos);
        let suma = 0;
        for (const x of datos) suma += x * x;
        const db = 20 * Math.log10(Math.sqrt(suma / datos.length) || 1e-6);   // -60 (silencio) a 0 (saturado)
        const pct = Math.max(0, Math.min(100, (db + 60) / 60 * 100));
        nivel.style.width = pct + "%";
        nivel.classList.toggle("medidor__nivel--alto", db > -6);
        requestAnimationFrame(ciclo);
      };
      ciclo();
    } catch (e) { /* sin medidor: no impide grabar */ }
  }

  function apagar() {
    if (grabador && grabador.state !== "inactive") grabador.stop();
    if (flujo) flujo.getTracks().forEach(t => t.stop());
    if (contexto) contexto.close();
    flujo = null; analizador = null; contexto = null;
  }

  function iniciar() {
    if (!flujo) throw new Error("Primero enciende la cámara.");
    tipo = tipoCompatible();
    if (!tipo) throw new Error("Este navegador no puede grabar video (MediaRecorder).");
    trozos = [];
    grabador = new MediaRecorder(flujo, { mimeType: tipo, videoBitsPerSecond: 6_000_000, audioBitsPerSecond: 160_000 });
    grabador.ondataavailable = e => { if (e.data && e.data.size) trozos.push(e.data); };
    grabador.start(1000);
  }

  function detener(nombreBase) {
    return new Promise(resolve => {
      if (!grabador || grabador.state === "inactive") return resolve(null);
      grabador.onstop = () => {
        const ext = tipo.includes("mp4") ? "mp4" : "webm";
        const blob = new Blob(trozos, { type: tipo.split(";")[0] });
        const nombre = `${nombreBase}.${ext}`;
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = nombre;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 4000);
        resolve({ nombre, mb: blob.size / 1e6 });
      };
      grabador.stop();
    });
  }

  const grabando = () => !!grabador && grabador.state === "recording";

  window.Grabadora = { encender, apagar, iniciar, detener, grabando, tipoCompatible };
})();
