---
name: Vitality Core
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#3c4a42'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#6c7a71'
  outline-variant: '#bbcabf'
  surface-tint: '#006c49'
  primary: '#006c49'
  on-primary: '#ffffff'
  primary-container: '#10b981'
  on-primary-container: '#00422b'
  inverse-primary: '#4edea3'
  secondary: '#2b6954'
  on-secondary: '#ffffff'
  secondary-container: '#adedd3'
  on-secondary-container: '#306d58'
  tertiary: '#55615a'
  on-tertiary: '#ffffff'
  tertiary-container: '#99a69e'
  on-tertiary-container: '#303c36'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#6ffbbe'
  primary-fixed-dim: '#4edea3'
  on-primary-fixed: '#002113'
  on-primary-fixed-variant: '#005236'
  secondary-fixed: '#b0f0d6'
  secondary-fixed-dim: '#95d3ba'
  on-secondary-fixed: '#002117'
  on-secondary-fixed-variant: '#0b513d'
  tertiary-fixed: '#d9e6dd'
  tertiary-fixed-dim: '#bdcac1'
  on-tertiary-fixed: '#131e19'
  on-tertiary-fixed-variant: '#3e4943'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  headline-xl:
    fontFamily: Manrope
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Manrope
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Manrope
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Manrope
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 14px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-max: 1280px
  gutter: 24px
  margin-desktop: 40px
  margin-mobile: 16px
---

## Brand & Style
The design system is centered on "Cognitive Clarity"—a philosophy that health management should reduce mental load, not increase it. The brand personality is professional, encouraging, and precise. It targets health-conscious individuals who value efficiency and data-driven insights.

The visual style is **Corporate Modern with a Tactile edge**. It utilizes a "Clean-Health" aesthetic: expansive whitespace to promote focus, a sophisticated interpretation of green to signify growth and vitality, and a structured layout that feels institutional yet warm. The interface should feel like a premium medical instrument redesigned for the home: high-fidelity, reliable, and aesthetically pleasing.

## Colors
The palette is rooted in the "Emerald Growth" spectrum. 

- **Primary (#10B981):** A vibrant, mid-tone green used for primary actions, success states, and progress indicators. It is the color of "action."
- **Secondary (#064E3B):** A deep, forest-toned green used for high-contrast text, headers, and navigation elements to provide grounding and authority.
- **Tertiary (#F0FDF4):** A soft mint wash used for large surface areas, background subtle highlights, and "soft" containers to reduce visual fatigue.
- **Neutral (#64748B):** A cool slate grey used for secondary information and supporting typography.

Backgrounds remain crisp white (#FFFFFF) or very light grey (#F8FAFC) to ensure the greens feel fresh and never muddy.

## Typography
The typographic system pairs **Manrope** for display and **Inter** for functional text. 

Manrope provides a modern, slightly geometric feel that works exceptionally well for numbers and data-heavy headlines. Use it for caloric totals, weight tracking milestones, and section titles. Inter is used for its high legibility in dense lists (food logs) and interface labels. 

Tighten letter-spacing on larger headlines to maintain a "premium" editorial look. Ensure all numerical data uses tabular figures where possible to keep columns aligned in meal logs.

## Layout & Spacing
The layout follows a **Fixed-Fluid Hybrid** model. On desktop, the main dashboard content is constrained to a 1280px container to ensure readability, while the background and sidebars may bleed to the edges. 

- **Grid:** A 12-column grid system.
- **Rhythm:** Use an 8px base unit. Component padding should lean towards generous (e.g., 24px or 32px inside cards) to create a sense of "air."
- **Breakpoints:**
  - *Mobile (<640px):* Single column, 16px margins. Bottom navigation bar.
  - *Tablet (640px - 1024px):* 2-column layout (Sidebar + Content). 24px margins.
  - *Desktop (>1024px):* 3-column potential (Sidebar + Main + AI/Stats Panel). 40px margins.

## Elevation & Depth
Depth is created through **Tonal Layering and Ambient Shadows**. Instead of heavy borders, use subtle elevation to separate information modules.

1.  **Level 0 (Base):** The main canvas, usually #F8FAFC.
2.  **Level 1 (Cards/Containers):** Pure white surfaces with a very soft, diffused shadow (0px 4px 20px rgba(0, 0, 0, 0.04)).
3.  **Level 2 (Active/Hover):** Slightly more pronounced shadow (0px 10px 30px rgba(0, 0, 0, 0.08)) to indicate interactivity.

Avoid pure black shadows; always tint shadows with a hint of the secondary green or slate grey to maintain the "clean" aesthetic.

## Shapes
The design system uses a **Rounded** language (0.5rem base) to feel approachable and friendly. 

- **Cards & Primary Containers:** Use 1rem (16px) for a soft, modern container feel.
- **Buttons:** Fully rounded (pill) or 0.75rem (12px) to differentiate from input fields.
- **Data Visualizations:** Bar charts should have rounded caps; donut charts should have a soft, rounded stroke terminal. This removes the "stiff" corporate feel and replaces it with an organic, health-centric vibe.

## Components
- **Buttons:** Primary buttons are solid Primary Green with white text. Secondary buttons use the Tertiary Green wash with Primary Green text. No borders.
- **AI Integration Area:** Unlike a chat bubble, the AI area is a "Command Surface." Use a subtle backdrop blur (Glassmorphism) and a dedicated gradient border (Primary to Secondary Green) to signify its "intelligence." Inputs here should be borderless with a soft inner shadow.
- **Data Visualization:** Use high-contrast greens against the white background. Use "Growth Rings" (circular progress bars) for daily macros.
- **Cards:** White background, 16px border-radius, soft shadow. Use a 4px vertical "accent stripe" on the left side of cards to categorize (e.g., Breakfast = Green, Exercise = Blue).
- **Input Fields:** Use a light grey background (#F1F5F9) instead of a border. When focused, transition to a white background with a Primary Green 2px ring.
- **Chips/Badges:** Use for food categories (e.g., "High Protein"). Pill-shaped, low-opacity background of the primary color with dark secondary green text.