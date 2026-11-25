import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export function Skeleton({ className, ...props }: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "rounded-[var(--radius-control)] bg-surface-muted motion-safe:animate-pulse",
        className
      )}
      {...props}
    />
  );
}

export function SkeletonText({
  lines = 3,
  className,
}: {
  lines?: number;
  className?: string;
}) {
  return (
    <div aria-hidden="true" className={cn("flex flex-col gap-2", className)}>
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          className={cn("h-4", index === lines - 1 ? "w-3/4" : "w-full")}
        />
      ))}
    </div>
  );
}

export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "rounded-[var(--radius-card)] border border-border bg-surface p-5 sm:p-6",
        className
      )}
    >
      <Skeleton className="h-4 w-24" />
      <Skeleton className="mt-3 h-5 w-2/3" />
      <SkeletonText lines={2} className="mt-3" />
    </div>
  );
}

export interface LoadingStateProps {
  label?: string;
  children?: ReactNode;
  className?: string;
}

/**
 * Accessible loading container announcing busy status to screen readers
 * while keeping visual skeleton shapes aria-hidden.
 */
export function LoadingState({
  label = "Loading content...",
  children,
  className,
}: LoadingStateProps) {
  return (
    <div
      role="status"
      aria-busy="true"
      aria-live="polite"
      className={cn("flex flex-col gap-4", className)}
    >
      <span className="sr-only">{label}</span>
      {children ?? <SkeletonCard />}
    </div>
  );
}
