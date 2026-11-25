# Foundry — Architecture

**Status:** Initial architecture  
**Version:** 1.0

## 1. Architecture overview

Foundry uses a TypeScript web frontend and a Python API/backend. The backend owns persistence, provider integrations, agent orchestration, matching, research and outreach generation.

```text
┌───────────────────────────────────────────────────────────┐
│                    Next.js + TypeScript                    │
│ Landing · Onboarding · Dashboard · Discovery · Outreach    │
└────────────────────────────┬──────────────────────────────┘
                             │ HTTP / JSON
                             ▼
┌───────────────────────────────────────────────────────────┐
│                    FastAPI application                     │
│ API routes · validation · auth boundary · error handling   │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────┐    ┌────────────────────────────┐
│ Application services     │    │ LangGraph workflows        │
│ Profiles · Matching      │    │ Candidate analysis         │
│ Research · Outreach      │    │ Discovery · Research        │
└──────────────┬───────────┘    │ Founder · Matching          │
               │                │ Outreach generation         │
               │                └──────────────┬─────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────┐    ┌────────────────────────────┐
│ SQLAlchemy repositories  │    │ Provider interfaces         │
│ SQLite for MVP            │    │ Gemini · Search · Research  │
│ Persistent workflow data  │    │ Founder discovery           │
└──────────────────────────┘    └────────────────────────────┘
```

## 2. Technology stack

### Frontend
- Next.js App Router.
- React.
- TypeScript.
- Tailwind CSS, if already present in the repository.
- Framer Motion for restrained interaction animation, if installed and useful.
- A small reusable component system.

### Backend
- Python 3.12+.
- FastAPI.
- Pydantic for request, response and structured model validation.
- SQLAlchemy for persistence.
- SQLite for local MVP development.
- PyMuPDF for PDF text extraction.
- LangChain for model/provider integrations where useful.
- LangGraph for stateful multi-step agent workflows.
- Google Gemini API through a backend-only provider.

### Testing and tooling
- Pytest for backend tests.
- Frontend linting and production build.
- HTTP integration tests for critical API flows.
- Environment variables for local configuration.

Do not add libraries simply because they are fashionable. Check the current project and use existing dependencies where suitable.

## 3. Suggested repository structure

```text
foundry/
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── layout.tsx
│   │   ├── globals.css
│   │   └── app/
│   │       ├── dashboard/page.tsx
│   │       ├── onboarding/page.tsx
│   │       ├── discovery/page.tsx
│   │       ├── companies/[id]/page.tsx
│   │       ├── outreach/page.tsx
│   │       ├── activity/page.tsx
│   │       └── settings/page.tsx
│   ├── components/
│   │   ├── marketing/
│   │   ├── dashboard/
│   │   ├── discovery/
│   │   ├── company/
│   │   ├── outreach/
│   │   ├── onboarding/
│   │   ├── shared/
│   │   └── ui/
│   ├── lib/
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── utils.ts
│   └── public/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── agents/
│   │   ├── graphs/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── providers/
│   │   ├── repositories/
│   │   └── core/
│   ├── tests/
│   └── pyproject.toml
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── DESIGN.md
│   ├── RULES.md
│   ├── TASKS.md
│   └── PROGRESS.md
├── .env.example
├── .gitignore
└── README.md
```

This is the target structure, not an instruction to move or delete existing files blindly. Inspect the repository first and adapt to its current layout.

## 4. Backend domain model

Initial entities:

- **User:** identity and account metadata.
- **CandidateProfile:** structured candidate information.
- **CandidatePreference:** role, location, work mode, industry and opportunity preferences.
- **Company:** normalized company identity and public metadata.
- **CompanyResearch:** research summary, evidence references, provider and timestamps.
- **FounderContact:** founder/contact identity, source and verification status.
- **MatchResult:** deterministic score, dimensions, explanation and workflow relation.
- **OutreachDraft:** recipient, subject, body, status and version.
- **AgentExecution:** workflow status, step events, errors and timing.

Use foreign keys and appropriate uniqueness constraints. Store timestamps in a consistent timezone-aware format. Avoid duplicating data that should be referenced by ID.

## 5. API boundaries

Suggested endpoints (adapt names to existing conventions):

```text
GET    /api/health

POST   /api/auth/demo
GET    /api/auth/me

POST   /api/candidate/resume
GET    /api/candidate/profile
PUT    /api/candidate/profile
PUT    /api/candidate/preferences

POST   /api/discovery/start
GET    /api/discovery/workflows/{workflow_id}
GET    /api/companies
GET    /api/companies/{company_id}

GET    /api/matches

GET    /api/outreach
GET    /api/outreach/{draft_id}
PUT    /api/outreach/{draft_id}
POST   /api/outreach/{draft_id}/approve
POST   /api/outreach/{draft_id}/reject

GET    /api/agent-executions
```

Use Pydantic schemas at API boundaries. Do not return ORM objects directly.

## 6. Data flow

### Resume and profile
1. Frontend uploads a PDF to FastAPI.
2. Backend validates file type, size and content.
3. PyMuPDF extracts text.
4. Gemini provider optionally converts text into a structured Pydantic candidate profile.
5. Backend validates and persists the result.
6. Frontend displays the extracted profile for user review and editing.

### Discovery and agent workflow
1. Frontend requests a discovery workflow.
2. FastAPI creates a persistent execution record.
3. LangGraph receives candidate profile and preferences.
4. Candidate analysis prepares normalized skills and role signals.
5. Search provider discovers candidate companies.
6. Research provider gathers source material.
7. Founder discovery provider identifies relevant contacts where evidence exists.
8. Matching service calculates deterministic scores.
9. Outreach service generates drafts for suitable matches.
10. Results and execution events are persisted.
11. Frontend polls or retrieves workflow status and displays results.

### Outreach approval
1. Candidate opens a draft.
2. Candidate edits if necessary.
3. Candidate explicitly approves or rejects.
4. Backend records the decision and version.
5. MVP stops at approval; it does not send email automatically.

## 7. Agent graph

Suggested high-level graph:

```text
START
  │
  ▼
candidate_analysis
  │
  ▼
startup_discovery
  │
  ▼
company_research
  │
  ▼
founder_research
  │
  ▼
candidate_matching
  │
  ├── no suitable matches ───────────────► END
  │
  ▼
outreach_generation
  │
  ▼
save_drafts
  │
  ▼
END
```

Use typed graph state. Persist intermediate results and execution events. Make retries bounded and steps idempotent where possible. Do not use an LLM for deterministic database operations or score arithmetic.

## 8. Provider interfaces

Define interfaces before provider-specific implementation:

- `LLMProvider`: structured generation and text generation.
- `SearchProvider`: company discovery.
- `ResearchProvider`: evidence collection and synthesis.
- `FounderDiscoveryProvider`: contact discovery.

Provide deterministic demo implementations. Demo data must be visibly labelled and must not masquerade as live research.

## 9. RAG boundary

RAG is an enhancement, not a prerequisite for the first working end-to-end flow.

Initial retrieval corpus:
- Candidate resume text.
- Candidate projects and profile.
- Company research documents and evidence.

Keep metadata such as user ID, company ID, source, document type and timestamps. Enforce user-level data isolation. Start with a simple retrieval abstraction and SQLite-backed fallback if needed. Add a vector store only when there is a measured need.

## 10. Configuration and secrets

Example backend `.env.example`:

```env
APP_ENV=development
DATABASE_URL=sqlite:///./foundry.db
GEMINI_API_KEY=
GEMINI_MODEL=
AI_PROVIDER=demo
SEARCH_PROVIDER=demo
RESEARCH_PROVIDER=demo
MAX_RESUME_SIZE_MB=5
```

The exact model identifier must be configured from a currently available model. Never expose `GEMINI_API_KEY` to browser code or commit real secrets.

## 11. Reliability and security

- Validate every request and upload.
- Use parameterized ORM operations.
- Apply timeouts and bounded retries to external calls.
- Avoid logging resumes, access tokens, API keys or full private messages.
- Keep demo and live providers explicit.
- Persist workflow failures with actionable error codes.
- Prevent duplicate workflow submissions where possible.
- Keep approval separate from sending.
- Add authentication and authorization before exposing private user data in production.
