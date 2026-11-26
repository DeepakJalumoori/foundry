"use client";

import { useRef, useState, type ChangeEvent } from "react";
import Link from "next/link";
import { PageContainer, Section } from "@/components/shared/page-container";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  Input,
  StatusIndicator,
  Textarea,
} from "@/components/ui";
import { cn } from "@/lib/utils";

type StepId = "welcome" | "profile" | "preferences" | "review";
type WorkMode = "Remote" | "Hybrid" | "On-site" | "Flexible";

interface OnboardingData {
  fullName: string;
  email: string;
  linkedinUrl: string;
  portfolioUrl: string;
  resumeFileName: string | null;
  desiredRole: string;
  skills: string;
  workMode: WorkMode;
  location: string;
  domains: string;
}

const STEPS: Array<{ id: StepId; label: string; number: string }> = [
  { id: "welcome", label: "Welcome", number: "01" },
  { id: "profile", label: "Profile", number: "02" },
  { id: "preferences", label: "Preferences", number: "03" },
  { id: "review", label: "Review", number: "04" },
];

const WORK_MODES: WorkMode[] = ["Remote", "Hybrid", "On-site", "Flexible"];

const INITIAL_DATA: OnboardingData = {
  fullName: "",
  email: "",
  linkedinUrl: "",
  portfolioUrl: "",
  resumeFileName: null,
  desiredRole: "",
  skills: "",
  workMode: "Flexible",
  location: "",
  domains: "",
};

function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

function isValidHttpUrl(value: string): boolean {
  try {
    const parsed = new URL(value.trim());
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

export function OnboardingFlow() {
  const [step, setStep] = useState<StepId>("welcome");
  const [data, setData] = useState<OnboardingData>(INITIAL_DATA);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [previewCompleted, setPreviewCompleted] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const updateField = <K extends keyof OnboardingData>(
    key: K,
    value: OnboardingData[K]
  ) => {
    setData((prev) => ({ ...prev, [key]: value }));
    setPreviewCompleted(false);
    setErrors((prev) => {
      if (!prev[key]) return prev;
      const next = { ...prev };
      delete next[key];
      return next;
    });
  };

  const handleResumeChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    setPreviewCompleted(false);

    if (!file) {
      updateField("resumeFileName", null);
      return;
    }

    const isPdf =
      file.type === "application/pdf" ||
      file.name.toLowerCase().endsWith(".pdf");
    if (!isPdf) {
      event.target.value = "";
      setErrors((prev) => ({
        ...prev,
        resume: "Resume must be a PDF file (.pdf).",
      }));
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      event.target.value = "";
      setErrors((prev) => ({
        ...prev,
        resume: "Resume PDF must be 5 MB or smaller.",
      }));
      return;
    }

    setErrors((prev) => {
      const next = { ...prev };
      delete next.resume;
      return next;
    });
    updateField("resumeFileName", file.name);
  };

  const validateProfile = (): boolean => {
    const nextErrors: Record<string, string> = {};

    if (!data.fullName.trim()) {
      nextErrors.fullName = "Enter your full name.";
    }
    if (!data.email.trim()) {
      nextErrors.email = "Enter your email address.";
    } else if (!isValidEmail(data.email)) {
      nextErrors.email = "Enter a valid email address (for example, name@example.com).";
    }
    if (data.linkedinUrl.trim() && !isValidHttpUrl(data.linkedinUrl)) {
      nextErrors.linkedinUrl = "Enter a valid URL starting with https:// or http://.";
    }
    if (data.portfolioUrl.trim() && !isValidHttpUrl(data.portfolioUrl)) {
      nextErrors.portfolioUrl = "Enter a valid URL starting with https:// or http://.";
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const validatePreferences = (): boolean => {
    const nextErrors: Record<string, string> = {};

    if (!data.desiredRole.trim()) {
      nextErrors.desiredRole = "Enter at least one desired role.";
    }
    if (!data.skills.trim()) {
      nextErrors.skills = "Enter your core skills or technologies.";
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleStepClick = (target: StepId) => {
    if (target === step) return;
    if (step === "profile" && (target === "preferences" || target === "review")) {
      if (!validateProfile()) return;
    }
    if (step === "preferences" && target === "review") {
      if (!validatePreferences()) return;
    }
    if (target === "review" && (!validateProfile() || !validatePreferences())) {
      return;
    }
    setErrors({});
    setStep(target);
  };

  return (
    <Section spacing="compact" className="py-8 sm:py-12">
      <PageContainer className="max-w-3xl">
        {/* Top context + stepper */}
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2.5">
            <Badge variant="warning">Onboarding preview</Badge>
            <StatusIndicator
              label="Not connected to backend yet"
              tone="warning"
            />
          </div>
          <Link
            href="/"
            className="rounded-[var(--radius-control)] text-[13px] font-medium text-muted hover:text-foreground focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2"
          >
            Back to landing page
          </Link>
        </div>

        <nav aria-label="Onboarding steps" className="mb-8">
          <ol className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
            {STEPS.map((item) => {
              const isCurrent = item.id === step;
              return (
                <li key={item.id}>
                  <button
                    type="button"
                    aria-current={isCurrent ? "step" : undefined}
                    onClick={() => handleStepClick(item.id)}
                    className={cn(
                      "flex w-full items-center gap-2 rounded-[var(--radius-control)] border px-3 py-2.5 text-left text-[13px] font-medium transition-colors",
                      "focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2",
                      isCurrent
                        ? "border-primary bg-primary-soft text-primary"
                        : "border-border bg-surface text-muted hover:bg-surface-muted/60 hover:text-foreground"
                    )}
                  >
                    <span className="font-mono text-[11px]">{item.number}</span>
                    <span>{item.label}</span>
                  </button>
                </li>
              );
            })}
          </ol>
        </nav>

        {/* Step 1: Welcome */}
        {step === "welcome" && (
          <Card variant="standard" className="rounded-[var(--radius-panel)]">
            <CardHeader>
              <Badge variant="primary" className="w-fit">
                Step 1 of 4 · Welcome
              </Badge>
              <CardTitle className="mt-3 text-[22px] sm:text-[26px]">
                Set up your Foundry candidate profile
              </CardTitle>
              <CardDescription className="mt-2 text-[15px]">
                Foundry helps you discover relevant early-stage startups,
                inspect sourced company and founder research, and prepare
                personalized outreach drafts you approve.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4">
              <div className="rounded-[var(--radius-card)] border border-border bg-surface-muted/45 p-4">
                <p className="text-[14px] font-semibold text-foreground">
                  What you&apos;ll enter in this preview
                </p>
                <ul className="mt-2 grid gap-1.5 text-[14px] text-muted">
                  <li>
                    • Basic profile details (name, email, optional LinkedIn,
                    portfolio/GitHub, and optional PDF resume)
                  </li>
                  <li>
                    • Opportunity preferences (desired role, skills, work mode,
                    and optional location or domain interests)
                  </li>
                </ul>
              </div>

              <div className="rounded-[var(--radius-card)] border border-warning/30 bg-warning/5 p-4">
                <p className="text-[13px] leading-relaxed text-foreground">
                  <span className="font-semibold">Preview notice:</span>{" "}
                  Backend APIs and resume parsing are not connected yet.
                  Information entered here stays in memory for this session only
                  and is not saved, uploaded, or submitted anywhere.
                </p>
              </div>
            </CardContent>
            <CardFooter>
              <Button variant="primary" onClick={() => setStep("profile")}>
                Continue to profile
              </Button>
            </CardFooter>
          </Card>
        )}

        {/* Step 2: Candidate Profile */}
        {step === "profile" && (
          <Card variant="standard" className="rounded-[var(--radius-panel)]">
            <CardHeader>
              <Badge variant="primary" className="w-fit">
                Step 2 of 4 · Candidate profile
              </Badge>
              <CardTitle className="mt-3 text-[22px]">
                Tell us about your background
              </CardTitle>
              <CardDescription>
                Required fields are marked with *. Optional links and resume
                PDF can be skipped.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <Input
                  label="Full name"
                  required
                  placeholder="Alex Rivera"
                  value={data.fullName}
                  onChange={(e) => updateField("fullName", e.target.value)}
                  error={errors.fullName}
                />
                <Input
                  type="email"
                  label="Email address"
                  required
                  placeholder="alex@example.com"
                  value={data.email}
                  onChange={(e) => updateField("email", e.target.value)}
                  error={errors.email}
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <Input
                  type="url"
                  label="LinkedIn URL (optional)"
                  placeholder="https://linkedin.com/in/your-profile"
                  value={data.linkedinUrl}
                  onChange={(e) => updateField("linkedinUrl", e.target.value)}
                  error={errors.linkedinUrl}
                />
                <Input
                  type="url"
                  label="Portfolio or GitHub URL (optional)"
                  placeholder="https://github.com/username"
                  value={data.portfolioUrl}
                  onChange={(e) => updateField("portfolioUrl", e.target.value)}
                  error={errors.portfolioUrl}
                />
              </div>

              <div className="rounded-[var(--radius-card)] border border-border bg-surface-muted/40 p-4">
                <p className="text-[13px] font-medium text-foreground">
                  Resume PDF (optional)
                </p>
                <p className="mt-1 text-[13px] text-muted">
                  PDF format only, up to 5 MB. Validated locally in your
                  browser—not uploaded yet.
                </p>
                <div className="mt-3 flex flex-wrap items-center gap-2.5">
                  <input
                    ref={fileInputRef}
                    id="onboarding-resume-pdf"
                    type="file"
                    accept=".pdf,application/pdf"
                    onChange={handleResumeChange}
                    className="sr-only"
                  />
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    {data.resumeFileName ? "Replace PDF" : "Choose PDF file"}
                  </Button>
                  {data.resumeFileName && (
                    <>
                      <span className="text-[13px] font-medium text-foreground">
                        {data.resumeFileName}
                      </span>
                      <Button
                        variant="tertiary"
                        size="sm"
                        onClick={() => {
                          if (fileInputRef.current) {
                            fileInputRef.current.value = "";
                          }
                          updateField("resumeFileName", null);
                        }}
                      >
                        Remove
                      </Button>
                    </>
                  )}
                </div>
                {errors.resume && (
                  <p role="alert" className="mt-2 text-[13px] text-danger">
                    {errors.resume}
                  </p>
                )}
              </div>
            </CardContent>
            <CardFooter className="justify-between">
              <Button
                variant="secondary"
                onClick={() => {
                  setErrors({});
                  setStep("welcome");
                }}
              >
                Back
              </Button>
              <Button
                variant="primary"
                onClick={() => {
                  if (validateProfile()) {
                    setStep("preferences");
                  }
                }}
              >
                Continue to preferences
              </Button>
            </CardFooter>
          </Card>
        )}

        {/* Step 3: Opportunity Preferences */}
        {step === "preferences" && (
          <Card variant="standard" className="rounded-[var(--radius-panel)]">
            <CardHeader>
              <Badge variant="primary" className="w-fit">
                Step 3 of 4 · Opportunity preferences
              </Badge>
              <CardTitle className="mt-3 text-[22px]">
                What kind of startups are you looking for?
              </CardTitle>
              <CardDescription>
                These preferences guide transparent candidate-company matching.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4">
              <Input
                label="Desired role"
                required
                placeholder="Backend Engineer, Full-Stack Engineer, AI Engineer"
                value={data.desiredRole}
                onChange={(e) => updateField("desiredRole", e.target.value)}
                error={errors.desiredRole}
              />

              <Textarea
                label="Skills and technologies"
                required
                placeholder="Python, TypeScript, FastAPI, PostgreSQL, React"
                value={data.skills}
                onChange={(e) => updateField("skills", e.target.value)}
                error={errors.skills}
                rows={3}
              />

              <fieldset className="grid gap-2">
                <legend className="text-[13px] font-medium text-foreground">
                  Preferred work mode
                </legend>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {WORK_MODES.map((mode) => {
                    const selected = data.workMode === mode;
                    return (
                      <label
                        key={mode}
                        className={cn(
                          "flex cursor-pointer items-center justify-center rounded-[var(--radius-control)] border px-3 py-2 text-[13px] font-medium transition-colors",
                          "focus-within:outline-2 focus-within:outline-primary focus-within:outline-offset-2",
                          selected
                            ? "border-primary bg-primary-soft text-primary"
                            : "border-border bg-surface text-foreground hover:bg-surface-muted/60"
                        )}
                      >
                        <input
                          type="radio"
                          name="workMode"
                          value={mode}
                          checked={selected}
                          onChange={() => updateField("workMode", mode)}
                          className="sr-only"
                        />
                        <span>{mode}</span>
                      </label>
                    );
                  })}
                </div>
              </fieldset>

              <div className="grid gap-4 sm:grid-cols-2">
                <Input
                  label="Preferred location (optional)"
                  placeholder="San Francisco, New York, or Remote"
                  value={data.location}
                  onChange={(e) => updateField("location", e.target.value)}
                />
                <Input
                  label="Startup domains or interests (optional)"
                  placeholder="Developer tools, AI infrastructure, Fintech"
                  value={data.domains}
                  onChange={(e) => updateField("domains", e.target.value)}
                />
              </div>
            </CardContent>
            <CardFooter className="justify-between">
              <Button
                variant="secondary"
                onClick={() => {
                  setErrors({});
                  setStep("profile");
                }}
              >
                Back
              </Button>
              <Button
                variant="primary"
                onClick={() => {
                  if (validatePreferences()) {
                    setStep("review");
                  }
                }}
              >
                Review details
              </Button>
            </CardFooter>
          </Card>
        )}

        {/* Step 4: Review */}
        {step === "review" && (
          <Card variant="standard" className="rounded-[var(--radius-panel)]">
            <CardHeader>
              <Badge variant="primary" className="w-fit">
                Step 4 of 4 · Review
              </Badge>
              <CardTitle className="mt-3 text-[22px]">
                Review your onboarding summary
              </CardTitle>
              <CardDescription>
                Check your details below. You can return to any step to edit
                your inputs without losing values.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-5">
              {/* Profile summary */}
              <div className="rounded-[var(--radius-card)] border border-border bg-surface-muted/35 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-3">
                  <h2 className="text-[15px] font-semibold text-foreground">
                    Candidate profile
                  </h2>
                  <Button
                    variant="tertiary"
                    size="sm"
                    onClick={() => setStep("profile")}
                  >
                    Edit profile
                  </Button>
                </div>
                <dl className="mt-3 grid gap-2.5 text-[13px] sm:grid-cols-2">
                  <div>
                    <dt className="text-muted">Full name</dt>
                    <dd className="font-medium text-foreground">
                      {data.fullName}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted">Email</dt>
                    <dd className="font-medium text-foreground">{data.email}</dd>
                  </div>
                  <div>
                    <dt className="text-muted">LinkedIn URL</dt>
                    <dd className="font-medium text-foreground break-all">
                      {data.linkedinUrl.trim() || "Not provided"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted">Portfolio / GitHub</dt>
                    <dd className="font-medium text-foreground break-all">
                      {data.portfolioUrl.trim() || "Not provided"}
                    </dd>
                  </div>
                  <div className="sm:col-span-2">
                    <dt className="text-muted">Resume PDF</dt>
                    <dd className="font-medium text-foreground">
                      {data.resumeFileName ?? "Not attached"}
                    </dd>
                  </div>
                </dl>
              </div>

              {/* Preferences summary */}
              <div className="rounded-[var(--radius-card)] border border-border bg-surface-muted/35 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-3">
                  <h2 className="text-[15px] font-semibold text-foreground">
                    Opportunity preferences
                  </h2>
                  <Button
                    variant="tertiary"
                    size="sm"
                    onClick={() => setStep("preferences")}
                  >
                    Edit preferences
                  </Button>
                </div>
                <dl className="mt-3 grid gap-2.5 text-[13px] sm:grid-cols-2">
                  <div>
                    <dt className="text-muted">Desired role</dt>
                    <dd className="font-medium text-foreground">
                      {data.desiredRole}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted">Work mode</dt>
                    <dd className="font-medium text-foreground">
                      {data.workMode}
                    </dd>
                  </div>
                  <div className="sm:col-span-2">
                    <dt className="text-muted">Skills &amp; technologies</dt>
                    <dd className="font-medium text-foreground">
                      {data.skills}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted">Preferred location</dt>
                    <dd className="font-medium text-foreground">
                      {data.location.trim() || "Not specified"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted">Domains / interests</dt>
                    <dd className="font-medium text-foreground">
                      {data.domains.trim() || "Not specified"}
                    </dd>
                  </div>
                </dl>
              </div>

              {previewCompleted && (
                <div
                  role="status"
                  aria-live="polite"
                  className="rounded-[var(--radius-card)] border border-primary/30 bg-primary-soft p-4 text-[13px] leading-relaxed text-foreground"
                >
                  <p className="font-semibold">
                    Onboarding preview complete — no data was saved or
                    submitted.
                  </p>
                  <p className="mt-1 text-muted">
                    Backend profile persistence, resume parsing, and startup
                    discovery are not connected yet. Your entries remain in
                    memory only until you leave or refresh this page.
                  </p>
                </div>
              )}
            </CardContent>
            <CardFooter className="justify-between">
              <Button
                variant="secondary"
                onClick={() => setStep("preferences")}
              >
                Back
              </Button>
              <Button
                variant="primary"
                onClick={() => setPreviewCompleted(true)}
              >
                Finish onboarding preview
              </Button>
            </CardFooter>
          </Card>
        )}
      </PageContainer>
    </Section>
  );
}
