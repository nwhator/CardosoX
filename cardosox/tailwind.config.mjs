/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        'on-secondary-fixed-variant': '#004395',
        'on-background': '#e5e2e1',
        'secondary-container': '#0566d9',
        'surface-variant': '#353534',
        'primary-fixed': '#e9ddff',
        'surface-dim': '#131313',
        'on-tertiary': '#482900',
        'inverse-primary': '#6d3bd7',
        'error-container': '#93000a',
        'on-primary-fixed-variant': '#5516be',
        'tertiary-fixed': '#ffdcbb',
        'tertiary-fixed-dim': '#ffb869',
        'secondary-fixed-dim': '#adc6ff',
        'inverse-surface': '#e5e2e1',
        'on-surface': '#e5e2e1',
        'surface-container-highest': '#353534',
        'tertiary': '#ffb869',
        'background': '#131313',
        'primary': '#d0bcff',
        'on-error-container': '#ffdad6',
        'on-primary-container': '#340080',
        'primary-fixed-dim': '#d0bcff',
        'on-surface-variant': '#cbc3d7',
        'on-primary': '#3c0091',
        'on-primary-fixed': '#23005c',
        'error': '#ffb4ab',
        'surface-container-low': '#1c1b1b',
        'surface-bright': '#3a3939',
        'tertiary-container': '#ca801e',
        'primary-container': '#a078ff',
        'on-tertiary-container': '#3f2300',
        'surface-container-high': '#2a2a2a',
        'on-secondary-fixed': '#001a42',
        'secondary': '#adc6ff',
        'on-error': '#690005',
        'on-tertiary-fixed-variant': '#673d00',
        'on-secondary-container': '#e6ecff',
        'outline-variant': '#494454',
        'surface': '#131313',
        'on-tertiary-fixed': '#2c1700',
        'outline': '#958ea0',
        'inverse-on-surface': '#313030',
        'on-secondary': '#002e6a',
        'surface-container': '#201f1f',
        'surface-tint': '#d0bcff',
        'surface-container-lowest': '#0e0e0e',
        'secondary-fixed': '#d8e2ff'
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
