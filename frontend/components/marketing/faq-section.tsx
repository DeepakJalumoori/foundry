"use client";

import { useState } from "react";
import { PageContainer, Section } from "@/components/shared/page-container";
import { Badge } from "@/components/ui";
import { cn } from "@/lib/utils";

const FAQ_ITEMS = [
  {
    id: "what-is-foundry",
    question: "What is Foundry?",
    answer:
      "Foundry is an AI-powered career discovery and founder-outreach platform. It is designed to help candidates structure their profile, discover relevant startups, inspect sourced company and founder research, review deterministic fit explanations, and prepare personalized outreach drafts.",
  },
  {
    id: "how-matching-works",
    question: "How does startup matching work?",
    answer:
      "Foundry uses a deterministic weighted scoring model across skills alignment (30%), role relevance (25%), experience alignment (15%), project relevance (15%), candidate preferences (10%), and location/work mode (5%). Scores are reproducible from stored inputs, and an LLM may explain the result without altering the numeric score.",
  },
  {
    id: "verified-info",
    question: "Is the startup and founder information verified?",
    answer:
      "Company claims and founder contacts are designed to carry source attribution and explicit verification status (verified, unverified, unavailable, or demo). On this landing page, all example companies, scores, and founder profiles are illustrative demo placeholders—live discovery and research providers are not yet connected.",
  },
  {
    id: "auto-send",
    question: "Does Foundry send emails automatically?",
    answer:
      "No. Foundry prepares outreach drafts only and never sends emails automatically. Every draft requires your explicit review and approval or rejection, and automatic sending is intentionally excluded from the MVP.",
  },
  {
    id: "edit-reject",
    question: "Can I edit or reject outreach drafts?",
    answer:
      "Yes. You can edit the subject line and message body, approve a draft, or reject it. You remain in control of the wording and whether any message is ever sent.",
  },
  {
    id: "guarantees",
    question: "Does Foundry guarantee interviews or jobs?",
    answer:
      "No. Foundry reduces manual research and outreach preparation burden, and fit scores are heuristic estimates—never a guarantee or prediction of interviews, founder replies, or employment.",
  },
  {
    id: "get-started",
    question: "What information do I need to get started?",
    answer:
      "You can start with a PDF resume, a LinkedIn or portfolio URL, and your role, technology, location, and work-mode preferences. Today this page provides an interactive frontend preview; full backend parsing and discovery workflows are scheduled for upcoming implementation phases.",
  },
] as const;

export function FaqSection() {
  const [openId, setOpenId] = useState<string | null>(FAQ_ITEMS[0].id);

  return (
    <Section
      id="faq"
      aria-labelledby="faq-heading"
      spacing="spacious"
      className="border-t border-border bg-surface/60"
    >
      <PageContainer>
        <div className="grid items-start gap-10 lg:grid-cols-12 lg:gap-12">
          <div className="lg:col-span-4">
            <Badge variant="neutral">FAQ</Badge>
            <h2 id="faq-heading" className="text-h2 mt-4 text-foreground">
              Common questions, answered plainly.
            </h2>
            <p className="text-body mt-4 text-muted">
              Clear details on how Foundry works, how uncertainty is labelled,
              and what is currently a frontend preview versus planned backend
              functionality.
            </p>
          </div>

          <div className="lg:col-span-8">
            <div className="divide-y divide-border rounded-[var(--radius-panel)] border border-border bg-surface">
              {FAQ_ITEMS.map((item) => {
                const isOpen = openId === item.id;
                const buttonId = `faq-trigger-${item.id}`;
                const panelId = `faq-panel-${item.id}`;

                return (
                  <div key={item.id}>
                    <h3>
                      <button
                        id={buttonId}
                        type="button"
                        aria-expanded={isOpen}
                        aria-controls={panelId}
                        onClick={() =>
                          setOpenId((current) =>
                            current === item.id ? null : item.id
                          )
                        }
                        className={cn(
                          "flex w-full items-center justify-between gap-4 px-5 py-4 text-left text-[15px] font-semibold text-foreground transition-colors sm:px-6",
                          "hover:bg-surface-muted/50 focus-visible:outline-2 focus-visible:outline-primary focus-visible:-outline-offset-2"
                        )}
                      >
                        <span>{item.question}</span>
                        <span
                          aria-hidden="true"
                          className="font-mono text-[16px] font-normal text-muted"
                        >
                          {isOpen ? "−" : "+"}
                        </span>
                      </button>
                    </h3>
                    <div
                      id={panelId}
                      role="region"
                      aria-labelledby={buttonId}
                      hidden={!isOpen}
                      className="px-5 pb-5 text-[14px] leading-relaxed text-muted sm:px-6"
                    >
                      {item.answer}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </PageContainer>
    </Section>
  );
}
