/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        'on-secondary-fixed-variant': '#f5f5f5',
        'on-background': '#f5f5f5',
        'secondary-container': '#242424',
        'surface-variant': '#202020',
        'primary-fixed': '#ffffff',
        'surface-dim': '#050505',
        'on-tertiary': '#ffffff',
        'inverse-primary': '#000000',
        'error-container': '#2a2a2a',
        'on-primary-fixed-variant': '#111111',
        'tertiary-fixed': '#ffffff',
        'tertiary-fixed-dim': '#d4d4d4',
        'secondary-fixed-dim': '#d4d4d4',
        'inverse-surface': '#ffffff',
        'on-surface': '#f5f5f5',
        'surface-container-highest': '#2d2d2d',
        'tertiary': '#d4d4d4',
        'background': '#050505',
        'primary': '#ffffff',
        'on-error-container': '#ffffff',
        'on-primary-container': '#ffffff',
        'primary-fixed-dim': '#e5e5e5',
        'on-surface-variant': '#bdbdbd',
        'on-primary': '#050505',
        'on-primary-fixed': '#050505',
        'error': '#ffffff',
        'surface-container-low': '#111111',
        'surface-bright': '#303030',
        'tertiary-container': '#1c1c1c',
        'primary-container': '#e5e5e5',
        'on-tertiary-container': '#ffffff',
        'surface-container-high': '#242424',
        'on-secondary-fixed': '#050505',
        'secondary': '#ffffff',
        'on-error': '#050505',
        'on-tertiary-fixed-variant': '#111111',
        'on-secondary-container': '#ffffff',
        'outline-variant': '#333333',
        'surface': '#050505',
        'on-tertiary-fixed': '#050505',
        'outline': '#777777',
        'inverse-on-surface': '#050505',
        'on-secondary': '#050505',
        'surface-container': '#171717',
        'surface-tint': '#ffffff',
        'surface-container-lowest': '#000000',
        'secondary-fixed': '#ffffff'
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
