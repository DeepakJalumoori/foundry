# Foundry — Engineering, Evidence, and AI Safety Rules

These rules apply to every coding agent and contributor working in this repository.

---

## 1. Before changing code

1. Inspect the actual repository, routes, components, and tests; never assume docs match code.
2. Read `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/DESIGN.md`, `docs/TASKS.md`, and `docs/PROGRESS.md`.
3. Reuse useful existing UI primitives (`frontend/components/ui/*`) instead of rebuilding them.
4. Preserve uncommitted T020 `ProfileWorkspace` files until inspected during M1; do not discard or overwrite them.

---

## 2. Scope discipline

- Prioritize working backend/agent functionality over UI polish.
- Do **not** build a 4-destination workspace, marketing landing page, onboarding wizard, settings dashboard, or CRM features.
- Do **not** add unnecessary infrastructure (external vector DBs, Redis, Celery, multi-tenant auth).
- Start RAG with **SQLite/BM25**; add embeddings only if retrieval evaluation proves it is needed.
- Defer selecting a live search/research vendor until M4 requirements are evaluated.
- Work one milestone/step at a time and verify before moving on.

---

## 3. Evidence and AI safety requirements (mandatory)

Every agent node, service, and UI view must enforce these rules:

1. **No unauthorized LinkedIn scraping:** Never scrape LinkedIn without authorization. Treat LinkedIn URL input via authorized APIs, user-provided context, or explicit demo fallbacks.
2. **No fabricated founder names or emails:** Never invent founder identities, roles, or email addresses. If unavailable, mark as `unavailable`.
3. **Email provenance and verification required:** Every discovered founder email must record its source URL/provenance and verification status (`verified`, `unverified`, `unavailable`).
4. **Source URLs and dates:** Company claims, funding evidence, and hiring signals must include source URLs and dates where available.
5. **Active vs. hidden distinction:** Clearly separate **Active opportunities** (relevant public job openings found) from **Hidden opportunities** (no public opening found, other credible evidence justifies an approach).
6. **Funding is not proof of hiring:** Never present funding announcements or funding stage alone as proof that a company is hiring.
7. **Deterministic match scores:** LLMs cannot invent, compute, or alter deterministic match-score arithmetic (`30/25/15/15/10/5%`).
8. **No automatic email sending:** Foundry generates drafts only. No SMTP/OAuth auto-sending.
9. **Candidate approval required:** Every outreach draft requires explicit human approval (`approved` / `rejected`) before manual sending by the candidate.
10. **Honest demo labelling:** Deterministic demo/fallback data must be explicitly labelled `demo`.

---

## 4. Code quality

### TypeScript / React
- Strict TypeScript; avoid `any`.
- Keep API calls centralized in `frontend/lib/api.ts`, separate from presentational components.
- Handle loading, error, empty, and retry states explicitly.
- Never leave dead buttons or suppress lint/type errors.

### Python
- Type hints on public functions and data structures.
- Pydantic v2 schemas at all FastAPI boundaries; never return ORM objects directly.
- Thin FastAPI routes; business logic in services, persistence in repositories, external integrations behind provider interfaces.
- Explicit domain errors, bounded retries, and timeouts on external calls.

---

## 5. Privacy and security

- Keep `GEMINI_API_KEY` and provider secrets strictly on the backend (never in `NEXT_PUBLIC_*` or browser code).
- Validate PDF uploads by extension, MIME/magic bytes, and `MAX_RESUME_SIZE_MB`.
- Avoid logging full resumes, secrets, or sensitive personal data.
- Use parameterized SQLAlchemy queries and explicit CORS configuration.

---

## 6. Testing and completion

A milestone step is complete only when:
1. Implemented behavior matches the frozen scope.
2. Relevant tests (`pytest` for backend, `lint` / `tsc` / `build` for frontend) are run and passing.
3. `docs/PROGRESS.md` is updated honestly, distinguishing implemented code, uncommitted work, and pending work.

Never claim an unrun test passed.
