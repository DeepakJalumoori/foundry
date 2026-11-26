import { PageContainer, Section } from "@/components/shared/page-container";
import { Badge } from "@/components/ui";

const PROBLEM_POINTS = [
  {
    number: "01",
    title: "Hidden opportunities",
    description:
      "Many promising early-stage startup opportunities are not advertised through traditional job portals.",
  },
  {
    number: "02",
    title: "Scattered research",
    description:
      "Candidates must independently research startups, understand their products, identify relevant founders, and determine whether their skills are relevant.",
  },
  {
    number: "03",
    title: "Generic outreach",
    description:
      "Generic cold messages rarely communicate why a candidate is relevant to a particular startup.",
  },
] as const;

const FOUNDRY_SOLUTIONS = [
  {
    label: "Discovery",
    text: "Discover promising startups beyond conventional job listings.",
  },
  {
    label: "Research",
    text: "Understand company context through sourced research.",
  },
  {
    label: "Contacts",
    text: "Identify relevant founders and contacts with verification status.",
  },
  {
    label: "Matching",
    text: "Evaluate candidate-company fit using transparent criteria.",
  },
  {
    label: "Outreach",
    text: "Prepare personalized outreach drafts that candidates can review and edit.",
  },
] as const;

export function ProblemSection() {
  return (
    <Section
      aria-labelledby="problem-heading"
      spacing="spacious"
      className="border-t border-border bg-surface/60"
    >
      <PageContainer>
        <div>
          <div className="max-w-2xl">
            <Badge variant="neutral">Why Foundry</Badge>
            <h2 id="problem-heading" className="text-h2 mt-4 text-foreground">
              The best early-stage roles rarely start on a crowded job board.
            </h2>
            <p className="text-body mt-4 text-muted">
              Applying blindly wastes hours on both sides. Foundry replaces
              repetitive guesswork with structured research, transparent fit
              signals, and introductions you control.
            </p>
          </div>

          <div className="mt-12 grid items-start gap-10 lg:grid-cols-12 lg:gap-12">
            {/* Left: Three core problems in an editorial numbered list */}
            <div className="lg:col-span-6">
              <p className="text-label text-muted uppercase">
                Where manual outreach breaks down
              </p>
              <ol className="mt-4 divide-y divide-border border-y border-border">
                {PROBLEM_POINTS.map((point) => (
                  <li key={point.number} className="py-5 first:pt-4 last:pb-4">
                    <div className="flex items-start gap-4">
                      <span
                        aria-hidden="true"
                        className="font-mono text-[13px] font-medium text-muted pt-0.5"
                      >
                        {point.number}
                      </span>
                      <div>
                        <h3 className="text-[17px] font-semibold text-foreground">
                          {point.title}
                        </h3>
                        <p className="mt-1.5 text-[14px] leading-relaxed text-muted">
                          {point.description}
                        </p>
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            </div>

            {/* Right: How Foundry addresses these problems */}
            <div className="rounded-[var(--radius-panel)] border border-border bg-surface p-6 shadow-xs sm:p-8 lg:col-span-6">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-4">
                <div>
                  <p className="text-label text-primary">With Foundry</p>
                  <h3 className="mt-1 text-[19px] font-semibold text-foreground">
                    One focused research and outreach workspace
                  </h3>
                </div>
                <Badge variant="primary">Candidate-controlled</Badge>
              </div>

              <ul className="mt-5 grid gap-3.5">
                {FOUNDRY_SOLUTIONS.map((item) => (
                  <li
                    key={item.label}
                    className="flex items-start gap-3 rounded-[var(--radius-card)] border border-border bg-surface-muted/45 px-4 py-3"
                  >
                    <span className="text-label mt-0.5 shrink-0 rounded-[var(--radius-control)] bg-primary-soft px-2 py-0.5 text-primary">
                      {item.label}
                    </span>
                    <span className="text-[14px] leading-relaxed text-foreground">
                      {item.text}
                    </span>
                  </li>
                ))}
              </ul>

              <p className="mt-5 border-t border-border pt-4 text-[13px] text-muted">
                Foundry organizes evidence and drafts—every outreach message
                requires your explicit review and approval.
              </p>
            </div>
          </div>
        </div>
      </PageContainer>
    </Section>
  );
}
