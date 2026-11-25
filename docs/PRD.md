# Foundry — Product Requirements Document

**Status:** Initial product definition  
**Version:** 1.0  
**Product:** Foundry  
**Tagline:** Your next opportunity isn't always posted.

## 1. Product vision

Foundry is an AI-powered career discovery and founder-outreach platform. It helps candidates identify relevant early-stage and growing startups, understand why they may be a fit, research the people behind those companies, and prepare thoughtful introductions.

Foundry is not another job board. Its central workflow is **candidate intelligence → startup discovery → company and founder research → transparent matching → human-approved outreach**.

The product should make proactive career discovery more focused, evidence-based, and less repetitive.

## 2. Target users

### Primary users
- Final-year university students seeking internships or entry-level roles.
- Early-career software engineers seeking startup opportunities.
- Backend, full-stack, AI/ML and infrastructure-focused candidates.

### Secondary users
- Experienced engineers interested in smaller companies.
- Candidates exploring companies before a role is publicly advertised.

### Initial candidate profile
The initial product is optimized for technically oriented candidates. It should support other professional profiles later without hard-coding the product around one degree, school, or technology stack.

## 3. User problem

Candidates often:
- Apply to many roles without knowing whether the company is a good fit.
- Compete in crowded application funnels.
- Struggle to identify the right founder or hiring contact.
- Send generic outreach that does not explain their relevance.
- Spend significant time researching companies manually.
- Have difficulty distinguishing genuine hiring signals from speculation.

Foundry should reduce this research and preparation burden while keeping the candidate in control.

## 4. Product promise

A candidate can provide a resume or profile, describe their preferences, and receive:
1. A structured candidate profile.
2. A shortlist of relevant startups.
3. Company research with traceable evidence.
4. Founder/contact information with source and verification status.
5. An explainable fit assessment.
6. A personalized outreach draft that the candidate can edit and approve.

Foundry must never promise a job, interview, reply, or hiring opportunity.

## 5. Core user journey

1. **Landing page:** The visitor understands the value proposition and starts onboarding.
2. **Profile input:** The candidate uploads a PDF resume and/or provides profile links and information.
3. **Profile extraction:** The system extracts structured information and presents it for correction.
4. **Preferences:** The candidate chooses role types, technologies, locations, work modes, industries, company stages and opportunity types.
5. **Discovery:** The candidate starts a discovery workflow.
6. **Research:** Foundry gathers company evidence and researches relevant founders or contacts.
7. **Matching:** Foundry calculates an explainable fit score from deterministic criteria.
8. **Results:** The candidate reviews matches, evidence, fit dimensions and missing skills.
9. **Outreach:** Foundry generates an editable, personalized draft.
10. **Approval:** The candidate explicitly approves or rejects the draft.
11. **Tracking:** The candidate sees draft and outreach statuses. Sending and inbox monitoring are later integrations, not assumed MVP capabilities.

## 6. MVP scope

### P0 — Required
- Responsive marketing landing page.
- Demo-mode onboarding and candidate profile.
- PDF resume upload and text extraction.
- Structured candidate profile extraction with Gemini when configured.
- Candidate profile editing and persistence.
- Candidate preferences.
- Startup discovery through a provider interface.
- Clearly labelled demo startup dataset when live search is not configured.
- Company research summaries based only on supplied evidence.
- Founder/contact discovery with source and verification fields.
- Deterministic candidate-company matching with dimension-level explanations.
- Personalized outreach draft generation.
- Human approval, rejection and editing workflow.
- Persistent workflow and agent execution status.
- Dashboard, discovery, company detail, outreach and activity screens.
- Useful loading, error, empty and retry states.
- Clear indication of demo, simulated, unverified and verified data.

### P1 — After MVP
- Production authentication and account management.
- Configurable live search provider.
- More robust research source ingestion and citation display.
- Semantic retrieval over candidate and company information.
- Improved workflow resumability and observability.
- Export of candidate profile and outreach history.

### Deferred
- Automatic email sending.
- Gmail or Outlook OAuth.
- Reply and inbox monitoring.
- Scheduled recurring discovery.
- Payments and subscription billing.
- Claims of verified hiring intent without reliable evidence.
- Complex multi-tenant organization features.

## 7. Functional requirements

### Candidate profile
The profile may contain:
- Name and contact details.
- Education and experience.
- Skills, languages, frameworks and databases.
- Projects and achievements.
- GitHub, LinkedIn and portfolio URLs.
- Candidate-written summary.

The candidate must be able to review and edit extracted information before it is used for matching or outreach.

### Preferences
Support:
- Target roles.
- Technologies.
- Location preferences.
- Remote, hybrid or onsite preference.
- Internship or full-time preference.
- Experience level.
- Preferred industries and company stages.

### Startup discovery
Each company record should distinguish:
- Known company facts.
- Research-derived claims.
- Unverified information.
- Demo-only content.

A company should not be presented as actively hiring unless a reliable source supports that claim. Lack of a public job listing must not be interpreted as proof that a company is hiring.

### Matching
The initial deterministic scoring model:
- Skills alignment: 30%.
- Role relevance: 25%.
- Experience alignment: 15%.
- Project relevance: 15%.
- Candidate preferences: 10%.
- Location/work-mode alignment: 5%.

The score must be reproducible from stored inputs. An LLM may explain the result but must not invent or silently alter the numeric score.

### Outreach
Drafts must be grounded in the candidate's actual profile and sourced company research. Drafts are editable and versioned. No message is sent automatically in the MVP.

## 8. Non-functional requirements

- Keep API keys and provider secrets on the backend.
- Validate all external and user-supplied input.
- Enforce file type and upload size limits.
- Avoid logging full resumes, secrets or unnecessary personal data.
- Use explicit timeouts and bounded retries for provider calls.
- Persist important workflow state and failures.
- Make long-running tasks observable to the frontend.
- Support desktop, tablet and mobile layouts.
- Respect reduced-motion preferences.
- Keep frontend and backend responsibilities clearly separated.
- Include tests for core business rules and API behavior.

## 9. Success criteria

The MVP is successful when a demo user can complete the core journey without manual database edits:
- Upload a resume or enter a profile.
- Review and save the extracted profile.
- Set preferences.
- Run a discovery workflow.
- View startup matches and supporting evidence.
- Open a company profile and inspect research.
- Generate, edit, approve or reject an outreach draft.
- Refresh the app and retain persisted data and statuses.

Success is measured by working, explainable product behavior—not fabricated match counts, reply rates or placement claims.

## 10. Product principles

1. **Candidate control:** The user makes the final decision.
2. **Evidence over confidence:** Show what supports a claim.
3. **Honest AI:** Clearly label uncertainty and demo behavior.
4. **Explainable matching:** Make scores inspectable.
5. **Privacy by design:** Collect and retain only what the workflow needs.
6. **Useful before clever:** Prefer a dependable end-to-end workflow over many disconnected agents.
