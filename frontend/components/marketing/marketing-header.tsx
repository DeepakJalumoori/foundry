import Link from "next/link";
import { PageContainer } from "@/components/shared/page-container";

export function MarketingHeader() {
  return (
    <header className="border-b border-border bg-surface/95">
      <PageContainer className="flex h-16 items-center justify-between gap-4">
        <Link
          href="/"
          className="inline-flex items-center gap-2.5 rounded-[var(--radius-control)] focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2"
        >
          <span
            aria-hidden="true"
            className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-control)] bg-primary text-[14px] font-semibold text-white"
          >
            F
          </span>
          <span className="text-[16px] font-semibold tracking-tight text-foreground">
            Foundry
          </span>
        </Link>

        <div className="flex items-center gap-4">
          <p className="hidden text-[13px] text-muted md:block">
            Your next opportunity isn&apos;t always posted.
          </p>
          <Link
            href="/onboarding"
            className="inline-flex h-9 items-center justify-center rounded-[var(--radius-control)] bg-primary px-3.5 text-[13px] font-medium text-white transition-colors hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2"
          >
            Get started
          </Link>
        </div>
      </PageContainer>
    </header>
  );
}
