"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  APP_NAV_ITEMS,
  getNavItemByPathname,
} from "@/components/app/nav-config";
import { AppNavIcon } from "@/components/app/nav-icons";
import { Badge } from "@/components/ui";
import { cn } from "@/lib/utils";

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(", ");

function SidebarBrand() {
  return (
    <div className="border-b border-border px-5 py-4">
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
      <p className="mt-1.5 text-[12px] text-muted">
        Your next opportunity isn&apos;t always posted.
      </p>
    </div>
  );
}

function SidebarNavList({
  pathname,
  onNavigate,
}: {
  pathname: string;
  onNavigate?: () => void;
}) {
  return (
    <ul className="grid gap-1">
      {APP_NAV_ITEMS.map((item) => {
        const isActive =
          item.href === "/app"
            ? pathname === "/app"
            : pathname.startsWith(item.href);

        return (
          <li key={item.href}>
            <Link
              href={item.href}
              aria-current={isActive ? "page" : undefined}
              onClick={onNavigate}
              className={cn(
                "flex min-h-11 items-center gap-3 rounded-[var(--radius-control)] px-3 py-2 text-[14px] font-medium transition-colors",
                "focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2",
                isActive
                  ? "bg-primary-soft text-primary"
                  : "text-muted hover:bg-surface-muted/70 hover:text-foreground"
              )}
            >
              <AppNavIcon name={item.icon} />
              <span>{item.label}</span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const activeItem = getNavItemByPathname(pathname);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const drawerPanelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!drawerOpen) return;

    const menuButton = menuButtonRef.current;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    drawerPanelRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setDrawerOpen(false);
        return;
      }

      if (event.key === "Tab" && drawerPanelRef.current) {
        const focusable = Array.from(
          drawerPanelRef.current.querySelectorAll<HTMLElement>(
            FOCUSABLE_SELECTOR
          )
        );
        if (focusable.length === 0) {
          event.preventDefault();
          drawerPanelRef.current.focus();
          return;
        }
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        const active = document.activeElement as HTMLElement | null;

        if (event.shiftKey) {
          if (active === first || active === drawerPanelRef.current) {
            event.preventDefault();
            last.focus();
          }
        } else if (active === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
      if (menuButton?.isConnected) {
        menuButton.focus();
      }
    };
  }, [drawerOpen]);

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      {/* Desktop persistent sidebar */}
      <aside className="hidden w-64 shrink-0 flex-col border-r border-border bg-surface lg:flex">
        <SidebarBrand />
        <nav aria-label="Application navigation" className="flex-1 p-3">
          <SidebarNavList pathname={pathname} />
        </nav>
        <div className="border-t border-border p-4">
          <div className="rounded-[var(--radius-control)] border border-border bg-surface-muted/50 px-3 py-2.5">
            <p className="text-[12px] font-medium text-foreground">
              Demo workspace
            </p>
            <p className="mt-0.5 text-[11px] text-muted">
              Frontend layout preview — no live backend connected.
            </p>
          </div>
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b border-border bg-surface/95 px-4 sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <button
              ref={menuButtonRef}
              type="button"
              aria-label="Open navigation menu"
              aria-expanded={drawerOpen}
              aria-controls="mobile-app-nav"
              onClick={() => setDrawerOpen(true)}
              className="inline-flex h-10 items-center gap-2 rounded-[var(--radius-control)] border border-border bg-surface px-3 text-[13px] font-medium text-foreground hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2 lg:hidden"
            >
              <svg
                aria-hidden="true"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={1.75}
                strokeLinecap="round"
                className="h-4 w-4"
              >
                <path d="M4 7h16M4 12h16M4 17h16" />
              </svg>
              <span>Menu</span>
            </button>

            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <p className="truncate text-[15px] font-semibold text-foreground">
                  {activeItem.label}
                </p>
                <Badge variant="warning" className="hidden sm:inline-flex">
                  Demo layout
                </Badge>
              </div>
              <p className="hidden truncate text-[12px] text-muted md:block">
                {activeItem.description}
              </p>
            </div>
          </div>

          {/* Candidate profile placeholder (honest demo label) */}
          <div className="flex shrink-0 items-center gap-2.5">
            <div className="hidden text-right sm:block">
              <p className="text-[13px] font-medium text-foreground">
                Demo Candidate
              </p>
              <p className="text-[11px] text-muted">Preview mode</p>
            </div>
            <div
              aria-label="Demo candidate avatar"
              className="flex h-9 w-9 items-center justify-center rounded-full border border-border bg-primary-soft text-[12px] font-semibold text-primary"
            >
              DC
            </div>
          </div>
        </header>

        <main
          id="main-content"
          tabIndex={-1}
          className="flex-1 px-4 py-6 focus:outline-none sm:px-6 lg:px-8 lg:py-8"
        >
          <div className="mx-auto w-full max-w-5xl">{children}</div>
        </main>
      </div>

      {/* Mobile / Tablet navigation drawer */}
      {drawerOpen && (
        <div
          className="fixed inset-0 z-50 flex bg-foreground/40 lg:hidden"
          onClick={(event) => {
            if (event.target === event.currentTarget) {
              setDrawerOpen(false);
            }
          }}
        >
          <div
            ref={drawerPanelRef}
            id="mobile-app-nav"
            role="dialog"
            aria-modal="true"
            aria-label="Application navigation"
            tabIndex={-1}
            className="flex h-full w-72 max-w-[85vw] flex-col border-r border-border bg-surface shadow-lg focus:outline-none"
          >
            <div className="flex items-center justify-between border-b border-border px-4 py-3.5">
              <Link
                href="/"
                onClick={() => setDrawerOpen(false)}
                className="inline-flex items-center gap-2 rounded-[var(--radius-control)] focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2"
              >
                <span
                  aria-hidden="true"
                  className="flex h-7 w-7 items-center justify-center rounded-[var(--radius-control)] bg-primary text-[13px] font-semibold text-white"
                >
                  F
                </span>
                <span className="text-[15px] font-semibold text-foreground">
                  Foundry
                </span>
              </Link>
              <button
                type="button"
                aria-label="Close navigation menu"
                onClick={() => setDrawerOpen(false)}
                className="inline-flex h-9 w-9 items-center justify-center rounded-[var(--radius-control)] border border-border bg-surface text-foreground hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2"
              >
                <span aria-hidden="true" className="text-[16px] leading-none">
                  ×
                </span>
              </button>
            </div>

            <nav aria-label="Mobile navigation" className="flex-1 overflow-y-auto p-3">
              <SidebarNavList
                pathname={pathname}
                onNavigate={() => setDrawerOpen(false)}
              />
            </nav>

            <div className="border-t border-border p-4">
              <p className="text-[12px] font-medium text-foreground">
                Demo workspace
              </p>
              <p className="mt-0.5 text-[11px] text-muted">
                Frontend layout preview — no live backend connected.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
