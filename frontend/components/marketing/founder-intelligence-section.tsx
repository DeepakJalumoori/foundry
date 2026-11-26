import { PageContainer, Section } from "@/components/shared/page-container";
import { Badge } from "@/components/ui";

const VERIFICATION_TIERS = [
  {
    label: "Verified",
    variant: "success" as const,
    text: "Backed by a direct, inspectable public source.",
  },
  {
    label: "Unverified",
    variant: "warning" as const,
    text: "Inferred or secondary context that needs your review.",
  },
  {
    label: "Unavailable",
    variant: "neutral" as const,
    text: "Not reliably found—never guessed or fabricated.",
  },
] as const;

export function FounderIntelligenceSection() {
  return (
    <Section
      id="founder-intelligence"
      aria-labelledby="founder-heading"
      spacing="spacious"
      className="border-t border-border bg-surface/60"
    >
      <PageContainer>
        <div className="grid items-start gap-10 lg:grid-cols-12 lg:gap-12">
          {/* Left: Editorial explanation & verification legend */}
          <div className="lg:col-span-5">
            <Badge variant="primary">Founder intelligence</Badge>
            <h2 id="founder-heading" className="text-h2 mt-4 text-foreground">
              Know who leads the team—and what actually backs it up.
            </h2>
            <p className="text-body mt-4 text-muted">
              Foundry helps you identify the right founder or technical leader
              to reach out to, paired with the specific context and sources that
              support why they are relevant.
            </p>
            <p className="mt-4 text-[14px] leading-relaxed text-muted">
              Every detail carries a source and verification status. When a
              direct email or contact detail cannot be reliably sourced, Foundry
              marks it unavailable instead of guessing.
            </p>

            <div className="mt-6 rounded-[var(--radius-card)] border border-border bg-surface p-4">
              <p className="text-label text-muted uppercase">
                How contact &amp; research status is labelled
              </p>
              <ul className="mt-3 grid gap-2.5">
                {VERIFICATION_TIERS.map((tier) => (
                  <li key={tier.label} className="flex items-start gap-2.5">
                    <Badge variant={tier.variant}>{tier.label}</Badge>
                    <span className="text-[13px] text-muted">{tier.text}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Right: Illustrative founder research interface */}
          <div className="rounded-[var(--radius-panel)] border border-border bg-surface p-6 shadow-xs sm:p-8 lg:col-span-7">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-4">
              <div>
                <p className="text-label text-muted">
                  Illustrative founder profile · Demo data
                </p>
                <h3 className="mt-1 text-[18px] font-semibold text-foreground">
                  Alex Rivera (Sample Founder)
                </h3>
                <p className="text-[13px] text-muted">
                  Co-founder &amp; CTO · Sample Startup A (Demo)
                </p>
              </div>
              <Badge variant="warning">Sample only</Badge>
            </div>

            {/* Research context & supporting evidence */}
            <div className="mt-5">
              <h4 className="text-[14px] font-semibold text-foreground">
                Research context &amp; supporting sources
              </h4>
              <ul className="mt-3 grid gap-2.5">
                <li className="flex flex-col items-start gap-2 rounded-[var(--radius-card)] border border-border bg-surface-muted/45 p-3.5 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-[13px] font-medium text-foreground">
                      Authored technical post on async worker reliability
                    </p>
                    <p className="text-[12px] text-muted">
                      Source: Illustrative company engineering blog
                    </p>
                  </div>
                  <Badge variant="success">Verified (Demo)</Badge>
                </li>
                <li className="flex flex-col items-start gap-2 rounded-[var(--radius-card)] border border-border bg-surface-muted/45 p-3.5 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-[13px] font-medium text-foreground">
                      Leads backend &amp; infrastructure architecture
                    </p>
                    <p className="text-[12px] text-muted">
                      Source: Illustrative team overview summary
                    </p>
                  </div>
                  <Badge variant="warning">Unverified</Badge>
                </li>
              </ul>
            </div>

            {/* Contact channels */}
            <div className="mt-5">
              <h4 className="text-[14px] font-semibold text-foreground">
                Contact channels &amp; verification
              </h4>
              <div className="mt-3 grid gap-2.5 sm:grid-cols-2">
                <div className="rounded-[var(--radius-card)] border border-border bg-surface p-3.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[13px] font-medium text-foreground">
                      Public profile
                    </span>
                    <Badge variant="success">Verified (Demo)</Badge>
                  </div>
                  <p className="mt-1.5 text-[12px] text-muted">
                    Illustrative public LinkedIn / GitHub link
                  </p>
                </div>

                <div className="rounded-[var(--radius-card)] border border-border bg-surface-muted/40 p-3.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[13px] font-medium text-foreground">
                      Direct email
                    </span>
                    <Badge variant="neutral">Unavailable</Badge>
                  </div>
                  <p className="mt-1.5 text-[12px] text-muted">
                    Not publicly listed — not guessed or fabricated
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </PageContainer>
    </Section>
  );
}
