---
name: ChatLaw
description: High-density module mosaic for Indian-law chat — ash ground, hairline modules, signal-red tabs.
colors:
  background: "#f5f5f5"
  surface: "#ffffff"
  foreground: "#111111"
  ink-muted: "#6b6b6b"
  line: "#d0d0d0"
  signal: "#db1b1a"
  signal-soft: "#fce8e8"
  signal-mid: "#f5c2c0"
  module-fill: "#f0f0f0"
  focus: "#111111"
  warn: "#9a3412"
  warn-bg: "#fff1f0"
  warn-line: "#f5c2c0"
  on-signal: "#ffffff"
typography:
  display:
    fontFamily: "\"Segoe UI\", \"Noto Sans\", \"Noto Sans Devanagari\", \"Noto Sans Tamil\", \"Noto Sans Bengali\", sans-serif"
    fontSize: "clamp(2.25rem, 5vw, 3.75rem)"
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "\"Segoe UI\", \"Noto Sans\", \"Noto Sans Devanagari\", \"Noto Sans Tamil\", \"Noto Sans Bengali\", sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.01em"
  title:
    fontFamily: "\"Segoe UI\", \"Noto Sans\", \"Noto Sans Devanagari\", \"Noto Sans Tamil\", \"Noto Sans Bengali\", sans-serif"
    fontSize: "0.875rem"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  body:
    fontFamily: "\"Segoe UI\", \"Noto Sans\", \"Noto Sans Devanagari\", \"Noto Sans Tamil\", \"Noto Sans Bengali\", sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "\"Segoe UI\", \"Noto Sans\", \"Noto Sans Devanagari\", \"Noto Sans Tamil\", \"Noto Sans Bengali\", sans-serif"
    fontSize: "0.6875rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0.02em"
rounded:
  none: "0"
  module: "2px"
spacing:
  tab-y: "0.4rem"
  tab-x: "0.65rem"
  module: "0.75rem"
  denser: "0.5rem"
  tight: "0.375rem"
  control: "2.75rem"
  header: "3rem"
  rail: "14rem"
components:
  button-primary:
    backgroundColor: "{colors.signal}"
    textColor: "{colors.on-signal}"
    rounded: "{rounded.none}"
    padding: "0 1.25rem"
    height: "{spacing.control}"
    typography: "{typography.label}"
  button-primary-hover:
    backgroundColor: "#a01010"
    textColor: "{colors.on-signal}"
    rounded: "{rounded.none}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.none}"
    padding: "0 1.25rem"
    height: "{spacing.control}"
    typography: "{typography.label}"
  module-tab:
    backgroundColor: "{colors.signal}"
    textColor: "{colors.on-signal}"
    rounded: "{rounded.none}"
    padding: "{spacing.tab-y} {spacing.tab-x}"
    typography: "{typography.label}"
  module-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.module}"
    padding: "{spacing.module}"
  input-field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.module}"
    padding: "0 0.75rem"
    height: "{spacing.control}"
    typography: "{typography.body}"
  nav-item-active:
    backgroundColor: "{colors.signal-soft}"
    textColor: "{colors.signal}"
    rounded: "{rounded.none}"
    padding: "0.625rem 0.75rem"
    typography: "{typography.label}"
  citation-chip:
    backgroundColor: "{colors.signal-soft}"
    textColor: "{colors.signal}"
    rounded: "{rounded.module}"
    padding: "0.125rem 0.5rem"
    typography: "{typography.body}"
  mark-cl:
    backgroundColor: "{colors.signal}"
    textColor: "{colors.on-signal}"
    rounded: "{rounded.none}"
    size: "1.75rem"
    typography: "{typography.label}"
---

# Design System: ChatLaw

## Overview

**Creative North Star: "High-Density Module Mosaic"**

ChatLaw’s shipped interface is a packed mosaic of ruled boxes on ash and white: every major zone — conversations, structured answers, sources, composer, product menu — is a hairline module capped by a utility-red tab. The world is Japanese high-density web adapted for civic Operate work: dense, legible, and edge-to-edge, not sparse mint SaaS chat.

Personality is plain, trustworthy, and civic. Signal red (`#db1b1a`) marks tabs, primary actions, and active emphasis; everything else stays ink, ash, and hairline gray. Typography is a compact gothic sans stack that stays Indic-script capable (Segoe UI + Noto Sans family). Persuade (landing) and Operate (product shell) wear the same world — landing is a denser mosaic demo of the chat loop, not a separate marketing aesthetic.

Confirmed refusals: sparse mint/forest SaaS chat, purple/indigo AI dashboards, glassmorphism, multi-layer shadows, decorative card stacks, and Latin-only display faces that break Hindi, Tamil, Bengali, or other product languages.

**Key Characteristics:**
- Ash page ground (`#f5f5f5`) with white module surfaces and 1px `#d0d0d0` hairlines
- Signal-red module tabs and square primary actions
- Near-square corners (2px module radius; primary CTAs and brand mark are 0)
- Compact Indic-capable sans; body at 14px / 1.5
- Edge-to-edge abutting columns and stacked modules — density as clarity, not decoration
- Flat depth: borders and tonal fills only; honor `prefers-reduced-motion`

## Colors

Utility palette: cool neutrals for structure, one loud signal red for tabs and commitment, soft pink tints for selection and citation chips.

### Primary
- **Signal Red** (`#db1b1a`): Module tabs (`.module-tab`), primary buttons (Sign in, New conversation, Send, Start with Chat), brand mark “CL”, text selection, theme color, and active emphasis text. Hover deepens toward `#a01010` on solid fills.

### Neutral
- **Ash Ground** (`#f5f5f5`): Page/`body` background; chat composer dock backdrop.
- **Module White** (`#ffffff`): Panels, shell chrome, composer surface.
- **Near-Black Ink** (`#111111`): Primary text and focus outline (`--focus`).
- **Muted Ink** (`#6b6b6b`): Secondary copy, hints, inactive nav.
- **Hairline** (`#d0d0d0`): All module borders, column rules, list dividers.
- **Module Fill** (`#f0f0f0`): Nested wells, hover fills on inactive nav, demo user bubbles.
- **Signal Soft / Mid** (`#fce8e8` / `#f5c2c0`): Active nav wash, citation chips, soft hover on chips.
- **On-Signal** (`#ffffff`): Text on red tabs and primary fills.

### Warning
- **Warn Ink / Wash / Line** (`#9a3412` / `#fff1f0` / `#f5c2c0`): Alerts, sign-in failure, destructive affordances — never as brand accent.

Legacy CSS aliases `--forest`, `--lime`, and `--warm` remap to `--signal`, `--signal-soft`, and `--focus`. New work should use the signal-family names.

### Named Rules
**The Signal Tab Rule.** Signal red owns module tabs and primary commitment actions. It is not a decorative wash across the canvas; soft pink is for selection and citations only.

**The Hairline Neutrals Rule.** Structure is ash + white + `#d0d0d0`. Do not reintroduce mint grounds, forest greens, or warm cream paper as product neutrals.

## Typography

**Display Font:** Segoe UI (with Noto Sans + Indic script fallbacks)  
**Body Font:** Same stack  
**Document sheet (exception):** Times New Roman / Times for `.document-sheet` draft previews only — not product chrome.

**Character:** Compact gothic sans — utilitarian, dense, bilingual-ready. No separate marketing serif or display face for UI chrome.

### Hierarchy
- **Display** (700, clamp ~2.25–3.75rem, ~1.05): Landing hero brand + signal subline only.
- **Headline** (600, ~1.5rem): Empty-state prompts (“Describe your situation”), sign-in titles.
- **Title** (700, 0.875rem): Shell page titles, conversation titles, brand wordmark.
- **Body** (400, 0.875rem / 1.5): Answers, forms, list copy. Prefer readable measure inside modules, not full-bleed walls of text.
- **Label** (700, ~11px / 0.6875rem, tracking ~0.02em, often uppercase): Module tabs, nav items, primary button labels, mobile tab bar.

### Named Rules
**The Indic Stack Rule.** Product UI must keep the Segoe UI + Noto Sans (Devanagari / Tamil / Bengali) stack. Never ship a Latin-only display face for chrome or answers.

**The Label Plate Rule.** Zone names and primary actions read as uppercase utility plates (tabs, nav, CTAs) — functional naming, not decorative eyebrows.

## Layout

Operate shell: ash full-bleed canvas; desktop left product rail (~14rem / `w-56`) with hairline right edge; sticky/top header (`h-12`); mobile fixed bottom 4-up tab bar (`min-h-14`) with hairline column rules. Chat Operate packs history | answer+composer | evidence as abutting modules (history `lg:w-72`; evidence as edge drawer). Landing Persuade uses a max-width mosaic (`max-w-6xl`) with a two-column hairline split: brand/CTA module beside a structured-answer demo module.

Rhythm is tight: module body padding `0.75rem`, tab padding `0.4rem 0.65rem`, denser gaps `0.5rem`, primary controls `min-h-11` (44px). Modules abut — prefer shared hairlines over large gutters. Chat scroll and document sheets use thin gray scrollbars.

### Named Rules
**The Abutting Mosaic Rule.** Columns and stacked panels share 1px hairlines; do not float isolated cards in empty mint space.

**The Touch Floor Rule.** Primary controls stay at least `min-h-11` (44px); icon-only chrome at least `min-h-10` / `min-w-10`.

## Elevation & Depth

Flat by default. Depth comes from hairline borders, white-on-ash stacking, and occasional `module-fill` / `signal-soft` wells — not drop shadows. Modal/drawer scrims use light black overlays (`bg-black/25`–`/30`). Focus is a 2px near-black ring/outline (`--focus`), offset 2px.

Motion is state-only: color transitions, 200ms panel slide, voice-bar scale animation. Honor `prefers-reduced-motion` (globals collapse animations/transitions).

### Named Rules
**The Flat Mosaic Rule.** No ambient or multi-layer shadows on modules. If it needs “lift,” use a border or a tonal fill, not a shadow stack.

## Shapes

Near-square geometry. `.module` uses `border-radius: 2px` with 1px `--line` stroke. Primary solid buttons, module tabs, and the “CL” mark are square (`0`). Secondary controls and inputs follow the module corner (`2px` / `rounded-sm`). Avoid pill shapes and large soft radii as identity.

### Named Rules
**The Square Commitment Rule.** Primary actions and red tabs stay square. Soft large radii (`rounded-2xl`, pills) are outside this world.

## Components

### Buttons
- **Shape:** Square primary (`0`); secondary bordered modules (`2px` max).
- **Primary:** Signal fill, white uppercase bold label (~11–14px), `min-h-11`, horizontal pad ~`1.25rem`. Hover deepens red (`#a01010` where implemented).
- **Secondary / Ghost:** White fill, hairline border, uppercase bold ink; hover may bring signal border.
- **Focus:** `focus-visible` ring/outline on `--focus` (`#111111`), offset 2px.

### Module tabs
- **Style:** Full-bleed or inline signal bar; white 11px bold label; padding `0.4rem 0.65rem`. Names the zone (“Conversations”, “Structured answer”, “Question input”, “Menu”).
- **Role:** Signature device of the world — every major Operate/Persuade zone should read as a tabbed module.

### Cards / Containers
- **Corner Style:** 2px (`.module` / `rounded-sm`).
- **Background:** White surface on ash ground; nested wells use `module-fill`.
- **Shadow Strategy:** None — see Elevation.
- **Border:** 1px `--line`; stacked lists use `hairline-grid` or `divide-y`.
- **Internal Padding:** `0.75rem` module body; denser `0.5rem` in chrome.

### Inputs / Fields
- **Style:** Hairline border, white or transparent-in-module fill, body 14px, `min-h-11`.
- **Focus:** Near-black ring (`--focus`), not a colored glow.
- **Composer:** Abutting module with red “Question input” tab, textarea + square Send.
- **Error:** Warn wash/line/ink triad; do not use signal red for errors.

### Navigation
- **Desktop rail:** White column, red “Menu” tab, uppercase bold labels + 11px hints; active = `signal-soft` wash + signal text; hover = `module-fill`.
- **Header:** Hairline bottom, brand mark + title, language control, square Sign in.
- **Mobile:** Four equal cells, hairline separators, 10px uppercase labels, active soft-signal wash.

### Citation chips (signature)
- Inline bordered soft-signal chips with signal text (`[n]`); hover shifts to `signal-mid`. Sources modules stack as abutting hairline rows with small Act/status plates.

### Brand mark
- 28×28 (`h-7 w-7`) square signal tile with 10px bold white “CL” beside the ChatLaw wordmark.

## Do's and Don'ts

### Do:
- **Do** label major zones with `.module-tab` (signal red, white uppercase plate).
- **Do** pack content into hairline modules on ash/white; abut columns and stacks.
- **Do** use signal red for tabs, primary CTAs, brand mark, and active emphasis only.
- **Do** keep the Indic-capable Segoe / Noto stack for all product UI copy.
- **Do** keep primary controls ≥44px tall and visible near-black focus rings.
- **Do** honor `prefers-reduced-motion` for voice and panel motion.

### Don't:
- **Don't** revive mint grounds, forest green primaries, or warm cream paper as the product palette.
- **Don't** build sparse ChatGPT-clone chrome or floating soft cards with large radii and shadows.
- **Don't** use purple/indigo AI gradients, glassmorphism, or glow accents.
- **Don't** ship Latin-only display typography that breaks Indic scripts.
- **Don't** treat module tabs as decorative kickers unrelated to the zone’s function.
- **Don't** use signal red for error/warning — use the warn triad.
