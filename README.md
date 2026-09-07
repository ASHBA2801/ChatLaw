# ChatLaw

ChatLaw is a secure, multilingual legal-information assistant and legal workflow platform designed to help Indian citizens, practitioners, and businesses understand their legal rights, draft structured legal agreements, locate relevant judicial forums and advocates, and organize case workspaces.

---

## Table of Contents

1. [Overview & Capabilities](#overview--capabilities)
2. [System Architecture](#system-architecture)
3. [Core Features](#core-features)
   - [Grounded Legal Q&A (RAG Engine)](#1-grounded-legal-qa-rag-engine)
   - [Speech & Voice Interface](#2-speech--voice-interface)
   - [Legal Document Builder & Drafting](#3-legal-document-builder--drafting)
   - [Case Intelligence, Court & Advocate Finder](#4-case-intelligence-court--advocate-finder)
   - [Case Workspace & Private Documents](#5-case-workspace--private-documents)
4. [Tech Stack](#tech-stack)
5. [Repository Structure](#repository-structure)
6. [Prerequisites & Environment Setup](#prerequisites--environment-setup)
7. [Running the Application (Step-by-Step)](#running-the-application-step-by-step)
   - [1. Clone & Install Dependencies](#step-1-clone--install-dependencies)
   - [2. Start Infrastructure Containers](#step-2-start-infrastructure-containers)
   - [3. Configure Environment Variables](#step-3-configure-environment-variables)
   - [4. Database Migration & Client Generation](#step-4-database-migration--client-generation)
   - [5. Run the Python RAG Engine](#step-5-run-the-python-rag-engine)
   - [6. Run the Next.js Web Application](#step-6-run-the-nextjs-web-application)
8. [Ingestion & Vector Corpus Preparation](#ingestion--vector-corpus-preparation)
9. [Running Tests & Linting](#running-tests--linting)
10. [Security & Privacy Principles](#security--privacy-principles)

---

## Overview & Capabilities

ChatLaw bridges the gap between complex statutory Indian legislation and everyday citizens:

- **Authoritative & Grounded**: Powered by a Python RAG (Retrieval-Augmented Generation) pipeline indexing statutory Indian laws (including Bharatiya Nyaya Sanhita (BNS), Bharatiya Nagarik Suraksha Sanhita (BNSS), Bharatiya Sakshya Adhiniyam (BSA), and key civil/commercial acts). Answers cite exact sections, subsections, and clauses without hallucinations.
- **Multilingual & Voice-Enabled**: Full continuous voice interaction and speech-to-text / text-to-speech support for multiple Indian languages.
- **Deterministic Document Generation**: Structured legal document generation (e.g., Non-Disclosure Agreements, Service Agreements, Notices) with customizable terms, version history, validation, and PDF/DOCX export.
- **Case Intelligence & Directory**: Deterministic categorization of legal matters, jurisdiction identification, suggested forum classification, and nearby court/advocate discovery with distance filtering.
- **Private Case Workspace**: Authenticated case management allowing users to organize legal matters, attach private PDF case documents, view case timelines, and track important deadlines.

---

## System Architecture

```
                                  ┌──────────────────────────────┐
                                  │      Client (Browser/PWA)    │
                                  └──────────────┬───────────────┘
                                                 │
                                                 ▼
                                  ┌──────────────────────────────┐
                                  │     Next.js Web Frontend     │
                                  │           (`web/`)           │
                                  └──────┬───────────────┬───────┘
                                         │               │
                            NextAuth /   │               │ Server-side
                            Prisma Client│               │ Authenticated Proxy
                                         ▼               ▼
                   ┌──────────────────────────┐    ┌──────────────────────────┐
                   │  PostgreSQL + pgvector   │    │    Python RAG Engine     │
                   │       (`database/`)      │◄───┤      (`rag-engine/`)     │
                   │                          │    │  (FastAPI / Gemini API)  │
                   └──────────────────────────┘    └──────────────────────────┘
```

- **`web/`**: Next.js 16 (App Router, React 19, Tailwind CSS v4) manages authentication, document creation, case workspaces, and UI streaming.
- **`rag-engine/`**: FastAPI service handling chunk retrieval, hybrid vector search (768-dim), reranking, citation assembly, and grounded Gemini response generation.
- **`database/`**: Shared PostgreSQL 17 database with `pgvector`, managed via Prisma 7 schema and migrations.

---

## Core Features

### 1. Grounded Legal Q&A (RAG Engine)
- **Hierarchical Knowledge Base**: Preserves structural legal hierarchies (`Act → Chapter → Section → Subsection → Clause`).
- **Hybrid Retrieval**: Combines semantic vector similarity search (`pgvector`) with keyword/statutory code lookups.
- **Strict Evidence Verification**: Every answer is grounded in retrieved chunks. Citations link directly to statutory sections with evidence preview cards.
- **Persistent Conversations**: Multi-turn chat persistence with conversation history search and management.

### 2. Speech & Voice Interface
- **Continuous Voice Mode**: Hands-free legal research with live transcript streaming, voice activity states, and auto-speaking audio playback.
- **Speech-to-Text & TTS**: Web Speech API integration supporting English and major Indian languages (Hindi, Tamil, Telugu, Kannada, Bengali, etc.).

### 3. Legal Document Builder & Drafting
- **Guided Workflows**: Interactive wizards for legal templates (e.g., Non-Disclosure Agreements, Consulting/Service Agreements).
- **Validation Engine**: Real-time validation of required parties, consideration, governing law, and conditions.
- **Version Control & History**: Every save creates an immutable version snapshot with rollback capabilities.
- **Multi-Format Export**: Generates clean, formatted PDF and DOCX downloads directly from client/server boundaries.

### 4. Case Intelligence, Court & Advocate Finder
- **Legal Domain Classification**: Deterministic classification covering Property, Tenancy, Family, Employment, Consumer, Criminal, Contract, and Cybercrime.
- **Urgency Detection**: Flags high-priority scenarios (imminent eviction, arrest risk, statutory deadlines) with appropriate caution.
- **Directory Provider Abstraction**: Extensible court and advocate lookup by city, state, practice area, and Haversine distance radius.
- **Source Transparency**: Retains verified source provenance without fabricating fictitious directory profiles.

### 5. Case Workspace & Private Documents
- **Private Case Management**: Create, search, update, and archive case records with granular server-side ownership checks.
- **Secure PDF Upload**: Validates MIME types, checksums, file sizes, and path traversal; extracts page counts and metadata.
- **Case Timelines**: Automated audit logs tracking case creation, document uploads, and case events.
- **Grounded Assistant Handoff**: Connects case records directly to conversational legal research.

---

## Tech Stack

| Layer | Technologies |
| --- | --- |
| **Frontend** | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, Lucide/Heroicons |
| **Auth & Security** | NextAuth v5 (Auth.js) with Database session strategy & Google OAuth provider |
| **Backend API** | Next.js Route Handlers + Python 3.11+ FastAPI backend |
| **RAG & NLP** | Google Gemini API (`gemini-2.5-flash` / `text-embedding-004`), custom rerankers |
| **Database & Vector Store** | PostgreSQL 17, `pgvector` extension (768 dimensions), Prisma 7 ORM |
| **Document Processing** | `pdf-lib`, `docx`, PyMuPDF (`fitz`), Python `pydantic` v2 |
| **Testing** | Vitest (frontend & integration), Pytest (RAG engine & retrieval) |

---

## Repository Structure

```
ChatLaw/
├── Law_files/           # IMMUTABLE raw statutory law PDFs and acts (read-only)
├── database/            # Shared Prisma schema, migrations, seed scripts
│   ├── prisma/
│   │   ├── schema.prisma # PostgreSQL & pgvector schema definitions
│   │   └── migrations/   # Version-controlled SQL migrations
│   └── lib/             # Direct vector-search queries (pgvector)
├── docker/              # Docker Compose definitions for Postgres & Redis
│   ├── postgres/        # PostgreSQL + pgvector container
│   └── redis/           # Redis container
├── docs/                # Architecture, RAG engine, and API contract docs
├── legal-data/          # Structured legal metadata, court hierarchies, and forms
├── rag-engine/          # Python FastAPI RAG Engine
│   ├── api/             # FastAPI routers and conversation endpoints
│   ├── ingestion/       # PDF parsing, hierarchy reconstruction, and chunking
│   ├── embeddings/      # Gemini embedding adapters
│   ├── retrieval/       # Vector search, keyword search, and reranker
│   ├── generation/      # Grounded response prompt assembly
│   └── data/            # Processed JSON/JSONL chunks (generated)
├── scripts/             # Development, testing, and deployment scripts
└── web/                 # Next.js 16 web application
    ├── app/             # App Router pages (/chat, /documents, /cases, /api)
    ├── components/      # UI components (Chat, Documents, Cases, Voice)
    ├── lib/             # Client/server libraries (Prisma client, RAG client)
    └── types/           # TypeScript definitions
```

---

## Prerequisites & Environment Setup

Ensure you have the following installed on your machine:
- **Node.js**: `v20.x` or `v22.x` (LTS)
- **Python**: `3.11` or `3.12`
- **Docker & Docker Compose**: For running PostgreSQL + pgvector
- **Google Gemini API Key**: From Google AI Studio

### Environment Files

Configure the `.env` files in their respective folders:

#### 1. Web Application (`web/.env`)
```env
DATABASE_URL="postgresql://postgres:postgres@localhost:5433/chatlaw?schema=public"
RAG_API_URL="http://127.0.0.1:8000"
RAG_API_SECRET="your-shared-secret-key-for-rag"

# NextAuth Configuration
AUTH_SECRET="your-generated-auth-secret-32-chars-min"
AUTH_TRUST_HOST="true"

# Google OAuth (Optional for local testing)
AUTH_GOOGLE_ID=""
AUTH_GOOGLE_SECRET=""

# Directory Providers (Optional)
COURT_PROVIDER_URL=""
ADVOCATE_PROVIDER_URL=""
```

#### 2. Python RAG Engine (`rag-engine/.env`)
```env
DATABASE_URL="postgresql://postgres:postgres@localhost:5433/chatlaw?schema=public"
GEMINI_API_KEY="your-gemini-api-key"
GEMINI_MODEL="gemini-2.5-flash"
GEMINI_EMBEDDING_MODEL="text-embedding-004"
RAG_API_SECRET="your-shared-secret-key-for-rag"
CHATLAW_FRONTEND_ORIGIN="http://localhost:3000"
LOG_LEVEL="INFO"
```

---

## Running the Application (Step-by-Step)

### Step 1: Clone & Install Dependencies

```bash
# Install root & workspace Node dependencies
npm install
```

### Step 2: Start Infrastructure Containers

Start PostgreSQL with pgvector (running on host port `5433` to prevent conflicts):

```bash
docker compose -f docker/postgres/compose.yml up -d
```

### Step 3: Configure Environment Variables

Create `.env` in `web/` and `rag-engine/` following the templates provided above or from `.env.example`.

### Step 4: Database Migration & Client Generation

```bash
# Apply migrations to local PostgreSQL
npm run db:migrate

# Generate Prisma Client for the Next.js app
npm run db:generate
```

### Step 5: Run the Python RAG Engine

In a new terminal window:

```bash
cd rag-engine

# Create virtual environment (if not already created)
python -m venv .venv

# Activate virtual environment
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
# source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Run FastAPI server with hot-reload
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

The RAG service will be available at `http://127.0.0.1:8000` (Health check: `http://127.0.0.1:8000/health`).

### Step 6: Run the Next.js Web Application

In your main terminal window:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser:
- **/chat**: Grounded Legal AI Research Assistant with Voice & Case Intelligence
- **/documents**: Legal Document Builder & Draft Manager
- **/cases**: Case Workspace, Document Uploader & Timeline Tracker

---

## Ingestion & Vector Corpus Preparation

To process raw statutory PDFs from `Law_files/` into chunked JSONL and generate vector embeddings:

```bash
cd rag-engine
.\.venv\Scripts\Activate.ps1

# 1. Ingest PDFs from Law_files into structured JSON
python scripts/ingest_pdfs.py

# 2. Chunk documents with legal boundary awareness
python scripts/chunk_documents.py

# 3. Generate embeddings and populate PostgreSQL pgvector
python scripts/embed_chunks.py
```

---

## Running Tests & Linting

### Frontend & Unit Tests
```bash
# Run Vitest test suite
npm run test --workspace @chatlaw/web

# Run TypeScript type check
npm run typecheck --workspace @chatlaw/web

# Run ESLint check
npm run lint --workspace @chatlaw/web

# Run production build validation
npm run build
```

### Python RAG Engine Tests
```bash
cd rag-engine
.\.venv\Scripts\Activate.ps1
pytest -q
```

---

## Security & Privacy Principles

1. **Zero Client Trust**: All case access, document records, and draft edits are authorized strictly server-side using the authenticated session user ID.
2. **Private File Handling**: Case documents are checked against user-scoped checksums and private keys; raw storage paths and credentials are never exposed to the client.
3. **No Hallucinated Legal Authority**: The RAG generation pipeline strictly rejects ungrounded generation and flags missing context explicitly.
4. **Cost-Controlled AI Usage**: Deterministic operations (PDF validation, page counts, distance calculation, filtering, document rendering) run completely offline without unnecessary Gemini API calls.
