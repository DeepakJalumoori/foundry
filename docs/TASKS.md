# Foundry — Implementation Roadmap

**Scope:** Personal AI-powered job search agent targeting pre-seed to Series C startups.
**Priority:** Working end-to-end agentic pipeline first; minimal, functional UI.

---

## M1: Minimal interface and candidate input

Keep M1 small—focus only on what is needed to accept candidate input, show processing state, and render structured results.

- **Deliverables:**
  1. Audit existing routes and dependencies; remove or redirect out-of-scope routes (`/onboarding`, `/app/matches`, `/app/contacts`, `/app/settings`, and SaaS marketing sections).
  2. Inspect uncommitted T020 `ProfileWorkspace` (`frontend/components/app/profile/`): reuse useful resume/input components, simplify unnecessary profile-management UI, and remove any separate profile workspace.
  3. Implement the minimal 4-state UI shell: minimal sign-in, candidate input (LinkedIn URL or PDF resume upload), agent processing state placeholder, and structured research results layout.
  4. Verify `npm run lint`, `npx tsc --noEmit`, and `npm run build`.
- **Dependencies:** None (uses existing Next.js app and `frontend/components/ui/*`).
- **Acceptance criteria:**
  - Frontend has only the minimal sign-in, candidate input, processing state, and results interface.
  - No 4-destination workspace, marketing landing page, or `/onboarding` flow remains active.
  - Lint, typecheck, and production build pass with zero errors.

---

## M2: Backend foundation and persistence

- **Deliverables:**
  1. Scaffold `Foundry/backend/` using Python 3.12 (`uv`), `pyproject.toml`, `.env.example`, and FastAPI app with CORS and `GET /api/health` (minimal single-user authentication deferred).
  2. Configure SQLAlchemy 2.x + SQLite (`foundry.db`) + Alembic migrations and implement initial ORM models (`Candidate`, `ResearchRun` with statuses `pending` | `processing` | `completed` | `failed`).
  3. Implement Pydantic v2 schemas, repository layer, local PDF file storage (`UPLOAD_DIR`), and `POST /api/runs` + `GET /api/runs/{run_id}` with strict input validation (HTTPS LinkedIn `/in/` URL or validated `.pdf` upload, mutually exclusive).
  4. Add isolated `pytest` suite for health, input validation, PDF storage/cleanup, run creation/retrieval, constraints, and DB isolation.
- **Dependencies:** None (can begin immediately after M1 or in parallel).
- **Acceptance criteria:**
  - FastAPI starts cleanly on Python 3.12 via `uv`.
  - Alembic upgrades a fresh SQLite database cleanly and persists/retrieves `Candidate` and `ResearchRun`.
  - All M2 `pytest` tests pass.

---

## M3: Resume/LinkedIn processing and candidate intelligence (Complete)

- **Deliverables:**
  1. Implemented PyMuPDF text extraction (`app/services/resume_extractor.py`) with path-traversal protection, page-number preservation, whitespace normalization, and scanned/image-only/encrypted/corrupted PDF detection.
  2. Implemented LinkedIn URL handling in `candidate_profile_service.py`: no unauthorized scraping; marks run `failed` (`LINKEDIN_EXTRACTION_UNSUPPORTED`) without fabricating a profile.
  3. Defined `LLMProvider` abstraction (`app/providers/llm.py`) with `GeminiLLMProvider` (using `google-genai` structured output) and deterministic `DemoLLMProvider` fallback, plus `profile_validator.py` for date/skill/evidence grounding and `CandidateProfile` persistence (`alembic` revision `20261127_0002`).
  4. Exposed `POST /api/runs/{run_id}/process` and `GET /api/candidates/{candidate_id}/profile`, and added isolated `pytest` tests across PDF extraction, schema/evidence validation, providers, service, API, and migrations.
- **Dependencies:** M2 (FastAPI, SQLAlchemy models, Pydantic schemas).
- **Acceptance criteria:**
  - Uploading a PDF or submitting a LinkedIn URL extracts and persists a structured `CandidateProfile`.
  - Missing `GEMINI_API_KEY` cleanly falls back to `DemoLLMProvider` with explicit `demo` labelling.
  - All M3 `pytest` tests pass.

---

## M4: Startup discovery, company research, funding/hiring signals, and founder discovery (Complete)

- **Deliverables:**
  1. Defined modular M4 provider interfaces (`StartupDiscoveryProvider`, `CompanyResearchProvider`, `FundingProvider`, `HiringSignalProvider`, `FounderProvider`) in `app/providers/m4_base.py`.
  2. Implemented deterministic `Demo*` providers in `app/providers/m4_demo.py` covering pre-seed to Series C startups with realistic funding signals, **Active** and **Hidden** hiring signals, and founder records (`data_origin="demo"`).
  3. Implemented M4 domain models (`SourceEvidence`, `EvidenceLink`, `DiscoveryRun`, `Company`, `CompanyResearch`, `FundingEvent`, `HiringSignal`, `JobOpportunity`, `Founder`) and Alembic migration `20261127_0003`, enforcing source provenance, funding != hiring, stale-job checks, and conflict detection.
  4. Exposed `/api/discovery` and `/api/companies` endpoints and added isolated `pytest` tests across discovery, deduplication, research, funding, hiring signals, founders, APIs, and migrations.
- **Dependencies:** M2 (persistence), M3 (candidate profile context).
- **Acceptance criteria:**
  - Discovery returns pre-seed to Series C startups with sourced company info, funding signals, hiring signals, and founder contacts.
  - Active and hidden opportunities are clearly distinguished; funding alone never marks a company as actively hiring.
  - All M4 `pytest` tests pass.

---

## M5: RAG, LangGraph orchestration, and deterministic matching

- **Deliverables:**
  1. Implement lightweight local RAG using **SQLite/BM25** over candidate profile chunks and company research/signal chunks with source metadata (evaluating whether embeddings are needed).
  2. Implement deterministic matching service (`30%` skills, `25%` role, `15%` experience, `15%` projects, `10%` preferences, `5%` location/work mode) plus LLM/template explanation and "why reach out" rationale grounded in retrieved evidence.
  3. Build the single orchestrated LangGraph `StateGraph` (`candidate_input` → `candidate_profile_extraction` → `startup_discovery` → `company_research` → `funding_signal_analysis` → `hiring_signal_analysis` → `founder_discovery` → `rag_context_retrieval` → `deterministic_candidate_company_matching` → `personalized_outreach_generation` → `structured_results`) with persisted step events, timeouts, and bounded retries.
  4. Expose `POST /api/runs`, `GET /api/runs/{run_id}`, and `GET /api/runs/{run_id}/results`; add `pytest` tests for score reproducibility, BM25 retrieval, and LangGraph failure/retry paths.
- **Dependencies:** M3 (candidate extraction) and M4 (discovery, signals, founders).
- **Acceptance criteria:**
  - Submitting candidate input runs the full 11-node LangGraph pipeline and persists step-level progress.
  - Match scores are 100% reproducible from stored inputs and never altered by an LLM.
  - All M5 `pytest` tests pass.

---

## M6: Personalized outreach, integration, testing, and portfolio demonstration

- **Deliverables:**
  1. Implement grounded personalized email draft generation (citing retrieved candidate + company evidence), draft editing (`PUT /api/outreach/{draft_id}`), and explicit `approve` / `reject` endpoints (no automatic email sending).
  2. Build centralized typed API client (`frontend/lib/api.ts`) and connect sign-in, candidate input, live workflow polling, structured results display, and draft approval/editing end-to-end.
  3. Run full verification: backend `pytest`, frontend `lint` / `tsc` / `build`, end-to-end browser walkthrough (desktop + mobile), and evidence/security audit.
  4. Update `README.md` and `docs/PROGRESS.md` with verified setup steps, demo walkthrough, and known limitations.
- **Dependencies:** M1 (minimal frontend) and M5 (orchestrated backend pipeline).
- **Acceptance criteria:**
  - A candidate can sign in, upload a resume or enter a LinkedIn URL, watch the agent run, inspect grounded startup/funding/hiring/founder/match results, edit a draft, and approve or reject it—with all state persisted in SQLite.
  - Zero fabricated contacts, zero unverified hiring claims, and zero automatic email sending.
