# Foundry — Engineering and AI Agent Rules

These rules apply to every coding agent and contributor working in this repository.

## 1. Before changing code

1. Inspect the existing repository, package files, routes, components and tests.
2. Read `PRD.md`, `ARCHITECTURE.md`, `DESIGN.md`, `TASKS.md` and `PROGRESS.md`.
3. Identify the smallest task that can be completed safely.
4. Reuse existing working code when appropriate.
5. State the files you intend to change before a large or cross-cutting change.
6. Do not assume the repository matches the proposed folder tree.

## 2. Scope discipline

- Implement one task at a time.
- Do not build future features unless the current task requires them.
- Do not rewrite working systems merely to match personal preferences.
- Do not add dependencies without a concrete need.
- Do not silently change API contracts, database schemas or product behavior.
- Keep pull-request-sized changes small and reviewable.
- If requirements are ambiguous, record the ambiguity and ask before making a risky assumption.

## 3. Code quality

### TypeScript / React
- Keep TypeScript strict; avoid `any` unless there is a documented reason.
- Prefer small, composable components.
- Keep API calls out of presentational components.
- Centralize API configuration and typed request helpers.
- Handle loading, error, empty and success states.
- Use semantic HTML and accessible labels.
- Do not leave dead buttons or misleading controls.
- Do not suppress lint or type errors to make a build pass.

### Python
- Use type hints for public functions and important data structures.
- Use Pydantic schemas at API boundaries.
- Keep routes thin; put business logic in services.
- Keep persistence logic in repositories or a clear data-access layer.
- Use SQLAlchemy consistently.
- Raise and handle explicit domain errors.
- Avoid broad `except Exception` unless the exception is logged safely and re-raised or converted at a deliberate boundary.
- Keep provider-specific code behind interfaces.

### General
- Prefer readable code over clever abstractions.
- Use descriptive names.
- Avoid duplicated business rules.
- Add tests for meaningful business logic.
- Keep functions focused.
- Update documentation when behavior or architecture changes.

## 4. AI and agent behavior

The AI coding agent must never:
- Invent a feature and claim it is implemented.
- Claim tests passed without running them.
- Claim an integration works without verifying it.
- Fabricate startup data, founder identities, emails, funding, hiring signals or citations.
- Treat model-generated text as verified evidence.
- Let an LLM decide deterministic score arithmetic.
- silently change the matching weights.
- send an email or contact a person without explicit user approval and a real sending integration.
- expose secrets or copy them into frontend code.
- commit API keys, passwords, tokens or private user data.
- delete user work, existing routes or working components without explicit need and explanation.
- replace real API data with hardcoded mock data while presenting it as live.
- hide errors behind fake success states.
- create placeholder controls that appear functional but do nothing.

If a capability is unavailable, show a clear unavailable or demo state.

## 5. Product truth and evidence

- Every company claim should have a source or be labelled as unverified/demo.
- Every founder/contact detail should have a source and verification status.
- A missing job listing does not prove a company is hiring.
- A match score is a heuristic fit estimate, not a probability of getting hired.
- Outreach must use facts from the candidate profile and available company evidence.
- Do not invent candidate skills, experience, projects, achievements or personal connections.
- Make it possible for users to inspect and edit AI-generated profile data and outreach.

## 6. Privacy and security

- Keep Gemini and other provider API keys on the backend.
- Never prefix server secrets with a frontend-exposed environment variable name.
- Validate file type, size and user input.
- Avoid logging resumes, tokens, API keys or unnecessary personal data.
- Enforce ownership checks for candidate, company-related private records, drafts and workflow access.
- Do not trust user IDs supplied by the client as proof of authorization.
- Keep CORS origins explicit outside local development.
- Use safe error messages that do not expose stack traces or secrets to users.

## 7. Agent workflow reliability

- Persist workflow execution status.
- Record step-level events and actionable failure reasons.
- Use bounded retries and timeouts.
- Make retried steps idempotent where possible.
- Avoid duplicate discovery runs caused by repeated clicks.
- Do not lose completed work when a later step fails.
- Keep human approval as a separate, persisted action.
- Do not describe generated drafts as sent messages.

## 8. UI and design rules

- Follow `DESIGN.md`.
- Keep typography, spacing, colors and component states consistent.
- Do not copy Backdoor AI's exact assets, text, source code or branding.
- Do not introduce a second unrelated visual language.
- Support keyboard navigation and visible focus.
- Respect reduced-motion preferences.
- Ensure mobile layouts are usable, not merely compressed.

## 9. Testing and completion

A task is complete only when:
1. The requested behavior is implemented.
2. Relevant tests are added or updated.
3. Tests or checks are run.
4. Failures are fixed or clearly documented.
5. Documentation and `PROGRESS.md` are updated.
6. No unrelated working behavior has been broken.

Report:
- What changed.
- Files changed.
- Commands/checks run.
- Results.
- Known limitations.
- Recommended next task.

Never report an unrun test as passing.
