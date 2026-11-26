import { PageContainer, Section } from "@/components/shared/page-container";
import { Badge } from "@/components/ui";

const WORKFLOW_STEPS = [
  {
    step: "01",
    title: "Build your candidate profile",
    description:
      "Start with your resume, LinkedIn, projects, skills, and preferences—then review and edit your profile before matching begins.",
    detail: "Candidate input · Editable profile",
  },
  {
    step: "02",
    title: "Discover relevant startups",
    description:
      "Find startups aligned with your skills, interests, and work preferences using transparent, explainable criteria.",
    detail: "Fit signals · Weighted criteria",
  },
  {
    step: "03",
    title: "Research companies and founders",
    description:
      "Present company context, founder information, and supporting sources transparently, distinguishing verified facts from unverified notes.",
    detail: "Source-attributed · Traceable",
  },
  {
    step: "04",
    title: "Prepare personalized outreach",
    description:
      "Generate an editable, personalized outreach draft grounded in your profile and company research—you review and approve before anything is sent.",
    detail: "Human approval · No auto-sending",
  },
] as const;

export function WorkflowSection() {
  return (
    <Section
      id="how-it-works"
      aria-labelledby="workflow-heading"
      spacing="spacious"
      className="border-t border-border bg-background"
    >
      <PageContainer>
        <div className="max-w-2xl">
          <Badge variant="primary">How it works</Badge>
          <h2 id="workflow-heading" className="text-h2 mt-4 text-foreground">
            Four steps from profile to a thoughtful introduction.
          </h2>
          <p className="text-body mt-4 text-muted">
            Each stage is designed to be inspectable—connecting your background
            to real company context while keeping final decisions in your hands.
          </p>
        </div>

        {/* Connected four-step progression */}
        <div className="relative mt-12">
          {/* Desktop horizontal connector line aligned with 40px step badges (24px pad + 20px) */}
          <div
            aria-hidden="true"
            className="pointer-events-none absolute top-11 right-12 left-12 hidden h-px bg-border lg:block"
          />

          <ol className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 lg:gap-5">
            {WORKFLOW_STEPS.map((item) => (
              <li
                key={item.step}
                className="relative flex flex-col justify-between rounded-[var(--radius-card)] border border-border bg-surface p-5 sm:p-6"
              >
                <div>
                  <div className="flex items-center justify-between gap-3">
                    <span
                      aria-hidden="true"
                      className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-primary/25 bg-primary-soft font-mono text-[13px] font-semibold text-primary"
                    >
                      {item.step}
                    </span>
                    <span className="text-label text-muted">
                      Step {Number(item.step)} of 4
                    </span>
                  </div>

                  <h3 className="mt-5 text-[17px] font-semibold text-foreground">
                    {item.title}
                  </h3>
                  <p className="mt-2 text-[14px] leading-relaxed text-muted">
                    {item.description}
                  </p>
                </div>

                <p className="mt-5 border-t border-border pt-3.5 text-[12px] font-medium text-foreground/80">
                  {item.detail}
                </p>
              </li>
            ))}
          </ol>
        </div>

        <div className="mt-8 flex flex-col gap-2 rounded-[var(--radius-card)] border border-border bg-surface-muted/60 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-[14px] font-medium text-foreground">
            You stay in control at every step.
          </p>
          <p className="text-[13px] text-muted">
            Edit your profile, inspect every source, and approve or reject every
            outreach draft manually.
          </p>
        </div>
      </PageContainer>
    </Section>
  );
}
