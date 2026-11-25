import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

export type BadgeVariant =
  | "neutral"
  | "primary"
  | "success"
  | "warning"
  | "danger";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  icon?: ReactNode;
  children: ReactNode;
}

const BADGE_VARIANTS: Record<BadgeVariant, string> = {
  neutral: "bg-surface-muted text-foreground border-border",
  primary: "bg-primary-soft text-primary border-primary/20",
  success: "bg-success/10 text-success border-success/25",
  warning: "bg-warning/10 text-warning border-warning/25",
  danger: "bg-danger/10 text-danger border-danger/25",
};

export function Badge({
  variant = "neutral",
  icon,
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "text-label inline-flex items-center gap-1.5 rounded-[var(--radius-control)] border px-2.5 py-0.5",
        BADGE_VARIANTS[variant],
        className
      )}
      {...props}
    >
      {icon && (
        <span aria-hidden="true" className="inline-flex items-center">
          {icon}
        </span>
      )}
      <span>{children}</span>
    </span>
  );
}
