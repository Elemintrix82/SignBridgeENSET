/**
 * SignBridge — Animations utilitaires
 * IntersectionObserver, countUp, micro-interactions générales
 */
(function () {
  'use strict';

  // ── IntersectionObserver : fade-in au scroll ──────────────────
  const fadeObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('fade-in');
      entry.target.style.opacity = '';
      fadeObserver.unobserve(entry.target);
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  document.addEventListener('DOMContentLoaded', () => {
    // Animer les éléments avec data-animate
    document.querySelectorAll('[data-animate]').forEach(el => {
      el.style.opacity = '0';
      fadeObserver.observe(el);
    });

    // Micro-interactions : hover boutons
    applyButtonMicroInteractions();

    // Nav underline slide
    applyNavUnderlines();

    // Stagger cards
    applyStaggerCards();
  });

  // ── Button micro-interactions ────────────────────────────────
  function applyButtonMicroInteractions() {
    document.querySelectorAll('.btn-primary, .btn-secondary, .btn-danger').forEach(btn => {
      if (btn.dataset.microdone) return;
      btn.dataset.microdone = '1';

      btn.addEventListener('mousedown', function () {
        this.style.transform = 'translateY(0) scale(0.98)';
      });
      btn.addEventListener('mouseup', function () {
        this.style.transform = '';
      });
      btn.addEventListener('mouseleave', function () {
        this.style.transform = '';
      });
    });
  }

  // ── Nav link underline animation ─────────────────────────────
  function applyNavUnderlines() {
    document.querySelectorAll('.nav-link:not([data-no-underline])').forEach(link => {
      if (link.dataset.underdone) return;
      link.dataset.underdone = '1';
      link.style.position = 'relative';

      const line = document.createElement('span');
      line.style.cssText = [
        'position:absolute', 'bottom:-2px', 'left:0', 'right:100%',
        'height:1.5px', 'background:var(--vert-cam)',
        'transition:right 200ms ease', 'border-radius:1px',
      ].join(';');
      link.appendChild(line);

      link.addEventListener('mouseenter', () => { line.style.right = '0'; });
      link.addEventListener('mouseleave', () => { line.style.right = '100%'; });
    });
  }

  // ── Stagger cards (apply delay to grid children) ─────────────
  function applyStaggerCards() {
    document.querySelectorAll('.signs-grid, .kpi-grid, .features-grid').forEach(grid => {
      Array.from(grid.children).forEach((child, i) => {
        child.style.animationDelay = (i * 60) + 'ms';
        child.classList.add('fade-in');
      });
    });
  }

  // ── CountUp utility ──────────────────────────────────────────
  window.countUp = function (el, target, suffix, duration) {
    duration = duration || 1200;
    const start   = Date.now();
    const from    = parseInt(el.textContent) || 0;

    function update() {
      const elapsed = Date.now() - start;
      const progress = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3); // cubic out
      el.textContent = Math.round(from + (target - from) * ease) + (suffix || '');
      if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
  };

  // ── Skeleton loader helpers ──────────────────────────────────
  window.showSkeleton = function (containerId, count, height) {
    const container = document.getElementById(containerId);
    if (!container) return;
    height = height || 20;
    container.innerHTML = Array(count || 3).fill(0).map(() =>
      `<div class="skeleton" style="height:${height}px;border-radius:6px;margin-bottom:10px"></div>`
    ).join('');
  };

  window.hideSkeleton = function (containerId) {
    const container = document.getElementById(containerId);
    if (container) container.innerHTML = '';
  };

  // ── Ripple effect on click ────────────────────────────────────
  document.addEventListener('click', function (e) {
    const btn = e.target.closest('.btn-primary, .btn-secondary');
    if (!btn || btn.disabled) return;

    const rect   = btn.getBoundingClientRect();
    const ripple = document.createElement('span');
    const size   = Math.max(rect.width, rect.height) * 1.5;
    const x      = e.clientX - rect.left - size / 2;
    const y      = e.clientY - rect.top  - size / 2;

    ripple.style.cssText = [
      'position:absolute',
      `width:${size}px`, `height:${size}px`,
      `left:${x}px`,     `top:${y}px`,
      'border-radius:50%',
      'background:rgba(255,255,255,0.15)',
      'transform:scale(0)',
      'animation:ripple-expand 400ms ease forwards',
      'pointer-events:none',
    ].join(';');

    const prev = btn.style.position;
    btn.style.position = 'relative';
    btn.style.overflow = 'hidden';
    btn.appendChild(ripple);
    setTimeout(() => { ripple.remove(); btn.style.position = prev; }, 450);
  });

  if (!document.getElementById('ripple-kf')) {
    const s = document.createElement('style');
    s.id = 'ripple-kf';
    s.textContent = '@keyframes ripple-expand{to{transform:scale(1);opacity:0}}';
    document.head.appendChild(s);
  }

  // ── Smooth scroll for anchor links ───────────────────────────
  document.addEventListener('click', function (e) {
    const a = e.target.closest('a[href^="#"]');
    if (!a) return;
    const target = document.querySelector(a.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });

  // ── Auto-resize textarea ──────────────────────────────────────
  document.addEventListener('input', function (e) {
    if (e.target.tagName !== 'TEXTAREA') return;
    const ta  = e.target;
    const max = parseInt(ta.style.maxHeight) || 9999;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, max) + 'px';
  });

  // ── Public API ────────────────────────────────────────────────
  window.SBAnimations = {
    applyButtonMicroInteractions,
    applyNavUnderlines,
    applyStaggerCards,
  };
})();
