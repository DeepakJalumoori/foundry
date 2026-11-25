import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface PageContainerProps {
  children: ReactNode;
  className?: string;
}

/**
 * Centered responsive content container (max-width 1160px) per DESIGN.md.
 */
export function PageContainer({ children, className }: PageContainerProps) {
  return (
    <div
      className={cn(
        "mx-auto w-full max-w-[var(--container-max)] px-4 sm:px-6 lg:px-8",
        className
      )}
    >
      {children}
    </div>
  );
}

interface SectionProps {
  children: ReactNode;
  className?: string;
  spacing?: "compact" | "default" | "spacious";
}

const SECTION_SPACING = {
  compact: "py-8 sm:py-12",
  default: "py-12 sm:py-16 lg:py-20",
  spacious: "py-16 sm:py-24 lg:py-28",
} as const;

/**
 * Consistent vertical section rhythm built on the 4px spacing scale.
 */
export function Section({
  children,
  className,
  spacing = "default",
}: SectionProps) {
  return (
    <section className={cn(SECTION_SPACING[spacing], className)}>
      {children}
    </section>
  );
}
