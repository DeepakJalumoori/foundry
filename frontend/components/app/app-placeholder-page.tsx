import Link from "next/link";
import {
  Badge,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  StatusIndicator,
} from "@/components/ui";

interface AppPlaceholderPageProps {
  title: string;
  subtitle: string;
  plannedScope: string[];
  phaseLabel?: string;
}

export function AppPlaceholderPage({
  title,
  subtitle,
  plannedScope,
  phaseLabel = "Scheduled in upcoming tasks",
}: AppPlaceholderPageProps) {
  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Badge variant="warning">Frontend layout preview</Badge>
          <h1 className="text-h2 mt-3 text-foreground">{title}</h1>
          <p className="text-body mt-2 max-w-2xl text-muted">{subtitle}</p>
        </div>
        <StatusIndicator label={phaseLabel} tone="neutral" />
      </div>

      <Card variant="standard">
        <CardHeader>
          <CardTitle>Planned functionality for this view</CardTitle>
          <CardDescription>
            This route is wired into the Foundry application shell. Live data
            and interactive workflows will connect once backend and feature
            phases are implemented.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          <ul className="grid gap-2 text-[14px] text-foreground">
            {plannedScope.map((item) => (
              <li key={item} className="flex items-start gap-2.5">
                <span
                  aria-hidden="true"
                  className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-primary"
                />
                <span>{item}</span>
              </li>
            ))}
          </ul>

          <div className="flex flex-wrap items-center gap-3 border-t border-border pt-4">
            <Link
              href="/onboarding"
              className="inline-flex h-9 items-center justify-center rounded-[var(--radius-control)] border border-border bg-surface px-3.5 text-[13px] font-medium text-foreground transition-colors hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2"
            >
              Open onboarding preview
            </Link>
            <Link
              href="/app"
              className="inline-flex h-9 items-center justify-center rounded-[var(--radius-control)] px-3 text-[13px] font-medium text-muted transition-colors hover:bg-surface-muted hover:text-foreground focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2"
            >
              Return to Overview
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
