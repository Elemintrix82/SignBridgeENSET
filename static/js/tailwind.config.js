/** @type {import('tailwindcss').Config} */
const path = require('path');
module.exports = {
  darkMode: 'class',
  content: [
    path.resolve(__dirname, '../../templates/**/*.html'),
    path.resolve(__dirname, './*.js'),
  ],
  theme: {
    extend: {
      colors: {
        'vert-cam':    '#007A5E',
        'vert-hover':  '#009970',
        'vert-light':  '#E6F4EE',
        'rouge-cam':   '#CE1126',
        'jaune-cam':   '#FCD116',
        'jaune-dark':  '#B8860B',
        'bg-base':     { DEFAULT: '#0D1117', light: '#FFFFFF' },
        'bg-surface':  { DEFAULT: '#161B22', light: '#F6F8FA' },
        'bg-elevated': { DEFAULT: '#21262D', light: '#FFFFFF' },
        'bg-overlay':  { DEFAULT: '#30363D', light: '#F0F2F5' },
        'border-subtle':  { DEFAULT: '#21262D', light: '#E1E4E8' },
        'border-default': { DEFAULT: '#30363D', light: '#D0D7DE' },
        'text-muted':     { DEFAULT: '#8B949E', light: '#656D76' },
        'text-secondary': { DEFAULT: '#C9D1D9', light: '#24292F' },
      },
      fontFamily: {
        poppins:  ['Poppins', 'sans-serif'],
        inter:    ['Inter', 'sans-serif'],
        mono:     ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        '2xs': '0.75rem',
        'xs':  '0.875rem',
        'sm':  '1rem',
        'md':  '1.125rem',
        'lg':  '1.5rem',
        'xl':  '2rem',
        '2xl': '3rem',
      },
      borderRadius: {
        'card': '12px',
        'btn':  '8px',
        'pill': '20px',
      },
      boxShadow: {
        'sm':  '0 1px 3px rgba(0,0,0,0.4)',
        'md':  '0 4px 12px rgba(0,0,0,0.5)',
        'lg':  '0 8px 32px rgba(0,0,0,0.6)',
        'sm-light': '0 1px 3px rgba(0,0,0,0.08)',
        'md-light': '0 4px 12px rgba(0,0,0,0.12)',
        'lg-light': '0 8px 32px rgba(0,0,0,0.16)',
      },
      animation: {
        'fade-in':        'fadeIn 0.4s ease forwards',
        'slide-up':       'slideUp 0.3s ease forwards',
        'slide-in-right': 'slideInRight 0.3s ease forwards',
        'pulse-slow':     'pulse 2s cubic-bezier(0.4,0,0.6,1) infinite',
        'ping-slow':      'ping 2s cubic-bezier(0,0,0.2,1) infinite',
        'bounce-soft':    'bounceSoft 0.6s ease infinite',
        'count-up':       'countUp 0.5s ease forwards',
        'skeleton':       'skeleton 1.5s ease-in-out infinite',
        'spin-slow':      'spin 2s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%':   { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%':   { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        bounceSoft: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%':      { transform: 'translateY(-6px)' },
        },
        skeleton: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      transitionDuration: {
        '150': '150ms',
        '200': '200ms',
        '300': '300ms',
        '400': '400ms',
      },
    },
  },
  plugins: [],
};
