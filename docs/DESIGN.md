# Foundry — Design System and Visual Direction

**Status:** Initial design specification  
**Version:** 1.0

## 1. Brand personality

Foundry should feel:
- Focused, not noisy.
- Intelligent, not robotic.
- Ambitious, not intimidating.
- Trustworthy, not salesy.
- Modern, not futuristic for its own sake.

The product should feel like a capable career research workspace—not a generic AI chatbot, crypto dashboard or crowded job board.

## 2. Design inspiration

Use the product storytelling and conversion flow of Backdoor AI as high-level inspiration:
- A clear, outcome-led hero.
- A simple explanation of the workflow.
- Strong product-interface previews.
- A direct path from profile input to useful results.
- Clear trust and user-control messaging.

Do not reproduce its exact page, copy, branding, illustrations, assets or proprietary components. Foundry must have its own visual identity.

## 3. Color tokens

Start with this neutral, light-first palette. Verify contrast in the actual UI.

| Token | Hex | Usage |
|---|---|---|
| `--background` | `#F7F8FA` | Main page background |
| `--surface` | `#FFFFFF` | Cards, panels, menus |
| `--surface-muted` | `#F0F2F5` | Secondary panels and input backgrounds |
| `--foreground` | `#171923` | Main text |
| `--muted` | `#687080` | Secondary text |
| `--border` | `#E4E7EC` | Dividers and card borders |
| `--primary` | `#4355DB` | Primary actions and active states |
| `--primary-hover` | `#3546C5` | Hover state |
| `--primary-soft` | `#EEF0FF` | Selected backgrounds |
| `--success` | `#16845B` | Confirmed positive states |
| `--warning` | `#A96812` | Pending or caution states |
| `--danger` | `#C33D4B` | Errors and destructive actions |

Do not use color alone to communicate status. Pair status colors with text or icons.

## 4. Typography

Preferred typeface: **Geist**. Use **Inter** if Geist is not already available.

Suggested scale:
- Display: 56–68px desktop, responsive down to 38–44px.
- H1: 44–56px.
- H2: 32–40px.
- H3: 22–28px.
- Body: 15–17px.
- Supporting text: 13–14px.
- Labels: 11–12px, with restrained letter spacing.

Use readable line lengths. Headlines should be short and outcome-oriented. Avoid excessive uppercase text.

## 5. Layout and spacing

- Use a centered content container, approximately 1120–1200px maximum width.
- Use generous vertical spacing between marketing sections.
- Use a consistent spacing scale based on 4px increments.
- Marketing sections should feel editorial and uncluttered.
- Application screens should prioritize information density without becoming cramped.
- Use a persistent sidebar on desktop and a suitable compact navigation on mobile.

## 6. Shape, borders and elevation

- Cards: 12–18px radius.
- Buttons and inputs: 9–12px radius.
- Large feature panels: 18–24px radius.
- Use thin neutral borders as the default card separation.
- Use subtle shadows only when elevation communicates hierarchy.
- Avoid excessive blur, glassmorphism and floating decorative objects.

## 7. Core components

Build reusable components for:
- Button: primary, secondary, tertiary, destructive.
- Input, textarea and file upload.
- Select and multi-select.
- Badge and status indicator.
- Card and section container.
- Avatar and company logo fallback.
- Match score display with an explanation affordance.
- Evidence/source item.
- Empty state, loading skeleton and error state.
- Confirmation dialog.
- Toast/feedback message.
- Sidebar and mobile navigation.
- Data table/list where appropriate.

Components must have clear disabled, loading, focus, hover and error states.

## 8. Landing page visual structure

1. **Hero:** Clear headline, short supporting copy, LinkedIn URL or resume entry, primary CTA and a realistic Foundry product preview.
2. **Problem:** Contrast scattered, generic applications with focused company research and direct introductions.
3. **How it works:** Four simple steps with clear labels.
4. **Startup discovery:** Company cards with stage, industry, technologies and evidence.
5. **Founder intelligence:** Founder/contact profile with source and verification status.
6. **Personalized outreach:** Email draft preview with edit and approval controls.
7. **Trust and control:** Human approval, transparent sources, privacy and uncertainty.
8. **Use cases:** Student, early-career engineer and experienced engineer scenarios. Do not invent testimonials.
9. **FAQ:** Product behavior, data, AI, matching and outreach.
10. **Final CTA/footer:** Reinforce the one-conversation value proposition.

Suggested hero copy:

**Stop applying everywhere. Start talking to the right founders.**

Foundry discovers startups that fit your experience, researches the people behind them, and prepares personalized introductions you control.

Primary CTA: **Find my startup matches**

Secondary CTA: **See how it works**

## 9. Application experience

### Navigation
- Overview
- Discover startups
- My matches
- Founder contacts
- Outreach drafts
- Conversations (future-ready; do not imply inbox integration exists)
- My profile
- Settings

### Dashboard
Prioritize:
- Current discovery workflow and status.
- Recent relevant matches.
- Drafts awaiting approval.
- Recent agent activity.
- Clear next action.

Do not lead with decorative metrics. Any demo figures must be explicitly labelled.

### Startup card
Show:
- Company identity and short description.
- Industry and stage, when known.
- Candidate fit score.
- Two or three fit reasons.
- Research status and evidence count.
- Clear action to inspect the company.

### Company detail
Separate:
- Company overview.
- What the company builds.
- Technologies and stage.
- Founder/contact details.
- Evidence and sources.
- Candidate fit explanation.
- Research limitations.

### Outreach editor
Show recipient, subject, editable body, personalization rationale and sources. Make approval and rejection distinct actions. Approval must never silently send a message.

## 10. Motion and interaction

- Use short, restrained transitions.
- Animate only when it helps communicate state or hierarchy.
- Avoid constant movement and decorative animation loops.
- Respect `prefers-reduced-motion`.
- Do not delay navigation or critical actions for animation.
- Use clear progress feedback for long-running agent workflows.

## 11. Responsive behavior

Test at:
- Desktop: 1440px.
- Tablet: 768px.
- Mobile: 390px.

Requirements:
- No horizontal overflow.
- Forms remain usable on touch screens.
- Cards stack naturally.
- Navigation remains accessible.
- Tables convert to readable cards or horizontally scroll only when appropriate.
- Product previews must not become unreadable on small screens.

## 12. Content and trust rules

- Never fabricate company facts, founder identities, contact details, funding, hiring signals or sources.
- Label demo content.
- Distinguish verified, unverified and inferred information.
- Do not imply that a match score predicts hiring success.
- Do not claim that outreach has been sent unless a sending integration confirms it.
- Use plain language to explain AI-generated content and uncertainty.
