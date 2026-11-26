import Link from "next/link";
import { PageContainer, Section } from "@/components/shared/page-container";
import { Badge } from "@/components/ui";

const FOOTER_LINKS = [
  { href: "#how-it-works", label: "How it works" },
  { href: "#startup-discovery", label: "Discovery" },
  { href: "#product-preview", label: "Product preview" },
  { href: "#founder-intelligence", label: "Founder research" },
  { href: "#personalized-outreach", label: "Outreach" },
  { href: "#trust", label: "Trust" },
  { href: "#use-cases", label: "Use cases" },
  { href: "#faq", label: "FAQ" },
] as const;

export function FinalCtaFooter() {
  return (
    <>
      <Section
        id="get-started"
        aria-labelledby="final-cta-heading"
        spacing="spacious"
        className="border-t border-border bg-background"
      >
        <PageContainer>
          <div className="rounded-[var(--radius-panel)] border border-border bg-surface p-8 shadow-xs sm:p-10 lg:p-12">
            <div className="max-w-2xl">
              <Badge variant="primary">Get started</Badge>
              <h2
                id="final-cta-heading"
                className="text-h2 mt-4 text-foreground"
              >
                One focused conversation starts with real research.
              </h2>
              <p className="text-body mt-4 text-muted">
                Try the interactive profile preview at the top of the page to
                see how Foundry structures candidate input—without uploading
                data or connecting external accounts.
              </p>

              <div className="mt-7 flex flex-wrap items-center gap-3">
                <Link
                  href="/onboarding"
                  className="inline-flex h-11 items-center justify-center rounded-[var(--radius-control)] bg-primary px-5 text-[15px] font-medium text-white transition-colors hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2"
                >
                  Start onboarding preview
                </Link>
                <a
                  href="#how-it-works"
                  className="inline-flex h-11 items-center justify-center rounded-[var(--radius-control)] border border-border bg-surface px-5 text-[15px] font-medium text-foreground transition-colors hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2"
                >
                  Review the workflow
                </a>
              </div>
            </div>
          </div>
        </PageContainer>
      </Section>

      <footer className="border-t border-border bg-surface py-10">
        <PageContainer className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <Link
              href="/"
              className="inline-flex items-center gap-2.5 rounded-[var(--radius-control)] focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2"
            >
              <span
                aria-hidden="true"
                className="flex h-7 w-7 items-center justify-center rounded-[var(--radius-control)] bg-primary text-[13px] font-semibold text-white"
              >
                F
              </span>
              <span className="text-[15px] font-semibold tracking-tight text-foreground">
                Foundry
              </span>
            </Link>
            <p className="mt-2 text-[13px] text-muted">
              Your next opportunity isn&apos;t always posted.
            </p>
          </div>

          <nav aria-label="Landing page sections">
            <ul className="flex flex-wrap gap-x-5 gap-y-2">
              {FOOTER_LINKS.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="rounded-[var(--radius-control)] text-[13px] text-muted transition-colors hover:text-foreground focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </PageContainer>
      </footer>
    </>
  );
}
