---
name: ModelForge Deep Tech
colors:
  surface: '#10131b'
  surface-dim: '#10131b'
  surface-bright: '#363941'
  surface-container-lowest: '#0b0e15'
  surface-container-low: '#181b23'
  surface-container: '#1d2027'
  surface-container-high: '#272a32'
  surface-container-highest: '#32353d'
  on-surface: '#e0e2ed'
  on-surface-variant: '#bbc9cf'
  inverse-surface: '#e0e2ed'
  inverse-on-surface: '#2d3038'
  outline: '#859399'
  outline-variant: '#3c494e'
  surface-tint: '#47d6ff'
  primary: '#a5e7ff'
  on-primary: '#003543'
  primary-container: '#00d2ff'
  on-primary-container: '#00566a'
  inverse-primary: '#00677f'
  secondary: '#d0bcff'
  on-secondary: '#3c0091'
  secondary-container: '#571bc1'
  on-secondary-container: '#c4abff'
  tertiary: '#69f6b9'
  on-tertiary: '#003824'
  tertiary-container: '#48d99e'
  on-tertiary-container: '#005b3d'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#b6ebff'
  primary-fixed-dim: '#47d6ff'
  on-primary-fixed: '#001f28'
  on-primary-fixed-variant: '#004e60'
  secondary-fixed: '#e9ddff'
  secondary-fixed-dim: '#d0bcff'
  on-secondary-fixed: '#23005c'
  on-secondary-fixed-variant: '#5516be'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#10131b'
  on-background: '#e0e2ed'
  surface-variant: '#32353d'
typography:
  headline-xl:
    fontFamily: Geist
    fontSize: 36px
    fontWeight: '600'
    lineHeight: 44px
    letterSpacing: -0.025em
  headline-xl-mobile:
    fontFamily: Geist
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.015em
  body-lg:
    fontFamily: Geist
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: -0.01em
  body-md:
    fontFamily: Geist
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: -0.005em
  body-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0em
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: -0.01em
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0em
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  space-2xs: 0.125rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-base: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
  space-2xl: 3rem
  gutter-mobile: 0.75rem
  gutter-desktop: 1.25rem
  margin-mobile: 1rem
  margin-desktop: 2rem
---

## Brand & Style
This design system establishes a high-performance, developer-first aesthetic tailored for deep learning engineers, MLOps specialists, and compiler architects. The visual atmosphere is precision-engineered, clinical, and authoritative, evoking the raw computational power and mathematical rigor of modern machine learning infrastructure.

The aesthetic fuses **Modern Technical Minimalism** with **Instrument-Grade Telemetry**. It prioritizes high information density, low optical fatigue across prolonged terminal and benchmarking sessions, and crisp visual hierarchies. Translucent glass treatments are employed sparingly to establish functional depth rather than superficial decoration, allowing critical execution statuses, quantization metrics, and hardware compilation pipelines to remain instantly legible.

## Colors
The color palette is built strictly for a dark-first environment, utilizing layered navy-charcoal surfaces, electric cyan primary accents, and telemetry-standard functional indicators.

### Surface System
- **Canvas Base (`neutral-950`):** `#080B12` — Deep void navy-charcoal background.
- **Surface Level 1 (`neutral-900`):** `#10151F` — Panels, cards, and primary app scaffolding.
- **Surface Level 2 (`neutral-850`):** `#151B26` — Sub-containers, elevated metrics modules, nested cards.
- **Surface Level 3 / Terminal (`neutral-800`):** `#1B2232` — Code viewports, log consoles, and input fields.
- **Structural Lines / Outlines:** `#1E2638` — Technical hairline dividers, matrix grid lines, and structural boundaries.

### Brand Accents
- **Primary Electric Cyan:** `#00D2FF` — Primary calls to action, compile triggers, active state glows, and telemetry highlights.
- **Primary Deep Cyan:** `#0284C7` — Hover states, gradient terminal endpoints, and focused container framing.
- **Secondary Ultraviolet:** `#8B5CF6` — Computational pipelines, TensorRT/ONNX graph transformations, and optimization flags.

### Telemetry & State Colors
- **Success / Compiled (`emerald`):** `#10B981` (Surface: `rgba(16, 185, 129, 0.08)`) — Verification, passed benchmarks, optimal throughput.
- **Warning / Queued (`amber`):** `#F59E0B` (Surface: `rgba(245, 158, 11, 0.08)`) — Cold starts, quantization accuracy loss, compilation queues.
- **Destructive / Error (`red`):** `#EF4444` (Surface: `rgba(239, 68, 68, 0.08)`) — Kernel failures, out-of-memory (OOM) exceptions, compile breaks.

## Typography
Typography is split purposefully between structural interface elements and technical telemetry:

- **Primary UI (`Geist`):** Delivers neutral, razor-sharp rendering at dense spatial rhythms. Used for navigation, layout headings, descriptions, modal prompts, and standard UI interactions. Headings leverage tight letter spacing (`-0.02em`) to mirror developer terminal tooling and modern CLI documentation.
- **Telemetry & Monospace (`JetBrains Mono`):** Applied to latency indicators, memory footprints, model weights/hashes, compiler flags, and raw terminal log viewports.
- **Numerics:** All monospace metrics must enforce tabular figures (`font-variant-numeric: tabular-nums`) to prevent layout shift during real-time hardware telemetry updates.

## Layout & Spacing
The layout architecture leverages a 12-column fluid grid system optimized for high-density console views and split-pane developer workspaces:

- **Desktop Form Factor (>1280px):** 12 columns, 20px (`1.25rem`) gutters, 32px (`2rem`) outer margin. Enables dense multi-pane views (e.g., compile tree on the left, telemetry charts in the center, compilation logs pinned to the right).
- **Tablet Form Factor (768px - 1279px):** 8 columns, 16px (`1rem`) gutters, 24px (`1.5rem`) outer margins. Right-hand telemetry panels collapse into tabbed draw views.
- **Mobile Form Factor (<768px):** 4 columns, 12px (`0.75rem`) gutters, 16px (`1rem`) outer margins. Dense metric arrays switch to horizontally scrollable micro-cards or vertical stacks.

### Density Rules
Interface components default to a compact 4px baseline sub-grid. Telemetry badges, code rows, and pipeline stages rely on strict `4px` / `8px` / `12px` paddings to maximize vertical scan area and screen real estate for complex architectures.

## Elevation & Depth
This design system rejects deep drop-shadows in favor of **Tonal Layering**, **Hairline Ghost Borders**, and **Subtle Translucent Luminance**:

- **Layer 0 (Canvas):** Pure `#080B12`.
- **Layer 1 (Module Panels / Cards):** Solid `#10151F` with a 1px structural border of `#1E2638`.
- **Layer 2 (Interactive Modules / Hovered Cards):** Solid `#151B26` with an upgraded border of `#2D3748` and an ambient diffuse glow: `0 0 20px rgba(0, 210, 255, 0.04)`.
- **Layer 3 (Overlays / Modals / Flyouts):** Acrylic glass styling utilizing `#10151F` at 85% opacity with `backdrop-filter: blur(12px)`, bounded by a 1px top-lit hairline `rgba(255, 255, 255, 0.1)`.
- **Active Compilation Glow:** Focused compilation nodes and active hardware runtimes emit a directional accent shadow (`0 0 12px rgba(0, 210, 255, 0.2)`).

## Shapes
The shape hierarchy emphasizes structural precision and technical exactness through controlled corner radii:

- **Micro Components (Badges, Chips, Checkboxes, Micro-inputs):** `4px` (`rounded-sm`).
- **Standard Controls (Buttons, Inputs, Select Menus):** `6px` (`rounded-md`).
- **Cards, Code Blocks, and Graph Nodes:** `8px` (`rounded-lg`) up to `12px` (`rounded-xl` for outer structural modules).
- **Pill Exceptions:** Restricted strictly to active pipeline connection pins, status indicator pulses, and terminal cursor indicators.

## Components

### Buttons
- **Primary:** Background `bg-[#00D2FF]`, text `#080B12` (`font-semibold`), border none. On hover: `bg-[#38BDF8]` with shadow `0 0 16px rgba(0, 210, 255, 0.35)`. Active: `scale(0.98)`.
- **Secondary / Action:** Background `#151B26`, text `#F1F5F9`, border `1px solid #1E2638`. On hover: border `#00D2FF` at 50% opacity, background `#1B2232`.
- **Terminal Ghost:** Background transparent, text `#94A3B8`, border `1px solid transparent`. On hover: background `#151B26`, text `#00D2FF`.

### Technical Badges & Status Chips
- Height `20px` to `24px`, padding `0 8px`, typography `label-sm` (`JetBrains Mono`).
- **Success (Compiled / Verified):** Text `#10B981`, background `rgba(16, 185, 129, 0.1)`, border `1px solid rgba(16, 185, 129, 0.25)`. Includes an optional leading 6px static dot.
- **Queued / Optimizing:** Text `#F59E0B`, background `rgba(245, 158, 11, 0.1)`, border `1px solid rgba(245, 158, 11, 0.25)`.
- **Quantization Specs (FP16, INT8, INT4):** Background `#151B26`, text `#00D2FF`, border `1px solid #1E2638`.

### Form Controls & Inputs
- **Inputs & Dropdowns:** Background `#10151F`, text `#F1F5F9`, border `1px solid #1E2638`, corner radius `6px`. Font: `Geist` 13px (placeholder `#64748B`).
- **Focus State:** Border `#00D2FF`, box shadow `0 0 0 1px #00D2FF`.
- **Checkboxes & Radios:** `16px x 16px`, background `#10151F`, border `1px solid #1E2638`. Checked state: background `#00D2FF` with `#080B12` inner tickmark.

### Cards & Telemetry Containers
- Background `#10151F`, border `1px solid #1E2638`, border-radius `12px` (`rounded-xl`), inner padding `16px` to `20px`.
- Card headers feature clean divider rules (`border-b border-[#1E2638]`) accompanied by metadata badges and action toggles aligned to the right edge.

### CI/CD Pipeline & Graph Nodes
- Graph nodes represent stages (e.g., PyTorch Parser, TensorRT Graph Surgeon, Quantization, Benchmarking).
- Enclosed within `#151B26` containers with `1px solid #1E2638`. Connected via dynamic SVG vector traces (`#1E2638` inactive, animated dashed `#00D2FF` active).

### Sparklines & Telemetry Streams
- Inline latency and VRAM telemetry graphs render on canvas or SVG without background fills.
- Lines use `#00D2FF` (1.5px stroke width) with an area fill gradient fading from `rgba(0, 210, 255, 0.15)` to `transparent`.