"use client";

import { useState } from "react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  ConfirmDialog,
  EmptyState,
  ErrorState,
  Input,
  LoadingState,
  SkeletonCard,
  StatusIndicator,
  Textarea,
} from "@/components/ui";

export function ComponentShowcase() {
  const [email, setEmail] = useState("");
  const [note, setNote] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogOutcome, setDialogOutcome] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showError, setShowError] = useState(true);
  const [retrying, setRetrying] = useState(false);

  const emailError =
    email.length > 0 && !email.includes("@")
      ? "Enter a valid email address."
      : undefined;

  const handleRetry = () => {
    setRetrying(true);
    setTimeout(() => {
      setRetrying(false);
      setShowError(false);
    }, 350);
  };

  return (
    <section aria-labelledby="showcase-heading" className="mt-8 grid gap-6">
      <h2 id="showcase-heading" className="sr-only">
        Component verification
      </h2>
      <Card variant="standard">
        <CardHeader>
          <CardTitle>Interactive Controls & State Patterns (T008)</CardTitle>
          <CardDescription>
            Temporary verification for loading, error, empty, status, and
            confirmation dialog states.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="neutral">Neutral</Badge>
            <Badge variant="primary">Primary</Badge>
            <Badge variant="success">Verified</Badge>
            <Badge variant="warning">Pending</Badge>
            <Badge variant="danger">Error</Badge>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <StatusIndicator label="Idle" tone="neutral" />
            <StatusIndicator label="Running" tone="running" live />
            <StatusIndicator label="Complete" tone="success" />
            <StatusIndicator label="Caution" tone="warning" />
            <StatusIndicator label="Failed" tone="danger" />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              type="email"
              label="Email"
              placeholder="candidate@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              error={emailError}
              hint="Checks for an @ symbol."
            />
            <Input
              type="url"
              label="Portfolio URL (disabled)"
              placeholder="https://example.com"
              disabled
            />
          </div>
          <Textarea
            label="Notes"
            placeholder="Write a short note..."
            value={note}
            onChange={(event) => setNote(event.target.value)}
            rows={3}
          />
          {dialogOutcome && (
            <p className="text-[13px] text-success">{dialogOutcome}</p>
          )}
        </CardContent>
        <CardFooter className="justify-between">
          <div className="flex flex-wrap gap-2">
            <Button variant="primary" onClick={() => setDialogOpen(true)}>
              Open confirmation dialog
            </Button>
            <Button
              variant="secondary"
              onClick={() => setIsLoading((prev) => !prev)}
            >
              {isLoading ? "Show loaded card" : "Simulate loading state"}
            </Button>
            <Button
              variant="tertiary"
              onClick={() => setShowError((prev) => !prev)}
            >
              {showError ? "Hide error sample" : "Show error sample"}
            </Button>
            <Button
              variant="tertiary"
              onClick={() => {
                setEmail("");
                setNote("");
                setDialogOutcome(null);
              }}
            >
              Reset fields
            </Button>
          </div>
        </CardFooter>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        {isLoading ? (
          <LoadingState label="Loading sample card...">
            <SkeletonCard />
          </LoadingState>
        ) : (
          <Card variant="bordered">
            <CardHeader>
              <CardTitle>Loaded State</CardTitle>
              <CardDescription>
                Toggle &ldquo;Simulate loading state&rdquo; above to inspect the
                accessible skeleton container.
              </CardDescription>
            </CardHeader>
          </Card>
        )}

        <EmptyState
          title="No items yet"
          description="Contextual actions help users recover or start a workflow cleanly."
          action={
            <Button
              variant="primary"
              size="sm"
              onClick={() => setDialogOpen(true)}
            >
              Start action
            </Button>
          }
          secondaryAction={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsLoading(true)}
            >
              Preview loading
            </Button>
          }
        />
      </div>

      {showError && (
        <ErrorState
          title="Sample error state"
          description="Something prevented this preview from loading."
          details="Error code: SAMPLE_PREVIEW_ERROR"
          onRetry={handleRetry}
          retrying={retrying}
          retryLabel="Retry"
          secondaryAction={
            <Button
              variant="tertiary"
              size="sm"
              onClick={() => setShowError(false)}
            >
              Dismiss
            </Button>
          }
        />
      )}

      <ConfirmDialog
        open={dialogOpen}
        onClose={() => {
          setDialogOpen(false);
          setDialogOutcome("Dialog cancelled.");
        }}
        onConfirm={() => {
          setDialogOpen(false);
          setDialogOutcome("Dialog confirmed.");
        }}
        title="Confirm action"
        description="Supports Tab focus trapping, Escape key, backdrop click, and focus restoration."
        confirmLabel="Confirm"
        cancelLabel="Cancel"
      />
    </section>
  );
}
