# Foundry — Progress Log

**Last updated:** 2026-11-26 | **Project status:** **M1 complete** (minimal frontend demo interface); ready for **M2** (Backend foundation and persistence)

---

## 1. Repository state breakdown (verified)

### A. Existing committed code (`d250128` through `6dea8c5`)
- **Frontend (`Foundry/frontend/`):**
  - Next.js `16.4.6` (App Router), React `19.3.0`, TypeScript, Tailwind CSS `4.3.3`, ESLint `9`.
  - Reusable UI primitives in `frontend/components/ui/` (`Button`, `Input`, `Textarea`, `Card`, `Badge`, `Dialog`, `ConfirmDialog`, `StatusIndicator`, `Skeleton`, `EmptyState`, `ErrorState`) and layout container (`frontend/components/shared/page-container.tsx`).
  - Design tokens and typography (`Geist` / `Geist Mono`) in `frontend/app/globals.css` and `frontend/app/layout.tsx`.

### B. M1 changes (uncommitted in working tree)
- **Minimal 4-state agent interface (`frontend/components/agent/` + `frontend/app/page.tsx`):**
  - `SignInCard`: Minimal frontend-only demo sign-in (real authentication deferred to M2).
  - `CandidateInputCard`: Accepts either a LinkedIn profile URL or a PDF resume (reusing T020's `ResumeUploadCard`, `isValidHttpUrl`, and `formatFileSize` validation). No backend upload or LinkedIn scraping is performed.
  - `ProcessingState`: Concise 4-stage simulated demo progress view.
  - `ResultsView` + `demo-results.ts`: Clearly labelled fictional/demo startup results showing funding/hiring signals with source links, **Active** vs. **Hidden** classification, founder email provenance/verification status, match score + explanation, and editable/copyable email drafts.
- **Removed out-of-scope UI:** Removed the 11-section marketing landing page (`components/marketing/*`), `/onboarding`, the 7-route `AppShell` (`/app/*`), `component-showcase.tsx`, and elaborate T020 profile-management components (`ProfileWorkspace`, `SkillsEditor`, `app/app/profile/page.tsx`), while preserving `ResumeUploadCard` and `profile-types.ts` helpers.
- **Verified checks:** `npm run lint`, `npx tsc --noEmit`, and `npm run build` all pass (`/` and `/_not-found` prerendered).

### C. Future work (not yet implemented)
- **No `backend/` directory** (no FastAPI app, SQLAlchemy models, or SQLite database).
- **No authentication / minimal sign-in**.
- **No PDF text extraction** (PyMuPDF), LinkedIn input processing, or Gemini extraction.
- **No startup discovery, company research, funding/hiring signal analysis, or founder discovery**.
- **No local RAG** (SQLite/BM25) or **LangGraph** orchestration.
- **No deterministic matching** or **persisted outreach draft approval**.

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
