# Foundry — Design System and Minimal Interface Direction

**Status:** Final frozen design specification | **Version:** 3.0

---

## 1. Design philosophy

Foundry is a **minimal, evidence-first job search agent interface**—not a multi-page SaaS platform, CRM, or marketing site.

The UI exists to let one candidate:
1. Sign in quickly.
2. Provide a LinkedIn URL or resume PDF.
3. Watch the agent process each stage honestly.
4. Inspect structured startup research, evidence, match explanations, and outreach drafts in one clean results view.

---

## 2. Color tokens and typography

Preserve the existing light-first design tokens and typography already configured in `frontend/app/globals.css` and `frontend/app/layout.tsx`:

| Token | Hex | Usage |
|---|---|---|
| `--background` | `#F7F8FA` | Page background |
| `--surface` | `#FFFFFF` | Cards, input panels, result containers |
| `--surface-muted` | `#F0F2F5` | Secondary panels, evidence blocks |
| `--foreground` | `#171923` | Primary text |
| `--muted` | `#687080` | Labels, dates, metadata |
| `--border` | `#E4E7EC` | Hairline borders |
| `--primary` | `#4355DB` | Primary actions |
| `--primary-hover` | `#3546C5` | Hover state |
| `--primary-soft` | `#EEF0FF` | Subtle highlights |
| `--success` | `#16845B` | Verified facts, active openings, approved drafts |
| `--warning` | `#A96812` | Hidden opportunities, unverified/pending states, demo notices |
| `--danger` | `#C33D4B` | Errors, rejected drafts |

- **Typography:** `Geist` (`--font-geist-sans`) and `Geist Mono` (`--font-geist-mono`).
- **Accessibility:** Visible `:focus-visible` outlines, semantic headings, `prefers-reduced-motion` support, and text labels paired with status colors.

---

## 3. Four-state minimal UI structure

Do **not** build a marketing landing page, four-destination sidebar workspace, onboarding wizard, or settings dashboard.

### 1. Minimal login / sign-in
- Clean centered card with Foundry title, concise single-line description, and minimal sign-in form.

### 2. Candidate input
- Single focused input panel accepting either:
  - **LinkedIn profile URL**, or
  - **PDF resume upload** (reusing validated file-upload patterns).
- Optional concise target-role/stage filter if helpful, without turning into a separate profile-management workspace.
- Primary action to start the agent run.

### 3. Agent processing state
- Clear step-by-step progress list reflecting the 11 LangGraph nodes (`candidate_input` → `structured_results`).
- Shows current active node, completed steps, provider mode (`Demo` vs. `Live`), and honest error/retry states if a step fails.

### 4. Research results interface
Each discovered startup card / detail panel presents:
- **Company header:** Company name, description, and funding stage (`Pre-seed` to `Series C`).
- **Opportunity badge:** Explicitly distinguishes **Active opportunity** (public opening found) from **Hidden opportunity** (no public opening found, other credible evidence).
- **Funding & hiring signals:** Separate sections for funding evidence and hiring signals, each with **source URLs and dates** where available. Funding alone is never labelled as a hiring signal.
- **Why reach out:** Concise, evidence-grounded rationale for why the candidate should approach this company.
- **Founder & email provenance:** Founder name and role, public professional email (if available; `Unavailable` otherwise), email source URL/method, and verification status (`Verified`, `Unverified`, `Unavailable`).
- **Match score & explanation:** Deterministic numeric score (`0–100`), dimension breakdown (`30/25/15/15/10/5%`), matched/missing skills, and RAG-grounded explanation.
- **Personalized email draft:** Editable subject and body, cited evidence, and explicit **Approve** / **Reject** controls (with clear notice that Foundry never sends emails automatically).

---

## 4. Component reuse and scope cleanup

- **Reuse:** Preserve `frontend/components/ui/*` (`Button`, `Input`, `Textarea`, `Card`, `Badge`, `Dialog`, `StatusIndicator`, `Skeleton`, `EmptyState`, `ErrorState`) and `PageContainer` where helpful.
- **Inspect in M1:** Inspect uncommitted T020 `ProfileWorkspace` (`frontend/components/app/profile/`) to extract useful resume/input controls while removing unnecessary profile-management UI.
- **Remove/redirect in M1:** Remove or redirect `/onboarding`, `/app/matches`, `/app/contacts`, `/app/settings`, the multi-section marketing landing page, and separate workspace pages after checking references.

---

## 5. Responsive layout

- Clean single-column or split-panel layout tested at `1440px` (desktop), `768px` (tablet), and `390px` (mobile) with zero horizontal overflow.
