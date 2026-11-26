import { PageContainer, Section } from "@/components/shared/page-container";
import { Badge } from "@/components/ui";

const MATCHING_DIMENSIONS = [
  {
    name: "Skills alignment",
    weight: 30,
    description: "Languages, frameworks, databases, and core technical stack.",
  },
  {
    name: "Role relevance",
    weight: 25,
    description: "Backend, full-stack, AI/ML, or infrastructure focus.",
  },
  {
    name: "Experience alignment",
    weight: 15,
    description: "Ownership scope and readiness for early-stage teams.",
  },
  {
    name: "Project relevance",
    weight: 15,
    description: "Shipped systems and portfolio work related to the company.",
  },
  {
    name: "Candidate preferences",
    weight: 10,
    description: "Preferred industries, company stages, and role types.",
  },
  {
    name: "Location & work mode",
    weight: 5,
    description: "Remote, hybrid, or onsite alignment.",
  },
] as const;

export function StartupDiscoverySection() {
  return (
    <Section
      id="startup-discovery"
      aria-labelledby="discovery-heading"
      spacing="spacious"
      className="border-t border-border bg-surface/60"
    >
      <PageContainer>
        <div className="grid items-start gap-10 lg:grid-cols-12 lg:gap-12">
          {/* Left: Editorial explanation */}
          <div className="lg:col-span-5">
            <Badge variant="primary">Startup discovery</Badge>
            <h2 id="discovery-heading" className="text-h2 mt-4 text-foreground">
              Find early-stage teams that actually fit how you build.
            </h2>
            <p className="text-body mt-4 text-muted">
              Instead of sorting through hundreds of generic job listings,
              Foundry organizes startup discovery around your skills, role
              focus, projects, and work-mode preferences.
            </p>
            <p className="mt-4 text-[14px] leading-relaxed text-muted">
              Every match is calculated from deterministic, inspectable weights
              rather than an opaque black-box score—so you can see both why a
              company fits and where gaps remain.
            </p>
            <div className="mt-6 rounded-[var(--radius-card)] border border-border bg-surface p-4">
              <p className="text-[13px] leading-relaxed text-muted">
                <span className="font-medium text-foreground">
                  Transparent heuristic:
                </span>{" "}
                A fit score helps prioritize research; it does not predict or
                guarantee hiring or interview outcomes.
              </p>
            </div>
          </div>

          {/* Right: Weighted criteria breakdown */}
          <div className="rounded-[var(--radius-panel)] border border-border bg-surface p-6 shadow-xs sm:p-8 lg:col-span-7">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-4">
              <div>
                <p className="text-label text-primary">
                  Deterministic matching criteria
                </p>
                <h3 className="mt-1 text-[18px] font-semibold text-foreground">
                  How candidate-company fit is weighted
                </h3>
              </div>
              <Badge variant="neutral">Reproducible · 100% total</Badge>
            </div>

            <ul className="mt-5 grid gap-4">
              {MATCHING_DIMENSIONS.map((dim) => (
                <li key={dim.name} className="grid gap-1.5">
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="text-[14px] font-medium text-foreground">
                      {dim.name}
                    </span>
                    <span className="font-mono text-[13px] font-semibold text-primary">
                      {dim.weight}%
                    </span>
                  </div>
                  <div
                    aria-hidden="true"
                    className="h-2 w-full overflow-hidden rounded-full bg-surface-muted"
                  >
                    <div
                      className="h-full rounded-full bg-primary"
                      style={{ width: `${dim.weight * 2.5}%` }}
                    />
                  </div>
                  <p className="text-[13px] text-muted">{dim.description}</p>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </PageContainer>
    </Section>
  );
}
