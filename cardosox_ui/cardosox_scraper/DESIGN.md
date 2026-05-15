---
name: CardosoX Scraper
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#3a3939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#cbc3d7'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#958ea0'
  outline-variant: '#494454'
  surface-tint: '#d0bcff'
  primary: '#d0bcff'
  on-primary: '#3c0091'
  primary-container: '#a078ff'
  on-primary-container: '#340080'
  inverse-primary: '#6d3bd7'
  secondary: '#adc6ff'
  on-secondary: '#002e6a'
  secondary-container: '#0566d9'
  on-secondary-container: '#e6ecff'
  tertiary: '#ffb869'
  on-tertiary: '#482900'
  tertiary-container: '#ca801e'
  on-tertiary-container: '#3f2300'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e9ddff'
  primary-fixed-dim: '#d0bcff'
  on-primary-fixed: '#23005c'
  on-primary-fixed-variant: '#5516be'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc6ff'
  on-secondary-fixed: '#001a42'
  on-secondary-fixed-variant: '#004395'
  tertiary-fixed: '#ffdcbb'
  tertiary-fixed-dim: '#ffb869'
  on-tertiary-fixed: '#2c1700'
  on-tertiary-fixed-variant: '#673d00'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display-lg:
    fontFamily: Geist
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-md:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  container-max: 1280px
  gutter: 24px
  margin-mobile: 16px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
  glass-padding: 24px
---

## Brand & Style

The design system is engineered for a high-performance, developer-centric scraping platform. It evokes a sense of "technological clairvoyance"—powerful, precise, and sophisticated. Drawing from **Glassmorphism** and **Modern Minimalism**, the UI prioritizes depth through transparency and luminosity rather than traditional skeuomorphism.

The aesthetic is inspired by high-end engineering tools like Linear and Vercel. It utilizes a deep "Obsidian" base to allow neon accents to function as functional beacons. The emotional response should be one of absolute control and premium reliability, using subtle motion and light to guide the developer through complex data extraction workflows.

## Colors

This design system utilizes a "Deep Space" palette. The foundation is `#0A0A0A`, providing a true-black environment that eliminates visual noise. 

- **Primary & Secondary**: Neon Purple and Electric Blue are used exclusively for interactive states, progress indicators, and primary call-to-actions. They should frequently appear as a gradient to imply dynamic energy.
- **Glass Fills**: Background surfaces use semi-transparent whites (`rgba(255, 255, 255, 0.03)`) combined with heavy backdrop blurs (20px+) to create a sense of layered glass.
- **Glows**: Interactive elements utilize soft outer glows (box-shadows with high spread and low opacity) to simulate light emission from the screen.

## Typography

The typography system relies on **Geist** for its precision and developer-friendly proportions. It is supplemented by **JetBrains Mono** for technical data, selector strings, and terminal outputs to maintain a "built-for-builders" aesthetic.

- **Contrast**: Headings should be pure white (`#FFFFFF`), while secondary body text should drop to an off-white/grey (`#A1A1AA`) to establish clear information hierarchy.
- **Micro-copy**: Use the `label-caps` style for section headers and small metadata to provide an architectural feel to the interface.

## Layout & Spacing

The layout utilizes a **Fixed Grid** model for desktop dashboards to ensure data density remains manageable and aesthetically centered. 

- **Grid System**: A 12-column grid with 24px gutters. 
- **Subtle Grid Patterns**: Backgrounds should feature a very faint "Blueprint Grid" (1px lines every 40px, opacity at 0.03) to reinforce the scraping/engineering theme.
- **Rhythm**: Use a 4px base unit. All internal component padding should be multiples of 8px to maintain a strict, technical alignment.
- **Mobile**: On mobile devices, columns collapse to a single-stack with 16px margins, while glass cards maintain their internal 24px padding for readability.

## Elevation & Depth

Depth is conveyed through **back-lit transparency** rather than traditional drop shadows.

1.  **Level 0 (Base)**: The `#0A0A0A` background with the subtle grid pattern.
2.  **Level 1 (Cards/Panels)**: Glass surfaces with `backdrop-filter: blur(20px)` and a `1px` solid border (`rgba(255, 255, 255, 0.08)`).
3.  **Level 2 (Popovers/Modals)**: Increased border opacity and a subtle "inner glow" using a white `1px` inset shadow at the top edge to simulate a light source from above.
4.  **Luminous Depth**: Use large, blurred "Gradient Blobs" (Purple/Blue) positioned deep behind the glass layers to create organic, floating pockets of color that move slightly on scroll.

## Shapes

The shape language is sophisticated and modern, utilizing generous corner radii to offset the technical "hardness" of the dark theme.

- **Standard Radius**: 16px (`rounded-lg`) is the default for cards and primary containers.
- **Component Radius**: 8px (`rounded-md`) for buttons and input fields to maintain a sense of precision.
- **Interactive States**: When hovered, cards may subtly expand or increase their border luminosity, but the corner radius remains constant to ensure the grid feels stable.

## Components

### Buttons
- **Primary**: Gradient fill (Purple to Blue). On hover, add a `box-shadow` of the same gradient with a 20px blur to create a "glowing" effect.
- **Secondary**: Ghost style with the 1px white/glass border. On hover, the background fills with `rgba(255, 255, 255, 0.05)`.

### Glass Cards
- All containers must have `backdrop-filter: blur(20px)`.
- Borders should be "gradient borders" if possible, or simple `rgba(255, 255, 255, 0.1)` strokes.

### Input Fields
- Background: `rgba(0, 0, 0, 0.4)`. 
- Border: Sharp 1px stroke. Focus state triggers a Primary Purple border and a subtle outer glow.
- Typeface: JetBrains Mono for "Scraper Selectors" or "Regex" inputs.

### Chips & Status
- **Active Scraper**: Pulse animation using a small 6px circle with a `secondary` blue glow.
- **Status Chips**: Low-opacity fills (e.g., Success Green at 10% opacity) with high-saturation text.

### Data Visualization
- Use thin, high-contrast lines for charts.
- Areas under lines should use vertical gradients fading from accent colors to transparent.