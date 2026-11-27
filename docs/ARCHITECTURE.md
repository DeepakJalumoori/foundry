# Foundry — Architecture

**Status:** Final frozen architecture | **Version:** 3.0

---

## 1. Architecture overview

Foundry uses a minimal **Next.js + TypeScript** frontend communicating over HTTP/JSON with a **Python FastAPI** backend. The backend owns persistence (SQLite), resume/input processing, provider interfaces, lightweight local RAG (SQLite/BM25), deterministic matching, and a single orchestrated **LangGraph** workflow.

```text
┌────────────────────────────────────────────────────────────────┐
│                  Minimal Frontend (Next.js + TS)               │
│   Sign-in  ·  Candidate Input (Resume / LinkedIn URL)          │
│   Agent Processing State  ·  Structured Research Results       │
└──────────────────────────────┬─────────────────────────────────┘
                               │ HTTP / JSON
                               ▼
┌────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI + Pydantic v2)             │
│   API Routes · Auth Gate · Upload Validation · Services        │
└──────────────┬────────────────────────────────┬────────────────┘
               │                                │
               ▼                                ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│  SQLAlchemy + SQLite         │  │  LangGraph Orchestrator      │
│  Candidate · Runs ·          │  │  11-node sequential pipeline │
│  Companies · Signals ·       │  │  Persisted step status       │
│  Founders · Matches · Drafts │  │  Bounded retries & timeouts  │
└──────────────┬───────────────┘  └──────────────┬───────────────┘
               │                                 │
               ▼                                 ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│  Local RAG (SQLite / BM25)   │  │  Provider Interfaces         │
│  Candidate & company chunks  │  │  LLMProvider (Gemini / Demo) │
│  (Embeddings only if needed) │  │  SearchProvider              │
└──────────────────────────────┘  │  ResearchProvider            │
                                  │  FounderDiscoveryProvider    │
                                  └──────────────────────────────┘
```

---

## 2. Technology stack

### Frontend
- **Framework:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4.
- **UI primitives:** Reuse existing accessible components in `frontend/components/ui/` (`Button`, `Input`, `Textarea`, `Card`, `Badge`, `Dialog`, `StatusIndicator`, `Skeleton`, `EmptyState`, `ErrorState`).

### Backend (to be implemented in M2–M6)
- **Runtime:** Python 3.12 or 3.13 (recommended over 3.14 for clean `LangChain` / `LangGraph` `pydantic.v1` compatibility).
- **API & Validation:** FastAPI + Pydantic v2.
- **Persistence:** SQLAlchemy + SQLite (`foundry.db` initially).
- **PDF Parsing:** PyMuPDF (`fitz`).
- **Agentic AI:**
  - **LangGraph** for the orchestrated multi-node workflow.
  - **LangChain** for LLM and retrieval integrations.
  - **Gemini API** initially via a backend-only `LLMProvider` (with deterministic demo fallback).
- **RAG:** Lightweight local retrieval using **SQLite/BM25** initially. Add embeddings only if retrieval evaluation demonstrates a need.

---

## 3. Frontend architecture and route cleanup

The frontend is a single minimal flow—not a four-destination application:

| View / State | Purpose |
|---|---|
| Minimal Sign-in | Simple single-user authentication gate. |
| Candidate Input | LinkedIn profile URL or PDF resume upload + run trigger. |
| Agent Processing State | Displays active LangGraph node progress and errors/retries. |
| Research Results Interface | Displays discovered startups, funding/hiring signals + sources, active vs. hidden badge, why to reach out, founder name/role, public email + provenance/verification, match score + explanation, and editable outreach draft with approve/reject controls. |

### Existing routes and uncommitted work (for M1 inspection)
- **Out-of-scope routes:** `/onboarding`, `/app/matches`, `/app/contacts`, and `/app/settings` (along with the multi-section SaaS marketing landing page and separate workspace pages) are outside the final scope. During **M1**, inspect references and dependencies, then remove or redirect them cleanly. Do **not** modify or delete them during this documentation task.
- **Uncommitted T020 `ProfileWorkspace`:** Preserve uncommitted work in `frontend/components/app/profile/` and `frontend/app/app/profile/page.tsx`. During **M1**, inspect it to reuse useful resume/profile input components, simplify unnecessary profile-management UI, and avoid maintaining a separate profile workspace.

---

## 4. LangGraph workflow

One orchestrated `StateGraph` executes the full pipeline with typed state and persisted step events:

```text
candidate_input
  → candidate_profile_extraction
  → startup_discovery
  → company_research
  → funding_signal_analysis
  → hiring_signal_analysis
  → founder_discovery
  → rag_context_retrieval
  → deterministic_candidate_company_matching
  → personalized_outreach_generation
  → structured_results
```

### Node responsibilities
1. `candidate_input`: Validate resume PDF or LinkedIn URL input and initialize run state.
2. `candidate_profile_extraction`: Extract text (PyMuPDF) and structure skills, experience, education, and projects via `LLMProvider` (Gemini or demo fallback).
3. `startup_discovery`: Discover pre-seed to Series C startups via `SearchProvider`.
4. `company_research`: Gather what each company does with source URLs and dates where available via `ResearchProvider`.
5. `funding_signal_analysis`: Identify funding stage and recent funding evidence (explicitly not treated as hiring proof).
6. `hiring_signal_analysis`: Inspect career-page and job-platform signals; classify each company as **Active** (public opening found) or **Hidden** (no public opening, other credible evidence).
7. `founder_discovery`: Identify founders and publicly available professional emails with provenance and verification status (`verified` | `unverified` | `unavailable`).
8. `rag_context_retrieval`: Index candidate and company evidence in SQLite/BM25 and retrieve top relevant chunks per company.
9. `deterministic_candidate_company_matching`: Compute reproducible weighted score (`30/25/15/15/10/5%`) in pure Python and generate an evidence-backed explanation + "why reach out" rationale.
10. `personalized_outreach_generation`: Draft a personalized founder email citing retrieved candidate and company evidence.
11. `structured_results`: Persist final structured results and mark the run complete (`drafts` remain `pending` for human approval).

---

## 5. Domain data model

Core SQLAlchemy entities in SQLite:
- `Candidate`: Submitted candidate input (`input_source`: `linkedin_url` | `resume_pdf`), validated `linkedin_url`, or resume metadata (`resume_filename`, `resume_content_type`, `resume_size_bytes`, `resume_storage_key`) plus timestamps.
- `CandidateProfile`: 1:1 with `Candidate` (`candidate_profiles` table, unique `candidate_id` FK). Stores extraction metadata (`extraction_status`: `extracted` | `extracted_with_warnings` | `requires_manual_review` | `failed`, `source_type`, `data_origin`: `real` | `demo`, `provider_name`, `model_name`, `page_count`, `warnings`, `error_code`, `error_message`) and a validated `profile_data` JSON document (`StructuredCandidateProfile` with `basic_info`, `skills`, `work_experience`, `education`, `projects`, `certifications_and_achievements`, `additional_info`, and `evidence`). Stored as a single validated JSON column rather than 6+ normalized child tables to keep SQLite migrations simple and preserve atomic profile updates.
- `ResearchRun`: Run ID, `candidate_id` FK, status (`pending` | `processing` | `completed` | `failed`), `error_code`/`error_message`, and `created_at`/`started_at`/`completed_at` timestamps. (Step-level LangGraph events and provider mode are added in M5.)
- `Company`: Name, description, website, funding stage (pre-seed to Series C), opportunity type (`active` | `hidden`), data origin (`demo` | `live`).
- `CompanySignal`: Company ID, signal category (`company_info` | `funding` | `hiring`), summary, source URL, source date (nullable), and verification status.
- `FounderContact`: Company ID, name, role, public professional email (nullable), email provenance/source URL, and verification status (`verified` | `unverified` | `unavailable`).
- `MatchResult`: Run ID, company ID, deterministic numeric score (`0–100`), dimension breakdown, matched/missing skills, why-reach-out rationale, and RAG-grounded explanation.
- `OutreachDraft`: Run ID, company ID, founder contact ID (nullable), subject, body, cited evidence IDs, approval status (`pending` | `approved` | `rejected`), version, and timestamps.

---

## 6. Provider interfaces and RAG boundary

### Provider interfaces
Define abstract interfaces (`Protocol` or `ABC`) before concrete implementations:
- `LLMProvider` (`GeminiLLMProvider`, `DemoLLMProvider`)
- `SearchProvider` (`DemoSearchProvider`, live adapter deferred until M4 vendor evaluation)
- `ResearchProvider` (`DemoResearchProvider`, live adapter deferred until M4 vendor evaluation)
- `FounderDiscoveryProvider` (`DemoFounderProvider`, live adapter deferred until M4 vendor evaluation)

Defer choosing a live search/research vendor until M4 requirements are evaluated. All demo outputs must be explicitly labelled `demo`.

### RAG implementation
- Start with **SQLite/BM25** full-text indexing over candidate chunks (skills, experience, projects) and company chunks (description, funding signals, hiring signals) with source metadata.
- Evaluate retrieval quality in M5; add embeddings only if evaluation shows BM25 is insufficient.
- No external vector database or unnecessary infrastructure.

---

## 7. API boundaries

Core FastAPI endpoints (Pydantic v2 schemas at all boundaries):

```text
GET    /api/health
POST   /api/auth/login                  # Minimal single-user sign-in
GET    /api/auth/session

POST   /api/runs                        # Submit LinkedIn URL or resume PDF & initialize run
POST   /api/runs/{run_id}/process       # Extract PDF text & generate structured CandidateProfile (M3)
GET    /api/runs/{run_id}               # Poll run status & profile_extraction_status
GET    /api/candidates/{candidate_id}/profile  # Retrieve structured CandidateProfile & evidence (M3)

POST   /api/discovery                   # Discover & research startups for a candidate (M4)
GET    /api/discovery/{run_id}          # Retrieve discovery run status & summary (M4)
GET    /api/companies                   # List discovered companies with pagination & filters (M4)
GET    /api/companies/{company_id}      # Retrieve normalized company profile & latest research (M4)
POST   /api/companies/{company_id}/research        # Refresh company intelligence (M4)
GET    /api/companies/{company_id}/funding         # Retrieve funding events & evidence (M4)
GET    /api/companies/{company_id}/hiring-signals  # Retrieve hiring signals & job opportunities (M4)
GET    /api/companies/{company_id}/founders        # Retrieve discovered founders & evidence (M4)

GET    /api/runs/{run_id}/results       # Retrieve structured company, signal, founder, match & draft results (M5–M6)

PUT    /api/outreach/{draft_id}         # Edit draft subject/body
POST   /api/outreach/{draft_id}/approve # Explicit candidate approval (never auto-sends)
POST   /api/outreach/{draft_id}/reject
```

---

## 8. Configuration and secrets

Backend `.env.example` (secrets never exposed to frontend):

```env
APP_ENV=development
DATABASE_URL=sqlite:///./foundry.db
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
AI_PROVIDER=demo
SEARCH_PROVIDER=demo
RESEARCH_PROVIDER=demo
MAX_RESUME_SIZE_MB=5
CORS_ORIGINS=http://localhost:3000
```
