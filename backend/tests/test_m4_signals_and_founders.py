from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.m4 import Company
from app.providers.m4_base import (
    DiscoveredStartupDTO,
    FounderDTO,
    FounderProvider,
    FundingEventDTO,
    FundingProvider,
    HiringIntelligenceDTO,
    HiringSignalDTO,
    HiringSignalProvider,
    JobPostingDTO,
)
from app.schemas.m4 import SourceEvidenceInput
from app.services.company_identity import resolve_or_create_company
from app.services.founder_service import discover_company_founders
from app.services.funding_service import collect_company_funding
from app.services.hiring_service import detect_hiring_signals


def _ev(url: str, title: str, days_ago: int | None = 5) -> SourceEvidenceInput:
    now = datetime.now(UTC)
    return SourceEvidenceInput(
        source_url=url,  # type: ignore[arg-type]
        source_title=title,
        source_domain="example.com",
        source_type="news_article",
        publication_date=now - timedelta(days=days_ago) if days_ago is not None else None,
        retrieved_at=now,
        excerpt=title,
        verification_status="verified",
        data_origin="demo",
    )


def _make_company(db: Session, name: str, domain: str) -> Company:
    company, _ = resolve_or_create_company(
        db,
        DiscoveredStartupDTO(name=name, official_website=f"https://{domain}"),
    )
    return company


def test_funding_classification_currencies_conflicts_and_dedup(db_session: Session) -> None:
    company = _make_company(db_session, "EuroStartup", "eurostartup.example.com")
    now = datetime.now(UTC)
    same_date = now - timedelta(days=30)

    class CustomFundingProvider(FundingProvider):
        def get_funding_events(self, _c):
            return [
                FundingEventDTO(
                    round_type="seed",
                    amount=3_000_000.0,
                    currency="EUR",
                    announced_date=same_date,
                    retrieved_at=now,
                    original_claim="Raised 3M EUR Seed",
                    confirmed=True,
                    evidence=[_ev("https://example.com/f1", "Seed EUR", 30)],
                ),
                # Duplicate date+round with conflicting amount -> triggers requires_review
                FundingEventDTO(
                    round_type="seed",
                    amount=3_500_000.0,
                    currency="EUR",
                    announced_date=same_date,
                    retrieved_at=now,
                    original_claim="Reported 3.5M EUR Seed",
                    confirmed=True,
                    evidence=[_ev("https://example.com/f2", "Seed EUR Conflict", 29)],
                ),
                # Unconfirmed rumor with undisclosed amount
                FundingEventDTO(
                    round_type="unknown",
                    amount=None,
                    currency=None,
                    announced_date=None,
                    retrieved_at=now,
                    original_claim="Rumor of upcoming round",
                    confirmed=False,
                    evidence=[],
                ),
                # Historical funding (>180 days)
                FundingEventDTO(
                    round_type="pre_seed",
                    amount=500_000.0,
                    currency="USD",
                    announced_date=now - timedelta(days=365),
                    retrieved_at=now,
                    original_claim="Pre-seed last year",
                    confirmed=True,
                    evidence=[_ev("https://example.com/f3", "Pre-seed", 365)],
                ),
            ]

    events = collect_company_funding(db_session, company, CustomFundingProvider())
    db_session.commit()

    # 3 distinct events (the conflicting duplicate updates the existing one)
    unique_ids = {e.id for e in events}
    assert len(unique_ids) == 3

    seed = next(e for e in events if e.round_type == "seed")
    assert seed.currency == "EUR"
    assert seed.verification_status == "requires_review"
    assert seed.is_recent is True

    rumor = next(e for e in events if e.round_type == "unknown")
    assert rumor.amount is None
    assert rumor.currency is None
    assert rumor.verification_status == "unverified"
    assert rumor.is_recent is None

    old_round = next(e for e in events if e.round_type == "pre_seed")
    assert old_round.is_recent is False


def test_hiring_signals_active_vs_hidden_stale_and_funding_only_rule(db_session: Session) -> None:
    company = _make_company(db_session, "SignalCorp", "signalcorp.example.com")
    now = datetime.now(UTC)

    class CustomHiringProvider(HiringSignalProvider):
        def get_hiring_signals(self, _c):
            return HiringIntelligenceDTO(
                signals=[
                    # Funding-only signal -> must NOT be treated as hiring signal
                    HiringSignalDTO(
                        signal_type="other",
                        title="Raised Seed Round",
                        observed_fact="Company raised $2M.",
                        is_funding_only=True,
                        has_confirmed_open_role=False,
                        evidence=[_ev("https://example.com/funding", "Funding")],
                    ),
                    # Hidden opportunity: expansion announcement without public job posting
                    HiringSignalDTO(
                        signal_type="team_expansion",
                        title="Opening London engineering hub",
                        observed_fact="CEO announced London office expansion.",
                        has_confirmed_open_role=False,
                        publication_date=None,
                        evidence=[_ev("https://example.com/london", "London Hub", None)],
                    ),
                    # Duplicate hidden signal
                    HiringSignalDTO(
                        signal_type="team_expansion",
                        title="Opening London engineering hub",
                        observed_fact="CEO announced London office expansion.",
                        has_confirmed_open_role=False,
                        evidence=[_ev("https://example.com/london", "London Hub", None)],
                    ),
                ],
                job_postings=[
                    # Stale job posting (>90 days old) -> must NOT be marked active
                    JobPostingDTO(
                        title="Old Engineer Role",
                        job_url="https://signalcorp.example.com/jobs/old",
                        posting_date=now - timedelta(days=150),
                        is_currently_confirmed=True,
                        evidence=[_ev("https://signalcorp.example.com/jobs/old", "Old Role", 150)],
                    )
                ],
            )

    signals, jobs = detect_hiring_signals(db_session, company, CustomHiringProvider())
    db_session.commit()

    assert len({s.id for s in signals}) == 1
    assert signals[0].opportunity_category == "hidden"
    assert len(jobs) == 1
    assert jobs[0].is_active is False
    assert jobs[0].verification_status == "requires_review"
    assert company.opportunity_type == "hidden"


def test_founder_discovery_dedup_missing_fields_and_conflicts(db_session: Session) -> None:
    company = _make_company(db_session, "FounderCorp", "foundercorp.example.com")

    class CustomFounderProvider(FounderProvider):
        def discover_founders(self, _c):
            return [
                FounderDTO(
                    full_name="Jane Doe",
                    role_title="CEO",
                    public_profile_url=None,
                    verification_status="verified",
                    evidence=[_ev("https://foundercorp.example.com/team", "Team")],
                ),
                # Conflicting role title for same founder
                FounderDTO(
                    full_name="Jane Doe",
                    role_title="CTO",
                    public_profile_url="https://foundercorp.example.com/jane",
                    verification_status="verified",
                    evidence=[_ev("https://news.example.com/jane", "News")],
                ),
                # Unverified founder with no evidence and missing role
                FounderDTO(
                    full_name="Bob Smith",
                    role_title=None,
                    public_profile_url=None,
                    verification_status="verified",
                    evidence=[],
                ),
            ]

    founders = discover_company_founders(db_session, company, CustomFounderProvider())
    db_session.commit()

    unique = {f.id: f for f in founders}
    assert len(unique) == 2

    jane = next(f for f in unique.values() if f.full_name == "Jane Doe")
    assert jane.verification_status == "requires_review"
    assert jane.conflict_notes is not None

    bob = next(f for f in unique.values() if f.full_name == "Bob Smith")
    assert bob.verification_status == "unverified"
    assert bob.role_title is None
