# Foundry — Implementation Tasks

**Execution rule:** Complete one task at a time. Verify it, update `PROGRESS.md`, then move to the next task. Do not start the next task while the current task has unresolved failures.

## Phase 0 — Repository reconnaissance

- [x] **T001** Inspect repository structure, existing Git state and current application entry points.
- [x] **T002** Inspect frontend dependencies, scripts, routes, styling and existing components.
- [x] **T003** Inspect backend dependencies, API routes, models, configuration and tests.
- [x] **T004** Read all six project documents and reconcile them with the actual repository.
- [x] **T005** Write a short implementation plan based on the real codebase. Do not modify product code yet.

**Exit criteria:** The current state and safe next step are documented. Existing work is preserved.

## Phase 1 — Frontend foundation and design system

- [x] **T006** Establish design tokens, typography, spacing and responsive container rules.
- [x] **T007** Build reusable buttons, inputs, cards, badges, dialogs and status components.
- [x] **T008** Build loading, error, empty and confirmation states.
- [x] **T009** Verify keyboard focus, accessible labels and reduced-motion behavior.
- [ ] **T010** Run lint/type checks and inspect desktop/mobile rendering.

**Exit criteria:** A consistent, accessible component foundation exists.

## Phase 2 — Marketing landing page

- [ ] **T011** Build the Foundry hero with profile input and clear CTA.
- [ ] **T012** Build the problem and value proposition section.
- [ ] **T013** Build the four-step workflow section.
- [ ] **T014** Build startup discovery and product preview sections.
- [ ] **T015** Build founder intelligence and outreach preview sections.
- [ ] **T016** Build trust, use cases, FAQ and final CTA/footer.
- [ ] **T017** Connect CTAs to actual onboarding routes.
- [ ] **T018** Verify responsive behavior and production build.

**Exit criteria:** Landing page is complete, truthful and navigable.

## Phase 3 — Application shell and onboarding

- [ ] **T019** Build application layout and responsive navigation.
- [ ] **T020** Build profile input and resume upload UI.
- [ ] **T021** Build candidate profile review/edit screen.
- [ ] **T022** Build candidate preference form.
- [ ] **T023** Build overview/dashboard with honest empty and demo states.
- [ ] **T024** Verify navigation and form validation.

**Exit criteria:** A user can complete onboarding in the frontend, with API integration either working or explicitly identified as pending.

## Phase 4 — Backend foundation and persistence

- [ ] **T025** Inspect and finalize backend configuration and application startup.
- [ ] **T026** Configure SQLAlchemy and database session lifecycle.
- [ ] **T027** Implement initial domain models and migrations/schema creation strategy.
- [ ] **T028** Implement Pydantic schemas and repository layer.
- [ ] **T029** Implement health and demo-user endpoints.
- [ ] **T030** Add tests for database setup, schemas and core endpoints.

**Exit criteria:** Backend starts reliably and persists core records.

## Phase 5 — Resume and candidate intelligence

- [ ] **T031** Implement secure PDF upload validation.
- [ ] **T032** Implement PDF text extraction with PyMuPDF.
- [ ] **T033** Define candidate extraction schema and validation.
- [ ] **T034** Implement Gemini provider behind an interface.
- [ ] **T035** Add explicit demo fallback when Gemini is not configured.
- [ ] **T036** Persist and expose candidate profile.
- [ ] **T037** Add profile edit and preference endpoints.
- [ ] **T038** Test extraction, malformed files, missing API key and provider failures.

**Exit criteria:** Candidate information can be extracted, reviewed, edited and persisted.

## Phase 6 — Startup discovery and research

- [ ] **T039** Define SearchProvider, ResearchProvider and FounderDiscoveryProvider interfaces.
- [ ] **T040** Add deterministic demo startup data with clear demo labels.
- [ ] **T041** Implement discovery service and persistence.
- [ ] **T042** Implement company research schema with evidence references.
- [ ] **T043** Implement research synthesis using only supplied evidence.
- [ ] **T044** Implement founder/contact records with source and verification status.
- [ ] **T045** Add tests for provider fallbacks and unsupported claims.

**Exit criteria:** Discovery and research results are persisted and their evidence status is visible.

## Phase 7 — LangGraph workflow

- [ ] **T046** Define typed workflow state.
- [ ] **T047** Implement candidate analysis node.
- [ ] **T048** Implement startup discovery node.
- [ ] **T049** Implement company research node.
- [ ] **T050** Implement founder research node.
- [ ] **T051** Implement matching node integration.
- [ ] **T052** Implement conditional routing and outreach generation node.
- [ ] **T053** Persist execution status and step events.
- [ ] **T054** Add retry, idempotency and failure-path tests.

**Exit criteria:** A discovery workflow can run end-to-end, persist progress and report failures honestly.

## Phase 8 — Matching and outreach

- [ ] **T055** Implement deterministic weighted matching.
- [ ] **T056** Persist dimension scores, reasons and missing skills.
- [ ] **T057** Implement candidate/company retrieval abstraction for grounded context.
- [ ] **T058** Implement outreach draft generation with source-grounded personalization.
- [ ] **T059** Implement draft editing and versioning.
- [ ] **T060** Implement explicit approve/reject endpoints and audit records.
- [ ] **T061** Test score reproducibility, grounding and approval state transitions.

**Exit criteria:** Matches are explainable and drafts can be edited and approved without automatic sending.

## Phase 9 — Frontend integration

- [ ] **T062** Implement centralized typed API client and error handling.
- [ ] **T063** Connect resume upload and profile extraction.
- [ ] **T064** Connect preferences and discovery workflow.
- [ ] **T065** Display workflow progress and failure/retry states.
- [ ] **T066** Connect startup results and company detail views.
- [ ] **T067** Connect outreach editing and approval/rejection.
- [ ] **T068** Connect activity/execution history.
- [ ] **T069** Test the complete user journey in the browser.

**Exit criteria:** The core journey works through the actual API, without hidden hardcoded substitutes.

## Phase 10 — Quality, documentation and demo

- [ ] **T070** Run backend tests and fix failures.
- [ ] **T071** Run frontend lint, type checks and production build.
- [ ] **T072** Test desktop, tablet and mobile layouts.
- [ ] **T073** Review security, privacy, ownership checks and secret handling.
- [ ] **T074** Verify demo/live labels and evidence presentation.
- [ ] **T075** Update README, architecture and implementation status.
- [ ] **T076** Prepare a repeatable demo flow and list known limitations.

**Exit criteria:** A reproducible, honest MVP demo is ready.

## Deferred backlog

- [ ] **D001** Production authentication and account recovery.
- [ ] **D002** Gmail/Outlook OAuth and sending, with explicit approval.
- [ ] **D003** Inbox/reply monitoring.
- [ ] **D004** Scheduled recurring discovery.
- [ ] **D005** Production search provider and richer evidence ingestion.
- [ ] **D006** Vector database integration if retrieval quality requires it.
- [ ] **D007** Billing and subscription plans.

## Working agreement

For every task:
1. State the task ID and expected outcome.
2. Inspect relevant files.
3. Make the smallest complete change.
4. Run relevant checks.
5. Update `PROGRESS.md`.
6. Report blockers and the next single task.
