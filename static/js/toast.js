/**
 * SignBridge — Toast notification system
 * window.toast.success / .error / .info / .warning
 */
(function () {
  'use strict';

  const DURATION = 4000;

  const ICONS = {
    success: '<i class="fas fa-check-circle" style="color:#22c55e;flex-shrink:0"></i>',
    error:   '<i class="fas fa-times-circle" style="color:#ef4444;flex-shrink:0"></i>',
    info:    '<i class="fas fa-info-circle"  style="color:#3b82f6;flex-shrink:0"></i>',
    warning: '<i class="fas fa-exclamation-triangle" style="color:#f59e0b;flex-shrink:0"></i>',
  };

  const BORDER_COLORS = {
    success: 'rgba(34,197,94,0.3)',
    error:   'rgba(239,68,68,0.3)',
    info:    'rgba(59,130,246,0.3)',
    warning: 'rgba(245,158,11,0.3)',
  };

  function getContainer() {
    let c = document.getElementById('toast-container');
    if (!c) {
      c = document.createElement('div');
      c.id = 'toast-container';
      c.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:8px;pointer-events:none';
      document.body.appendChild(c);
    }
    return c;
  }

  function show(message, type) {
    const container = getContainer();
    const toast     = document.createElement('div');

    toast.className = 'toast';
    toast.style.cssText = [
      'min-width:280px;max-width:360px',
      'background:var(--bg-surface)',
      'border:1px solid ' + (BORDER_COLORS[type] || 'var(--border-default)'),
      'border-radius:10px',
      'padding:14px 16px',
      'box-shadow:var(--shadow-lg)',
      'pointer-events:auto',
      'transform:translateX(120%)',
      'opacity:0',
      'transition:transform 300ms cubic-bezier(0.34,1.56,0.64,1),opacity 300ms ease',
      'overflow:hidden',
      'position:relative',
      'cursor:pointer',
    ].join(';');

    toast.innerHTML = [
      '<div style="display:flex;align-items:flex-start;gap:10px">',
      ICONS[type] || ICONS.info,
      '<span style="font-size:14px;line-height:1.5;flex:1;color:var(--text-primary)">' + escapeHtml(message) + '</span>',
      '<button style="background:none;border:none;color:var(--text-muted);cursor:pointer;padding:0;font-size:14px;flex-shrink:0;line-height:1" onclick="this.closest(\'.toast\').remove()">',
      '<i class="fas fa-times"></i>',
      '</button>',
      '</div>',
      '<div class="toast-progress" style="position:absolute;bottom:0;left:0;height:2px;background:' + (BORDER_COLORS[type] || 'var(--vert-cam)') + ';width:100%;animation:toast-shrink ' + DURATION + 'ms linear forwards"></div>',
    ].join('');

    // Inject keyframe once
    if (!document.getElementById('toast-kf')) {
      const style = document.createElement('style');
      style.id = 'toast-kf';
      style.textContent = '@keyframes toast-shrink{from{width:100%}to{width:0%}}';
      document.head.appendChild(style);
    }

    container.appendChild(toast);

    // Trigger enter animation
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        toast.style.transform = 'translateX(0)';
        toast.style.opacity   = '1';
      });
    });

    // Auto dismiss
    const timer = setTimeout(() => dismiss(toast), DURATION);

    toast.addEventListener('click', function () {
      clearTimeout(timer);
      dismiss(toast);
    });
  }

  function dismiss(toast) {
    toast.style.transform = 'translateX(120%)';
    toast.style.opacity   = '0';
    setTimeout(() => toast.remove(), 350);
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  window.toast = {
    success: (msg) => show(msg, 'success'),
    error:   (msg) => show(msg, 'error'),
    info:    (msg) => show(msg, 'info'),
    warning: (msg) => show(msg, 'warning'),
  };
})();
