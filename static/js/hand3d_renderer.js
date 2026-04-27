/**
 * SignBridge — Hand3DRenderer
 * Main 3D procédurale construite à partir des landmarks MediaPipe (21 points × 3D).
 * Chaque lettre/chiffre ASL est une pose définie par les vraies données de la DB.
 *
 * Dépendance : Three.js doit être chargé avant ce fichier.
 *
 * API :
 *   const h = new Hand3DRenderer('canvas-id')
 *   h.loadPoses({ A:[{x,y,z}×21], B:[...], ... })
 *   h.playSequence(['B','O','N','J','O','U','R'], { holdMs:900, transMs:450 })
 *   h.stop()
 *   h.destroy()
 *   h.onSignChange = (letter, idx, total) => { ... }
 *   h.onComplete   = () => { ... }
 */
class Hand3DRenderer {

  /* ── Topologie MediaPipe (21 points) ─────────────────────────────────── */
  static CONNECTIONS = [
    [0,1],[1,2],[2,3],[3,4],           // pouce
    [0,5],[5,6],[6,7],[7,8],           // index
    [0,9],[9,10],[10,11],[11,12],      // majeur
    [0,13],[13,14],[14,15],[15,16],    // annulaire
    [0,17],[17,18],[18,19],[19,20],    // auriculaire
    [5,9],[9,13],[13,17],              // paume
  ];

  /* Couleur par doigt : poignet, pouce, index, majeur, annulaire, auriculaire */
  static COLORS = [0x22c55e, 0xf59e0b, 0x3b82f6, 0xa855f7, 0xec4899, 0x06b6d4];

  static _fingerIdx(i) {
    if (i === 0)  return 0;
    if (i <= 4)   return 1;
    if (i <= 8)   return 2;
    if (i <= 12)  return 3;
    if (i <= 16)  return 4;
    return 5;
  }

  /* ── Constructeur ────────────────────────────────────────────────────── */

  constructor(canvasId) {
    this.canvas = typeof canvasId === 'string'
      ? document.getElementById(canvasId) : canvasId;

    this._poses   = {};      // lettre → [{x,y,z}×21]
    this._current = null;    // pose courante (interpolée)
    this._from    = null;    // pose de départ du tween
    this._to      = null;    // pose cible du tween
    this._tweenDur   = 450;  // ms transition entre poses
    this._tweenStart = 0;

    this._sequence = [];
    this._seqIdx   = 0;
    this._holdDur  = 900;    // ms d'affichage par signe
    this._seqTimer = null;
    this._isPlaying = false;

    /** Callbacks publics */
    this.onSignChange = null;  // (letter, idx, total)
    this.onComplete   = null;

    this._raf = null;
    this._initThree();
    this._buildHand();
    this._current = this._neutralPose();
    this._applyPose(this._current);
    this._startLoop();
  }

  /* ── Initialisation Three.js ─────────────────────────────────────────── */

  _initThree() {
    const W = this.canvas.clientWidth  || 420;
    const H = this.canvas.clientHeight || 480;

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas, antialias: true, alpha: true,
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(W, H, false);
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.shadowMap.enabled = true;

    this.scene  = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(50, W / H, 0.01, 50);
    this.camera.position.set(0, 0.25, 2.40);
    this.camera.lookAt(0, 0.25, 0);

    /* Fond dégradé (plan derrière la main) */
    const bgGeo = new THREE.PlaneGeometry(4, 4);
    const bgMat = new THREE.MeshBasicMaterial({
      color: 0x07101A, transparent: true, opacity: 0,
    });
    const bg = new THREE.Mesh(bgGeo, bgMat);
    bg.position.z = -0.5;
    this.scene.add(bg);

    /* Lumières */
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.55));
    const key = new THREE.DirectionalLight(0xffffff, 0.90);
    key.position.set(1.5, 2.5, 2);
    this.scene.add(key);
    const fill = new THREE.DirectionalLight(0x88aaff, 0.40);
    fill.position.set(-1.5, 0, 1);
    this.scene.add(fill);
    const rim = new THREE.DirectionalLight(0x00ff88, 0.20);
    rim.position.set(0, -1, -1);
    this.scene.add(rim);

    /* Resize automatique */
    new ResizeObserver(() => {
      const w = this.canvas.clientWidth || 420;
      const h = this.canvas.clientHeight || 480;
      this.camera.aspect = w / h;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(w, h, false);
    }).observe(this.canvas);
  }

  /* ── Construction de la main (sphères + cylindres) ─────────────────── */

  _buildHand() {
    /* 21 articulations (sphères) */
    this._joints = [];
    for (let i = 0; i < 21; i++) {
      const isTip  = [4,8,12,16,20].includes(i);
      const isWrist = i === 0;
      const r   = isWrist ? 0.040 : isTip ? 0.026 : 0.021;
      const col = Hand3DRenderer.COLORS[Hand3DRenderer._fingerIdx(i)];
      const mat = new THREE.MeshPhongMaterial({
        color: col, shininess: 110, specular: 0x555555,
        emissive: col, emissiveIntensity: 0.08,
      });
      const mesh = new THREE.Mesh(new THREE.SphereGeometry(r, 14, 14), mat);
      this.scene.add(mesh);
      this._joints.push(mesh);
    }

    /* Os (cylindres reliant les articulations) */
    this._bones = [];
    for (const [a, b] of Hand3DRenderer.CONNECTIONS) {
      const col = Hand3DRenderer.COLORS[Hand3DRenderer._fingerIdx(a)];
      const mat = new THREE.MeshPhongMaterial({
        color: col, shininess: 60, transparent: true, opacity: 0.88,
      });
      const mesh = new THREE.Mesh(
        new THREE.CylinderGeometry(0.012, 0.012, 1, 8), mat
      );
      this.scene.add(mesh);
      this._bones.push({ mesh, a, b });
    }
  }

  /* ── Pose neutre (main ouverte) ─────────────────────────────────────── */

  _neutralPose() {
    return [
      {x: 0.000, y: 0.000, z: 0.000},   // 0  poignet
      {x:-0.058, y: 0.042, z: 0.028},   // 1  pouce CMC
      {x:-0.098, y: 0.092, z: 0.018},   // 2  pouce MCP
      {x:-0.128, y: 0.142, z: 0.008},   // 3  pouce IP
      {x:-0.148, y: 0.188, z:-0.002},   // 4  pouce tip
      {x:-0.032, y: 0.178, z: 0.010},   // 5  index MCP
      {x:-0.032, y: 0.268, z: 0.004},   // 6  index PIP
      {x:-0.032, y: 0.328, z:-0.002},   // 7  index DIP
      {x:-0.032, y: 0.372, z:-0.008},   // 8  index tip
      {x: 0.010, y: 0.188, z: 0.010},   // 9  majeur MCP
      {x: 0.010, y: 0.282, z: 0.004},   // 10 majeur PIP
      {x: 0.010, y: 0.348, z:-0.002},   // 11 majeur DIP
      {x: 0.010, y: 0.398, z:-0.008},   // 12 majeur tip
      {x: 0.052, y: 0.178, z: 0.010},   // 13 annulaire MCP
      {x: 0.052, y: 0.268, z: 0.004},   // 14 annulaire PIP
      {x: 0.052, y: 0.328, z:-0.002},   // 15 annulaire DIP
      {x: 0.052, y: 0.372, z:-0.008},   // 16 annulaire tip
      {x: 0.088, y: 0.162, z: 0.010},   // 17 auriculaire MCP
      {x: 0.088, y: 0.238, z: 0.004},   // 18 auriculaire PIP
      {x: 0.088, y: 0.288, z:-0.002},   // 19 auriculaire DIP
      {x: 0.088, y: 0.328, z:-0.008},   // 20 auriculaire tip
    ];
  }

  /* ── Application d'une pose aux meshes ─────────────────────────────── */

  _applyPose(pose) {
    const S = 0.75;   // scale : réduit pour que les poses extrêmes (Z, 5...) restent dans le cadre
    const up = new THREE.Vector3(0, 1, 0);

    for (let i = 0; i < 21; i++) {
      const p = pose[i];
      /* MediaPipe : Y pointe vers le bas → Three.js : Y vers le haut → on inverse Y */
      this._joints[i].position.set(p.x * S, -p.y * S, p.z * S);
    }

    for (const { mesh, a, b } of this._bones) {
      const pA  = this._joints[a].position;
      const pB  = this._joints[b].position;
      const mid = new THREE.Vector3().addVectors(pA, pB).multiplyScalar(0.5);
      const dir = new THREE.Vector3().subVectors(pB, pA);
      const len = dir.length();
      mesh.position.copy(mid);
      mesh.scale.set(1, len, 1);
      if (len > 0.0005) {
        mesh.quaternion.setFromUnitVectors(up, dir.clone().normalize());
      }
    }
  }

  /* ── Interpolation ease-in-out ──────────────────────────────────────── */

  static _lerp(a, b, t) {
    /* Ease in-out quadratique */
    const s = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    return a.map((pa, i) => ({
      x: pa.x + (b[i].x - pa.x) * s,
      y: pa.y + (b[i].y - pa.y) * s,
      z: pa.z + (b[i].z - pa.z) * s,
    }));
  }

  /* ── Boucle de rendu ────────────────────────────────────────────────── */

  _startLoop() {
    const tick = (ts) => {
      this._raf = requestAnimationFrame(tick);

      /* Tween actif → interpoler la pose */
      if (this._from && this._to) {
        const t = Math.min((ts - this._tweenStart) / this._tweenDur, 1);
        this._current = Hand3DRenderer._lerp(this._from, this._to, t);
        this._applyPose(this._current);
        if (t >= 1) { this._from = null; this._to = null; }
      }

      this.renderer.render(this.scene, this.camera);
    };
    this._raf = requestAnimationFrame(tick);
  }

  /* ── API publique ───────────────────────────────────────────────────── */

  /**
   * Charger les poses depuis le serveur.
   * @param {Object} posesObj  { 'A': [{x,y,z}×21], 'B': [...], ... }
   */
  loadPoses(posesObj) {
    this._poses = posesObj;
  }

  /**
   * Afficher un signe immédiatement (avec transition fluide).
   * @param {string} letter
   */
  showSign(letter) {
    const key  = String(letter).toUpperCase();
    const pose = this._poses[key] || this._neutralPose();
    this._from       = this._current ? [...this._current] : this._neutralPose();
    this._to         = pose;
    this._tweenStart = performance.now();
  }

  /**
   * Jouer une séquence de lettres/chiffres.
   * @param {string[]} letters
   * @param {Object}   options  { holdMs, transMs }
   */
  playSequence(letters, options = {}) {
    this.stop();
    this._holdDur  = options.holdMs  || 900;
    this._tweenDur = options.transMs || 450;
    this._sequence = letters.filter(l => /^[A-Z0-9 ]$/i.test(l));
    this._seqIdx   = 0;
    this._isPlaying = true;
    this._stepSequence();
  }

  _stepSequence() {
    if (!this._isPlaying || this._seqIdx >= this._sequence.length) {
      this._isPlaying = false;
      /* Retour à pose neutre */
      this._from       = this._current ? [...this._current] : this._neutralPose();
      this._to         = this._neutralPose();
      this._tweenStart = performance.now();
      if (this.onComplete) this.onComplete();
      return;
    }
    const letter = this._sequence[this._seqIdx];
    if (letter === ' ') {
      /* Espace : pause sans changer de signe */
      this._seqIdx++;
      this._seqTimer = setTimeout(() => this._stepSequence(), 400);
      return;
    }
    this.showSign(letter);
    if (this.onSignChange) {
      this.onSignChange(letter.toUpperCase(), this._seqIdx, this._sequence.length);
    }
    this._seqIdx++;
    this._seqTimer = setTimeout(() => this._stepSequence(), this._holdDur);
  }

  /** Arrêter la séquence en cours. */
  stop() {
    this._isPlaying = false;
    clearTimeout(this._seqTimer);
  }

  /** Réinitialiser à la pose neutre. */
  reset() {
    this.stop();
    this._from       = this._current ? [...this._current] : this._neutralPose();
    this._to         = this._neutralPose();
    this._tweenStart = performance.now();
    this._seqIdx     = 0;
  }

  /** Libérer les ressources Three.js. */
  destroy() {
    this.stop();
    if (this._raf) cancelAnimationFrame(this._raf);
    this.renderer.dispose();
  }
}
