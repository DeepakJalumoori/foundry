# Foundry — Product Requirements Document

**Status:** Final frozen product scope | **Version:** 3.0 | **Product:** Foundry
**Nature:** Personal AI-powered job search agent targeting pre-seed to Series C startups (Agentic AI portfolio project, NOT a commercial SaaS product)

---

## 1. Product definition

Foundry is a simple AI-powered job search agent designed for candidates targeting **pre-seed to Series C startups**.

It is built for personal use and as a serious Agentic AI engineering portfolio project. It is **not** a commercial SaaS product—there are no subscriptions, billing, marketing landing pages, or multi-tenant CRM features.

The candidate signs in, provides a **LinkedIn profile URL or resume**, and the agent:

1. Extracts the candidate's skills, experience, education, and projects.
2. Discovers relevant pre-seed to Series C startups.
3. Researches what each company does.
4. Identifies recent funding information.
5. Finds hiring signals from company career pages and job platforms.
6. Discovers company founders.
7. Finds publicly available professional founder email addresses where possible.
8. Explains why the candidate should approach each company.
9. Calculates explainable candidate-company match scores.
10. Uses RAG to retrieve relevant candidate and company evidence.
11. Generates personalized founder outreach email drafts.

Foundry generates drafts; the candidate manually reviews, approves, and sends them.

---

## 2. Target user and problem

### Target user
A technical candidate (student or engineer) targeting pre-seed to Series C startups.

### Problem
- Searching across scattered startup lists, funding announcements, and career pages is slow and repetitive.
- Many promising early-stage startups do not post formal openings on major job boards, or post them only on their own career pages.
- Finding the right founder and verifying whether a public professional email exists takes manual effort.
- Generic cold emails fail because they do not connect the candidate's specific projects and skills to sourced company evidence.

---

## 3. Core workflow

Foundry runs a single orchestrated LangGraph workflow:

```text
candidate_input
  → candidate_profile_extraction
  → startup_discovery
  → company_research
  → funding_signal_analysis
  → hiring_signal_analysis
  → founder_discovery
  → rag_context_retrieval
  → deterministic_candidate_company_matching
  → personalized_outreach_generation
  → structured_results
```

---

## 4. Opportunity classification

Every discovered startup must be classified honestly based on available evidence:

- **Active opportunities:** Relevant public job openings have been found on company career pages or job platforms (with source URLs and dates where available).
- **Hidden opportunities:** No relevant public opening was found, but other credible evidence (such as product direction, technical stack alignment, team growth, or recent milestones) justifies considering a proactive approach.

**Rule:** Funding alone is **not** proof of hiring. Recent funding is recorded as a funding signal, never as a substitute for a hiring signal.

---

## 5. Minimal frontend scope

The frontend is intentionally minimal—no four-destination workspace, no marketing landing page, no elaborate onboarding, and no settings or CRM dashboards.

It consists of four focused views/states:

1. **Minimal login/sign-in:** Simple single-user entry gate.
2. **Candidate input:** LinkedIn profile URL or PDF resume upload (plus optional target role/preference hints).
3. **Agent processing state:** Live step-by-step progress of the LangGraph workflow.
4. **Research results interface:** Structured results per company showing:
   - Company name and description.
   - Funding stage and funding evidence (source URL and date where available).
   - Hiring signals and their sources (clearly distinguishing **Active** vs. **Hidden** opportunities).
   - Why the candidate should reach out.
   - Founder name and role.
   - Public professional email, if available.
   - Email source and verification status.
   - Deterministic match score and explanation.
   - Personalized email draft (editable, with explicit candidate approval).

---

## 6. Functional and safety requirements

### Candidate input and extraction
- Accept a PDF resume upload (validated for type and size) or a LinkedIn profile URL.
- **No unauthorized LinkedIn scraping:** LinkedIn URL input must never perform unauthorized scraping; it relies on user-supplied/publicly authorized data or explicit demo fallback until an authorized integration exists.
- Allow the candidate to review extracted skills, experience, education, and projects.

### Discovery, signals, and founder contacts
- Target startups from **pre-seed to Series C**.
- Include source URLs and dates (where available) for company claims, funding evidence, and hiring signals.
- Never fabricate founder names or email addresses.
- Record email provenance (source URL/method) and verification status (`verified`, `unverified`, `unavailable`).

### RAG and deterministic matching
- Index candidate profile/resume chunks and company research/signal documents using a lightweight local retriever (**SQLite/BM25** initially; add embeddings only if retrieval evaluation demonstrates a need).
- Compute candidate-company match scores deterministically in Python (`30%` skills, `25%` role, `15%` experience, `15%` projects, `10%` preferences, `5%` location/work mode).
- LLMs may explain match scores using retrieved evidence, but **cannot** invent or alter deterministic match-score arithmetic.

### Outreach and human control
- Generate personalized founder outreach email drafts grounded in retrieved candidate and company evidence.
- Require explicit candidate approval before outreach; **no automatic email sending**.

---

## 7. Explicitly out of scope

- Marketing landing page, FAQ, pricing/billing, or SaaS conversion sections.
- Multi-destination workspace navigation (Overview dashboard, separate Profile workspace, separate Discovery workspace, separate Outreach workspace, Matches, Contacts, Settings).
- Elaborate multi-step onboarding wizards.
- CRM features, inbox/reply monitoring, or Gmail/Outlook auto-sending.
- Multi-tenant organizations or commercial SaaS infrastructure.

---

## 8. Acceptance criteria

The MVP is complete when one candidate can:
1. Sign in via the minimal login screen.
2. Provide a resume PDF or LinkedIn URL.
3. Trigger the LangGraph agent and observe step-by-step processing.
4. Inspect structured results containing company info, funding/hiring signals with sources, active vs. hidden classification, founder details and email provenance, deterministic match score + explanation, and personalized outreach drafts.
5. Edit and explicitly approve or reject a draft (persisted in SQLite) without automatic sending.
