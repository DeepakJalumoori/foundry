import { PageContainer, Section } from "@/components/shared/page-container";
import { Badge, StatusIndicator } from "@/components/ui";

const SAMPLE_COMPANIES = [
  {
    id: "sample-a",
    name: "Sample Startup A",
    domain: "Developer Infrastructure · Seed (Demo)",
    score: 84,
    scoreVariant: "success" as const,
    reasons: [
      "Aligns with Python and TypeScript backend experience",
      "Relevant distributed task-queue project in profile",
    ],
    evidenceCount: "2 demo evidence items",
    hiringNote: "Hiring status unverified",
    selected: true,
  },
  {
    id: "sample-b",
    name: "Sample Startup B",
    domain: "Workflow Automation · Pre-seed (Demo)",
    score: 76,
    scoreVariant: "primary" as const,
    reasons: [
      "Matches FastAPI and evaluation interest",
      "Remote-friendly preference alignment",
    ],
    evidenceCount: "1 demo evidence item",
    hiringNote: "No public job listing",
    selected: false,
  },
] as const;

export function ProductPreviewSection() {
  return (
    <Section
      id="product-preview"
      aria-labelledby="preview-heading"
      spacing="spacious"
      className="border-t border-border bg-background"
    >
      <PageContainer>
        <div className="max-w-2xl">
          <Badge variant="warning">Illustrative preview · Demo data</Badge>
          <h2 id="preview-heading" className="text-h2 mt-4 text-foreground">
            Inspect why a startup fits before you write a word.
          </h2>
          <p className="text-body mt-4 text-muted">
            Below is an illustrative preview of Foundry&apos;s discovery and
            evidence view. Company names, scores, and sources shown here are
            sample placeholders—not live startup records.
          </p>
        </div>

        {/* Product preview window */}
        <div className="mt-10 overflow-hidden rounded-[var(--radius-panel)] border border-border bg-surface shadow-xs">
          {/* Preview top bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-surface-muted/60 px-5 py-3.5 sm:px-6">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="text-[13px] font-semibold text-foreground">
                Discovery Workspace Preview
              </span>
              <Badge variant="warning">Demo data</Badge>
            </div>
            <StatusIndicator
              label="Illustrative example — not live search"
              tone="warning"
            />
          </div>

          <div className="grid divide-y divide-border lg:grid-cols-12 lg:divide-x lg:divide-y-0">
            {/* Left pane: Illustrative startup shortlist */}
            <div className="p-5 sm:p-6 lg:col-span-5">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-[14px] font-semibold text-foreground">
                  Illustrative shortlist
                </h3>
                <span className="text-label text-muted">2 sample matches</span>
              </div>

              <div className="mt-4 grid gap-3.5">
                {SAMPLE_COMPANIES.map((company) => (
                  <div
                    key={company.id}
                    className={
                      company.selected
                        ? "rounded-[var(--radius-card)] border border-primary/40 bg-primary-soft/35 p-4"
                        : "rounded-[var(--radius-card)] border border-border bg-surface p-4"
                    }
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <p className="text-[15px] font-semibold text-foreground">
                          {company.name}
                        </p>
                        <p className="text-[12px] text-muted">
                          {company.domain}
                        </p>
                      </div>
                      <Badge variant={company.scoreVariant}>
                        Fit {company.score}/100 (Demo)
                      </Badge>
                    </div>

                    <ul className="mt-3 grid gap-1.5 text-[13px] text-foreground/90">
                      {company.reasons.map((reason) => (
                        <li key={reason} className="flex items-start gap-2">
                          <span
                            aria-hidden="true"
                            className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary"
                          />
                          <span>{reason}</span>
                        </li>
                      ))}
                    </ul>

                    <div className="mt-3 flex flex-wrap items-center justify-between gap-x-3 gap-y-1 border-t border-border/80 pt-2.5 text-[12px] text-muted">
                      <span>{company.evidenceCount}</span>
                      <span>{company.hiringNote}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right pane: Match explanation + research evidence */}
            <div className="p-5 sm:p-6 lg:col-span-7">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-4">
                <div>
                  <p className="text-label text-primary">
                    Selected sample · Match &amp; evidence detail
                  </p>
                  <h3 className="mt-1 text-[17px] font-semibold text-foreground">
                    Sample Startup A — Why it matched
                  </h3>
                </div>
                <Badge variant="neutral">Illustrative only</Badge>
              </div>

              {/* Match explanation */}
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <div className="rounded-[var(--radius-card)] border border-border bg-surface-muted/45 p-4">
                  <p className="text-label text-success">Matched signals</p>
                  <p className="mt-1.5 text-[13px] leading-relaxed text-foreground">
                    Python, TypeScript, FastAPI experience, and a distributed
                    queue project align with the startup&apos;s core stack.
                  </p>
                </div>
                <div className="rounded-[var(--radius-card)] border border-border bg-surface-muted/45 p-4">
                  <p className="text-label text-warning">
                    Missing or unconfirmed
                  </p>
                  <p className="mt-1.5 text-[13px] leading-relaxed text-foreground">
                    Production Kubernetes experience is not present in the
                    sample profile and is surfaced transparently as a gap.
                  </p>
                </div>
              </div>

              {/* Research evidence */}
              <div className="mt-5">
                <h4 className="text-[14px] font-semibold text-foreground">
                  Research evidence &amp; verification status
                </h4>
                <ul className="mt-3 grid gap-2.5">
                  <li className="flex flex-col items-start gap-2 rounded-[var(--radius-card)] border border-border bg-surface p-3.5 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-[13px] font-medium text-foreground">
                        Sample engineering note on API latency &amp; worker queues
                      </p>
                      <p className="text-[12px] text-muted">
                        Source: Illustrative engineering blog reference
                      </p>
                    </div>
                    <Badge variant="warning">Demo source</Badge>
                  </li>
                  <li className="flex flex-col items-start gap-2 rounded-[var(--radius-card)] border border-border bg-surface p-3.5 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-[13px] font-medium text-foreground">
                        No public job listing found for this role
                      </p>
                      <p className="text-[12px] text-muted">
                        Lack of a listing is not treated as proof of hiring
                      </p>
                    </div>
                    <Badge variant="neutral">Unverified hiring</Badge>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </PageContainer>
    </Section>
  );
}
