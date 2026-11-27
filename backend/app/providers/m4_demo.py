from datetime import UTC, datetime, timedelta

from app.core.config import Settings
from app.providers.m4_base import (
    CompanyIdentityDTO,
    CompanyResearchDTO,
    CompanyResearchProvider,
    DiscoveredStartupDTO,
    DiscoveryQuery,
    FounderDTO,
    FounderProvider,
    FundingEventDTO,
    FundingProvider,
    HiringIntelligenceDTO,
    HiringSignalDTO,
    HiringSignalProvider,
    JobPostingDTO,
    M4ProviderError,
    ResearchClaimDTO,
    StartupDiscoveryProvider,
)
from app.schemas.m4 import CompanyStage, SourceEvidenceInput


def _demo_now() -> datetime:
    return datetime(2026, 11, 20, 12, 0, 0, tzinfo=UTC)


def _demo_evidence(
    url: str,
    title: str,
    domain: str,
    excerpt: str,
    days_ago: int | None = 15,
) -> SourceEvidenceInput:
    now = _demo_now()
    pub_date = now - timedelta(days=days_ago) if days_ago is not None else None
    return SourceEvidenceInput(
        source_url=url,  # type: ignore[arg-type]
        source_title=title,
        source_domain=domain,
        source_type="demo",
        publication_date=pub_date,
        retrieved_at=now,
        excerpt=excerpt,
        verification_status="verified",
        data_origin="demo",
    )


_DEMO_CATALOG: list[dict] = [
    {
        "name": "Kestrel Data Systems",
        "official_website": "https://kestreldata.example.com",
        "domain": "kestreldata.example.com",
        "external_id": "demo-kestrel-001",
        "description": "Real-time SQLite and DuckDB edge analytics engine for developer teams.",
        "industry": "Developer Tools",
        "product_or_service": "Embedded analytical query engine and cloud sync.",
        "headquarters": "San Francisco, CA",
        "founded_year": 2024,
        "stage": "seed",
        "employee_range": "11-25",
        "tech_stack": ["Python", "Rust", "FastAPI", "SQLite", "Docker"],
        "business_model": "B2B SaaS + Open-Core",
    },
    {
        "name": "Verdant BioCompute",
        "official_website": "https://verdantbio.example.com",
        "domain": "verdantbio.example.com",
        "external_id": "demo-verdant-002",
        "description": "AI-assisted protein folding workflow orchestration for wet-lab teams.",
        "industry": "Biotech AI",
        "product_or_service": "Cloud simulation pipeline for molecular design.",
        "headquarters": "Boston, MA",
        "founded_year": 2023,
        "stage": "series_a",
        "employee_range": "26-50",
        "tech_stack": ["Python", "PyTorch", "PostgreSQL", "Kubernetes"],
        "business_model": "Enterprise B2B",
    },
    {
        "name": "HarborPay Ledger",
        "official_website": "https://harborpay.example.com",
        "domain": "harborpay.example.com",
        "external_id": "demo-harbor-003",
        "description": "Cross-border treasury reconciliation API for mid-market exporters.",
        "industry": "FinTech",
        "product_or_service": "Automated multi-currency ledger and settlement API.",
        "headquarters": "New York, NY",
        "founded_year": 2022,
        "stage": "series_b",
        "employee_range": "51-100",
        "tech_stack": ["Go", "TypeScript", "PostgreSQL", "React"],
        "business_model": "B2B API",
    },
]


class DemoStartupDiscoveryProvider(StartupDiscoveryProvider):
    """Deterministic demo startup discovery provider."""

    def discover_startups(self, query: DiscoveryQuery) -> list[DiscoveredStartupDTO]:
        results: list[DiscoveredStartupDTO] = []
        allowed_stages: set[CompanyStage] = set(query.company_stages) if query.company_stages else set()

        for item in _DEMO_CATALOG:
            if allowed_stages and item["stage"] not in allowed_stages:
                continue
            if query.target_industries:
                lowered = {i.lower() for i in query.target_industries}
                if item["industry"].lower() not in lowered:
                    continue

            results.append(
                DiscoveredStartupDTO(
                    name=item["name"],
                    official_website=item["official_website"],
                    external_id=item["external_id"],
                    description=item["description"],
                    industry=item["industry"],
                    headquarters=item["headquarters"],
                    stage=item["stage"],
                    employee_range=item["employee_range"],
                    tech_stack=list(item["tech_stack"]),
                    data_origin="demo",
                    evidence=[
                        _demo_evidence(
                            f"{item['official_website']}/about",
                            f"{item['name']} — Demo Company Directory",
                            item["domain"],
                            item["description"],
                            days_ago=10,
                        )
                    ],
                )
            )
            if len(results) >= query.max_companies:
                break

        return results


class DemoCompanyResearchProvider(CompanyResearchProvider):
    """Deterministic demo company research provider."""

    def research_company(self, company: CompanyIdentityDTO) -> CompanyResearchDTO:
        match = next(
            (c for c in _DEMO_CATALOG if c["domain"] == company.normalized_domain or c["name"] == company.name),
            None,
        )
        if match is None:
            return CompanyResearchDTO(
                summary=f"Limited demo profile for {company.name}.",
                status="completed_with_warnings",
                data_origin="demo",
                warnings=["No extended demo catalog entry found for this company."],
                evidence=[],
            )

        ev = _demo_evidence(
            f"{match['official_website']}/platform",
            f"{match['name']} Platform Overview (Demo)",
            match["domain"],
            match["product_or_service"],
            days_ago=14,
        )
        return CompanyResearchDTO(
            description=match["description"],
            industry=match["industry"],
            product_or_service=match["product_or_service"],
            headquarters=match["headquarters"],
            founded_year=match["founded_year"],
            stage=match["stage"],
            employee_range=match["employee_range"],
            tech_stack=list(match["tech_stack"]),
            business_model=match["business_model"],
            summary=f"{match['name']} builds {match['product_or_service'].lower()}",
            claims=[
                ResearchClaimDTO(field_name="headquarters", value=match["headquarters"], evidence=ev),
                ResearchClaimDTO(field_name="business_model", value=match["business_model"], evidence=ev),
            ],
            status="completed",
            data_origin="demo",
            evidence=[ev],
        )


class DemoFundingProvider(FundingProvider):
    """Deterministic demo funding intelligence provider."""

    def get_funding_events(self, company: CompanyIdentityDTO) -> list[FundingEventDTO]:
        now = _demo_now()
        if company.normalized_domain == "kestreldata.example.com":
            return [
                FundingEventDTO(
                    round_type="seed",
                    amount=4_200_000.0,
                    currency="USD",
                    announced_date=now - timedelta(days=45),
                    retrieved_at=now,
                    investors=["Demo Seed Ventures", "Northstar Angels"],
                    lead_investor="Demo Seed Ventures",
                    original_claim="Kestrel Data Systems announced a $4.2M Seed round led by Demo Seed Ventures.",
                    confirmed=True,
                    data_origin="demo",
                    evidence=[
                        _demo_evidence(
                            "https://kestreldata.example.com/blog/seed-round",
                            "Kestrel Data Systems Seed Announcement (Demo)",
                            "kestreldata.example.com",
                            "Raised $4.2M Seed led by Demo Seed Ventures.",
                            days_ago=45,
                        )
                    ],
                )
            ]
        if company.normalized_domain == "verdantbio.example.com":
            return [
                FundingEventDTO(
                    round_type="series_a",
                    amount=18_000_000.0,
                    currency="USD",
                    announced_date=now - timedelta(days=60),
                    retrieved_at=now,
                    investors=["BioFrontier Capital"],
                    lead_investor="BioFrontier Capital",
                    original_claim="Verdant BioCompute closed $18M Series A led by BioFrontier Capital.",
                    confirmed=True,
                    data_origin="demo",
                    evidence=[
                        _demo_evidence(
                            "https://verdantbio.example.com/news/series-a",
                            "Verdant BioCompute Series A (Demo)",
                            "verdantbio.example.com",
                            "Closed $18M Series A.",
                            days_ago=60,
                        )
                    ],
                )
            ]
        return [
            FundingEventDTO(
                round_type="series_b",
                amount=None,
                currency=None,
                announced_date=now - timedelta(days=420),
                retrieved_at=now,
                investors=["Atlantic Growth Partners"],
                lead_investor="Atlantic Growth Partners",
                original_claim="HarborPay Ledger completed an undisclosed Series B round.",
                confirmed=True,
                data_origin="demo",
                evidence=[
                    _demo_evidence(
                        "https://harborpay.example.com/press/series-b",
                        "HarborPay Series B Press Release (Demo)",
                        "harborpay.example.com",
                        "Completed Series B financing with undisclosed terms.",
                        days_ago=420,
                    )
                ],
            )
        ]


class DemoHiringSignalProvider(HiringSignalProvider):
    """Deterministic demo hiring signal provider covering Active and Hidden opportunities."""

    def get_hiring_signals(self, company: CompanyIdentityDTO) -> HiringIntelligenceDTO:
        now = _demo_now()
        if company.normalized_domain == "kestreldata.example.com":
            # Active opportunity: confirmed public job posting
            job_ev = _demo_evidence(
                "https://kestreldata.example.com/careers/backend-engineer",
                "Backend Systems Engineer — Kestrel Careers (Demo)",
                "kestreldata.example.com",
                "Hiring a Backend Systems Engineer (Python/FastAPI/SQLite) in San Francisco.",
                days_ago=5,
            )
            return HiringIntelligenceDTO(
                signals=[
                    HiringSignalDTO(
                        signal_type="public_job_posting",
                        title="Active Backend Systems Engineer opening",
                        observed_fact="Public job listing posted 5 days ago on company careers page.",
                        description="Seeking Python and storage engine engineers.",
                        role_titles=["Backend Systems Engineer"],
                        department="Engineering",
                        location="San Francisco, CA",
                        job_posting_url="https://kestreldata.example.com/careers/backend-engineer",
                        publication_date=now - timedelta(days=5),
                        has_confirmed_open_role=True,
                        data_origin="demo",
                        evidence=[job_ev],
                    )
                ],
                job_postings=[
                    JobPostingDTO(
                        title="Backend Systems Engineer",
                        job_url="https://kestreldata.example.com/careers/backend-engineer",
                        location="San Francisco, CA",
                        employment_type="Full-time",
                        posting_date=now - timedelta(days=5),
                        is_currently_confirmed=True,
                        data_origin="demo",
                        evidence=[job_ev],
                    )
                ],
            )

        if company.normalized_domain == "verdantbio.example.com":
            # Hidden opportunity: leadership announcement of new ML team, no public job posting
            exp_ev = _demo_evidence(
                "https://verdantbio.example.com/blog/ml-infrastructure-expansion",
                "Expanding our ML Platform Team (Demo)",
                "verdantbio.example.com",
                "CTO announced formation of a new ML infrastructure group in Q4.",
                days_ago=12,
            )
            return HiringIntelligenceDTO(
                signals=[
                    HiringSignalDTO(
                        signal_type="leadership_statement",
                        title="CTO announced new ML infrastructure team",
                        observed_fact="Leadership blog post describes launching a new ML platform team.",
                        description="No formal job board postings published yet.",
                        role_titles=[],
                        department="ML Infrastructure",
                        location="Boston, MA",
                        publication_date=now - timedelta(days=12),
                        has_confirmed_open_role=False,
                        uncertainties="No public job requisition URL is available yet.",
                        data_origin="demo",
                        evidence=[exp_ev],
                    )
                ],
                job_postings=[],
            )

        return HiringIntelligenceDTO(signals=[], job_postings=[])


class DemoFounderProvider(FounderProvider):
    """Deterministic demo founder discovery provider (never fabricates emails)."""

    def discover_founders(self, company: CompanyIdentityDTO) -> list[FounderDTO]:
        if company.normalized_domain == "kestreldata.example.com":
            ev = _demo_evidence(
                "https://kestreldata.example.com/team",
                "Kestrel Team Page (Demo)",
                "kestreldata.example.com",
                "Elena Rostova, Co-founder & CEO; Marcus Vance, Co-founder & CTO.",
                days_ago=10,
            )
            return [
                FounderDTO(
                    full_name="Elena Rostova",
                    role_title="Co-founder & CEO",
                    public_profile_url="https://kestreldata.example.com/team#elena",
                    biography="Previously built distributed storage systems.",
                    verification_status="verified",
                    data_origin="demo",
                    evidence=[ev],
                ),
                FounderDTO(
                    full_name="Marcus Vance",
                    role_title="Co-founder & CTO",
                    public_profile_url="https://kestreldata.example.com/team#marcus",
                    biography="Database kernel engineer.",
                    verification_status="verified",
                    data_origin="demo",
                    evidence=[ev],
                ),
            ]
        if company.normalized_domain == "verdantbio.example.com":
            ev = _demo_evidence(
                "https://verdantbio.example.com/about",
                "Verdant BioCompute About (Demo)",
                "verdantbio.example.com",
                "Dr. Aris Thorne, Co-founder & CEO.",
                days_ago=20,
            )
            return [
                FounderDTO(
                    full_name="Dr. Aris Thorne",
                    role_title="Co-founder & CEO",
                    public_profile_url="https://verdantbio.example.com/about#aris",
                    biography="Computational biology researcher.",
                    verification_status="verified",
                    data_origin="demo",
                    evidence=[ev],
                )
            ]
        return []


def get_discovery_provider(settings: Settings) -> StartupDiscoveryProvider:
    if settings.demo_mode or settings.discovery_provider == "demo":
        return DemoStartupDiscoveryProvider()
    raise M4ProviderError(
        "PROVIDER_NOT_CONFIGURED",
        f"Discovery provider '{settings.discovery_provider}' is not configured.",
        status_code=503,
    )


def get_company_research_provider(settings: Settings) -> CompanyResearchProvider:
    if settings.demo_mode or settings.company_research_provider == "demo":
        return DemoCompanyResearchProvider()
    raise M4ProviderError(
        "PROVIDER_NOT_CONFIGURED",
        f"Company research provider '{settings.company_research_provider}' is not configured.",
        status_code=503,
    )


def get_funding_provider(settings: Settings) -> FundingProvider:
    if settings.demo_mode or settings.funding_provider == "demo":
        return DemoFundingProvider()
    raise M4ProviderError(
        "PROVIDER_NOT_CONFIGURED",
        f"Funding provider '{settings.funding_provider}' is not configured.",
        status_code=503,
    )


def get_hiring_signal_provider(settings: Settings) -> HiringSignalProvider:
    if settings.demo_mode or settings.hiring_signal_provider == "demo":
        return DemoHiringSignalProvider()
    raise M4ProviderError(
        "PROVIDER_NOT_CONFIGURED",
        f"Hiring signal provider '{settings.hiring_signal_provider}' is not configured.",
        status_code=503,
    )


def get_founder_provider(settings: Settings) -> FounderProvider:
    if settings.demo_mode or settings.founder_provider == "demo":
        return DemoFounderProvider()
    raise M4ProviderError(
        "PROVIDER_NOT_CONFIGURED",
        f"Founder provider '{settings.founder_provider}' is not configured.",
        status_code=503,
    )
