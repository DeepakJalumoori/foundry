# Foundry — Progress Log

**Last updated:** 2026-11-25  
**Project status:** Pre-implementation (Phase 0 complete — T001–T005 done)  
**Current phase:** Phase 0 — Repository reconnaissance (complete; awaiting approval for Phase 1 / T006)

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
- [ ] No application implementation exists yet.

## 4. Current task

**T005 complete.** Awaiting user approval before starting **T006** (Phase 1 — Frontend foundation and design system).

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

| Date | Decision | Reason |
|---|---|---|
| 2026-11-25 | Use Foundry as the product name | Product identity |
| 2026-11-25 | Use a clean, light-first SaaS direction | Clear, trustworthy product experience |
| 2026-11-25 | Keep human approval mandatory for outreach | User control and safety |
| 2026-11-25 | Use deterministic match scoring | Reproducibility and explainability |
| 2026-11-25 | Label demo and simulated data | Avoid misleading users |

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
- **T006** — *Establish design tokens, typography, spacing and responsive container rules* (waiting for user approval).

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
