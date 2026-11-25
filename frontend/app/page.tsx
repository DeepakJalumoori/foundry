import { PageContainer, Section } from "@/components/shared/page-container";
import { ComponentShowcase } from "@/components/shared/component-showcase";
import { Badge } from "@/components/ui";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col">
      <Section spacing="compact">
        <PageContainer>
          <div className="rounded-[var(--radius-panel)] border border-border bg-surface p-6 sm:p-8">
            <Badge variant="primary">Foundry · UI Foundation (T007)</Badge>
            <h1 className="text-h2 mt-4 text-foreground">
              Your next opportunity isn&apos;t always posted.
            </h1>
            <p className="text-body mt-2 text-muted">
              Temporary placeholder verifying the reusable UI component
              foundation before landing page and application routes are built.
            </p>
          </div>
          <ComponentShowcase />
        </PageContainer>
      </Section>
    </main>
  );
}
