# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary users are Indian citizens facing a live legal problem (landlord deposit, arrest risk, workplace dispute, family matter). They often use a phone, may not be fluent in legal English, and need plain-language explanation with sources they can check. Practitioners and businesses may use the same tools (documents, cases, research) but are not the lead audience for the visual world.

## Product Purpose

ChatLaw helps people understand Indian law in their own language. The visitor describes a situation; the product asks focused follow-ups, then explains the law in plain language with checkable statutory citations. The same product also drafts structured legal documents, holds private case workspaces, and searches legal sources.

Success means the user leaves with a clearer understanding of their situation, grounded in cited Indian law, without mistaking the product for a lawyer or court.

## Positioning

Describe the situation in English or an Indian language; ChatLaw interviews, then returns a plain-language answer grounded in retrieved Indian statutory text with section-level citations the user can verify. Neighboring chatbots cannot truthfully claim the same RAG-grounded Indian statute corpus with hierarchical act/chapter/section evidence.

## Operating Context

- Guided legal chat (interview clarifications → structured answer + citations)
- Voice input/output across supported Indian languages
- Language preference across 22+ Indian languages
- Document draft workspace with filing disclaimer, version history, export
- Private authenticated case workspaces (matters, documents, dates, timelines)
- Research source search (statutes/sources, not a second chatbot)
- Case intelligence (forum/advocate discovery) as a supporting tool
- PWA installable client; Google sign-in for account-backed drafts and cases
- Informational assistance only — not a substitute for a lawyer or court

## Capabilities and Constraints

- Grounded Q&A via Python RAG engine over Indian statutes (including BNS, BNSS, BSA, and key civil/commercial acts)
- Persistent conversations; citation panels; research deep-links
- Deterministic document generation (templates, validation, PDF/DOCX export)
- Auth: Google OAuth via NextAuth; documents and cases require sign-in; research chat remains available without signing in
- UI type must remain Indic-script capable (Noto Sans / Segoe UI stack or equivalent); a display face on English marketing copy must not break Hindi, Tamil, Bengali, and other product languages
- Out of scope for redesign: rag-engine behavior, database schema, auth providers, API contracts
- Undecided: none material for this redesign

## Brand Commitments

- Product name: ChatLaw
- Voice: plain, trustworthy, civic; no hype, gamification, or fake social proof
- Required disclaimer: informational assistance only — not a substitute for a lawyer or court
- Do not invent testimonials, accuracy claims, court outcomes, pricing, or legal-advice framing

## Evidence on Hand

- Live product UI under `web/` (landing, chat, documents, cases, research, account, sign-in)
- Legal corpus and RAG pipeline under `rag-engine/` and `legal_corpus/`
- No customer testimonials, press quotes, or third-party accuracy benchmarks on hand — future work must not fabricate them

## Product Principles

1. Ground every answer in checkable sources; never invent legal authority.
2. Prefer the citizen’s language and plain wording over legal jargon.
3. Make the interview → cited-answer loop the proof of the product.
4. Keep trust signals visible: disclaimers, citations, and clear non-lawyer framing.
5. Operate for stress: scanability and familiar affordances outrank decorative expression.

## Accessibility & Inclusion

- Support 22+ Indian languages with Indic-script-capable UI typography
- Prefer touch targets of at least 44px (`min-h-11`) on primary controls
- Honor `prefers-reduced-motion`
- Maintain visible focus and readable contrast on all interactive chrome
