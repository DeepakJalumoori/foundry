"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  EmptyState,
  ErrorState,
  Input,
  Textarea,
} from "@/components/ui";
import {
  ApiRequestError,
  approveOutreachDraft,
  archiveOutreachDraft,
  generateOutreachDraft,
  getCompanyFounders,
  getMatchingRunResults,
  getOutreachDraftEvidence,
  getOutreachDraftVersions,
  listOutreachDrafts,
  reviewOutreachDraft,
  updateOutreachDraft,
  type CompanyFounderItem,
  type MatchResultSummary,
  type OutreachDraft,
  type OutreachDraftEvidenceItem,
  type OutreachDraftStatus,
  type OutreachDraftVersionItem,
  type OutreachIntent,
} from "@/lib/api";

function statusBadgeVariant(status: OutreachDraftStatus) {
  if (status === "approved") return "success" as const;
  if (status === "reviewed") return "warning" as const;
  if (status === "archived") return "neutral" as const;
  return "neutral" as const;
}

function defaultIntentForOpportunity(
  opp: MatchResultSummary["opportunity_type"],
): OutreachIntent {
  if (opp === "active") return "job_interest";
  if (opp === "hidden") return "exploratory";
  return "general_interest";
}

export function OutreachWorkspacePanel() {
  const [candidateIdInput, setCandidateIdInput] = useState("");
  const [matchingRunIdInput, setMatchingRunIdInput] = useState("");
  const [matches, setMatches] = useState<MatchResultSummary[]>([]);
  const [selectedMatchId, setSelectedMatchId] = useState<string>("");
  const [founders, setFounders] = useState<CompanyFounderItem[]>([]);
  const [selectedFounderId, setSelectedFounderId] = useState<string>("");
  const [intent, setIntent] = useState<OutreachIntent>("exploratory");

  const [savedDrafts, setSavedDrafts] = useState<OutreachDraft[]>([]);
  const [activeDraft, setActiveDraft] = useState<OutreachDraft | null>(null);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [evidence, setEvidence] = useState<OutreachDraftEvidenceItem[]>([]);
  const [versions, setVersions] = useState<OutreachDraftVersionItem[]>([]);

  const [loadingMatches, setLoadingMatches] = useState(false);
  const [loadingDrafts, setLoadingDrafts] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [mutating, setMutating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const loadDraftDetails = useCallback(async (draft: OutreachDraft) => {
    setActiveDraft(draft);
    setSubject(draft.subject);
    setBody(draft.body);
    try {
      const [evRes, verRes] = await Promise.all([
        getOutreachDraftEvidence(draft.id),
        getOutreachDraftVersions(draft.id),
      ]);
      setEvidence(evRes.items);
      setVersions(verRes.items);
    } catch {
      setEvidence([]);
      setVersions([]);
    }
  }, []);

  const refreshSavedDrafts = useCallback(async () => {
    setLoadingDrafts(true);
    try {
      const res = await listOutreachDrafts({ limit: 20, offset: 0 });
      setSavedDrafts(res.items);
    } catch {
      // Backend may be offline when viewing demo-only mode; fail quietly here
      setSavedDrafts([]);
    } finally {
      setLoadingDrafts(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    listOutreachDrafts({ limit: 20, offset: 0 })
      .then((res) => {
        if (active) setSavedDrafts(res.items);
      })
      .catch(() => {
        if (active) setSavedDrafts([]);
      });
    return () => {
      active = false;
    };
  }, []);

  const handleLoadRun = async () => {
    const runId = matchingRunIdInput.trim();
    if (!runId) return;
    setLoadingMatches(true);
    setErrorMessage(null);
    setFeedbackMessage(null);
    try {
      const res = await getMatchingRunResults(runId);
      setMatches(res.items);
      if (res.items.length > 0) {
        const first = res.items[0];
        setSelectedMatchId(first.match_id);
        setIntent(defaultIntentForOpportunity(first.opportunity_type));
        const founderRes = await getCompanyFounders(first.company_id);
        setFounders(founderRes.items);
        setSelectedFounderId(founderRes.items[0]?.id ?? "");
      } else {
        setSelectedMatchId("");
        setFounders([]);
        setSelectedFounderId("");
      }
    } catch (err) {
      setErrorMessage(
        err instanceof ApiRequestError
          ? `${err.code}: ${err.message}`
          : "Unable to load matching run results from backend.",
      );
    } finally {
      setLoadingMatches(false);
    }
  };

  const handleSelectMatch = async (matchId: string) => {
    setSelectedMatchId(matchId);
    const match = matches.find((m) => m.match_id === matchId);
    if (!match) return;
    setIntent(defaultIntentForOpportunity(match.opportunity_type));
    setErrorMessage(null);
    try {
      const founderRes = await getCompanyFounders(match.company_id);
      setFounders(founderRes.items);
      setSelectedFounderId(founderRes.items[0]?.id ?? "");
    } catch (err) {
      setFounders([]);
      setSelectedFounderId("");
      setErrorMessage(
        err instanceof ApiRequestError
          ? `${err.code}: ${err.message}`
          : "Unable to load company founders.",
      );
    }
  };

  const handleGenerate = async () => {
    const selectedMatch = matches.find((m) => m.match_id === selectedMatchId);
    if (!selectedMatch || !selectedFounderId || !candidateIdInput.trim()) {
      setErrorMessage(
        "Candidate ID, matching run, match result, and founder are required.",
      );
      return;
    }

    setGenerating(true);
    setErrorMessage(null);
    setFeedbackMessage(null);
    try {
      const created = await generateOutreachDraft({
        candidate_id: candidateIdInput.trim(),
        matching_run_id: selectedMatch.matching_run_id,
        match_result_id: selectedMatch.match_id,
        company_id: selectedMatch.company_id,
        founder_id: selectedFounderId,
        outreach_intent: intent,
      });
      await loadDraftDetails(created);
      await refreshSavedDrafts();
      setFeedbackMessage("Outreach draft generated and persisted.");
    } catch (err) {
      setErrorMessage(
        err instanceof ApiRequestError
          ? `${err.code}: ${err.message}`
          : "Failed to generate outreach draft.",
      );
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveEdits = async () => {
    if (!activeDraft) return;
    setMutating(true);
    setErrorMessage(null);
    setFeedbackMessage(null);
    try {
      const updated = await updateOutreachDraft(activeDraft.id, {
        expected_version: activeDraft.version,
        subject,
        body,
      });
      await loadDraftDetails(updated);
      await refreshSavedDrafts();
      setFeedbackMessage(`Saved version ${updated.version}.`);
    } catch (err) {
      setErrorMessage(
        err instanceof ApiRequestError
          ? `${err.code}: ${err.message}`
          : "Failed to save draft changes.",
      );
    } finally {
      setMutating(false);
    }
  };

  const handleTransition = async (
    action: "review" | "approve" | "archive",
  ) => {
    if (!activeDraft) return;
    setMutating(true);
    setErrorMessage(null);
    setFeedbackMessage(null);
    try {
      const updated =
        action === "review"
          ? await reviewOutreachDraft(activeDraft.id)
          : action === "approve"
            ? await approveOutreachDraft(activeDraft.id)
            : await archiveOutreachDraft(activeDraft.id);
      await loadDraftDetails(updated);
      await refreshSavedDrafts();
      setFeedbackMessage(`Draft marked as ${updated.status}.`);
    } catch (err) {
      setErrorMessage(
        err instanceof ApiRequestError
          ? `${err.code}: ${err.message}`
          : `Failed to ${action} draft.`,
      );
    } finally {
      setMutating(false);
    }
  };

  const isEditable =
    activeDraft?.status === "draft" || activeDraft?.status === "reviewed";

  return (
    <Card variant="standard">
      <CardHeader className="border-b border-border pb-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <CardTitle className="text-[18px]">
              Founder Outreach Workspace (Backend API)
            </CardTitle>
            <CardDescription className="mt-1">
              Generate evidence-grounded drafts from a completed matching run,
              inspect supporting evidence, edit, and mark reviewed or approved.
            </CardDescription>
          </div>
          <Badge variant="neutral">No auto-send</Badge>
        </div>
      </CardHeader>

      <CardContent className="grid gap-5 pt-5">
        {errorMessage && (
          <ErrorState
            title="Outreach action failed"
            description={errorMessage}
          />
        )}
        {feedbackMessage && (
          <p className="rounded-[var(--radius-control)] border border-primary/20 bg-primary-soft px-3 py-2 text-[13px] text-foreground">
            {feedbackMessage}
          </p>
        )}

        {/* Run & match selection */}
        <div className="grid gap-3 rounded-[var(--radius-control)] border border-border p-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <Input
              label="Candidate ID"
              placeholder="UUID from /api/runs"
              value={candidateIdInput}
              onChange={(e) => setCandidateIdInput(e.target.value)}
            />
            <Input
              label="Matching Run ID"
              placeholder="UUID from /api/matching-runs"
              value={matchingRunIdInput}
              onChange={(e) => setMatchingRunIdInput(e.target.value)}
            />
            <div className="flex items-end">
              <Button
                variant="secondary"
                onClick={handleLoadRun}
                disabled={loadingMatches || !matchingRunIdInput.trim()}
              >
                {loadingMatches ? "Loading..." : "Load matching results"}
              </Button>
            </div>
          </div>

          {matches.length > 0 && (
            <div className="grid gap-3 border-t border-border pt-3 sm:grid-cols-3">
              <label className="grid gap-1.5 text-[13px]">
                <span className="font-medium text-foreground">Company match</span>
                <select
                  className="h-9 rounded-[var(--radius-control)] border border-border bg-surface px-2.5 text-[13px] text-foreground"
                  value={selectedMatchId}
                  onChange={(e) => void handleSelectMatch(e.target.value)}
                >
                  {matches.map((m) => (
                    <option key={m.match_id} value={m.match_id}>
                      {m.company_name} ({m.opportunity_type}, {Math.round(m.fit_score)}/100)
                    </option>
                  ))}
                </select>
              </label>

              <label className="grid gap-1.5 text-[13px]">
                <span className="font-medium text-foreground">Founder</span>
                <select
                  className="h-9 rounded-[var(--radius-control)] border border-border bg-surface px-2.5 text-[13px] text-foreground"
                  value={selectedFounderId}
                  onChange={(e) => setSelectedFounderId(e.target.value)}
                >
                  {founders.length === 0 ? (
                    <option value="">No founders discovered</option>
                  ) : (
                    founders.map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.full_name}
                        {f.role_title ? ` — ${f.role_title}` : ""} ({f.verification_status})
                      </option>
                    ))
                  )}
                </select>
              </label>

              <label className="grid gap-1.5 text-[13px]">
                <span className="font-medium text-foreground">Outreach intent</span>
                <select
                  className="h-9 rounded-[var(--radius-control)] border border-border bg-surface px-2.5 text-[13px] text-foreground"
                  value={intent}
                  onChange={(e) => setIntent(e.target.value as OutreachIntent)}
                >
                  <option value="job_interest">job_interest (confirmed opening)</option>
                  <option value="exploratory">exploratory (credible signals)</option>
                  <option value="general_interest">general_interest (cautious)</option>
                </select>
              </label>
            </div>
          )}

          {matches.length > 0 && (
            <div className="flex justify-end">
              <Button
                onClick={handleGenerate}
                disabled={generating || !selectedFounderId || !candidateIdInput.trim()}
              >
                {generating ? "Generating draft..." : "Generate outreach draft"}
              </Button>
            </div>
          )}
        </div>

        {/* Saved drafts selector */}
        <div className="grid gap-2">
          <div className="flex items-center justify-between">
            <h3 className="text-[14px] font-semibold text-foreground">
              Saved Outreach Drafts ({savedDrafts.length})
            </h3>
            <Button
              variant="tertiary"
              size="sm"
              onClick={() => void refreshSavedDrafts()}
              disabled={loadingDrafts}
            >
              {loadingDrafts ? "Refreshing..." : "Refresh"}
            </Button>
          </div>
          {savedDrafts.length === 0 ? (
            <EmptyState
              title="No saved outreach drafts"
              description="Load a completed matching run above to generate a draft, or connect the backend API."
            />
          ) : (
            <div className="flex flex-wrap gap-2">
              {savedDrafts.map((d) => (
                <Button
                  key={d.id}
                  variant={activeDraft?.id === d.id ? "primary" : "secondary"}
                  size="sm"
                  onClick={() => void loadDraftDetails(d)}
                >
                  {d.company_name} · {d.founder.full_name} ({d.status}, v{d.version})
                </Button>
              ))}
            </div>
          )}
        </div>

        {/* Active draft editor & review */}
        {activeDraft && (
          <div className="grid gap-4 border-t border-border pt-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={statusBadgeVariant(activeDraft.status)}>
                  Status: {activeDraft.status}
                </Badge>
                <Badge variant="neutral">
                  Intent: {activeDraft.outreach_intent}
                </Badge>
                <Badge variant={activeDraft.data_origin === "demo" ? "warning" : "success"}>
                  Origin: {activeDraft.data_origin} ({activeDraft.generation_provider})
                </Badge>
                <Badge variant="neutral">v{activeDraft.version}</Badge>
              </div>
              <p className="text-[12px] text-muted">
                Founder email: {activeDraft.founder.email ?? "Unavailable (not fabricated)"}
              </p>
            </div>

            {activeDraft.review_warnings.length > 0 && (
              <div className="rounded-[var(--radius-control)] border border-warning/40 bg-warning/5 p-3">
                <p className="text-[12px] font-semibold text-foreground">
                  Review warnings
                </p>
                <ul className="mt-1 list-disc pl-4 text-[12px] text-muted">
                  {activeDraft.review_warnings.map((w, idx) => (
                    <li key={idx}>{w}</li>
                  ))}
                </ul>
              </div>
            )}

            <Input
              label="Subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              disabled={!isEditable || mutating}
            />
            <Textarea
              label="Email body"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={8}
              disabled={!isEditable || mutating}
            />

            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-[12px] text-muted">
                Approval marks this draft ready for your manual use. Foundry never sends emails automatically.
              </p>
              <div className="flex flex-wrap gap-2">
                {isEditable && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleSaveEdits}
                    disabled={mutating}
                  >
                    Save changes
                  </Button>
                )}
                {activeDraft.status === "draft" && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => void handleTransition("review")}
                    disabled={mutating}
                  >
                    Mark reviewed
                  </Button>
                )}
                {(activeDraft.status === "draft" ||
                  activeDraft.status === "reviewed") && (
                  <Button
                    size="sm"
                    onClick={() => void handleTransition("approve")}
                    disabled={mutating}
                  >
                    Approve draft
                  </Button>
                )}
                {activeDraft.status !== "archived" && (
                  <Button
                    variant="tertiary"
                    size="sm"
                    onClick={() => void handleTransition("archive")}
                    disabled={mutating}
                  >
                    Archive
                  </Button>
                )}
              </div>
            </div>

            {/* Personalization rationale & Evidence */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-[var(--radius-control)] border border-border p-3.5">
                <h4 className="text-[13px] font-semibold text-foreground">
                  Personalization rationale
                </h4>
                <p className="mt-1 text-[13px] text-muted">
                  {activeDraft.personalization_rationale}
                </p>
                {activeDraft.candidate_strengths_used.length > 0 && (
                  <p className="mt-2 text-[12px] text-muted">
                    Strengths used: {activeDraft.candidate_strengths_used.join(", ")}
                  </p>
                )}
              </div>

              <div className="rounded-[var(--radius-control)] border border-border p-3.5">
                <h4 className="text-[13px] font-semibold text-foreground">
                  Supporting evidence ({evidence.length})
                </h4>
                {evidence.length === 0 ? (
                  <p className="mt-1 text-[12px] text-muted">
                    No evidence links recorded.
                  </p>
                ) : (
                  <ul className="mt-1 grid gap-2 text-[12px]">
                    {evidence.map((ev) => (
                      <li key={ev.id} className="border-b border-border/60 pb-1.5 last:border-none">
                        <p className="font-medium text-foreground">
                          [{ev.claim_category}] {ev.claim_text}
                        </p>
                        <p className="text-muted">
                          {ev.support_status} · {ev.verification_status}
                          {ev.source_url && (
                            <>
                              {" · "}
                              <a
                                href={ev.source_url}
                                target="_blank"
                                rel="noreferrer"
                                className="underline"
                              >
                                {ev.source_title ?? ev.source_url}
                              </a>
                            </>
                          )}
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {versions.length > 0 && (
              <div className="rounded-[var(--radius-control)] border border-border p-3.5">
                <h4 className="text-[13px] font-semibold text-foreground">
                  Version history ({versions.length})
                </h4>
                <ul className="mt-1 grid gap-1 text-[12px] text-muted">
                  {versions.map((v) => (
                    <li key={v.id}>
                      v{v.version} · {v.change_type} ({v.status_at_version}) — {v.subject}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
