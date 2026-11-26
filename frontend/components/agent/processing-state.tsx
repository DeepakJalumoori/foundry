"use client";

import { useEffect, useState } from "react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  StatusIndicator,
} from "@/components/ui";
import type { CandidateRunInput } from "@/components/agent/candidate-input-card";

const PROCESSING_STAGES = [
  "Analyzing candidate profile",
  "Discovering startups",
  "Researching companies and founders",
  "Preparing outreach drafts",
] as const;

interface ProcessingStateProps {
  input: CandidateRunInput;
  onComplete: () => void;
  onCancel: () => void;
}

export function ProcessingState({
  input,
  onComplete,
  onCancel,
}: ProcessingStateProps) {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveIndex((prev) => {
        if (prev >= PROCESSING_STAGES.length - 1) {
          clearInterval(timer);
          return prev;
        }
        return prev + 1;
      });
    }, 650);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (activeIndex === PROCESSING_STAGES.length - 1) {
      const doneTimer = setTimeout(onComplete, 700);
      return () => clearTimeout(doneTimer);
    }
  }, [activeIndex, onComplete]);

  const inputSummary = input.resume
    ? `Resume PDF: ${input.resume.name}`
    : `LinkedIn URL: ${input.linkedinUrl}`;

  return (
    <div className="mx-auto w-full max-w-xl">
      <Card variant="standard">
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <Badge variant="warning">Simulated demo progress</Badge>
            <StatusIndicator label="Frontend demo only" tone="warning" live />
          </div>
          <CardTitle className="mt-2 text-[20px]">
            Running job search agent
          </CardTitle>
          <CardDescription>
            {inputSummary} — simulating the pipeline before displaying clearly
            labelled demo results.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ol className="grid gap-3">
            {PROCESSING_STAGES.map((stage, index) => {
              const isDone = index < activeIndex;
              const isCurrent = index === activeIndex;
              return (
                <li
                  key={stage}
                  className="flex items-center justify-between gap-3 rounded-[var(--radius-control)] border border-border bg-surface-muted/40 px-3.5 py-2.5"
                >
                  <span className="text-[14px] font-medium text-foreground">
                    {index + 1}. {stage}
                  </span>
                  <Badge
                    variant={
                      isDone ? "success" : isCurrent ? "primary" : "neutral"
                    }
                  >
                    {isDone ? "Done" : isCurrent ? "In progress" : "Pending"}
                  </Badge>
                </li>
              );
            })}
          </ol>
        </CardContent>
        <CardFooter className="justify-between">
          <Button variant="tertiary" size="sm" onClick={onCancel}>
            Back to input
          </Button>
          <Button variant="secondary" size="sm" onClick={onComplete}>
            View demo results now
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
