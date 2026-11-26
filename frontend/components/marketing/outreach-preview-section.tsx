"use client";

import { useState } from "react";
import { PageContainer, Section } from "@/components/shared/page-container";
import {
  Badge,
  Button,
  Input,
  StatusIndicator,
  Textarea,
} from "@/components/ui";

const INITIAL_SUBJECT =
  "Question about Sample Startup A's async worker architecture";

const INITIAL_BODY = `Hi Alex,

I'm a final-year computer science student focused on Python and FastAPI backend systems.

I recently built a distributed task queue with bounded retries and idempotent workers, which made your engineering note on API latency and queue reliability especially interesting.

I'd appreciate the chance to learn more about how your team approaches reliability as Sample Startup A grows.

Thanks for your time — happy to share my project notes if useful.

Best,
Sample Candidate`;

type DraftState = "pending" | "approved" | "rejected";

export function OutreachPreviewSection() {
  const [subject, setSubject] = useState(INITIAL_SUBJECT);
  const [body, setBody] = useState(INITIAL_BODY);
  const [isEditing, setIsEditing] = useState(false);
  const [draftState, setDraftState] = useState<DraftState>("pending");

  const statusConfig = {
    pending: {
      label: isEditing ? "Editing demo draft" : "Awaiting your approval",
      tone: "warning" as const,
    },
    approved: {
      label: "Approved (demo — not sent)",
      tone: "success" as const,
    },
    rejected: {
      label: "Rejected (demo)",
      tone: "danger" as const,
    },
  }[draftState];

  const handleReset = () => {
    setSubject(INITIAL_SUBJECT);
    setBody(INITIAL_BODY);
    setIsEditing(false);
    setDraftState("pending");
  };

  return (
    <Section
      id="personalized-outreach"
      aria-labelledby="outreach-heading"
      spacing="spacious"
      className="border-t border-border bg-background"
    >
      <PageContainer>
        <div className="grid items-start gap-10 lg:grid-cols-12 lg:gap-12">
          {/* Left: Editorial explanation */}
          <div className="lg:col-span-5">
            <Badge variant="primary">Personalized outreach</Badge>
            <h2 id="outreach-heading" className="text-h2 mt-4 text-foreground">
              Thoughtful introductions grounded in your real work.
            </h2>
            <p className="text-body mt-4 text-muted">
              Foundry drafts a concise message connecting your actual skills
              and projects to the startup&apos;s public work—never generic
              templates or invented claims.
            </p>
            <p className="mt-4 text-[14px] leading-relaxed text-muted">
              Every draft stays editable and requires your explicit approval or
              rejection. Approving a draft records your decision; Foundry never
              sends emails automatically.
            </p>

            <div className="mt-6 rounded-[var(--radius-card)] border border-border bg-surface p-4">
              <p className="text-[13px] leading-relaxed text-muted">
                <span className="font-medium text-foreground">
                  Human-in-the-loop by design:
                </span>{" "}
                You control the wording, recipient, and timing. Try editing,
                approving, or rejecting the sample draft to preview the review
                flow.
              </p>
            </div>
          </div>

          {/* Right: Illustrative editable outreach draft */}
          <div className="rounded-[var(--radius-panel)] border border-border bg-surface p-6 shadow-xs sm:p-8 lg:col-span-7">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[14px] font-semibold text-foreground">
                  Outreach Draft Preview
                </span>
                <Badge variant="warning">Demo data</Badge>
              </div>
              <StatusIndicator
                label={statusConfig.label}
                tone={statusConfig.tone}
                live
              />
            </div>

            <div className="mt-4 flex flex-wrap items-center justify-between gap-2 rounded-[var(--radius-control)] bg-surface-muted/60 px-3.5 py-2.5 text-[13px]">
              <span className="text-foreground">
                <span className="text-muted">To:</span> Alex Rivera (Sample
                Founder · Sample Startup A)
              </span>
              <span className="text-muted">Manual review only</span>
            </div>

            <div className="mt-4 grid gap-4">
              {isEditing ? (
                <>
                  <Input
                    label="Subject line"
                    value={subject}
                    onChange={(event) => {
                      setSubject(event.target.value);
                      setDraftState("pending");
                    }}
                  />
                  <Textarea
                    label="Message body"
                    value={body}
                    onChange={(event) => {
                      setBody(event.target.value);
                      setDraftState("pending");
                    }}
                    rows={9}
                  />
                </>
              ) : (
                <div className="rounded-[var(--radius-card)] border border-border bg-surface-muted/30 p-4 sm:p-5">
                  <p className="text-[13px] font-medium text-muted">
                    Subject:{" "}
                    <span className="text-foreground">{subject}</span>
                  </p>
                  <div className="mt-3 whitespace-pre-line border-t border-border pt-3 text-[14px] leading-relaxed text-foreground">
                    {body}
                  </div>
                </div>
              )}
            </div>

            {/* Action controls */}
            <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
              <div className="flex flex-wrap items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsEditing((prev) => !prev)}
                >
                  {isEditing ? "Done editing" : "Edit draft"}
                </Button>
                <Button
                  variant="tertiary"
                  size="sm"
                  onClick={handleReset}
                >
                  Reset sample
                </Button>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => {
                    setIsEditing(false);
                    setDraftState("rejected");
                  }}
                >
                  Reject
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    setIsEditing(false);
                    setDraftState("approved");
                  }}
                >
                  Approve draft
                </Button>
              </div>
            </div>

            {draftState !== "pending" && (
              <p
                role="status"
                aria-live="polite"
                className="mt-3 text-[12px] text-muted"
              >
                {draftState === "approved"
                  ? "Preview state: Marked approved locally. Approving a draft never sends an email automatically."
                  : "Preview state: Marked rejected locally. No message was sent."}
              </p>
            )}
          </div>
        </div>
      </PageContainer>
    </Section>
  );
}
