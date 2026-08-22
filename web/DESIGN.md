# ChatLaw Design System

Captured from Phase 22 Operate surfaces (`/chat`, `/documents`, `/cases`, `/research`, `/account`).

## Mode

**Operate** — task completion for authenticated and public legal-assistant work. Brand expression stays restrained; clarity and trust outrank decoration.

## Product tokens

| Token | Value | Role |
| --- | --- | --- |
| `--background` | `#f5f7f2` | Soft mint page ground |
| `--foreground` | `#17221d` | Primary ink |
| `--ink-muted` | `#65736b` | Secondary copy |
| `--line` | `#dce5dd` | Borders / dividers |
| `--forest` | `#174936` | Primary actions and emphasis |
| `--lime` | `#cce85a` | Selection / soft accent |
| `--warm` | `#f4b46a` | Focus outline |

Lime-tint chips use `#eef5d0` for status pills. Warning/error text uses `#935a1e` with supporting soft backgrounds where needed.

## Typography

Product UI uses a familiar sans stack: `"Segoe UI", "Noto Sans", sans-serif`. Document draft sheets may use serif (`.document-sheet`). Heading scale is tight (Operate), not marketing-fluid.

## Layout patterns

- App shell: desktop left sidebar + sticky top bar; mobile bottom nav + compact top bar
- Content padding `px-4 sm:px-6 lg:px-8`; chat may use wider max width
- Panels: white `rounded-2xl` with `border-[var(--line)]`
- Touch targets: prefer `min-h-11` / `min-h-10`
- Focus: warm ring (`focus-visible:ring-2 focus-visible:ring-[var(--warm)]`)
- Language selector: compact searchable popover (native name first)

## Motion

State feedback only (150–250ms). Honor `prefers-reduced-motion`. No page-load choreography on Operate surfaces.

## Surfaces

- **Chat:** interview clarifications, structured legal answer cards, citations, research deep-links
- **Research:** statute/source search (not a second chatbot)
- **Documents:** AI draft workspace with filing disclaimer
- **Cases:** personal matters workspace (not public case-law discovery)
- **Account:** profile + language preference

## Anti-patterns to avoid

- Purple/indigo AI-dashboard tropes
- Glassmorphism and multi-layer shadows
- Decorative gradient hero density on Operate screens
- Cards used only for decoration
- ChatGPT-clone chrome without legal-assistant structure
