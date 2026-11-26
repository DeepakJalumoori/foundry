"use client";

import { useState, type FormEvent } from "react";
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
} from "@/components/ui";
import { ResumeUploadCard } from "@/components/app/profile/resume-upload-card";
import {
  isValidHttpUrl,
  type ResumeFileMeta,
} from "@/components/app/profile/profile-types";

export interface CandidateRunInput {
  linkedinUrl: string;
  resume: ResumeFileMeta | null;
}

interface CandidateInputCardProps {
  initialInput: CandidateRunInput;
  onRunAgent: (input: CandidateRunInput) => void;
}

export function CandidateInputCard({
  initialInput,
  onRunAgent,
}: CandidateInputCardProps) {
  const [linkedinUrl, setLinkedinUrl] = useState(initialInput.linkedinUrl);
  const [resume, setResume] = useState<ResumeFileMeta | null>(
    initialInput.resume
  );
  const [urlError, setUrlError] = useState<string | undefined>(undefined);
  const [formError, setFormError] = useState<string | undefined>(undefined);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setUrlError(undefined);
    setFormError(undefined);

    const trimmedUrl = linkedinUrl.trim();

    if (!trimmedUrl && !resume) {
      setFormError(
        "Provide either a LinkedIn profile URL or a PDF resume to run the agent."
      );
      return;
    }

    if (trimmedUrl && !isValidHttpUrl(trimmedUrl)) {
      setUrlError(
        "Enter a valid URL starting with https:// or http:// (for example, https://linkedin.com/in/your-name)."
      );
      return;
    }

    onRunAgent({ linkedinUrl: trimmedUrl, resume });
  };

  return (
    <div className="mx-auto w-full max-w-2xl">
      <form onSubmit={handleSubmit} noValidate className="grid gap-5">
        <Card variant="standard">
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <CardTitle className="text-[20px]">Candidate input</CardTitle>
              <Badge variant="warning">Demo preview only</Badge>
            </div>
            <CardDescription>
              Provide a LinkedIn profile URL or attach a PDF resume. Only one
              input method is required per run.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            <Input
              type="url"
              label="LinkedIn profile URL"
              placeholder="https://linkedin.com/in/your-profile"
              value={linkedinUrl}
              onChange={(event) => {
                setLinkedinUrl(event.target.value);
                if (urlError) setUrlError(undefined);
                if (formError) setFormError(undefined);
              }}
              error={urlError}
              hint="No unauthorized LinkedIn scraping is performed."
            />
          </CardContent>
        </Card>

        <ResumeUploadCard
          resume={resume}
          onChange={(nextResume) => {
            setResume(nextResume);
            if (formError) setFormError(undefined);
          }}
        />

        {formError && (
          <p role="alert" className="text-[13px] font-medium text-danger">
            {formError}
          </p>
        )}

        <Card variant="bordered">
          <CardFooter className="flex-col items-stretch justify-between gap-3 sm:flex-row sm:items-center">
            <p className="text-[12px] text-muted">
              Demo action: resumes are not uploaded to a backend and LinkedIn
              profiles are not fetched yet.
            </p>
            <Button type="submit" variant="primary" size="md">
              Run job search agent (Demo)
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  );
}
