/**
 * SignBridge — WebcamClient v5
 *
 * Architecture optimale (state-of-art ASL recognition) :
 *   MediaPipe Hands JS (GPU navigateur) → 63 floats → WebSocket → RF serveur
 *
 * Avantages vs envoi d'image :
 *   • ~500 octets vs ~100 Ko par frame → latence ×10 plus faible
 *   • MediaPipe tourne sur GPU local → pas de charge serveur
 *   • Squelette dessiné localement sans aller-retour réseau
 *   • Fallback auto si CDN MediaPipe non disponible (envoi image)
 */
class WebcamClient {
  constructor(options = {}) {
    this.videoEl    = document.getElementById(options.videoEl  || 'webcam-video');
    this.canvasEl   = document.getElementById(options.canvasEl || 'webcam-canvas');
    const wsProto   = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    this.wsUrl      = options.wsUrl || (wsProto + window.location.host + '/ws/sign-recognition/');

    this.onConnected    = options.onConnected    || (() => {});
    this.onConnecting   = options.onConnecting   || (() => {});
    this.onDisconnected = options.onDisconnected || (() => {});
    this.onGesture      = options.onGesture      || (() => {});
    this.onLandmarks    = options.onLandmarks    || (() => {});
    this.onNoHand       = options.onNoHand       || (() => {});
    this.onMlStatus     = options.onMlStatus     || (() => {});

    this.ws           = null;
    this.stream       = null;
    this.isActive     = false;
    this.SEND_MS      = 80;   // ~12 fps max vers le serveur

    // Mode MediaPipe JS (prioritaire)
    this._mpHands     = null;
    this._mpReady     = false;
    this._rafHandle   = null;    // requestAnimationFrame — tourne à 30fps
    this._mpBusy      = false;   // évite les appels overlappants
    this._lastWSSend  = 0;       // throttle envoi WS séparé du rendu

    // Fallback : capture canvas + envoi image
    this._sendInterval    = null;
    this._captureCanvas   = document.createElement('canvas');
  }

  /* ── API publique ──────────────────────────────────────────────────────── */

  async startCamera() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
        audio: false,
      });
      this.videoEl.srcObject = this.stream;
      this.videoEl.style.display = 'block';
      await new Promise(r => { this.videoEl.onloadedmetadata = r; });
      await this.videoEl.play();

      this.isActive = true;
      this._connectWS();

      // Essaie d'abord MediaPipe JS, fallback image si indisponible
      await this._initMediaPipeJS();
      this._startSending();
      return true;
    } catch (err) {
      console.error('Webcam error:', err);
      return false;
    }
  }

  stopCamera() {
    this.isActive = false;

    clearInterval(this._sendInterval);
    this._sendInterval = null;
    if (this._rafHandle) { cancelAnimationFrame(this._rafHandle); this._rafHandle = null; }

    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      this.stream = null;
    }
    if (this.videoEl) {
      this.videoEl.srcObject = null;
      this.videoEl.style.display = 'none';
    }
    this._disconnectWS();
    if (this.canvasEl) {
      const ctx = this.canvasEl.getContext('2d');
      ctx.clearRect(0, 0, this.canvasEl.width, this.canvasEl.height);
    }
  }

  /* ── Initialisation MediaPipe Hands JS ─────────────────────────────────── */

  async _initMediaPipeJS() {
    // Chargement dynamique du script MediaPipe si absent
    if (typeof window.Hands === 'undefined') {
      await new Promise(resolve => {
        const s = document.createElement('script');
        s.src         = 'https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js';
        s.crossOrigin = 'anonymous';
        s.onload  = resolve;
        s.onerror = resolve;   // ne bloque pas si CDN indisponible
        document.head.appendChild(s);
      });
    }

    if (typeof window.Hands === 'undefined') {
      console.warn('[SignBridge] MediaPipe Hands JS non disponible → mode image (fallback)');
      this._mpReady = false;
      return;
    }

    try {
      this._mpHands = new window.Hands({
        locateFile: f => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${f}`,
      });
      this._mpHands.setOptions({
        maxNumHands:             1,
        modelComplexity:         1,     // 0=lite 1=full — full meilleure précision
        minDetectionConfidence:  0.70,
        minTrackingConfidence:   0.60,
      });
      this._mpHands.onResults(r => this._onMPResults(r));
      await this._mpHands.initialize();
      this._mpReady = true;
      console.log('[SignBridge] MediaPipe Hands JS actif ✓ — envoi landmarks uniquement');
    } catch (e) {
      console.warn('[SignBridge] Erreur init MediaPipe JS:', e, '→ mode image (fallback)');
      this._mpReady = false;
    }
  }

  /* ── Envoi frames ──────────────────────────────────────────────────────── */

  _startSending() {
    if (this._mpReady) {
      this._startMPLoop();   // 30fps pour squelette/disparition immédiate
    } else {
      // Fallback : envoi image JPEG
      clearInterval(this._sendInterval);
      this._sendInterval = setInterval(() => this._captureAndSend(), this.SEND_MS);
    }
  }

  /**
   * Boucle MediaPipe JS à 30fps (requestAnimationFrame).
   * Le rendu squelette / disparition est immédiat.
   * L'envoi WebSocket est throttlé séparément à SEND_MS.
   */
  _startMPLoop() {
    const loop = async () => {
      if (!this.isActive) return;
      if (!this._mpBusy && this.videoEl.readyState >= 2) {
        this._mpBusy = true;
        try { await this._mpHands.send({ image: this.videoEl }); } catch (_) {}
        this._mpBusy = false;
      }
      this._rafHandle = requestAnimationFrame(loop);
    };
    this._rafHandle = requestAnimationFrame(loop);
  }

  /**
   * Callback MediaPipe JS — appelé à chaque frame (~30fps).
   *
   * Rendu (squelette, disparition overlay) → IMMÉDIAT, chaque frame.
   * Envoi WebSocket → throttlé à SEND_MS pour ne pas surcharger le serveur.
   */
  _onMPResults(results) {
    if (!this.isActive) return;

    if (!results.multiHandLandmarks || !results.multiHandLandmarks.length) {
      // Main absente → effacement immédiat, pas d'attente serveur
      if (this.canvasEl) {
        const ctx = this.canvasEl.getContext('2d');
        ctx.clearRect(0, 0, this.canvasEl.width, this.canvasEl.height);
      }
      this.onNoHand();
      return;
    }

    const lm = results.multiHandLandmarks[0];

    // ── Affichage immédiat du squelette (chaque frame, 30fps) ──────────────
    this.onLandmarks(lm);

    // ── Envoi WS throttlé à SEND_MS (prédiction serveur) ──────────────────
    const now = Date.now();
    if (now - this._lastWSSend < this.SEND_MS) return;
    this._lastWSSend = now;

    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

    const wrist = lm[0];
    // Normalisation d'échelle : distance poignet→MCP-majeur (point 9)
    const mcp9  = lm[9];
    const dx9   = mcp9.x - wrist.x, dy9 = mcp9.y - wrist.y, dz9 = mcp9.z - wrist.z;
    const scale = Math.sqrt(dx9*dx9 + dy9*dy9 + dz9*dz9) || 1;

    const features = lm.flatMap(p => [
      (p.x - wrist.x) / scale,
      (p.y - wrist.y) / scale,
      (p.z - wrist.z) / scale,
    ]);
    this.ws.send(JSON.stringify({ landmarks: features }));
  }

  /** Fallback : capture canvas → JPEG → envoi (si MediaPipe JS non disponible). */
  _captureAndSend() {
    if (!this.isActive || !this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    if (!this.videoEl || this.videoEl.readyState < 2) return;

    const W = 480, H = 360;
    this._captureCanvas.width  = W;
    this._captureCanvas.height = H;
    this._captureCanvas.getContext('2d').drawImage(this.videoEl, 0, 0, W, H);
    try {
      const b64 = this._captureCanvas.toDataURL('image/jpeg', 0.85);
      this.ws.send(JSON.stringify({ frame: b64 }));
    } catch (e) { /* canvas tainted */ }
  }

  /* ── WebSocket ─────────────────────────────────────────────────────────── */

  _connectWS() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return;
    this.onConnecting();
    this.ws = new WebSocket(this.wsUrl);

    this.ws.onopen  = () => this.onConnected();
    this.ws.onclose = () => {
      this.onDisconnected();
      if (this.isActive) setTimeout(() => this._connectWS(), 2000);
    };
    this.ws.onerror = () => this.onDisconnected();
    this.ws.onmessage = (event) => {
      try { this._handleMessage(JSON.parse(event.data)); }
      catch (e) { console.error('WS parse error:', e); }
    };
  }

  _disconnectWS() {
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.close();
      this.ws = null;
    }
    this.onDisconnected();
  }

  _handleMessage(data) {
    switch (data.type) {
      case 'gesture_detected':
        this.onGesture(data);
        // Landmarks déjà dessinés par MediaPipe JS ; serveur n'en renvoie plus
        if (data.landmarks && data.landmarks.length) {
          this.onLandmarks(data.landmarks);
        }
        break;

      case 'hand_detected':
        if (data.landmarks && data.landmarks.length) {
          this.onLandmarks(data.landmarks);
        }
        break;

      case 'no_hand':
        if (this.canvasEl) {
          const ctx = this.canvasEl.getContext('2d');
          ctx.clearRect(0, 0, this.canvasEl.width, this.canvasEl.height);
        }
        this.onNoHand();
        break;

      case 'connection_established':
        if (this.onMlStatus) this.onMlStatus(data.ml_ready);
        break;

      case 'error':
        console.warn('WS error:', data.error);
        break;
    }
  }
}
