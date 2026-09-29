---
name: Modern Document Intelligence
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
  on-surface-variant: '#464555'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#0058be'
  on-secondary: '#ffffff'
  secondary-container: '#2170e4'
  on-secondary-container: '#fefcff'
  tertiary: '#005338'
  on-tertiary: '#ffffff'
  tertiary-container: '#006e4b'
  on-tertiary-container: '#67f4b7'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc6ff'
  on-secondary-fixed: '#001a42'
  on-secondary-fixed-variant: '#004395'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '600'
    lineHeight: 44px
    letterSpacing: -0.025em
  headline-lg:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22.4px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.01em
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-tablet: 1.5rem
  margin-desktop: 2rem
  space-xs: 0.5rem
  space-sm: 0.75rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
  space-2xl: 3rem
---

## Brand & Style

This design system embodies a modern, focused productivity workspace engineered for conversational document analysis. It bridges technical precision with quiet approachability, drawing inspiration from high-craft productivity software such as Linear and Notion. 

The emotional tone is calm, credible, and frictionless. Users dealing with dense legal, financial, or technical documents require an interface that minimizes cognitive load, maintains high legibility, and instills confidence in AI-generated answers. The aesthetic avoids ornamental distractions, relying instead on deliberate spacing, refined typographic rhythm, crisp micro-borders, and tactile interaction feedback.

## Colors

The palette uses Indigo as the authoritative anchor for primary interactions, paired with Slate neutrals for visual balance and structural hierarchy.

### System Roles
- **Primary Indigo (`#4F46E5`)**: Key user actions, focused inputs, active document selections, and primary AI cues. Hover state settles at `#4338CA`; soft tint is `#EEF2FF`.
- **Informational / Processing Blue (`#3B82F6`)**: Vector indexing, asynchronous parsing, and real-time inference activity. Soft tint: `#EFF6FF`.
- **Success Emerald (`#10B981`)**: Complete ingestion, verified citations, and positive status tokens. Soft tint: `#ECFDF5`.
- **Warning Amber (`#F59E0B`)**: Token limits, truncated context warnings, or low-confidence matches. Soft tint: `#FFFBEB`.
- **Critical Rose (`#F43F5E`)**: File parsing errors, rejected uploads, and service interruptions. Soft tint: `#FFF1F2`.

### Neutral Surfaces & Theme Modes
- **Light Theme**: Canvas background is `#F8FAFC` (Slate-50), container surfaces are `#FFFFFF`, and structural borders use `#E2E8F0` (Slate-200). Text defaults to `#0F172A` (Slate-900) for headings and `#334155` (Slate-700) for body copy.
- **Dark Theme**: Canvas shifts to `#0F172A` (Slate-900), elevated panels and cards rest on `#1E293B` (Slate-800), with hairline borders at `#334155` (Slate-700). High-emphasis text relies on `#F8FAFC`.

## Typography

The type scale relies entirely on Inter for interface elements and JetBrains Mono for technical metadata, document references, and code blocks. 

Headings carry a tight tracking profile (`-0.01em` to `-0.025em`) at weight `600` (semibold) to yield an assertive, editorial presence. Body text balances legibility and comfort using a relaxed `1.6` line-height ratio on 14px (`body-md`), ensuring long conversational extracts and analytical summaries remain effortless to scan. Monospaced tokens appear in inline citations, document hashes, and page anchor stamps.

## Layout & Spacing

The layout is constructed around an 8px baseline grid, translating to standard REM units (`space-xs` = 8px, `space-md` = 16px, `space-lg` = 24px, `space-xl` = 32px, `space-2xl` = 48px).

### Viewport Modes & Adaptation
- **Desktop (1024px and above)**: Employs a split-pane productivity layout. The document viewing pane and the chat interaction feed share a fluid horizontal split with a persistent 280px navigation rail. Margins scale to `2rem` (32px), with `1.5rem` (24px) gutters.
- **Tablet (768px – 1023px)**: Sidebars collapse into slide-out sheets. The interface prioritizes either the PDF viewer or the chat thread via a dual-tab segmented toggle.
- **Mobile (< 768px)**: Canvas margins drop to `1rem` (16px). Content stacks vertically in a single-column flow, with full-width bottom sheets for citations and PDF page previews.

## Elevation & Depth

Visual hierarchy is maintained through subtle tonal contrast coupled with precise, low-spread ambient shadows and 1px structural boundaries.

- **Flat/Resting (`elevation-0`)**: Content panels, split panes, and inline document viewports sit flush at `#FFFFFF` (Dark: `#1E293B`) encased in a 1px border of `#E2E8F0` (Dark: `#334155`).
- **Low Elevation / Interactive (`elevation-1`)**: Dropdown lists, card hovers, and floating chat bars use `0 1px 3px 0 rgba(15, 23, 42, 0.06), 0 1px 2px -1px rgba(15, 23, 42, 0.04)`.
- **Medium Elevation / Overlays (`elevation-2`)**: Document upload modals, citation popovers, and contextual action menus use `0 4px 6px -1px rgba(15, 23, 42, 0.08), 0 2px 4px -2px rgba(15, 23, 42, 0.04)`.
- **High Elevation / Modals (`elevation-3`)**: File drop overlays and full dialogs use `0 20px 25px -5px rgba(15, 23, 42, 0.1), 0 8px 10px -6px rgba(15, 23, 42, 0.04)`.

Dark mode reduces shadow reliance and introduces a 1px inner border highlight (`inset 0 1px 0 0 rgba(255, 255, 255, 0.05)`) on elevated containers.

## Shapes

The design uses a balanced rounded geometry to create a modern yet structured feel.
- **Cards & Modals**: Standardized at `rounded-lg` (12px / 0.75rem), yielding clean structural grouping.
- **Buttons, Text Inputs & Dropdown Triggers**: Set to `rounded-md` (8px / 0.5rem) for a compact, click-focused silhouette.
- **Pill Badges & Citations**: Explicitly set to full radius (`9999px`) to distinguish interactive metadata and document status flags from block UI elements.

## Components

### Buttons
- **Primary**: Solid Indigo (`#4F46E5`), text white, `8px` border-radius, font-medium (`label-md`). Hover state `#4338CA`. Active state `#3730A3`. Focus ring: `2px` offset, `2px` Indigo-500.
- **Secondary (Outlined)**: 1px border in `#E2E8F0`, text Slate-700, background `#FFFFFF`. Hover state switches to `#F8FAFC`.
- **Ghost**: Transparent background, text Slate-600, padding identical to outlined buttons. Hover: `#F1F5F9` (Slate-100).

### Status Badges
Pill-shaped containers (`rounded-full`, vertical padding `2px`, horizontal padding `10px`, font size `label-sm`).
- **UPLOADED**: Background `#F1F5F9`, border `#E2E8F0`, text `#475569`.
- **PROCESSING**: Background `#EFF6FF`, border `#BFDBFE`, text `#1D4ED8`. Accompanied by a leading 12px animated SVG spinner.
- **READY**: Background `#ECFDF5`, border `#A7F3D0`, text `#047857`. Leading 6px solid emerald dot.
- **FAILED**: Background `#FFF1F2`, border `#FECDD3`, text `#BE123C`.

### Text Inputs & Search
Inputs use a height of 40px, `rounded-md` (8px), `#FFFFFF` background, and a 1px border in `#CBD5E1`. Placeholder text sits in `#94A3B8`. Focus state applies a border of `#4F46E5` paired with `box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15)`. Labels sit 6px above inputs in `label-sm` (Slate-700). Helper and validation texts render below at `body-sm`.

### Checkboxes & Radio Buttons
Control footprints are 16px × 16px with a 1px border in `#CBD5E1` (checkboxes: `rounded`, radios: `rounded-full`). On checked state, they fill with `#4F46E5` displaying a crisp white micro-check or centered dot.

### Cards & Container Panels
Surfaces use `#FFFFFF` (Dark: `#1E293B`), `rounded-lg` (12px), an outer 1px border of `#E2E8F0`, and `elevation-0` or `elevation-1`. Headers within cards have an internal bottom border dividing the header and content zone with a unified 16px inner padding.

### Chat & Citation Artifacts
- **User Bubble**: Align right, background `#EEF2FF`, border 1px solid `#E0E7FF`, text `#1E1B4B`, `rounded-lg` with the bottom-right corner slightly tapered.
- **Assistant Bubble**: Align left, background `#FFFFFF` (Dark: `#1E293B`), border 1px solid `#E2E8F0`, text `#0F172A`. Contains markdown styling with code snippets styled via `JetBrains Mono` and subtle background tint `#F1F5F9`.
- **Citation Chip**: Inline clickable token formatted as `[p. X]`. Background `#F8FAFC`, border 1px solid `#CBD5E1`, text `#4F46E5`, `rounded-full`, font size `code-sm`. Hover invokes an instant document jump and highlights the corresponding coordinate overlay in the PDF viewer.