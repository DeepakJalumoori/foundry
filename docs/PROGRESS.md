# Foundry — Progress Log

**Last updated:** 2026-11-26 | **Project status:** Final scope frozen; ready for **M1** (Minimal interface and candidate input)

---

## 1. Repository state breakdown (verified)

### A. Existing committed code (`d250128` through `9c52011`)
- **Frontend (`Foundry/frontend/`):**
  - Next.js `16.4.6` (App Router), React `19.3.0`, TypeScript, Tailwind CSS `4.3.3`, ESLint `9`.
  - Reusable UI primitives in `frontend/components/ui/` (`Button`, `Input`, `Textarea`, `Card`, `Badge`, `Dialog`, `ConfirmDialog`, `StatusIndicator`, `Skeleton`, `EmptyState`, `ErrorState`).
  - Design tokens and typography (`Geist` / `Geist Mono`) in `frontend/app/globals.css` and `frontend/app/layout.tsx`.
  - Pre-reset multi-section SaaS marketing landing page (`frontend/app/page.tsx`, `frontend/components/marketing/*`) and `/onboarding` flow (`frontend/app/onboarding/page.tsx`).
  - Application shell (`frontend/components/app/app-shell.tsx`) and 7 placeholder routes (`/app`, `/app/discover`, `/app/matches`, `/app/contacts`, `/app/outreach`, `/app/profile`, `/app/settings`).
  - **Scope note:** `/onboarding`, `/app/matches`, `/app/contacts`, `/app/settings`, the marketing landing page, and separate multi-destination workspaces are outside the final frozen scope and are scheduled for removal or redirection during **M1**.

### B. Uncommitted T020 work (preserved in working tree)
- `frontend/app/app/profile/page.tsx` (modified)
- `frontend/components/app/profile/` (`profile-types.ts`, `profile-workspace.tsx`, `resume-upload-card.tsx`, `skills-editor.tsx` — untracked)
- **Status:** Preserved untouched as an in-memory UI preview (client-side form, skills editor, and PDF file validation; no backend persistence or parsing).
- **M1 plan:** Inspect these files during **M1** to reuse useful resume/profile input components, simplify unnecessary profile-management UI, and avoid maintaining a separate profile workspace.

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

- **M1 — Minimal interface and candidate input:** Audit/remove out-of-scope routes, inspect and selectively reuse T020 `ProfileWorkspace` input components, and build the minimal 4-state UI.
