export type AppNavIconName =
  | "overview"
  | "discover"
  | "matches"
  | "contacts"
  | "outreach"
  | "profile"
  | "settings";

export interface AppNavItem {
  href: string;
  label: string;
  description: string;
  icon: AppNavIconName;
}

export const APP_NAV_ITEMS: AppNavItem[] = [
  {
    href: "/app",
    label: "Overview",
    description: "Workspace summary, active discovery status, and next steps.",
    icon: "overview",
  },
  {
    href: "/app/discover",
    label: "Discover Startups",
    description: "Run startup discovery workflows and inspect candidate criteria.",
    icon: "discover",
  },
  {
    href: "/app/matches",
    label: "My Matches",
    description: "Review deterministic candidate-company fit scores and reasons.",
    icon: "matches",
  },
  {
    href: "/app/contacts",
    label: "Founder Contacts",
    description: "Inspect founder profiles, sources, and verification status.",
    icon: "contacts",
  },
  {
    href: "/app/outreach",
    label: "Outreach Drafts",
    description: "Edit, approve, or reject personalized outreach drafts.",
    icon: "outreach",
  },
  {
    href: "/app/profile",
    label: "My Profile",
    description: "Review and edit extracted candidate profile and preferences.",
    icon: "profile",
  },
  {
    href: "/app/settings",
    label: "Settings",
    description: "Manage workspace preferences and provider mode indicators.",
    icon: "settings",
  },
];

export function getNavItemByPathname(pathname: string): AppNavItem {
  if (pathname === "/app") {
    return APP_NAV_ITEMS[0];
  }
  const match = APP_NAV_ITEMS.find(
    (item) => item.href !== "/app" && pathname.startsWith(item.href)
  );
  return match ?? APP_NAV_ITEMS[0];
}
