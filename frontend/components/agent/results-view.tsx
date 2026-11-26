"use client";

import { useState } from "react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Textarea,
} from "@/components/ui";
import type {
  DemoStartupResult,
  EmailVerificationStatus,
} from "@/components/agent/types";
import type { CandidateRunInput } from "@/components/agent/candidate-input-card";

interface ResultsViewProps {
  input: CandidateRunInput;
  results: DemoStartupResult[];
  onResetSearch: () => void;
}

function verificationBadgeVariant(status: EmailVerificationStatus) {
  if (status === "verified") return "success" as const;
  if (status === "unverified") return "warning" as const;
  return "neutral" as const;
}

function verificationLabel(status: EmailVerificationStatus): string {
  if (status === "verified") return "Verified";
  if (status === "unverified") return "Unverified";
  return "Unavailable";
}

function StartupResultCard({ result }: { result: DemoStartupResult }) {
  const [subject, setSubject] = useState(result.emailDraftSubject);
  const [body, setBody] = useState(result.emailDraftBody);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const fullText = `Subject: ${subject}\n\n${body}`;
    try {
      await navigator.clipboard.writeText(fullText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  return (
    <Card variant="standard">
      <CardHeader className="border-b border-border pb-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle className="text-[20px]">
                {result.companyName}
              </CardTitle>
              <Badge
                variant={
                  result.opportunityType === "active" ? "success" : "warning"
                }
              >
                {result.opportunityType === "active"
                  ? "Active opportunity"
                  : "Hidden opportunity"}
              </Badge>
              <Badge variant="neutral">{result.fundingStage}</Badge>
            </div>
            <CardDescription className="mt-1.5">
              {result.description}
            </CardDescription>
          </div>
          <div className="rounded-[var(--radius-control)] border border-primary/20 bg-primary-soft px-3 py-2 text-right">
            <p className="text-[11px] font-medium text-muted">Match score</p>
            <p className="font-mono text-[18px] font-semibold text-primary">
              {result.matchScore}/100
            </p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="grid gap-5 pt-5">
        {/* Match explanation & Why reach out */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-[var(--radius-control)] border border-border bg-surface-muted/40 p-3.5">
            <h3 className="text-[13px] font-semibold text-foreground">
              Why reach out
            </h3>
            <p className="mt-1 text-[13px] leading-relaxed text-muted">
              {result.whyReachOut}
            </p>
          </div>
          <div className="rounded-[var(--radius-control)] border border-border bg-surface-muted/40 p-3.5">
            <h3 className="text-[13px] font-semibold text-foreground">
              Match explanation
            </h3>
            <p className="mt-1 text-[13px] leading-relaxed text-muted">
              {result.matchExplanation}
            </p>
          </div>
        </div>

        {/* Funding & Hiring signals */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-[var(--radius-control)] border border-border p-3.5">
            <h3 className="text-[13px] font-semibold text-foreground">
              Funding evidence
            </h3>
            <p className="mt-1 text-[13px] text-foreground">
              {result.fundingEvidence.detail}
            </p>
            <p className="mt-1.5 text-[12px] text-muted">
              Source:{" "}
              <a
                href={result.fundingEvidence.sourceUrl}
                target="_blank"
                rel="noreferrer"
                className="underline hover:text-foreground"
              >
                {result.fundingEvidence.sourceLabel}
              </a>{" "}
              ({result.fundingEvidence.date})
            </p>
          </div>

          <div className="rounded-[var(--radius-control)] border border-border p-3.5">
            <h3 className="text-[13px] font-semibold text-foreground">
              Hiring signals
            </h3>
            <ul className="mt-1 grid gap-2">
              {result.hiringSignals.map((signal) => (
                <li key={signal.label} className="text-[13px]">
                  <p className="text-foreground">{signal.detail}</p>
                  <p className="mt-1 text-[12px] text-muted">
                    Source:{" "}
                    <a
                      href={signal.sourceUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="underline hover:text-foreground"
                    >
                      {signal.sourceLabel}
                    </a>{" "}
                    ({signal.date})
                  </p>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Founder & Email provenance */}
        <div className="rounded-[var(--radius-control)] border border-border p-3.5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-[13px] font-semibold text-foreground">
              Founder contact
            </h3>
            <Badge variant={verificationBadgeVariant(result.emailVerification)}>
              Email: {verificationLabel(result.emailVerification)}
            </Badge>
          </div>
          <div className="mt-2 grid gap-2 text-[13px] sm:grid-cols-3">
            <div>
              <p className="text-[12px] text-muted">Founder</p>
              <p className="font-medium text-foreground">
                {result.founderName} — {result.founderRole}
              </p>
            </div>
            <div>
              <p className="text-[12px] text-muted">Public professional email</p>
              <p className="font-mono text-[13px] text-foreground">
                {result.founderEmail ?? "Unavailable"}
              </p>
            </div>
            <div>
              <p className="text-[12px] text-muted">Email provenance</p>
              <p className="text-foreground">{result.emailSource}</p>
            </div>
          </div>
        </div>

        {/* Personalized email draft */}
        <div className="grid gap-3 border-t border-border pt-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-[14px] font-semibold text-foreground">
              Personalized founder email draft (Demo)
            </h3>
            <Button variant="secondary" size="sm" onClick={handleCopy}>
              {copied ? "Copied draft" : "Copy draft"}
            </Button>
          </div>
          <Input
            label="Subject"
            value={subject}
            onChange={(event) => setSubject(event.target.value)}
          />
          <Textarea
            label="Email body"
            value={body}
            onChange={(event) => setBody(event.target.value)}
            rows={7}
          />
          <p className="text-[12px] text-muted">
            Foundry generates drafts only—no emails are sent automatically.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

export function ResultsView({
  input,
  results,
  onResetSearch,
}: ResultsViewProps) {
  const inputSummary = input.resume
    ? `Resume PDF (${input.resume.name})`
    : input.linkedinUrl;

  return (
    <div className="grid gap-6">
      <div className="flex flex-col gap-3 rounded-[var(--radius-card)] border border-warning/30 bg-warning/5 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="warning">Fictional / Demo Data</Badge>
            <span className="text-[13px] font-medium text-foreground">
              Sample output for {inputSummary}
            </span>
          </div>
          <p className="mt-1 text-[12px] text-muted">
            All companies, funding rounds, hiring signals, founder names,
            emails, and match scores below are fictional demo examples. Live
            backend research will be connected in M2–M6.
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={onResetSearch}
          className="shrink-0"
        >
          New search
        </Button>
      </div>

      <div className="grid gap-6">
        {results.map((result) => (
          <StartupResultCard key={result.id} result={result} />
        ))}
      </div>
    </div>
  );
}
