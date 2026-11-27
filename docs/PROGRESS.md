# Foundry — Progress Log

**Last updated:** 2026-11-27 | **Project status:** **M2 complete** (backend foundation & persistence); ready for **M3** (Resume/LinkedIn processing and candidate intelligence)

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

### B. M2 implementation (`Foundry/backend/`, uncommitted for review)
- **Backend foundation (`uv`, Python `3.12.0`, FastAPI, Pydantic v2, SQLAlchemy 2.x, SQLite, Alembic):**
  - `app/core/config.py` & `app/core/database.py`: Pydantic Settings configuration, CORS for `http://localhost:3000`, SQLite engine with `PRAGMA foreign_keys=ON`.
  - `app/models/candidate.py` & `app/models/research_run.py`: `Candidate` (`candidates`) and `ResearchRun` (`research_runs`) with check constraints, foreign keys, indexes, and `pending` | `processing` | `completed` | `failed` statuses.
  - `alembic/` (`alembic.ini`, `env.py`, `20261127_0001_initial_schema.py`): Initial migration creating `candidates` and `research_runs`.
  - `app/services/file_storage.py` & `app/services/run_service.py`: Local PDF storage under `UPLOAD_DIR` with opaque UUID keys, `.pdf` extension, `application/pdf` MIME check, `%PDF-` magic-byte check, bounded-chunk `5 MB` size enforcement (`413` on oversize), partial-file cleanup on failure, and strict HTTPS `linkedin.com/in/...` + mutual-exclusivity validation (`422`).
  - `app/api/routes/health.py` & `app/api/routes/runs.py`: `GET /api/health` (`200` / `503`), `POST /api/runs` (`201`), `GET /api/runs/{run_id}` (`200` / `404`).
  - `tests/`: Isolated `pytest` suite using per-test temporary SQLite databases and temporary upload directories.
- **Deferred / out of scope in M2:** Authentication (`/api/auth/*`) is deferred (future security requirements remain in `docs/RULES.md`). Resume files are stored locally; PDF text extraction (`PyMuPDF`), LinkedIn processing, and LLM extraction belong to **M3**.

### C. Future work (not yet implemented)
- **No authentication / minimal sign-in** (deferred).
- **No PDF text extraction** (PyMuPDF), LinkedIn input processing, or Gemini extraction (M3).
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
