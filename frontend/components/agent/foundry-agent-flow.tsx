"use client";

import { useState } from "react";
import { PageContainer } from "@/components/shared/page-container";
import { Badge, Button } from "@/components/ui";
import { SignInCard } from "@/components/agent/sign-in-card";
import {
  CandidateInputCard,
  type CandidateRunInput,
} from "@/components/agent/candidate-input-card";
import { ProcessingState } from "@/components/agent/processing-state";
import { ResultsView } from "@/components/agent/results-view";
import { DEMO_STARTUP_RESULTS } from "@/components/agent/demo-results";

type FlowStep = "signin" | "input" | "processing" | "results";

const EMPTY_INPUT: CandidateRunInput = {
  linkedinUrl: "",
  resume: null,
};

export function FoundryAgentFlow() {
  const [step, setStep] = useState<FlowStep>("signin");
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [runInput, setRunInput] = useState<CandidateRunInput>(EMPTY_INPUT);

  const handleSignIn = (email: string) => {
    setUserEmail(email);
    setStep("input");
  };

  const handleSignOut = () => {
    setUserEmail(null);
    setRunInput(EMPTY_INPUT);
    setStep("signin");
  };

  const handleRunAgent = (input: CandidateRunInput) => {
    setRunInput(input);
    setStep("processing");
  };

  return (
    <div className="flex min-h-full flex-1 flex-col">
      <header className="border-b border-border bg-surface">
        <PageContainer className="flex h-14 items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <span
              aria-hidden="true"
              className="flex h-7 w-7 items-center justify-center rounded-[var(--radius-control)] bg-primary text-[13px] font-semibold text-white"
            >
              F
            </span>
            <span className="text-[15px] font-semibold tracking-tight text-foreground">
              Foundry
            </span>
            <Badge variant="warning">Frontend Demo</Badge>
          </div>

          {userEmail && (
            <div className="flex items-center gap-3">
              <span className="hidden text-[13px] text-muted sm:inline">
                {userEmail}
              </span>
              <Button variant="tertiary" size="sm" onClick={handleSignOut}>
                Sign out
              </Button>
            </div>
          )}
        </PageContainer>
      </header>

      <main
        id="main-content"
        tabIndex={-1}
        className="flex-1 py-8 sm:py-10 focus:outline-none"
      >
        <PageContainer>
          {step === "signin" && <SignInCard onSignIn={handleSignIn} />}

          {step === "input" && (
            <CandidateInputCard
              initialInput={runInput}
              onRunAgent={handleRunAgent}
            />
          )}

          {step === "processing" && (
            <ProcessingState
              input={runInput}
              onComplete={() => setStep("results")}
              onCancel={() => setStep("input")}
            />
          )}

          {step === "results" && (
            <ResultsView
              input={runInput}
              results={DEMO_STARTUP_RESULTS}
              onResetSearch={() => setStep("input")}
            />
          )}
        </PageContainer>
      </main>
    </div>
  );
}
