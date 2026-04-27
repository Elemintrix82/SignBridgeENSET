/**
 * SignBridge — AvatarPlayer v3
 * Affiche les signes ASL via HandSignRenderer (Canvas 2D).
 * Chaque signe correspond à la vraie configuration de main ASL.
 *
 * CORRECTION race condition : compteur de génération (_gen).
 * Toute nouvelle séquence invalide la précédente — plus de conflit
 * entre deux appels successifs à playSignSequence().
 */
class AvatarPlayer {

  constructor(canvasId) {
    this.canvas     = typeof canvasId === 'string'
                        ? document.getElementById(canvasId)
                        : canvasId;
    this.isPlaying  = false;
    this.isPaused   = false;
    this.speed      = 1.0;
    this.callbacks  = {};
    this._renderer  = null;
    this._animCache = new Map();
    this._gen       = 0;   // ← compteur de génération (anti race-condition)

    this._init();
  }

  /* ── Initialisation ───────────────────────────────────────────────────────── */

  _init() {
    if (!this.canvas) return;
    if (typeof HandSignRenderer !== 'undefined') {
      this._renderer = new HandSignRenderer(this.canvas);
      this._drawIdle();
    } else {
      this._drawFallbackIdle();
    }
    if (window.ResizeObserver) {
      new ResizeObserver(() => {
        if (this._currentSign && this._renderer) this._renderer.draw(this._currentSign);
        else this._drawIdle();
      }).observe(this.canvas);
    }
  }

  _drawIdle() {
    if (!this.canvas) return;
    const ctx = this.canvas.getContext('2d');
    const W   = this.canvas.clientWidth  || 400;
    const H   = this.canvas.clientHeight || 300;
    this.canvas.width  = W;
    this.canvas.height = H;
    const bg = ctx.createRadialGradient(W/2, H/2, 10, W/2, H/2, W * 0.9);
    bg.addColorStop(0, '#131f2e');
    bg.addColorStop(1, '#0A0F1A');
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);
  }

  _drawFallbackIdle() {
    if (!this.canvas) return;
    const ctx = this.canvas.getContext('2d');
    const W = this.canvas.clientWidth  || 400;
    const H = this.canvas.clientHeight || 300;
    this.canvas.width = W; this.canvas.height = H;
    ctx.fillStyle = '#0A0F1A';
    ctx.fillRect(0, 0, W, H);
  }

  /* ── Lecture d'une séquence ───────────────────────────────────────────────── */

  async playSignSequence(sequence, callbacks = {}) {
    // ── Invalider TOUTE animation précédente ──────────────────────────────────
    this._gen++;
    const myGen = this._gen;

    this.callbacks = callbacks;
    this.isPlaying = true;
    this.isPaused  = false;

    const totalDur = sequence.reduce((s, it) => s + (it.duration_ms || 1200), 0);
    let elapsed = 0;

    for (let i = 0; i < sequence.length; i++) {
      // Abandonner si une nouvelle séquence a démarré
      if (myGen !== this._gen) return;

      const item = sequence[i];
      if (callbacks.onWordStart) callbacks.onWordStart(item.word, i);
      if (callbacks.onProgress)
        callbacks.onProgress((elapsed / totalDur) * 100, item.word.toUpperCase());

      if (item.animation_url && this._mixer && this._avatar) {
        await this._playGLBThree(item.animation_url, item.duration_ms || 1200, myGen);
      } else if (item.fallback === 'alphabet' && item.letters?.length) {
        await this._playLetters(item.letters, myGen);
      } else {
        const sign = item.word.charAt(0).toUpperCase();
        await this._playSign(sign, item.duration_ms || 1200, myGen);
      }

      elapsed += item.duration_ms || 1200;
    }

    // Finaliser seulement si on est encore la séquence courante
    if (myGen !== this._gen) return;
    this.isPlaying = false;
    if (callbacks.onProgress)        callbacks.onProgress(100, 'Terminé');
    if (callbacks.onSequenceComplete) callbacks.onSequenceComplete();
  }

  /* ── Affichage d'un signe unique ──────────────────────────────────────────── */

  async _playSign(char, durationMs, gen) {
    if (gen !== undefined && gen !== this._gen) return;
    this._currentSign = char;
    if (this._renderer) this._renderer.startAnimation(char);

    await this._waitMs(durationMs, gen);

    // Figer le signe seulement si cette séquence est encore active
    if (gen === undefined || gen === this._gen) {
      if (this._renderer) {
        this._renderer.stop();
        this._renderer.draw(char);
      }
    }
  }

  /* ── Épellation lettre par lettre ────────────────────────────────────────── */

  async _playLetters(letters, gen) {
    for (const letter of letters) {
      if (gen !== undefined && gen !== this._gen) return;
      await this._playSign(letter, 700, gen);
      await this._waitMs(80, gen);
    }
  }

  /* ── GLB Three.js (futur) ────────────────────────────────────────────────── */

  async _playGLBThree(url, durationMs, gen) {
    return new Promise(resolve => {
      const cached = this._animCache.get(url);
      if (cached) {
        const action = this._mixer.clipAction(cached);
        action.timeScale = this.speed;
        action.reset().play();
        setTimeout(() => { action.stop(); resolve(); }, durationMs / this.speed);
        return;
      }
      if (typeof THREE === 'undefined' || typeof THREE.GLTFLoader === 'undefined') {
        setTimeout(resolve, durationMs); return;
      }
      const loader = new THREE.GLTFLoader();
      loader.load(url, gltf => {
        const clip = gltf.animations[0];
        if (!clip) { setTimeout(resolve, durationMs); return; }
        this._animCache.set(url, clip);
        const action = this._mixer.clipAction(clip);
        action.timeScale = this.speed;
        action.reset().play();
        setTimeout(() => { action.stop(); resolve(); }, durationMs / this.speed);
      }, undefined, () => setTimeout(resolve, durationMs));
    });
  }

  /* ── Attente avec pause + invalidation par génération ───────────────────── */

  _waitMs(ms, gen) {
    return new Promise(resolve => {
      let remaining = ms / this.speed;
      let lastTick  = Date.now();
      const tick = () => {
        // Abandon si nouvelle génération
        if (gen !== undefined && gen !== this._gen) { resolve(); return; }
        if (!this.isPlaying) { resolve(); return; }
        const now = Date.now();
        if (!this.isPaused) remaining -= (now - lastTick);
        lastTick = now;
        if (remaining <= 0) { resolve(); return; }
        setTimeout(tick, 30);
      };
      setTimeout(tick, 30);
    });
  }

  /* ── Contrôles publics ────────────────────────────────────────────────────── */

  setSpeed(multiplier) { this.speed = multiplier; }

  togglePause() {
    this.isPaused = !this.isPaused;
    if (this._renderer && this._currentSign) {
      if (this.isPaused) {
        this._renderer.stop();
        this._renderer.draw(this._currentSign);
      } else {
        this._renderer.startAnimation(this._currentSign);
      }
    }
  }

  reset() {
    this._gen++;            // invalide toute boucle en cours
    this.isPlaying    = false;
    this.isPaused     = false;
    this._currentSign = null;
    if (this._renderer) this._renderer.stop();
    this._drawIdle();
  }
}
