# Foundry — Progress Log

**Last updated:** 2026-11-27 | **Project status:** **M6 complete** (evidence-grounded founder outreach generation, structured claim validation, prompt-injection & concurrency protection, human review/approval lifecycle, version history, and frontend outreach workspace); **119 backend `pytest` tests passing** (100 M1–M5 + 19 M6).

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

### C. M4 implementation (`Foundry/backend/`)
- **Startup intelligence pipeline (synchronous Python orchestration, deterministic `Demo*` providers):**
  - `app/models/m4.py` & `alembic/versions/20261127_0003_add_m4_intelligence_tables.py`: Added `source_evidence`, `evidence_links`, `discovery_runs`, `companies`, `company_research`, `funding_events`, `hiring_signals`, `job_opportunities`, and `founders`.
  - `app/providers/m4_base.py` & `app/providers/m4_demo.py`: Modular provider ABCs and deterministic `Demo*` providers (`DISCOVERY_PROVIDER`, `COMPANY_RESEARCH_PROVIDER`, `FUNDING_PROVIDER`, `HIRING_SIGNAL_PROVIDER`, `FOUNDER_PROVIDER` defaulting to `demo`).
  - `app/services/`: `source_validation.py`, `company_identity.py` (domain/external-id/cautious-name deduplication), `company_research_service.py` (conflict preservation), `funding_service.py` (currency/amount separation & 180-day recency), `hiring_service.py` (**Active** vs. **Hidden** classification; funding alone never proves hiring; 90-day stale-job guard), `founder_service.py` (conflict detection, no fabricated emails), and `discovery_orchestrator.py`.
  - `app/api/routes/discovery.py` & `app/api/routes/companies.py`: `/api/discovery`, `/api/discovery/{run_id}`, `/api/companies`, `/api/companies/{company_id}`, `/api/companies/{company_id}/research`, `/funding`, `/hiring-signals`, and `/founders`.
  - `tests/`: Added `test_m4_discovery_and_research.py`, `test_m4_signals_and_founders.py`, and `test_m4_api_and_migration.py` (80 total passing tests across M2–M4).
- **Known M4 limitations:** Only deterministic `Demo*` providers are implemented; real external discovery/funding/job/founder APIs require configuring and implementing concrete adapters.

### D. M5 implementation (`Foundry/backend/`)
- **RAG, LangGraph & Explainable Matching (`alembic` revision `20261127_0004`):**
  - `app/models/m5.py` & `alembic/versions/20261127_0004_add_m5_matching_tables.py`: Added `evidence_documents`, `evidence_documents_fts` (SQLite FTS5 virtual table), `matching_runs`, `company_assessments`, `match_results`, and `retrieval_records`.
  - `app/services/evidence_documents.py` & `app/services/fts_retriever.py`: Implemented `EvidenceDocumentNormalizer` (normalizing M4 records while preserving `source_evidence_id` provenance and SHA-256 `content_hash`), application-managed FTS5 index synchronization (`sync_fts_upsert`, `sync_fts_delete`, `rebuild_fts_index`), `SQLiteFTSRetriever` (lexical FTS5 BM25 retrieval with company isolation and metadata filters), and `FoundryLangChainRetriever` (`BaseRetriever` adapter).
  - `app/providers/llm.py` & `app/services/company_assessment_service.py`: Added `assess_candidate_company_fit` using `ChatPromptTemplate` with `<UNTRUSTED_EVIDENCE>` prompt-injection boundaries, `StructuredCompanyAssessment` validation, and cross-company/unsupported claim stripping.
  - `app/services/fit_scoring.py`, `app/services/opportunity_classifier.py`, & `app/services/ranking.py`: Implemented deterministic `fit_v1` scoring (`40/25/15/10/10` with coverage normalization), independent opportunity classification (`active` | `hidden` | `insufficient_evidence` + `strong` | `moderate` | `weak` | `insufficient`), and fit-dominant deterministic `rank_v2` prioritization.
  - `app/graphs/matching_graph.py`, `app/services/matching_service.py`, & `app/api/routes/matching.py`: Implemented the 11-node LangGraph `StateGraph` (`MatchingState`) and exposed `/api/matching-runs` and `/api/matches` endpoints.
- **Known M5 limitations:** Retrieval is lexical SQLite FTS5 (no semantic vector search); initial company intelligence uses M4 `Demo*` providers (`data_origin="demo"`); live Gemini API integration requires `GEMINI_API_KEY` and `AI_PROVIDER=gemini`; concurrent matching-run duplicate prevention is currently application-level rather than atomically guaranteed.

### E. M6 implementation (uncommitted, ready for review)
- **Evidence-grounded founder outreach & human review (Alembic chain `20261127_0001` → `20261127_0002` → `20261127_0003` → `20261127_0004` → `20261127_0005` → `20261127_0006`):**
  - `app/models/m6.py`, `20261127_0005_add_m6_outreach_tables.py`, & `20261127_0006_add_m6_active_draft_unique_index.py`: `0005` introduces `outreach_drafts`, `outreach_draft_evidence`, and `outreach_draft_versions` with UUID PKs, FKs, check constraints for intents (`job_interest`, `exploratory`, `general_interest`) and statuses (`draft`, `reviewed`, `approved`, `archived`), and preserved `original_subject`/`original_body`; `0006` adds the `uq_outreach_drafts_active_unique` partial unique index (`WHERE status != 'archived'`) for concurrency-safe duplicate draft prevention.
  - `app/services/outreach_grounding.py`: Sanitized candidate/company/founder context assembly, company-isolated FTS5 evidence collection, structured claim-to-text validation, cross-company `source_evidence_id` stripping, `<untrusted_evidence>` prompt-injection span removal, unverified email redaction, and M4 `STALE_JOB_DAYS` (90-day) / verified active-job enforcement.
  - `app/providers/llm.py` & `app/graphs/outreach_graph.py`: Extended `LLMProvider` (`DemoLLMProvider` + `GeminiLLMProvider`) with `build_outreach_strategy` and `generate_outreach_draft`, and implemented the 8-node `build_outreach_graph` LangGraph workflow.
  - `app/services/outreach_service.py` & `app/api/routes/outreach.py`: Exposed `/api/outreach-drafts` (generate, list with filters/pagination, get, `PATCH` edit requiring `expected_version` with atomic version increment and HTTP `409` on stale versions or immutable `approved`/`archived` drafts, `/review`, `/approve`, `/archive`, `/evidence`, `/versions`) with explicit status transition validation and zero email-sending capability.
  - `frontend/lib/api.ts`, `frontend/components/agent/outreach-panel.tsx`, & `frontend/components/agent/results-view.tsx`: Added typed API client (tracked via `!frontend/lib/` and `!frontend/lib/**` in `.gitignore`) and `OutreachWorkspacePanel` for draft generation, editing, evidence inspection, and review/approval.
  - `tests/test_m6_grounding_and_security.py` & `tests/test_m6_api_and_integration.py`: Added 19 M6 tests covering unit, adversarial grounding/prompt-injection, multi-threaded SQLite concurrency, transaction rollback, 89/90/91-day job freshness boundaries, API, integration (Scenarios A–E), and Alembic `0004` ↔ `0006` upgrade/downgrade; **119 backend tests passed** (100 M1–M5 + 19 M6). Frontend `eslint`, `tsc --noEmit`, and `next build --webpack` passed.
- **Known M6 limitations:** Automated tests used `DemoLLMProvider` and a mocked Gemini client; live Gemini API calls and live browser E2E testing have not been performed. `next build` requires `--webpack` on Windows due to Turbopack worker spawning; no email sending is implemented by design.

### F. Future work (not yet implemented)
- **No authentication / minimal sign-in** (deferred).

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
