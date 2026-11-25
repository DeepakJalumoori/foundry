import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Foundry — Your next opportunity isn't always posted.",
    template: "%s | Foundry",
  },
  description:
    "Foundry helps candidates discover relevant early-stage startups, research the people behind them, and prepare thoughtful, human-approved introductions.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground font-sans">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:rounded-[var(--radius-control)] focus:bg-surface focus:px-4 focus:py-2 focus:text-[14px] focus:font-medium focus:text-foreground focus:shadow-md focus:outline-2 focus:outline-primary"
        >
          Skip to main content
        </a>
        {children}
      </body>
    </html>
  );
}
