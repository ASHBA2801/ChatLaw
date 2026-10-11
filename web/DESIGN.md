---
name: ChatLaw
description: Quiet product-minimal interface for Indian-law chat — cool tinted neutrals, one cobalt accent, soft geometry.
colors:
  background: "#f6f7f9"
  surface: "#ffffff"
  fill: "#f0f2f5"
  foreground: "#12151c"
  ink-muted: "#596172"
  ink-faint: "#8a91a1"
  line: "#e2e5eb"
  line-strong: "#cbd1dc"
  accent: "#2455d4"
  accent-strong: "#1b44b0"
  accent-soft: "#edf2ff"
  accent-mid: "#d3dffc"
  on-accent: "#ffffff"
  focus: "#2455d4"
  warn: "#b42318"
  warn-bg: "#fef3f2"
  warn-line: "#fecdca"
  ok: "#067647"
  ok-bg: "#ecfdf3"
  ok-line: "#abefc6"
  caution: "#93370d"
  caution-bg: "#fffaeb"
  caution-line: "#fedf89"
typography:
  display:
    fontFamily: "ui-sans-serif, system-ui, \"Segoe UI\", \"Noto Sans\" + Indic Noto families"
    fontSize: "clamp(2.25rem, 5vw, 3.5rem)"
    fontWeight: 600
    lineHeight: 1.08
    letterSpacing: "-0.02em"
  headline:
    fontSize: "1.5rem–2.25rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  title:
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.35
  body:
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontSize: "0.75rem–0.8125rem"
    fontWeight: 600
    lineHeight: 1.3
rounded:
  control: "0.625rem"
  panel: "0.875rem–1.125rem"
  composer: "1rem–1.5rem"
  pill: "9999px"
spacing:
  control: "2.75rem"
  control-compact: "2.5rem"
  header: "3.5rem"
  rail: "15rem"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    rounded: "{rounded.control}"
    height: "{spacing.control}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.control}"
    height: "{spacing.control}"
  nav-item-active:
    backgroundColor: "{colors.accent-soft}"
    textColor: "{colors.accent}"
    rounded: "{rounded.control}"
  citation-chip:
    backgroundColor: "{colors.accent-soft}"
    textColor: "{colors.accent}"
    rounded: "{rounded.control}"
---

# Design System: ChatLaw

## Overview

**Creative North Star: "Quiet Product"**

ChatLaw is used by people under stress, often on a phone, often outside their first language. The interface stays out of the way: cool, slightly blue-tinted neutrals, one cobalt accent, soft rounded surfaces and generous reading measure. Hierarchy comes from type size, weight and whitespace — not from colored bars, boxes inside boxes, or decoration.

Landing (Persuade) and product shell (Operate) share the same world. The landing page demonstrates the chat loop (question → follow-up → sources) with a small example conversation; it does not claim accuracy figures, testimonials or outcomes.

Confirmed refusals: purple/indigo AI gradients, glassmorphism, glow accents, emoji used as icons, uppercase "kicker" labels, nested bordered cards, and Latin-only display faces that break Indic scripts.

## Colors

Tokens live in `app/globals.css` (`:root`). Components reference them as `var(--token)`.

- **Background** `#f6f7f9` – page ground and, on Chat, the sidebar (the conversation area is `surface`). **Surface** `#fff` – panels, composer, shell chrome. **Fill** `#f0f2f5` – assistant bubble, hover wells, segmented-control tracks.
- **Foreground** `#12151c`, **Ink muted** `#596172` (secondary copy, AA on background and surface), **Ink faint** `#8a91a1` (hints, disclaimers, timestamps only — never for required reading).
- **Line** `#e2e5eb` for hairlines and card borders; **Line strong** `#cbd1dc` for controls and the composer.
- **Accent** `#2455d4` (hover `#1b44b0`): primary buttons, user bubble, active nav, links, citation chips, focus ring. **Accent soft / mid** for selected states and chip backgrounds.
- **Warn** (`#b42318`) for errors and destructive actions, **Ok** for success/relevance, **Caution** for advisory states. Red is never the brand colour.

**The One Accent Rule.** Cobalt is the only brand colour. Soft accent tints mark selection; status colours are reserved for status.

## Typography

System UI stack with Noto Sans fallbacks for Devanagari, Tamil, Bengali, Telugu, Gujarati, Kannada, Malayalam, Gurmukhi and Odia (`--font-ui`). No webfont is downloaded, so Indic scripts always have a matching fallback and there is no layout shift. Document previews (`.document-sheet`) use Times New Roman and are the only exception.

- **Display** 600, `clamp(2.25rem, 5vw, 3.5rem)`, tight leading — landing hero only.
- **Headline** 600, 1.5–2.25rem — page titles, empty states.
- **Title** 600, 1rem — card and section headings (including answer sections).
- **Body** 15px / 1.55 (answers use 15px / 1.75). **Label** 12–13px, 600, sentence case.
- Headings use `text-wrap: balance`; paragraphs `text-wrap: pretty`.

**The Sentence Case Rule.** No `uppercase` + tracking labels. Names of regions are plain headings or quiet `section-label` captions.

## Layout

- **Sidebar (desktop):** one left sidebar on every product page: logo + wordmark, a collapse toggle, a "New chat" row, the four product links, and Account / Sign in at the bottom. It is 16rem wide and collapses to a 4.25rem icon rail; the choice is saved. On Chat the sidebar also holds the conversation history (search + date-grouped single-line rows, delete on hover/focus) between the links and the account row. Chat history is plugged in through `ChatSidebarContext`, so the shell owns the sidebar and the chat page owns its content.
- **Sidebar (mobile):** other pages keep the five-item bottom tab bar and a slim top bar. Chat has no tab bar: a menu button in the chat header opens the same sidebar as a left drawer (85% wide, scrim, Esc to close), so the composer gets the full height.
- **Chat:** sidebar | one centred column (max `3xl`) on a white surface. The header is borderless: menu (mobile), conversation title, language, and a new-chat icon on mobile. Empty state: logo, "What legal question can I help with?", the coverage line, the composer and four suggestion cards, all centred vertically. Once there are messages the composer docks at the bottom. User messages are right-aligned `fill` bubbles; assistant replies are flat text with the logo avatar (hidden on phones) — no card around the answer. The composer is a 24px-radius box with an auto-growing textarea; below it: dictation mic + speech language, a Voice button (opens the voice conversation panel) and a round send button. The character counter only appears under 1,000 characters left.
- **Pages:** `max-w-6xl` content, 16–32px gutters, one primary action per page header.
- Touch floor: primary controls ≥ 44px (`min-h-11`), compact controls ≥ 40px.

**The One Surface Rule.** A card contains content, not other bordered cards. Separate sub-regions with a hairline (`border-t`) or whitespace.

## Elevation & Shape

Mostly flat: 1px `line` borders, with `--shadow-soft` on cards and `--shadow-raised` only for floating layers (dropdowns, dialogs, hero demo). Corners: controls 10px, panels 14–18px, composer 16–24px, chips and status badges fully rounded. Native `button`/`input`/`select` default to the control radius in `@layer base`; Tailwind `rounded-*` utilities override it.

## Components

Reusable classes in `app/globals.css` (`@layer components`, so utilities can override them):

- `.btn-primary`, `.btn-secondary` (+ `.btn-sm`): 44px (40px small) buttons/links.
- `.section-label`: 12px muted caption for a region.
- `.panel`, `.panel-flat`: standard surface.
- `.rise-in` (+ `-delay-1…3`): short entrance on landing and empty states; honours `prefers-reduced-motion`.
- `BrandMark` (`components/layout/BrandMark.tsx`): round ChatLaw logo (same artwork as the favicon, `public/ChatLaw Logo.png`) + wordmark, used by landing, sign-in and shell.
- `CategoryIcon` (`components/documents/CategoryIcon.tsx`) and `ChatIcons`/`NavIcons`: the only icon sources — stroke SVGs, 1.8 width. No emoji.

## Motion

State changes only: 150ms colour/border transitions, 420ms rise-in for first paint, voice-bar scale while recording, `animate-pulse` for loading. No bounce or elastic easing. Reduced-motion collapses all of it.

## Do's and Don'ts

**Do** keep every answer sourced and visible disclaimers on landing, sign-in and the composer. **Do** use `var(--accent)` for emphasis, links and selection. **Do** keep Indic fallbacks in the font stack. **Do** use real icons.

**Don't** add uppercase labels, coloured top bars, nested bordered cards, gradients, glow, or red as a brand colour. **Don't** use `ink-faint` for text users must read. **Don't** invent testimonials, accuracy claims or pricing.
