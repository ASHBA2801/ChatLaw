# Cases tab — complaints, petitions and filing

The Cases tab is the place where a person turns a legal problem into a filed
document. A case already holds the person's facts, documents, dates and
timeline. On top of that, the **filing agent** writes the complaint or
petition for the office or court the person chooses, finds where to send it,
and hands it over ready to print or one click away from being emailed.

ChatLaw never sends anything on the user's behalf. Every email opens in the
user's own mail client (Gmail, Outlook, or the system mail app) with the
recipients, subject and text filled in; the user presses Send.

## What the other tabs already give us

| Tab | Feature reused in Cases |
| --- | --- |
| Chat | Grounded answers over the statute embeddings (`legal_chunks`), citation validation (`verification/evidence.py`), language preference, voice input |
| Research | Section lookup and semantic provisions (`ResearchService.law`), Gemini + Google Search grounding restricted to official `*.gov.in` / `*.nic.in` hosts, download-and-check verification, Postgres caching of discovered facts |
| Documents | Template specs, placeholder rules (`[FIELD REQUIRED]` instead of invented facts), DOCX export, filing disclaimer |
| Cases (existing) | Private case workspace, PDF uploads with extracted text, timeline, important dates, case-scoped Q&A, court/advocate directory |

## Features

| Feature | Where |
| --- | --- |
| Filing intake: facts from the case, complainant details, location (typed or "use my location") | `FilingStudio.tsx`, `Case.filingProfile` |
| Matter analysis: category, severity, offences/causes of action, public-servant / central-government / women / child / cyber flags, missing facts | `rag-engine/complaints/analysis.py` (model + deterministic rules) |
| Severity-based escalation ladder: which offices and courts are recommended, and why | `rag-engine/complaints/taxonomy.py` |
| Authority buttons: local police station, SP / Commissioner, Collector, Vigilance (DVAC/ACB), CM cell, CBI, PMO (CPGRAMS), plus NCW, NHRC and Cyber Crime when the facts call for them | `FilingStudio.tsx` |
| Court buttons: district court by subject (civil, criminal, family, consumer), the High Court for the state, the Supreme Court | `FilingStudio.tsx`, `taxonomy.COURT_FORUMS` |
| Nearby police stations and courts from OpenStreetMap around the user's location | `rag-engine/complaints/geo.py` (Nominatim + Overpass) |
| Official contact lookup: curated national directory, then grounded search for district / state offices, accepted only when the email is found on the official page | `rag-engine/complaints/contacts.py`, `authority_contacts` |
| Drafting-template library in pgvector: format exemplars for every office and court, retrieved per draft | `legal_corpus/drafting_templates/`, `drafting_template_chunks`, `scripts/embed_drafting_templates.py` |
| Drafting agent: writes the document for the chosen office from the facts, the matched template and the retrieved statute text; citations must map to retrieved provisions | `rag-engine/complaints/drafting.py` |
| Saved filings per case with edit, version of record, timeline entry | `case_filings`, `/api/cases/[id]/filings` |
| Print (print stylesheet, Indic-safe), DOCX download, copy text | `/cases/[id]/filings/[filingId]` |
| Email hand-off: Gmail / Outlook / mail-app compose with To, Cc, Subject and Body filled; long documents switch to a cover note + attachment reminder | `web/lib/filings/mail.ts` |
| Court filing hand-off: e-filing portal links instead of email | `taxonomy.COURT_FORUMS` |

## Agent flow

```
case facts + uploaded document text + complainant + location
        │
        ▼
 POST /api/complaints/analyze ───────────────────────────────────────────────┐
   ├─ model: structured reading of the facts (no invented facts)              │
   ├─ rules: severity, flags, escalation ladder, court subjects               │
   └─ statute search: ResearchService.law → provisions with law keys          │
        │                                                                     │
        ▼                                                                     │
 POST /api/complaints/authorities  (user clicks an office or court)          │
   ├─ geo: geocode / reverse-geocode, nearby police stations or courts (OSM)  │
   ├─ contacts: curated directory → authority_contacts cache → grounded       │
   │            search on official sites → email must appear on that page     │
   └─ returns recipients (verified only) + portal / e-filing links            │
        │                                                                     │
        ▼                                                                     │
 POST /api/complaints/draft  (office/court + recipient + analysis) ◄──────────┘
   ├─ template retrieval: pgvector over drafting_template_chunks
   │                      (falls back to the template files)
   ├─ evidence: provisions from analysis (re-searched if missing)
   ├─ model: JSON {subject, addressee, sections[], prayer, enclosures}
   ├─ checks: [n] citations map to evidence, uncited "Section N" claims flagged,
   │          missing facts kept as [PLACEHOLDERS], disclaimer attached
   └─ deterministic template rendering when no model is configured
        │
        ▼
 web: saved as case_filings row → document page → Print / DOCX / Email hand-off
```

## Severity ladder

| Severity | Typical facts | Recommended first | Escalation |
| --- | --- | --- | --- |
| Low | Service grievance, civic issue, small consumer dispute | Collector / department, CPGRAMS, Consumer Commission | CM cell |
| Moderate | Cognizable offence, cheating, theft, harassment | Police station (FIR, s.173 BNSS) | SP / Commissioner (s.173(4)), Magistrate (s.175(3)) |
| Serious | Police refusal to register, bribe demand by a state official, violence, cyber fraud, offences against women | SP / Commissioner, Vigilance (DVAC / ACB), Cyber Crime, NCW | CM cell, Magistrate, High Court writ |
| Grave | Corruption by central-government officials, custodial violence, inter-state or large-scale fraud, threat to life | CBI (central officials / court order / state consent), NHRC, High Court writ | PMO (CPGRAMS), Supreme Court (Art. 32) |

Rules that are never relaxed:

- CBI is only recommended for central-government employees or PSUs, matters
  needing inter-state investigation, or when a court has ordered it; the draft
  says so. Otherwise the button still works but carries the caveat.
- PMO grievances go through CPGRAMS (`pgportal.gov.in`); the portal states that
  grievances sent by email are not entertained, so the PMO draft is formatted
  for the portal and the email button is replaced by "Open CPGRAMS".
- Supreme Court Article 32 petitions are only for violations of fundamental
  rights; the draft notes the High Court (Article 226) alternative.
- A Zero FIR can be filed at any police station (s.173(1) BNSS); the nearest
  station is shown with that note, not as the jurisdictional one.

## Contacts: what counts as verified

- Curated national entries (`rag-engine/complaints/data/authorities.json`) were
  checked against the official site on 2026-10-14 and carry their source URL.
- Local and state entries are found with Gemini + Google Search restricted to
  official hosts. An email is used only if the official page (HTTPS or HTTP on
  `*.gov.in` / `*.nic.in`) is downloaded and contains the address, after
  undoing the usual obfuscation (`[at]`, `(dot)`, ...).
- Results are cached in `authority_contacts` for 90 days (`CONTACT_CACHE_DAYS`),
  including "none found", so repeat lookups are instant and cheap.
- Unverified addresses are never placed in the To field.

## Drafting templates

`legal_corpus/drafting_templates/*.md` holds one format per office or court,
written from public statutory formats and official guidance (BNSS 2023, CPC
Order VII, Consumer Protection Act 2019 and the 2020 Commission procedure
regulations, Supreme Court Rules 2013, High Court writ practice, CPGRAMS
guidance). Each file has front matter (`kind`, `forum`, `title`, `sources`)
and `##` sections. `scripts/embed_drafting_templates.py` chunks by section,
embeds with the configured provider (768-d) and upserts into
`drafting_templates` / `drafting_template_chunks`. Add a format by adding a
file and re-running the script.

## API

| Route (rag-engine) | Purpose |
| --- | --- |
| `GET /api/complaints/kinds` | Offices and courts with labels, filing channel, prerequisites |
| `POST /api/complaints/analyze` | Matter analysis + recommended offices/courts + provisions |
| `POST /api/complaints/authorities` | Recipients for one office/court kind near a location |
| `POST /api/complaints/geocode` | Forward or reverse geocoding for the location step |
| `POST /api/complaints/draft` | Write the document for one office/court |

| Route (web, signed in, owner only) | Purpose |
| --- | --- |
| `POST /api/cases/[id]/filings/analyze` | Builds facts from the case + documents, calls analyze, saves `filingProfile` |
| `POST /api/cases/[id]/filings/authorities` | Recipient lookup for the case location |
| `POST /api/cases/[id]/filings/geocode` | Location step helper |
| `GET/POST /api/cases/[id]/filings` | List / draft and save a filing |
| `GET/PATCH/DELETE /api/cases/[id]/filings/[filingId]` | Read, edit text/recipients/status, delete |
| `GET /api/cases/[id]/filings/[filingId]/export` | DOCX download |

## Limits

- Police-station email addresses are not published consistently; where none can
  be verified the user gets the station's address/phone (from OSM) and the
  state police online-complaint portal, and the draft is printed or filed in
  person.
- OpenStreetMap coverage of police stations and courts varies by district.
- This is informational assistance only — not a substitute for a lawyer or
  court. Court documents in particular should be checked by an advocate before
  filing.
