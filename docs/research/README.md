# Research tab

The Research tab answers two questions for a section or a legal situation:
**what does the law say**, and **which judgments apply it**. Statute text comes
straight from the embedded corpus; case law comes from ChatLaw's verified case
library, and from official court websites when the library does not yet cover
the law being researched.

Nothing is shown as a judgment unless an official government copy of it was
downloaded and checked to name the parties.

## Features

| Feature | Status | Where |
| --- | --- | --- |
| Section lookup by reference (`Section 103 BNS`, `BNS 103`, `s. 2(7) CPA 2019`, `Articles 14, 21`) | Built | `rag-engine/research/law_reference.py` |
| Repealed code mapping (IPC → BNS, CrPC → BNSS, Evidence Act → BSA) for commonly cited sections | Built | `law_reference._REPEALED_CODES` |
| Full section text assembled from all of a section's chunks | Built | `CaseLawStore.statute_section` |
| Semantic retrieval of related provisions (existing pgvector + reranker) | Built | `ResearchService._semantic_provisions` |
| Plain-language explanation: ingredients, key points, penalties/remedies, exceptions, related provisions, next steps — written only from the retrieved text | Built | `research/articulation.py` |
| Case discovery on official sites (Supreme Court, High Courts, District Courts, Tribunals) | Built | `research/discovery.py` |
| Link verification: HTTPS `*.gov.in` / `*.nic.in` only, document downloaded, parties matched in the cause title | Built | `research/verification.py` |
| Case library in Postgres; repeat research on the same law served from the database | Built | `research/store.py`, `research_law_lookups` |
| Semantic search over stored cases (summary embeddings in `court_case_chunks`) | Built | `CaseLawStore.similar_cases` |
| Detailed judgment summary (facts, issues, held, ratio, outcome) from the official judgment text, cached on the case | Built | `ResearchService.case_summary` |
| Browse Acts → sections → landmark judgments | Built | `BrowseActs.tsx`, `/api/research/acts` |
| Landmark seeding for every section in the embeddings, and Act-level seeding for Acts not yet ingested | Built (script) | `rag-engine/scripts/seed_case_law.py` |
| Court-level filter, "search official sites again" refresh | Built | `ResearchWorkspace.tsx` |
| Terminal research CLI | Built | `rag-engine/scripts/research.py` |

## How a search works

```
query ──► law_reference: explicit Act/section refs ─┐
      └─► pgvector search over legal_chunks ─────────┴─► provisions + law keys      POST /api/research/law
                                                         │
             ┌───────────────────────────────────────────┤ (in parallel)
             ▼                                           ▼
   articulation (Gemini, statute text only)     case library lookup                POST /api/research/cases
   cached in research_queries                    ├─ court_case_laws by law key
                                                 ├─ cached results for this query
                                                 └─ similar stored cases (embeddings)
                                                         │ fewer than 3 cases AND law not searched in 30 days
                                                         ▼
                                                 grounded Google search (Gemini)
                                                 → candidate judgments
                                                 → verify official copy (download + party match)
                                                 → per-case link search for unverified ones (45 s budget)
                                                 → store verified cases, link to law keys, embed summary
```

A **law key** is `ACT_ID:SECTION` (`BNS2023:103`, `HMA1955:13`, `CONSTITUTION:21`) or an
Act id for Act-level research. Act ids come from `legal_documents.metadata.act_id`
and `legal_corpus/acts/catalog.json`.

### Caching rules

- A law key is searched on official sites at most once per `RESEARCH_CACHE_DAYS`
  (default 30), whether or not anything was found. Later research on the same law
  is served from `court_cases` + `court_case_laws`.
- A research query's explanation and case ids are cached in `research_queries`.
- "Search official court websites again" (`refresh: true`) bypasses the cache.
- Detailed judgment summaries are stored in `court_cases.metadata.detailed_summary`.

## Why grounded search instead of the court portals

`sci.gov.in`, `scr.sci.gov.in` and `judgments.ecourts.gov.in` put judgment search
behind CAPTCHAs, and ChatLaw does not bypass them. Discovery uses Gemini with
Google Search grounding instead, restricted to official hosts, and every
proposed link is independently verified:

- `api.sci.gov.in` answers `200` with an empty body for paths that do not exist,
  so a status code proves nothing — the document is downloaded and parsed.
- Party names are matched only in the first ~4,000 characters (the cause title),
  so a judgment that merely cites a case is not mistaken for it.
- `main.sci.gov.in` links are rewritten to `api.sci.gov.in`; `/jonew/judgments/`
  and `/jonew/judis/` variants are both tried. `digiscr.sci.gov.in` no longer
  resolves in DNS.

Expect roughly a third to a half of model-proposed judgments to verify. Recent
Supreme Court judgments verify well; older judgments and High Court orders often
have no indexed official copy and are left out rather than shown unverified.

## Database

Migration `20261013100000_research_case_law` adds:

- `court_case_laws` — case ↔ law key, `isLandmark`, `origin` (`CURATED` / `SEED` / `DISCOVERED`)
- `research_law_lookups` — last discovery per law key (`FOUND` / `NONE_FOUND` / `FAILED`), hit counts
- `research_queries` — cached explanation and case ids per query

Existing `court_cases` stores the judgments (id = hash of the verified URL) and
`court_case_chunks` holds one summary embedding per case.

## Building the case library

```bash
cd rag-engine
python scripts/seed_case_law.py --import-curated           # re-verify the bundled curated cases
python scripts/seed_case_law.py --acts BNS2023,BNSS2023,BSA --dry-run
python scripts/seed_case_law.py --acts BNS2023 --workers 3  # landmark cases for every BNS section
python scripts/seed_case_law.py --all-acts --workers 4      # every section in the embeddings
python scripts/seed_case_law.py --act-level pending         # Income-tax, Labour Codes, family Acts, Railways, ...
```

Runs are resumable: sections searched in the last 30 days are skipped. A full
`--all-acts` run is about 2,600 sections ≈ 9,000 grounded Gemini searches, so
start with the Acts users research most and watch the API bill.

## API (rag-engine, proxied by the web app at `/api/rag/...`)

| Method | Path | Body / query |
| --- | --- | --- |
| POST | `/api/research/law` | `{query}` → provisions, law keys, notes |
| POST | `/api/research/articulate` | `{query}` → explanation |
| POST | `/api/research/cases` | `{query, law_keys?, court_levels?, refresh?, limit?}` |
| POST | `/api/research/judgment-summary` | `{case_id}` |
| GET | `/api/research/acts` | Acts with section and case counts |
| GET | `/api/research/acts/{act_id}/sections` | Sections with case counts |
| GET | `/api/research/law-cases?law_key=` | Stored cases for one law key (no web search) |

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `GEMINI_RESEARCH_MODEL` | `GEMINI_GENERATION_MODEL` | Model for grounded case discovery |
| `GEMINI_RESEARCH_THINKING_LEVEL` | `low` | Keeps discovery around 20 s per call |
| `GEMINI_RESEARCH_TIMEOUT_SECONDS` | `90` | Per grounded call |
| `RESEARCH_LINK_SEARCH_BUDGET_SECONDS` | `45` | Time allowed for per-case link searches during interactive research |
| `RESEARCH_CACHE_DAYS` | `30` | How long a law's discovery result is reused |
| `RESEARCH_SIMILAR_CASE_THRESHOLD` | `0.72` | Minimum similarity for stored cases matched by meaning |

## Known gaps

- **Corpus coverage.** Income-tax Act 2025, the four Labour Codes, the Railways Act,
  most family-law Acts (HSA, HAMA, DV Act, SMA, ...) and the Constitution are not
  embedded. Research still finds case law for them at Act level, but cannot show
  their text. Ingest them to get section-level research.
- **Outdated statute text.** `Law_files/HMA1955.pdf` is the 1955 Gazette as enacted,
  without the 1976 amendments (s.13(1)(ia) cruelty, s.13B mutual consent). Other
  amended Acts should be checked against the consolidated India Code versions.
- **BNSS has no section numbers** in `legal_chunks` (the chunker read it as a
  schedule), so BNSS section lookup and section-level seeding do not work until
  it is re-chunked. Semantic search still returns BNSS text.
- The bundled curated cases (`web/data/legal/*.json`) link to `digiscr.sci.gov.in`
  (retired) and High Court URLs that return 404. The seed script re-verifies them;
  the Chat answer card still shows them directly.

## Roadmap

1. Re-ingest consolidated Acts and fix BNSS chunking (unblocks section-level research).
2. Run section seeding Act by Act, starting with BNS, BNSS, BSA, CPA 2019, HMA.
3. Offline Supreme Court index from the open `indian-supreme-court-judgments` dataset
   (party names, dates, citations) to resolve official links without a model call.
4. Citation graph: store which judgments a judgment cites, show "followed in" / "overruled by".
5. Save research to a Case workspace and export a research memo (PDF/DOCX).
6. Full-text judgment chunks with embeddings for passage-level case search.
7. Section-to-section mapping tables for the full IPC/CrPC/IEA → BNS/BNSS/BSA comparison.
8. Answer and explain in the user's language, like Chat.
