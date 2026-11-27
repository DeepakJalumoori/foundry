# Foundry — Progress Log

**Last updated:** 2026-11-27 | **Project status:** **M3 complete** (candidate intelligence & structured profile extraction); ready for **M4** (startup discovery, signals, and founder discovery)

---

## 1. Repository state breakdown (verified)

### A. Committed code (`d250128` through `17bfef4`)
- **Frontend (`Foundry/frontend/`):**
  - Next.js `16.4.6` (App Router), React `19.3.0`, TypeScript, Tailwind CSS `4.3.3`, ESLint `9`.
  - Reusable UI primitives in `frontend/components/ui/` (`Button`, `Input`, `Textarea`, `Card`, `Badge`, `Dialog`, `ConfirmDialog`, `StatusIndicator`, `Skeleton`, `EmptyState`, `ErrorState`) and layout container (`frontend/components/shared/page-container.tsx`).
  - Design tokens and typography (`Geist` / `Geist Mono`) in `frontend/app/globals.css` and `frontend/app/layout.tsx`.
  - Minimal 4-state agent interface (`frontend/components/agent/` + `frontend/app/page.tsx`, committed at `17bfef4`):
    - `SignInCard`: Minimal frontend-only demo sign-in.
    - `CandidateInputCard`: Accepts a LinkedIn profile URL or PDF resume (reusing `ResumeUploadCard`, `isValidHttpUrl`, and `formatFileSize`). **Future integration note:** currently retains only `ResumeFileMeta` (`name`, `sizeBytes`) rather than the browser `File` object; when connected to the backend in a later milestone, it will need to retain the `File` and submit via `FormData`.
    - `ProcessingState`: Concise 4-stage simulated demo progress view.
    - `ResultsView` + `demo-results.ts`: Clearly labelled fictional/demo startup results.

### B. M2 & M3 implementation (`Foundry/backend/`)
- **Backend foundation (`uv`, Python `3.12.0`, FastAPI, Pydantic v2, SQLAlchemy 2.x, SQLite, Alembic):**
  - `app/core/config.py` & `app/core/database.py`: Pydantic Settings configuration (including `AI_PROVIDER`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `LLM_TIMEOUT_SECONDS`, `LLM_MAX_RETRIES`, `DEMO_MODE`), CORS for `http://localhost:3000`, SQLite engine with `PRAGMA foreign_keys=ON`.
  - `app/models/candidate.py`, `app/models/research_run.py`, & `app/models/candidate_profile.py`: `Candidate` (`candidates`), `ResearchRun` (`research_runs`), and `CandidateProfile` (`candidate_profiles`) with check constraints, foreign keys, unique `candidate_id`, and indexes.
  - `alembic/` (`20261127_0001_initial_schema.py`, `20261127_0002_add_candidate_profiles.py`): Migrations creating `candidates`, `research_runs`, and `candidate_profiles`.
  - `app/services/file_storage.py`, `app/services/resume_extractor.py`, `app/services/profile_validator.py`, & `app/services/candidate_profile_service.py`: Local PDF storage, PyMuPDF page-numbered text extraction (with path-safety, encrypted/corrupt/empty/image-only detection), evidence grounding, date ordering & skill deduplication, and synchronous extraction orchestration.
  - `app/providers/llm.py`: `LLMProvider` abstraction with `DemoLLMProvider` (explicitly labelled `demo`) and `GeminiLLMProvider` (`google-genai` structured output, bounded retries/timeouts, safe error handling).
  - `app/api/routes/`: `GET /api/health`, `POST /api/runs`, `GET /api/runs/{run_id}`, `POST /api/runs/{run_id}/process`, `GET /api/candidates/{candidate_id}/profile`.
  - `tests/`: Isolated `pytest` suite (67 passing tests across M2 and M3) using per-test temporary SQLite databases, temporary upload directories, and synthetic PDFs.
- **Known M3 limitations:** Extraction executes synchronously on `POST /api/runs/{run_id}/process` (no background worker/queue); scanned image-only PDFs are marked `requires_manual_review` without OCR; LinkedIn URLs are rejected (`LINKEDIN_EXTRACTION_UNSUPPORTED`) without scraping.

### C. Future work (not yet implemented)
- **No authentication / minimal sign-in** (deferred).
- **No startup discovery, company research, funding/hiring signal analysis, or founder discovery** (M4).
- **No local RAG** (SQLite/BM25) or **LangGraph** orchestration (M5).
- **No deterministic matching** or **persisted outreach draft approval** (M5–M6).

---

## 2. Final frozen product scope (2026-11-26)

Foundry is a **simple AI-powered job search agent** for candidates targeting **pre-seed to Series C startups** (personal-use Agentic AI portfolio project, not a SaaS product):
- **Minimal UI:** Minimal sign-in → Candidate input (LinkedIn URL or resume upload) → Agent processing state → Structured research results interface.
- **11-node LangGraph workflow:** `candidate_input` → `candidate_profile_extraction` → `startup_discovery` → `company_research` → `funding_signal_analysis` → `hiring_signal_analysis` → `founder_discovery` → `rag_context_retrieval` → `deterministic_candidate_company_matching` → `personalized_outreach_generation` → `structured_results`.
- **Evidence & safety:** Distinguish **Active** vs. **Hidden** opportunities; funding alone is never proof of hiring; no unauthorized LinkedIn scraping; no fabricated founders/emails; email provenance + verification required; deterministic matching; candidate approval required (no auto-send).
- **RAG:** Start with lightweight local **SQLite/BM25**; add embeddings only if evaluation shows a need.
- **Providers:** Create search/research interfaces and defer live vendor selection until M4.

---

## 3. Historical pre-reset log

- **T001–T005:** Repository reconnaissance, Git init in `Foundry/`, `.gitignore`, docs setup, Python 3.14 compatibility check.
- **T006–T010:** Next.js scaffold, design tokens, reusable `components/ui/*` primitives, accessibility & responsive QA.
- **T011–T018:** Marketing landing page and `/onboarding` preview (outside final scope; to be removed/redirected in M1).
- **T019:** `AppShell` and 7 `/app/*` placeholder routes (to be simplified in M1).
- **T020 (uncommitted):** `ProfileWorkspace` UI in `/app/profile` (preserved for M1 inspection/reuse).

---

## 4. Known risks

- **Python 3.14 compatibility:** Local environment has Python `3.14.2`. Use **Python 3.12 or 3.13** when scaffolding `backend/` in **M2** to avoid `LangChain`/`LangGraph` `pydantic.v1` compatibility issues.

---

## 5. Next milestone

- **M2 — Backend foundation and persistence:** Scaffold `Foundry/backend/` using Python 3.12 or 3.13, FastAPI, Pydantic v2, SQLAlchemy + SQLite, minimal `/api/auth/login`, `/api/health`, and `pytest` suite.
