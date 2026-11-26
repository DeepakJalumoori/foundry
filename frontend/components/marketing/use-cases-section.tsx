import { PageContainer, Section } from "@/components/shared/page-container";
import { Badge } from "@/components/ui";

const USE_CASES = [
  {
    audience: "Final-year students",
    subtitle: "Seeking internships or entry-level roles",
    description:
      "Turn academic projects, internships, and core technical skills into focused startup research instead of sending generic applications into crowded portals.",
    focus: "Projects · Fundamentals · Stage fit",
  },
  {
    audience: "Early-career engineers",
    subtitle: "Exploring small, product-focused teams",
    description:
      "Evaluate early-stage and growing startups by engineering context, product focus, and work preferences before deciding who to introduce yourself to.",
    focus: "Stack alignment · Role scope · Evidence",
  },
  {
    audience: "Domain-focused candidates",
    subtitle: "Targeting specific technologies or industries",
    description:
      "Focus on startups building in areas like backend infrastructure, AI/ML, or developer tools, and prepare tailored introductions grounded in relevant work.",
    focus: "Domain interest · Technical depth · Tailored drafts",
  },
] as const;

export function UseCasesSection() {
  return (
    <Section
      id="use-cases"
      aria-labelledby="use-cases-heading"
      spacing="spacious"
      className="border-t border-border bg-background"
    >
      <PageContainer>
        <div className="max-w-2xl">
          <Badge variant="neutral">Use cases</Badge>
          <h2 id="use-cases-heading" className="text-h2 mt-4 text-foreground">
            Designed for candidates who want signal over volume.
          </h2>
          <p className="text-body mt-4 text-muted">
            Foundry is built first for technically oriented candidates exploring
            early-stage teams—without locking you into a single stack or school.
          </p>
        </div>

        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {USE_CASES.map((item) => (
            <article
              key={item.audience}
              className="flex flex-col justify-between rounded-[var(--radius-card)] border border-border bg-surface p-6"
            >
              <div>
                <p className="text-label text-primary">{item.subtitle}</p>
                <h3 className="mt-2 text-[18px] font-semibold text-foreground">
                  {item.audience}
                </h3>
                <p className="mt-3 text-[14px] leading-relaxed text-muted">
                  {item.description}
                </p>
              </div>
              <p className="mt-5 border-t border-border pt-3.5 text-[12px] font-medium text-foreground/80">
                {item.focus}
              </p>
            </article>
          ))}
        </div>
      </PageContainer>
    </Section>
  );
}
