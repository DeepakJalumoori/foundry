import { cn } from "@/lib/utils";

export type StatusTone =
  | "neutral"
  | "info"
  | "running"
  | "success"
  | "warning"
  | "danger";

export interface StatusIndicatorProps {
  label: string;
  tone?: StatusTone;
  live?: boolean;
  className?: string;
}

const TONE_TEXT: Record<StatusTone, string> = {
  neutral: "text-muted",
  info: "text-primary",
  running: "text-primary",
  success: "text-success",
  warning: "text-warning",
  danger: "text-danger",
};

const TONE_DOT: Record<StatusTone, string> = {
  neutral: "bg-muted",
  info: "bg-primary",
  running: "bg-primary motion-safe:animate-pulse",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
};

export function StatusIndicator({
  label,
  tone = "neutral",
  live = false,
  className,
}: StatusIndicatorProps) {
  return (
    <span
      role={live ? "status" : undefined}
      aria-live={live ? "polite" : undefined}
      className={cn(
        "inline-flex items-center gap-2 text-[13px] font-medium",
        TONE_TEXT[tone],
        className
      )}
    >
      <span
        aria-hidden="true"
        className={cn("h-2 w-2 shrink-0 rounded-full", TONE_DOT[tone])}
      />
      <span>{label}</span>
    </span>
  );
}
