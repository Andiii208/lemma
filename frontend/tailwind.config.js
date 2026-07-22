/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      /* ── 所有颜色引用 CSS 变量，自动跟随主题切换 ── */
      colors: {
        bg: {
          DEFAULT: 'var(--color-bg)',
          secondary: 'var(--color-bg-secondary)',
          tertiary: 'var(--color-bg-tertiary)',
          elevated: 'var(--color-bg-elevated)',
        },
        text: {
          DEFAULT: 'var(--color-text)',
          secondary: 'var(--color-text-secondary)',
          muted: 'var(--color-text-muted)',
        },
        accent: {
          DEFAULT: 'var(--color-accent)',
          hover: 'var(--color-accent-hover)',
          soft: 'var(--color-accent-soft)',
        },
        gold: 'var(--color-gold)',
        border: {
          DEFAULT: 'var(--color-border)',
          strong: 'var(--color-border-strong)',
        },
        success: 'var(--color-success)',
        warning: 'var(--color-warning)',
        error: 'var(--color-error)',
        amber: { 50: '#fffbeb', 100: '#fef3c7', 500: '#f59e0b', 700: '#b45309', 900: '#78350f' },
        red: { 50: '#fef2f2', 200: '#fecaca', 300: '#fca5a5', 500: '#ef4444', 600: '#dc2626', 700: '#b91c1c', 800: '#991b1b', 900: '#7f1d1d' },
        green: { 500: '#22c55e', 600: '#16a34a' },
      },

      /* ── 四层排版系统 ── */
      fontFamily: {
        display: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        serif: ['"Crimson Pro"', 'Georgia', 'serif'],
        sans: ['system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', '"PingFang SC"', '"Microsoft YaHei"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'Consolas', '"Courier New"', 'monospace'],
      },

      fontSize: {
        'display': ['36px', { lineHeight: '1.2', letterSpacing: '-0.02em' }],
        'h1':      ['28px', { lineHeight: '1.3', letterSpacing: '-0.01em' }],
        'h2':      ['22px', { lineHeight: '1.35', letterSpacing: '0' }],
        'h3':      ['16px', { lineHeight: '1.4', letterSpacing: '0.05em' }],
        'body':    ['15px', { lineHeight: '1.6' }],
        'ui':      ['13px', { lineHeight: '1.5' }],
        'caption': ['11px', { lineHeight: '1.4', letterSpacing: '0.08em' }],
      },

      borderRadius: {
        'editorial': '2px',
        'card': '4px',
      },

      animation: {
        'fade-in': 'fadeIn 0.25s var(--ease-out, ease-out)',
        'slide-up': 'slideUp 0.25s var(--ease-out, ease-out)',
        'view-enter': 'viewEnter 0.2s var(--ease-out, ease-out)',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        viewEnter: {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
