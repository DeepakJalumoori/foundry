# Foundry

**An AI-powered job search agent for candidates targeting pre-seed to Series C startups.**

Foundry is a personal-use Agentic AI engineering portfolio project—not a commercial SaaS product. A candidate signs in, provides a **LinkedIn profile URL or PDF resume**, and the agent researches relevant startups, analyzes funding and hiring signals, identifies founders and public professional emails where available, retrieves grounded evidence via RAG, calculates explainable match scores, and drafts personalized outreach emails for manual candidate review.

---

## What Foundry does

1. **Extracts candidate intelligence:** Parses skills, experience, education, and projects from a resume PDF or LinkedIn URL input (no unauthorized LinkedIn scraping).
2. **Discovers pre-seed to Series C startups:** Identifies relevant early- and growth-stage companies via pluggable search/research interfaces.
3. **Analyzes company, funding, and hiring signals:** Researches what each company does, recent funding evidence, and hiring signals from career pages and job platforms—recording source URLs and dates where available.
4. **Distinguishes Active vs. Hidden opportunities:**
   - **Active opportunities:** Relevant public job openings have been found.
   - **Hidden opportunities:** No relevant public opening was found, but other credible evidence justifies considering an approach. *(Funding alone is never treated as proof of hiring.)*
5. **Discovers founders and public emails:** Identifies founders and publicly available professional email addresses with explicit provenance and verification status—never fabricating names or emails.
6. **Retrieves evidence with RAG & scores deterministically:** Uses lightweight local retrieval (**SQLite/BM25** initially) and reproducible weighted scoring to explain why the candidate should reach out.
7. **Drafts personalized outreach:** Generates tailored founder email drafts grounded in retrieved evidence. The candidate manually reviews, edits, approves, and sends them—**no automatic email sending**.

---

## Orchestrated LangGraph workflow

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

---

## Technology stack

### Frontend (minimal 4-state interface)
- **Next.js 16** (App Router), **React 19**, **TypeScript**, **Tailwind CSS v4**
- Minimal sign-in, candidate input (LinkedIn URL or resume upload), agent processing state, and structured research results interface.

### Backend & Agentic AI (planned in M2–M6)
- **Python 3.12 / 3.13**, **FastAPI**, **Pydantic v2**
- **SQLAlchemy** + **SQLite**
- **PyMuPDF** for PDF resume extraction
- **LangGraph** + **LangChain** + **Gemini API** (backend-only `LLMProvider` with deterministic demo fallback)
- **SQLite/BM25** local RAG retrieval (embeddings added only if evaluation demonstrates a need)

---

## Current development status

Foundry has completed **M1 (minimal frontend)**, **M2 (backend foundation)**, **M3 (candidate intelligence)**, **M4 (startup discovery & intelligence)**, **M5 (RAG + LangGraph + explainable matching)**, and **M6 (evidence-grounded founder outreach & human review)**:

- **Implemented:**
  - Minimal 4-state Next.js frontend (`frontend/components/agent/`, `frontend/components/ui/`, `frontend/lib/api.ts`) with M6 backend-connected `OutreachWorkspacePanel` for draft generation, editing, evidence inspection, and review/approval (no auto-send).
  - FastAPI + SQLAlchemy 2.x + SQLite + Alembic backend (`Foundry/backend/`) with M2–M6 endpoints (`/api/health`, `/api/runs`, `/api/candidates/{id}/profile`, `/api/discovery`, `/api/companies`, `/api/matching-runs`, `/api/matches`, `/api/outreach-drafts`).
  - PyMuPDF PDF text extraction, structured `CandidateProfile` schema + evidence validation, `LLMProvider` abstraction (`DemoLLMProvider` and `GeminiLLMProvider`).
  - M4 startup discovery, domain-based company deduplication, company research with conflict detection, funding intelligence, explainable hiring signal detection (**Active** vs. **Hidden**), founder discovery, and shared `source_evidence` provenance (`alembic` revision `20261127_0003`, deterministic `Demo*` providers).
  - M5 local **SQLite FTS5** lexical RAG (`evidence_documents` + `evidence_documents_fts`, `SQLiteFTSRetriever` + LangChain `FoundryLangChainRetriever`), 11-node **LangGraph** `StateGraph` (`build_matching_graph`), deterministic candidate-fit scoring (`fit_v1`: `40/25/15/10/10` with coverage normalization), independent opportunity classification (`active` / `hidden` / `insufficient_evidence` + evidence strength), deterministic ranking (`rank_v1`), and M5 persistence (`alembic` revision `20261127_0004`).
  - M6 8-node **LangGraph** outreach workflow (`build_outreach_graph`), structured claim-level evidence grounding & prompt-injection/factual-claim validation (`outreach_grounding.py`), three outreach intents (`job_interest`, `exploratory`, `general_interest`), `OutreachDraft` / `OutreachDraftEvidence` / `OutreachDraftVersion` persistence (`alembic` chain `20261127_0001` → `20261127_0005` outreach tables → `20261127_0006` active-draft partial unique index), `expected_version` optimistic concurrency on `PATCH /api/outreach-drafts/{draft_id}`, and explicit `draft` → `reviewed` → `approved` → `archived` lifecycle (no email sending). Automated backend suite: **119 passed** (100 M1–M5 + 19 M6 tests; live Gemini and browser E2E not performed).

See [`docs/PRD.md`](docs/PRD.md), [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/TASKS.md`](docs/TASKS.md), and [`docs/PROGRESS.md`](docs/PROGRESS.md) for full details.

---

## Local setup

### Prerequisites
- **Node.js** 20+ and `npm`
- **Python** 3.12 or 3.13 (required starting in **M2**)

### Frontend (currently runnable)

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

### Backend (M2 foundation)

```bash
cd backend
uv sync --python 3.12
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Run the isolated backend test suite:

```bash
cd backend
uv run pytest
```

The FastAPI backend uses SQLite (`foundry.db`) and local resume storage (`UPLOAD_DIR=./uploads`). By default (`AI_PROVIDER=demo`), candidate profile extraction runs deterministically via `DemoLLMProvider` without requiring a Gemini API key. Copy `backend/.env.example` to `backend/.env` and set `AI_PROVIDER=gemini` with `GEMINI_API_KEY` to use Gemini.
