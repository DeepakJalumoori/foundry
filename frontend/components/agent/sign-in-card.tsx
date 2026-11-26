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
import { isValidEmail } from "@/components/app/profile/profile-types";

interface SignInCardProps {
  onSignIn: (email: string) => void;
}

export function SignInCard({ onSignIn }: SignInCardProps) {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | undefined>(undefined);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = email.trim();
    if (!trimmed) {
      setError("Enter your email address to continue.");
      return;
    }
    if (!isValidEmail(trimmed)) {
      setError("Enter a valid email address (for example, name@example.com).");
      return;
    }
    setError(undefined);
    onSignIn(trimmed);
  };

  return (
    <div className="mx-auto w-full max-w-md pt-6 sm:pt-12">
      <Card variant="standard">
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <Badge variant="primary">Foundry</Badge>
            <Badge variant="warning">Demo sign-in</Badge>
          </div>
          <CardTitle className="mt-2 text-[22px]">
            Sign in to Foundry
          </CardTitle>
          <CardDescription>
            Minimal AI job search agent for pre-seed to Series C startups.
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit} noValidate>
          <CardContent className="grid gap-4">
            <Input
              type="email"
              label="Email address"
              required
              placeholder="you@example.com"
              value={email}
              onChange={(event) => {
                setEmail(event.target.value);
                if (error) setError(undefined);
              }}
              error={error}
            />
            <p className="rounded-[var(--radius-control)] border border-border bg-surface-muted/50 px-3 py-2 text-[12px] text-muted">
              Frontend demo sign-in only. Backend authentication will be
              implemented in M2.
            </p>
          </CardContent>
          <CardFooter>
            <Button type="submit" variant="primary" size="md" className="w-full">
              Continue
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
