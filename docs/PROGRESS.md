# Foundry — Progress Log

**Last updated:** 2026-11-26  
**Project status:** Phase 1 complete (T006–T010 done; awaiting approval for Phase 2 / T011)
**Current phase:** Phase 1 — Frontend foundation and design system (complete)

## 1. Current state

The product direction, architecture, design system, rules, and task breakdown are documented in `docs/*.md` inside the `Foundry/` project root.

Phase 0 (T001–T005) is complete:

- **Git initialization:** Initialized an empty Git repository inside `Foundry/` (`Foundry/.git`).
- **Documentation organization:** Created `Foundry/docs/` and moved all six Markdown files (`PRD.md`, `ARCHITECTURE.md`, `DESIGN.md`, `RULES.md`, `TASKS.md`, `PROGRESS.md`) into `Foundry/docs/`.
- **Repository hygiene:** Added `Foundry/.gitignore` covering Python, Node.js/Next.js, environment/secret files, SQLite databases, build artifacts, and IDE/OS files.
- **No application code or dependencies yet:** Neither `frontend/` nor `backend/` has been scaffolded, and no packages have been installed.

The design direction is a clean, light-first SaaS product inspired by the product storytelling and user journey of Backdoor AI, while retaining an original Foundry identity.

**Important:** This file records verified planning and reconnaissance state only. No application code, integrations, or tests exist yet.

## 2. Product decisions

- Product name: Foundry.
- Tagline: Your next opportunity isn't always posted.
- Primary audience: students and early-career engineers, with broader candidate support later.
- Core journey: profile → discovery → research → founder identification → matching → outreach draft → human approval.
- Frontend: Next.js and TypeScript.
- Backend: Python 3.12+ and FastAPI.
- Agent orchestration: LangGraph.
- LLM integration: Gemini through a backend-only provider.
- Persistence: SQLAlchemy and SQLite for the MVP.
- Resume extraction: PyMuPDF plus structured model output.
- Matching: deterministic weighted score with explainable dimensions.
- Outreach: drafts only; no automatic sending in the MVP.
- Demo data and simulated provider behavior must be labelled clearly.

## 3. Completed

### Planning

- [x] Product vision and target audience defined.
- [x] Core user journey documented.
- [x] MVP and deferred scope documented.
- [x] Initial stack and architecture documented.
- [x] Initial visual direction documented.
- [x] Coding-agent safety and quality rules documented.
- [x] Task breakdown created.

### Reconnaissance (Phase 0)

- [x] **T001** Inspected workspace structure, Git state, and entry points.
- [x] **T002** Inspected frontend state (greenfield; Node `v24.13.0` and npm `11.6.2` available).
- [x] **T003** Inspected backend state (greenfield; Python `3.14.2` and pip `25.3` available).
- [x] **T004** Read all six documentation files and reconciled them against the actual workspace.
- [x] **T005** Initialized Git in `Foundry/`, organized docs into `Foundry/docs/`, added `.gitignore`, evaluated Python 3.14 dependency compatibility, and wrote the repository-specific implementation plan.

### Implementation

- [x] **T006** Scaffolded `Foundry/frontend/` (Next.js 16.4.6 App Router, React 19.3.0, TypeScript, Tailwind CSS 4.3.3, ESLint), configured `DESIGN.md` color/layout tokens and Geist typography in `app/globals.css` and `app/layout.tsx`, added `lib/utils.ts` and `components/shared/page-container.tsx`, and added a minimal Foundry placeholder in `app/page.tsx`. Verified `npm run lint`, `npx tsc --noEmit`, and `npm run build` pass.
- [x] **T007** Built reusable UI components under `frontend/components/ui/` (`Button`, `Input`, `Textarea`, `Card`, `Badge`, `Dialog`/`ConfirmDialog`, `StatusIndicator`, `Skeleton`/`SkeletonCard`, `EmptyState`, `ErrorState`, `index.ts`) and added a temporary interactive verification preview (`components/shared/component-showcase.tsx`) on `app/page.tsx`. Verified `npm run lint`, `npx tsc --noEmit`, and `npm run build` pass.
- [x] **T008** Completed and verified loading, error, empty, status, and confirmation state patterns: added `Tab`/`Shift+Tab` focus trapping, body scroll lock, and `dismissible` rules to `Dialog`/`ConfirmDialog`; added `SkeletonText` and accessible `LoadingState` (`role="status"`, `aria-busy="true"`, `sr-only` label) to `skeleton.tsx`; added `secondaryAction` to `EmptyState`; added `retrying`, `details`, and `secondaryAction` to `ErrorState`; added `live` (`role="status"`, `aria-live="polite"`) to `StatusIndicator`; updated `component-showcase.tsx` to exercise all states. Verified `npm run lint`, `npx tsc --noEmit`, and `npm run build` pass.
- [x] **T009** Audited and improved keyboard accessibility, ARIA/semantic HTML, focus management, and reduced-motion behavior: added a keyboard-accessible skip-to-main-content link in `app/layout.tsx` targeting `#main-content` in `app/page.tsx`, stabilized `Dialog` `onClose` via ref so parent re-renders do not overwrite `previousFocusRef` (with `isConnected` guard on focus restoration), switched `Button` loading spinner to `motion-safe:animate-spin`, and added semantic `<section>` + `<h2>` hierarchy in `component-showcase.tsx`. Verified `npm run lint`, `npx tsc --noEmit`, and `npm run build` pass.
- [x] **T010** Verified `npm run lint`, `npx tsc --noEmit`, `npm run build`, and live browser rendering of `http://localhost:3000` at `1440x900`, `1280x800`, `768x1024`, `390x844`, and `360x800` via Chrome DevTools. Zero console errors, zero horizontal overflow, clean typography scaling, responsive wrapping, working loading/error/empty states, centered dialog + Escape dismissal, and visible `:focus-visible` outlines.

## 4. Current task

**T010 complete (Phase 1 exit criteria met).** Awaiting user approval before starting **T011** (Build the Foundry hero with profile input and clear CTA).

## 5. Known risks, runtime compatibility, and open questions

- **Python 3.14.2 compatibility evaluation:** Only Python `3.14.2` (64-bit) is installed locally (`py -0`).
  - **Supported on Python 3.14:** `FastAPI` (0.118.3+), `Pydantic` v2 (2.12+ / `pydantic-core`), `SQLAlchemy` (2.0+/2.1+), `PyMuPDF` (pre-built wheels in 1.26.x+/2.x), and `google-genai`.
  - **Compatibility risk (`pydantic.v1`):** `Pydantic` v1 is incompatible with Python 3.14+. Some `LangChain` / `LangGraph` code paths or transitive dependencies still reference `pydantic.v1`, which can raise `UserWarning` or runtime errors on Python 3.14.
  - **Mitigation:** When scaffolding `backend/` in Phase 4, either use a Python 3.12/3.13 virtual environment (e.g., via `uv`) or verify that pinned `langchain`/`langgraph` versions run cleanly without `pydantic.v1` failures on 3.14.
- **Greenfield scaffolding:** `frontend/` (Next.js App Router + TypeScript + Tailwind CSS) and `backend/` (FastAPI + Python) must be scaffolded before their respective implementation phases.
- **Gemini model availability:** Exact `GEMINI_MODEL` identifier and API key configuration must be verified when integrating the live provider (with explicit demo fallback).
- **Live startup discovery & founder contact data:** Require reliable providers, source attribution, and explicit verified/unverified/demo labelling.
- **Production concerns (deferred post-MVP):** SQLite replacement, production auth/authorization, and email sending/inbox monitoring.

## 6. Bugs and blockers

No implementation bugs have been recorded because implementation has not yet been verified.

Record each issue here with:

- Date.
- Task ID.
- Reproduction steps.
- Expected behavior.
- Actual behavior.
- Error/log excerpt with secrets and personal data removed.
- Resolution or next action.

## 7. Decision log

| Date       | Decision                                   | Reason                                |
| ---------- | ------------------------------------------ | ------------------------------------- |
| 2026-11-25 | Use Foundry as the product name            | Product identity                      |
| 2026-11-25 | Use a clean, light-first SaaS direction    | Clear, trustworthy product experience |
| 2026-11-25 | Keep human approval mandatory for outreach | User control and safety               |
| 2026-11-25 | Use deterministic match scoring            | Reproducibility and explainability    |
| 2026-11-25 | Label demo and simulated data              | Avoid misleading users                |

## 8. Repository-specific implementation plan & next steps

### Current structure

```text
Foundry/
├── .git/
├── .gitignore
└── docs/
    ├── ARCHITECTURE.md
    ├── DESIGN.md
    ├── PRD.md
    ├── PROGRESS.md
    ├── RULES.md
    └── TASKS.md
```

### Implementation plan (post-approval)

1. **Phase 1 (T006–T010) — Frontend foundation:** Scaffold `Foundry/frontend/` (Next.js App Router, TypeScript, Tailwind CSS), define `DESIGN.md` tokens/typography (Geist/Inter), build reusable UI primitives (`Button`, `Input`, `Card`, `Badge`, `Dialog`, status/loading/error/empty states), and verify lint/typecheck/responsive rendering.
2. **Phase 2 (T011–T018) — Marketing landing page:** Build the 10-section landing page in `frontend/` with honest product previews, connect CTAs to `/app/onboarding`, and verify responsive layout + production build.
3. **Phase 3 (T019–T024) — Application shell & onboarding:** Build `/app/*` layout (persistent desktop sidebar, mobile nav), onboarding/resume upload UI, profile review/edit, preferences form, and dashboard with explicit demo/empty states.
4. **Phase 4 (T025–T030) — Backend foundation:** Scaffold `Foundry/backend/` (using Python 3.12/3.13 venv or verified 3.14-compatible pins), configure FastAPI + Pydantic v2 + SQLAlchemy + SQLite, implement domain models, repositories, `/api/health`, `/api/auth/demo`, and pytest suite.
5. **Phase 5 (T031–T038) — Resume & candidate intelligence:** Add validated PDF upload, PyMuPDF extraction, `LLMProvider` interface with Gemini + deterministic demo fallback, and profile/preference persistence.
6. **Phase 6 (T039–T045) — Startup discovery & research:** Implement `SearchProvider`, `ResearchProvider`, and `FounderDiscoveryProvider` interfaces with labelled demo dataset, evidence references, and verification status.
7. **Phase 7 (T046–T054) — LangGraph workflow:** Implement typed stateful graph (`candidate_analysis → startup_discovery → company_research → founder_research → candidate_matching → outreach_generation → save_drafts`) with persistent `AgentExecution` events, bounded retries, and idempotency.
8. **Phase 8 (T055–T061) — Matching & outreach:** Implement deterministic weighted scoring (30/25/15/15/10/5%), grounded outreach draft generation, draft versioning, and explicit approve/reject endpoints (no auto-send).
9. **Phase 9 (T062–T069) — Frontend-backend integration:** Add typed `lib/api.ts` client and connect onboarding, discovery polling, company detail, outreach approval, and activity history end-to-end.
10. **Phase 10 (T070–T076) — Quality & demo readiness:** Run full pytest, lint, typecheck, production build, responsive checks (1440/768/390px), security/privacy review, and update `README.md` + `docs/`.

### Immediate next task

- **T011** — _Build the Foundry hero with profile input and clear CTA_ (Phase 2 — Marketing landing page; waiting for user approval).

## 9. Update format

After each task, update this file with:

```text
Date:
Task ID:
Status: Done / Blocked / In progress
Files changed:
Checks run:
Results:
Known issues:
Next task:
```

Never mark a task done unless its acceptance criteria have been checked.

---

### Task Log

```text
Date: 2026-11-25
Task ID: T001–T004
Status: Done
Files changed: Foundry/PROGRESS.md
Checks run: Get-ChildItem -Recurse -Force; git status; git log -n 5 --oneline; node --version; npm --version; python --version; git --version
Results: Workspace contains only Foundry/{ARCHITECTURE,DESIGN,PRD,PROGRESS,RULES,TASKS}.md. No .git repo, no frontend/, no backend/, no dependencies. Local runtimes: Node v24.13.0, npm 11.6.2, Python 3.14.2, Git 2.43.0.windows.1.
Known issues: Docs are in Foundry/ rather than docs/; no Git repo initialized; no application scaffolding exists yet.
Next task: T005 (Write a short implementation plan based on the real codebase), awaiting user approval before T006 or any application implementation.
```

```text
Date: 2026-11-25
Task ID: T005
Status: Done
Files changed: Foundry/.gitignore, Foundry/docs/{PRD,ARCHITECTURE,DESIGN,RULES,TASKS,PROGRESS}.md (moved from Foundry/)
Checks run: git init; Move-Item *.md docs/; py -0; pip --version; Get-ChildItem -Recurse -Force; web compatibility checks for PyMuPDF, Pydantic, FastAPI, SQLAlchemy, LangChain, LangGraph, google-genai on Python 3.14
Results: Git initialized in Foundry/. All 6 docs moved to Foundry/docs/. .gitignore created. Python 3.14.2 is the only Python installed; FastAPI/SQLAlchemy/PyMuPDF/google-genai/Pydantic v2 support 3.14, but LangChain/LangGraph have pydantic.v1 compatibility risks on 3.14.
Known issues: LangChain/LangGraph compatibility with Python 3.14.2 must be mitigated (via Python 3.12/3.13 venv or verified dependency pins) in Phase 4.
Next task: T006 (Establish design tokens, typography, spacing and responsive container rules) — awaiting user approval.
```

```text
Date: 2026-11-26
Task ID: T006
Status: Done
Files changed: Foundry/frontend/ (scaffolded Next.js app), Foundry/frontend/app/globals.css, Foundry/frontend/app/layout.tsx, Foundry/frontend/app/page.tsx, Foundry/frontend/lib/utils.ts, Foundry/frontend/components/shared/page-container.tsx, Foundry/docs/TASKS.md, Foundry/docs/PROGRESS.md
Checks run: npm run lint; npx tsc --noEmit; npm run build (after clearing .next)
Results: ESLint passed with 0 errors/warnings; TypeScript typecheck passed with 0 errors; Next.js production build compiled and prerendered / and /_not-found.
Known issues: next/font/google requires network access during build to fetch Geist/Geist Mono; an earlier stale .next cache caused a transient Turbopack worker panic on Windows, resolved by clearing .next before building.
Next task: T007 (Build reusable buttons, inputs, cards, badges, dialogs and status components) — awaiting user approval.
```

```text
Date: 2026-11-26
Task ID: T007
Status: Done
Files changed: Foundry/frontend/components/ui/{button,input,textarea,card,badge,dialog,status-indicator,skeleton,empty-state,error-state,index}.ts(x), Foundry/frontend/components/shared/component-showcase.tsx, Foundry/frontend/app/page.tsx, Foundry/docs/TASKS.md, Foundry/docs/PROGRESS.md
Checks run: npm run lint; npx tsc --noEmit; npm run build (after clearing .next)
Results: ESLint passed with 0 errors/warnings; TypeScript typecheck passed with 0 errors; Next.js production build compiled in 4.2s and prerendered / and /_not-found.
Known issues: None in code; same Windows Turbopack .next cache note and network requirement for next/font/google during build.
Next task: T008 — awaiting user approval.
```

```text
Date: 2026-11-26
Task ID: T008
Status: Done
Files changed: Foundry/frontend/components/ui/{dialog,skeleton,empty-state,error-state,status-indicator,index}.ts(x), Foundry/frontend/components/shared/component-showcase.tsx, Foundry/docs/TASKS.md, Foundry/docs/PROGRESS.md
Checks run: npm run lint; npx tsc --noEmit; npm run build (after clearing .next)
Results: ESLint passed with 0 errors/warnings; TypeScript typecheck passed with 0 errors; Next.js production build compiled in 8.2s and prerendered / and /_not-found.
Known issues: No frontend unit/component test runner is installed yet (only lint, typecheck, and build were run).
Next task: T009 (Verify keyboard focus, accessible labels and reduced-motion behavior) — awaiting user approval.
```

```text
Date: 2026-11-26
Task ID: T009
Status: Done
Files changed: Foundry/frontend/app/layout.tsx, Foundry/frontend/app/page.tsx, Foundry/frontend/components/ui/dialog.tsx, Foundry/frontend/components/ui/button.tsx, Foundry/frontend/components/shared/component-showcase.tsx, Foundry/docs/TASKS.md, Foundry/docs/PROGRESS.md
Checks run: npm run lint; npx tsc --noEmit; npm run build (after clearing .next)
Results: ESLint passed with 0 errors/warnings; TypeScript typecheck passed with 0 errors; Next.js production build compiled in 7.6s and prerendered / and /_not-found.
Known issues: Automated browser/screen-reader testing was not run; T010 covers desktop/mobile rendering inspection.
Next task: T010 (Run lint/type checks and inspect desktop/mobile rendering) — awaiting user approval.
```

```text
Date: 2026-11-26
Task ID: T010
Status: Done
Files changed: Foundry/docs/TASKS.md, Foundry/docs/PROGRESS.md
Checks run: npm run lint; npx tsc --noEmit; npm run build; live Chrome DevTools inspection of http://localhost:3000 at 1440x900, 1280x800, 768x1024, 390x844, 360x800
Results: Automated checks passed (ESLint 0 errors, tsc 0 errors, Next.js build compiled in 652ms and prerendered / and /_not-found). Browser inspection passed across all 5 viewports with zero console errors, zero horizontal overflow, responsive wrapping, working loading/error/empty states, centered dialog + Escape dismissal, and visible keyboard focus outlines.
Known issues: None.
Next task: T011 (Build the Foundry hero with profile input and clear CTA) — awaiting user approval.
```
