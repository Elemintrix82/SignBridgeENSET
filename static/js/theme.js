/**
 * SignBridge — Theme manager
 * Dark/light mode toggle with localStorage persistence
 */
(function () {
  'use strict';

  const STORAGE_KEY = 'sb-theme';
  const ROOT = document.documentElement;

  function getTheme() {
    return localStorage.getItem(STORAGE_KEY) ||
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  }

  function applyTheme(theme) {
    ROOT.classList.toggle('dark', theme === 'dark');
    localStorage.setItem(STORAGE_KEY, theme);
    updateIcons(theme);
    dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
  }

  function updateIcons(theme) {
    const sun  = document.getElementById('icon-sun');
    const moon = document.getElementById('icon-moon');
    if (!sun || !moon) return;
    if (theme === 'dark') {
      sun.classList.remove('hidden');
      moon.classList.add('hidden');
    } else {
      sun.classList.add('hidden');
      moon.classList.remove('hidden');
    }
  }

  window.toggleTheme = function () {
    const current = getTheme();
    applyTheme(current === 'dark' ? 'light' : 'dark');
  };

  window.getCurrentTheme = getTheme;

  // Apply on DOM ready (icons may not exist yet during inline script)
  document.addEventListener('DOMContentLoaded', function () {
    updateIcons(getTheme());
  });

  // Sync across tabs
  window.addEventListener('storage', function (e) {
    if (e.key === STORAGE_KEY && e.newValue) applyTheme(e.newValue);
  });
})();
