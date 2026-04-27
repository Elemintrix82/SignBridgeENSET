/**
 * SignBridge — HandSignRenderer v4
 * Affiche les vrais signes ASL via les images du dataset.
 * Animation flottante (breathing) conservée via requestAnimationFrame.
 *
 * API identique à v3 :
 *   new HandSignRenderer(canvasOrId)
 *   .draw(sign)            → affiche l'image statique
 *   .startAnimation(sign)  → affiche avec animation flottante
 *   .stop()                → arrête l'animation
 */
class HandSignRenderer {

  static IMG_BASE = '/static/images/signs/';

  /* ── Cache des images préchargées ──────────────────────────────────────── */
  static _cache = new Map();

  static _load(sign) {
    const key = String(sign).toUpperCase();
    if (HandSignRenderer._cache.has(key)) return HandSignRenderer._cache.get(key);
    const img = new Image();
    const p = new Promise(resolve => {
      img.onload  = () => resolve(img);
      img.onerror = () => resolve(null);
    });
    img.src = HandSignRenderer.IMG_BASE + key + '.jpg';
    HandSignRenderer._cache.set(key, p);
    return p;
  }

  /* ── Palette fond ───────────────────────────────────────────────────────── */
  static C = {
    bg0: '#07101A',
    bg1: '#0F1B2A',
    labelBg0:   'rgba(5,150,105,0.96)',
    labelBg1:   'rgba(4,120,87,0.96)',
    labelBorder:'rgba(52,211,153,0.55)',
  };

  constructor(canvasId) {
    this.canvas = typeof canvasId === 'string'
      ? document.getElementById(canvasId)
      : canvasId;
    this.ctx   = this.canvas?.getContext('2d');
    this._raf  = null;
    this._t    = 0;
    this._sign = 'A';
  }

  /* ── API publique ─────────────────────────────────────────────────────── */

  draw(sign) {
    this._sign = this._normalize(sign);
    this.stop();
    HandSignRenderer._load(this._sign).then(img => {
      this._render(0, img);
    });
  }

  startAnimation(sign) {
    this._sign = this._normalize(sign);
    if (this._raf) cancelAnimationFrame(this._raf);

    HandSignRenderer._load(this._sign).then(img => {
      const loop = () => {
        this._t += 0.03;
        this._render(this._t, img);
        this._raf = requestAnimationFrame(loop);
      };
      loop();
    });
  }

  stop() {
    if (this._raf) { cancelAnimationFrame(this._raf); this._raf = null; }
  }

  /* ── Rendu principal ─────────────────────────────────────────────────── */

  _render(t, img) {
    const cv = this.canvas, ctx = this.ctx;
    if (!ctx || !cv) return;

    const W = cv.clientWidth  || 280;
    const H = cv.clientHeight || 340;
    cv.width = W; cv.height = H;

    // Fond dégradé
    const bg = ctx.createRadialGradient(W/2, H*0.38, 15, W/2, H*0.5, W * 0.92);
    bg.addColorStop(0, HandSignRenderer.C.bg1);
    bg.addColorStop(1, HandSignRenderer.C.bg0);
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);

    if (img) {
      // Animation flottante (breathing)
      const bounce = Math.sin(t * 1.2) * 6;
      const pulse  = 1 + Math.sin(t * 1.2) * 0.012;

      // Calcul taille pour couvrir ~80% du canvas en conservant le ratio
      const ratio   = img.naturalWidth / img.naturalHeight;
      let iW = W * 0.82 * pulse;
      let iH = iW / ratio;
      if (iH > H * 0.82) { iH = H * 0.82 * pulse; iW = iH * ratio; }

      const ix = (W - iW) / 2;
      const iy = (H - iH) / 2 + bounce;

      // Halo vert subtil derrière l'image
      ctx.save();
      ctx.shadowColor  = 'rgba(16,185,129,0.22)';
      ctx.shadowBlur   = 28;
      ctx.drawImage(img, ix, iy, iW, iH);
      ctx.restore();

      // Badge lettre/chiffre
      this._drawLabel(ctx, this._sign);
    } else {
      // Fallback texte si image absente
      ctx.fillStyle = 'rgba(52,211,153,0.6)';
      ctx.font      = `bold ${Math.min(W, H) * 0.45}px Poppins, Inter, sans-serif`;
      ctx.textAlign    = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(this._sign, W / 2, H / 2);
      ctx.textAlign    = 'left';
      ctx.textBaseline = 'alphabetic';
    }
  }

  /* ── Badge lettre ───────────────────────────────────────────────────── */

  _drawLabel(ctx, sign) {
    const C  = HandSignRenderer.C;
    const bw = 46, bh = 46, br = 10;
    const bx = this.canvas.width  - bw - 10;
    const by = 10;

    ctx.beginPath();
    ctx.roundRect(bx, by, bw, bh, br);
    const g = ctx.createLinearGradient(bx, by, bx, by + bh);
    g.addColorStop(0, C.labelBg0);
    g.addColorStop(1, C.labelBg1);
    ctx.fillStyle = g;
    ctx.fill();
    ctx.strokeStyle = C.labelBorder;
    ctx.lineWidth = 1.5;
    ctx.stroke();

    ctx.fillStyle    = '#ffffff';
    ctx.font         = 'bold 24px Poppins, Inter, sans-serif';
    ctx.textAlign    = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(sign, bx + bw / 2, by + bh / 2 + 1);
    ctx.textAlign    = 'left';
    ctx.textBaseline = 'alphabetic';
  }

  /* ── Normalisation ──────────────────────────────────────────────────── */

  _normalize(sign) {
    const s = String(sign).toUpperCase().trim();
    return /^[A-Z0-9]$/.test(s) ? s : (s[0] || 'A');
  }
}
