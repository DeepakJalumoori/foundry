import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export interface ErrorStateProps {
  title?: string;
  description: string;
  details?: string;
  onRetry?: () => void;
  retryLabel?: string;
  retrying?: boolean;
  secondaryAction?: ReactNode;
  className?: string;
}

export function ErrorState({
  title = "Something went wrong",
  description,
  details,
  onRetry,
  retryLabel = "Try again",
  retrying = false,
  secondaryAction,
  className,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-start gap-3 rounded-[var(--radius-card)] border border-danger/30 bg-danger/5 p-5 sm:flex-row sm:items-center sm:justify-between",
        className
      )}
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-[15px] font-semibold text-danger">{title}</h3>
        <p className="text-[14px] text-foreground">{description}</p>
        {details && <p className="text-[13px] text-muted">{details}</p>}
      </div>
      {(onRetry || secondaryAction) && (
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {onRetry && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onRetry}
              loading={retrying}
            >
              {retryLabel}
            </Button>
          )}
          {secondaryAction}
        </div>
      )}
    </div>
  );
}
