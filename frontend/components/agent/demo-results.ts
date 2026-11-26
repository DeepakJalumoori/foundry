import type { DemoStartupResult } from "@/components/agent/types";

export const DEMO_STARTUP_RESULTS: DemoStartupResult[] = [
  {
    id: "demo-verge-compute",
    companyName: "Verge Compute (Demo)",
    description:
      "Builds lightweight inference routing and GPU utilization tooling for small AI engineering teams.",
    fundingStage: "Seed ($4.2M)",
    fundingEvidence: {
      label: "Seed round announcement",
      detail:
        "Announced $4.2M Seed round to expand distributed inference scheduling.",
      sourceLabel: "Example Tech News (Fictional Demo Source)",
      sourceUrl: "https://example.com/demo/verge-compute-seed",
      date: "2026-09-14",
    },
    opportunityType: "active",
    hiringSignals: [
      {
        label: "Public job opening",
        detail:
          "Careers page lists 'Backend / Distributed Systems Engineer (Early Career)'.",
        sourceLabel: "Verge Compute Careers (Fictional Demo)",
        sourceUrl: "https://example.com/demo/verge-compute-careers",
        date: "2026-11-10",
      },
    ],
    whyReachOut:
      "Active backend/systems opening aligns with Python, FastAPI, and distributed systems experience; small engineering team makes direct founder outreach high-signal.",
    founderName: "Maya Chen (Fictional)",
    founderRole: "Co-founder & CTO",
    founderEmail: "maya@vergecompute.example",
    emailSource: "Company engineering blog author bio (Fictional Demo)",
    emailVerification: "verified",
    matchScore: 88,
    matchExplanation:
      "Strong overlap on Python/FastAPI backend systems and AI infrastructure interest. Demo score only—not calculated by a live backend.",
    emailDraftSubject:
      "Backend / distributed systems interest — Verge Compute",
    emailDraftBody: `Hi Maya,

I saw Verge Compute's recent work on inference routing and the Backend / Distributed Systems Engineer role on your careers page.

I've been building Python and FastAPI services for LLM orchestration workflows and would love to contribute to your scheduling layer.

Would you be open to a brief 15-minute chat this week?

Best,
[Your Name]`,
  },
  {
    id: "demo-ledger-weave",
    companyName: "LedgerWeave (Demo)",
    description:
      "Automates reconciliation and audit trails for B2B fintech platforms using deterministic rule engines.",
    fundingStage: "Series A ($11M)",
    fundingEvidence: {
      label: "Series A announcement",
      detail:
        "Raised $11M Series A to support compliance automation for mid-market fintechs.",
      sourceLabel: "Example Venture Wire (Fictional Demo Source)",
      sourceUrl: "https://example.com/demo/ledgerweave-series-a",
      date: "2026-08-02",
    },
    opportunityType: "hidden",
    hiringSignals: [
      {
        label: "No public job openings found",
        detail:
          "No active engineering roles listed on careers page or major job boards. Funding alone is not treated as proof of hiring; surfaced based on recent product API launch and engineering blog activity.",
        sourceLabel: "LedgerWeave Engineering Changelog (Fictional Demo)",
        sourceUrl: "https://example.com/demo/ledgerweave-changelog",
        date: "2026-11-18",
      },
    ],
    whyReachOut:
      "Hidden opportunity: despite no public job posting, their new Python/SQLAlchemy audit API aligns closely with your backend and data validation background.",
    founderName: "Daniel Okafor (Fictional)",
    founderRole: "Co-founder & CEO",
    founderEmail: "daniel@ledgerweave.example",
    emailSource: "Public conference speaker page (Fictional Demo)",
    emailVerification: "unverified",
    matchScore: 79,
    matchExplanation:
      "Good alignment on Python, SQLAlchemy, and deterministic validation pipelines; lower score due to no confirmed public job opening. Demo score only.",
    emailDraftSubject:
      "Reaching out regarding LedgerWeave's audit API",
    emailDraftBody: `Hi Daniel,

I read LedgerWeave's recent changelog on deterministic audit trails and wanted to reach out directly.

I've built structured validation and persistence pipelines in Python and SQLAlchemy and am looking for a focused early-stage engineering team. Even if you don't have a formal posting open, I'd welcome a quick conversation.

Best,
[Your Name]`,
  },
  {
    id: "demo-fieldnote-ai",
    companyName: "Fieldnote AI (Demo)",
    description:
      "Helps hardware and robotics teams index test-bench logs and failure reports for faster root-cause analysis.",
    fundingStage: "Pre-seed ($1.5M)",
    fundingEvidence: {
      label: "Pre-seed announcement",
      detail:
        "Backed by $1.5M pre-seed round to build structured search over hardware test logs.",
      sourceLabel: "Example Startup Directory (Fictional Demo Source)",
      sourceUrl: "https://example.com/demo/fieldnote-preseed",
      date: "2026-10-05",
    },
    opportunityType: "active",
    hiringSignals: [
      {
        label: "Job platform posting",
        detail:
          "Founding Full-Stack / AI Engineer listing on startup job board.",
        sourceLabel: "Example Startup Jobs (Fictional Demo)",
        sourceUrl: "https://example.com/demo/fieldnote-job",
        date: "2026-11-20",
      },
    ],
    whyReachOut:
      "Active founding engineer role focused on search/retrieval and TypeScript + Python full-stack delivery.",
    founderName: "Elena Rostova (Fictional)",
    founderRole: "Founder & CEO",
    founderEmail: null,
    emailSource: "No public professional email found (Fictional Demo)",
    emailVerification: "unavailable",
    matchScore: 84,
    matchExplanation:
      "Strong match across Next.js/TypeScript frontend, Python backend, and retrieval workflows. Demo score only.",
    emailDraftSubject:
      "Founding Full-Stack / AI Engineer — Fieldnote AI",
    emailDraftBody: `Hi Elena,

I saw Fieldnote AI's Founding Full-Stack / AI Engineer role and was excited by your focus on structured retrieval over hardware test logs.

I've been working across TypeScript/Next.js and Python/FastAPI search pipelines and would love to learn more about what you're building.

Best,
[Your Name]`,
  },
];
