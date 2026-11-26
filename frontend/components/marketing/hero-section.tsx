"use client";

import { useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { PageContainer, Section } from "@/components/shared/page-container";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  Input,
  StatusIndicator,
} from "@/components/ui";

export function HeroSection() {
  const router = useRouter();
  const [profileUrl, setProfileUrl] = useState("");
  const [resumeFileName, setResumeFileName] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | undefined>(undefined);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    setFormError(undefined);
    const file = event.target.files?.[0];
    if (!file) {
      setResumeFileName(null);
      return;
    }

    const isPdf =
      file.type === "application/pdf" ||
      file.name.toLowerCase().endsWith(".pdf");
    if (!isPdf) {
      setResumeFileName(null);
      setFormError("Please select a PDF resume file.");
      event.target.value = "";
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setResumeFileName(null);
      setFormError("Resume file must be 5 MB or smaller.");
      event.target.value = "";
      return;
    }

    setResumeFileName(file.name);
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(undefined);

    const trimmedUrl = profileUrl.trim();
    if (trimmedUrl) {
      try {
        const parsed = new URL(trimmedUrl);
        if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
          setFormError("URL must start with https:// or http://.");
          return;
        }
      } catch {
        setFormError("Enter a valid URL (for example, https://linkedin.com/in/your-name).");
        return;
      }
    }

    router.push("/onboarding");
  };

  const scrollToWorkflow = () => {
    const target =
      document.getElementById("how-it-works") ??
      document.getElementById("hero-product-preview");
    target?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <Section spacing="spacious" className="pt-10 sm:pt-14 lg:pt-16">
      <PageContainer>
        <div className="grid items-start gap-10 lg:grid-cols-12 lg:gap-12">
          {/* Left column: Positioning, copy, profile input & CTAs */}
          <div className="lg:col-span-7">
            <div className="flex flex-wrap items-center gap-2.5">
              <Badge variant="primary">Foundry</Badge>
              <span className="text-[13px] font-medium text-muted">
                Your next opportunity isn&apos;t always posted.
              </span>
            </div>

            <h1 className="text-display mt-5 text-foreground">
              Stop applying everywhere. Start talking to the right founders.
            </h1>

            <p className="text-body mt-5 max-w-xl text-muted">
              Foundry helps candidates discover promising startups that fit their
              experience, research the founders behind them with traceable
              evidence, and prepare personalized outreach you review and approve
              before anything is ever sent.
            </p>

            {/* Profile / Resume Input */}
            <form
              onSubmit={handleSubmit}
              noValidate
              className="mt-8 rounded-[var(--radius-panel)] border border-border bg-surface p-5 shadow-xs sm:p-6"
            >
              <div className="grid gap-4">
                <Input
                  type="url"
                  label="LinkedIn or portfolio URL"
                  placeholder="https://linkedin.com/in/your-profile"
                  value={profileUrl}
                  onChange={(event) => {
                    setProfileUrl(event.target.value);
                    setFormError(undefined);
                  }}
                  error={formError}
                  hint="Optional here, or attach a PDF resume below (max 5 MB) — continue to the onboarding preview."
                />

                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <input
                      ref={fileInputRef}
                      id="hero-resume-upload"
                      type="file"
                      accept=".pdf,application/pdf"
                      onChange={handleFileChange}
                      className="sr-only"
                    />
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      {resumeFileName ? "Change PDF resume" : "Attach PDF resume"}
                    </Button>
                    {resumeFileName && (
                      <span className="text-[13px] font-medium text-foreground">
                        {resumeFileName}
                      </span>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center gap-2.5">
                    <Button
                      variant="tertiary"
                      size="md"
                      onClick={scrollToWorkflow}
                    >
                      See how it works
                    </Button>
                    <Button type="submit" variant="primary" size="md">
                      Find my startup matches
                    </Button>
                  </div>
                </div>
              </div>
            </form>

            {/* Honest trust cues */}
            <ul className="mt-5 flex flex-wrap gap-x-6 gap-y-2 text-[13px] text-muted">
              <li>Explainable fit criteria</li>
              <li>Sourced founder &amp; company context</li>
              <li>Human approval required — no auto-sending</li>
            </ul>
          </div>

          {/* Right column: Illustrative Product Preview */}
          <div
            id="hero-product-preview"
            tabIndex={-1}
            className="focus:outline-none lg:col-span-5"
          >
            <Card
              variant="standard"
              className="rounded-[var(--radius-panel)] shadow-xs"
            >
              <CardHeader className="border-b border-border pb-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <Badge variant="neutral">Illustrative product preview</Badge>
                  <StatusIndicator label="Human review required" tone="warning" />
                </div>
                <h2 className="mt-2 text-[16px] font-semibold text-foreground">
                  How Foundry prepares an introduction
                </h2>
              </CardHeader>

              <CardContent className="grid gap-4">
                {/* Step 1: Fit */}
                <div className="rounded-[var(--radius-card)] border border-border bg-surface-muted/50 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-label text-muted">
                      1. Transparent fit breakdown
                    </span>
                    <Badge variant="success">Sample match</Badge>
                  </div>
                  <p className="mt-1.5 text-[14px] font-medium text-foreground">
                    Example Seed-Stage Infrastructure Startup
                  </p>
                  <p className="mt-1 text-[13px] text-muted">
                    Weighted across skills, role relevance, projects, and work
                    preferences — never a black-box guarantee.
                  </p>
                </div>

                {/* Step 2: Evidence */}
                <div className="rounded-[var(--radius-card)] border border-border bg-surface-muted/50 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-label text-muted">
                      2. Sourced company &amp; founder research
                    </span>
                    <Badge variant="neutral">Source-attributed</Badge>
                  </div>
                  <p className="mt-1.5 text-[13px] text-muted">
                    Distinguishes verified public sources from unverified notes
                    so you know what backs every claim.
                  </p>
                </div>

                {/* Step 3: Draft */}
                <div className="rounded-[var(--radius-card)] border border-border bg-surface p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-label text-muted">
                      3. Editable outreach draft
                    </span>
                    <Badge variant="warning">Awaiting approval</Badge>
                  </div>
                  <p className="mt-1.5 text-[13px] text-foreground">
                    Grounded in your actual projects and the company&apos;s
                    work. You edit, approve, or reject every draft.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </PageContainer>
    </Section>
  );
}
