/** @type {import('tailwindcss').Config} */
const colorToken = (name) => `rgb(var(--color-${name}) / <alpha-value>)`;

export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        'background': colorToken('background'),
        'on-background': colorToken('on-background'),
        'surface': colorToken('surface'),
        'on-surface': colorToken('on-surface'),
        'surface-variant': colorToken('surface-variant'),
        'on-surface-variant': colorToken('on-surface-variant'),
        'surface-dim': colorToken('surface-dim'),
        'surface-bright': colorToken('surface-bright'),
        'surface-tint': colorToken('surface-tint'),
        'surface-container-lowest': colorToken('surface-container-lowest'),
        'surface-container-low': colorToken('surface-container-low'),
        'surface-container': colorToken('surface-container'),
        'surface-container-high': colorToken('surface-container-high'),
        'surface-container-highest': colorToken('surface-container-highest'),
        'primary': colorToken('primary'),
        'on-primary': colorToken('on-primary'),
        'primary-container': colorToken('primary-container'),
        'on-primary-container': colorToken('on-primary-container'),
        'primary-fixed': colorToken('primary-fixed'),
        'on-primary-fixed': colorToken('on-primary-fixed'),
        'primary-fixed-dim': colorToken('primary-fixed-dim'),
        'on-primary-fixed-variant': colorToken('on-primary-fixed-variant'),
        'secondary': colorToken('secondary'),
        'on-secondary': colorToken('on-secondary'),
        'secondary-container': colorToken('secondary-container'),
        'on-secondary-container': colorToken('on-secondary-container'),
        'secondary-fixed': colorToken('secondary-fixed'),
        'on-secondary-fixed': colorToken('on-secondary-fixed'),
        'secondary-fixed-dim': colorToken('secondary-fixed-dim'),
        'on-secondary-fixed-variant': colorToken('on-secondary-fixed-variant'),
        'tertiary': colorToken('tertiary'),
        'on-tertiary': colorToken('on-tertiary'),
        'tertiary-container': colorToken('tertiary-container'),
        'on-tertiary-container': colorToken('on-tertiary-container'),
        'tertiary-fixed': colorToken('tertiary-fixed'),
        'on-tertiary-fixed': colorToken('on-tertiary-fixed'),
        'tertiary-fixed-dim': colorToken('tertiary-fixed-dim'),
        'on-tertiary-fixed-variant': colorToken('on-tertiary-fixed-variant'),
        'error': colorToken('error'),
        'on-error': colorToken('on-error'),
        'error-container': colorToken('error-container'),
        'on-error-container': colorToken('on-error-container'),
        'outline': colorToken('outline'),
        'outline-variant': colorToken('outline-variant'),
        'inverse-surface': colorToken('inverse-surface'),
        'inverse-on-surface': colorToken('inverse-on-surface'),
        'inverse-primary': colorToken('inverse-primary')
      },
      borderRadius: {
        DEFAULT: '0.25rem',
        'lg': '0.5rem',
        'xl': '0.75rem',
        'full': '9999px'
      },
      spacing: {
        'gutter': '24px',
        'margin-mobile': '16px',
        'stack-md': '16px',
        'stack-sm': '8px',
        'glass-padding': '24px',
        'container-max': '1280px',
        'stack-lg': '32px'
      },
      fontFamily: {
        'body-md': ['Geist', 'sans-serif'],
        'headline-lg': ['Geist', 'sans-serif'],
        'display-lg': ['Geist', 'sans-serif'],
        'code-sm': ['JetBrains Mono', 'monospace']
      },
      fontSize: {
        'body-md': ['16px', { lineHeight: '24px', fontWeight: '400' }],
        'headline-lg': ['32px', { lineHeight: '40px', letterSpacing: '-0.01em', fontWeight: '600' }],
        'headline-lg-mobile': ['24px', { lineHeight: '32px', fontWeight: '600' }],
        'display-lg': ['48px', { lineHeight: '56px', letterSpacing: '-0.02em', fontWeight: '700' }],
        'label-caps': ['12px', { lineHeight: '16px', letterSpacing: '0.05em', fontWeight: '600' }],
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-soft': 'pulseSoft 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' }
        }
      }
    }
  },
  plugins: []
}
