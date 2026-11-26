import { PageContainer, Section } from "@/components/shared/page-container";
import { Badge } from "@/components/ui";

const TRUST_COMMITMENTS = [
  {
    title: "You review and control your profile",
    description:
      "Extracted resume details and preferences are always editable before they are used for matching or outreach.",
  },
  {
    title: "Sources and verification stay visible",
    description:
      "Company research and founder contacts show their supporting source and clearly distinguish verified, unverified, and unavailable details.",
  },
  {
    title: "Transparent matching explanations",
    description:
      "Fit scores are computed from deterministic weights with dimension-level reasons and missing-skill gaps—never an opaque black box.",
  },
  {
    title: "Outreach drafts require your approval",
    description:
      "Every draft is editable and must be explicitly approved or rejected by you.",
  },
  {
    title: "No automatic email sending",
    description:
      "Approving a draft records your decision only. Foundry never sends messages automatically.",
  },
  {
    title: "No guaranteed interviews or employment",
    description:
      "Foundry helps reduce manual research and preparation burden; it never promises interviews, replies, or job offers.",
  },
] as const;

export function TrustSection() {
  return (
    <Section
      id="trust"
      aria-labelledby="trust-heading"
      spacing="spacious"
      className="border-t border-border bg-surface/60"
    >
      <PageContainer>
        <div className="grid items-start gap-10 lg:grid-cols-12 lg:gap-12">
          <div className="lg:col-span-5">
            <Badge variant="primary">Trust &amp; candidate control</Badge>
            <h2 id="trust-heading" className="text-h2 mt-4 text-foreground">
              Built to keep you informed—and in control.
            </h2>
            <p className="text-body mt-4 text-muted">
              Foundry is a career research and preparation workspace, not an
              automated application bot. Every claim, score, and draft is
              designed to be inspected by you.
            </p>
          </div>

          <div className="lg:col-span-7">
            <ul className="divide-y divide-border border-y border-border">
              {TRUST_COMMITMENTS.map((item) => (
                <li key={item.title} className="py-4 first:pt-3 last:pb-3">
                  <h3 className="text-[16px] font-semibold text-foreground">
                    {item.title}
                  </h3>
                  <p className="mt-1 text-[14px] leading-relaxed text-muted">
                    {item.description}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </PageContainer>
    </Section>
  );
}
