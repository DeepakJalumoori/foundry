"use client";

import { useRef, useState, type ChangeEvent } from "react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui";
import {
  formatFileSize,
  type ResumeFileMeta,
} from "@/components/app/profile/profile-types";

const MAX_RESUME_BYTES = 5 * 1024 * 1024;

interface ResumeUploadCardProps {
  resume: ResumeFileMeta | null;
  onChange: (nextResume: ResumeFileMeta | null) => void;
}

export function ResumeUploadCard({ resume, onChange }: ResumeUploadCardProps) {
  const [resumeError, setResumeError] = useState<string | undefined>(undefined);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const isPdf =
      file.type === "application/pdf" ||
      file.name.toLowerCase().endsWith(".pdf");

    if (!isPdf) {
      setResumeError("Only PDF files (.pdf) are supported.");
      event.target.value = "";
      return;
    }

    if (file.size > MAX_RESUME_BYTES) {
      setResumeError("File exceeds the 5 MB maximum size limit.");
      event.target.value = "";
      return;
    }

    setResumeError(undefined);
    onChange({
      name: file.name,
      sizeBytes: file.size,
    });
  };

  const handleRemove = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    setResumeError(undefined);
    onChange(null);
  };

  return (
    <Card variant="standard">
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <CardTitle>Resume PDF</CardTitle>
          <Badge variant={resume ? "primary" : "neutral"}>
            {resume ? "Selected locally" : "Not selected"}
          </Badge>
        </div>
        <CardDescription>
          PDF only, up to 5 MB. Files are validated locally in your browser and
          are not uploaded or parsed yet.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4">
        <input
          ref={fileInputRef}
          id="profile-resume-pdf"
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileChange}
          className="sr-only"
        />

        {resume ? (
          <div className="flex flex-col gap-3 rounded-[var(--radius-card)] border border-border bg-surface-muted/45 p-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <p className="truncate text-[14px] font-semibold text-foreground">
                {resume.name}
              </p>
              <p className="mt-0.5 text-[12px] text-muted">
                {formatFileSize(resume.sizeBytes)} · Validated locally (not
                parsed or uploaded)
              </p>
            </div>
            <div className="flex shrink-0 flex-wrap items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
              >
                Replace PDF
              </Button>
              <Button variant="tertiary" size="sm" onClick={handleRemove}>
                Remove
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center rounded-[var(--radius-card)] border border-dashed border-border bg-surface-muted/35 px-4 py-6 text-center">
            <p className="text-[14px] font-medium text-foreground">
              No resume PDF selected
            </p>
            <p className="mt-1 text-[12px] text-muted">
              Choose a PDF file (max 5 MB) to preview attachment validation.
            </p>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              className="mt-4"
            >
              Choose PDF file
            </Button>
          </div>
        )}

        {resumeError && (
          <p role="alert" className="text-[13px] text-danger">
            {resumeError}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
