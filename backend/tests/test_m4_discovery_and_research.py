from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.candidate import Candidate
from app.models.candidate_profile import CandidateProfile
from app.models.m4 import Company, SourceEvidence
from app.providers.m4_base import (
    CompanyResearchDTO,
    CompanyResearchProvider,
    DiscoveredStartupDTO,
    M4ProviderError,
    ResearchClaimDTO,
    StartupDiscoveryProvider,
)
from app.providers.m4_demo import (
    DemoCompanyResearchProvider,
    DemoFounderProvider,
    DemoFundingProvider,
    DemoHiringSignalProvider,
    DemoStartupDiscoveryProvider,
)
from app.repositories.m4_repository import M4Repository
from app.schemas.candidate_profile import BasicInfo, SkillItem, StructuredCandidateProfile
from app.schemas.m4 import DiscoveryCriteriaRequest, SourceEvidenceInput
from app.services.candidate_profile_service import CandidateNotFoundError, ProfileNotFoundError
from app.services.company_identity import resolve_or_create_company
from app.services.company_research_service import run_company_research
from app.services.discovery_orchestrator import run_startup_discovery_pipeline


def _ev(url: str, title: str, domain: str, excerpt: str) -> SourceEvidenceInput:
    return SourceEvidenceInput(
        source_url=url,  # type: ignore[arg-type]
        source_title=title,
        source_domain=domain,
        source_type="official_website",
        retrieved_at=datetime.now(UTC),
        excerpt=excerpt,
        verification_status="verified",
        data_origin="demo",
    )


def _create_candidate_with_profile(db: Session) -> Candidate:
    cand = Candidate(
        input_source="resume_pdf",
        resume_filename="resume.pdf",
        resume_content_type="application/pdf",
        resume_size_bytes=123,
        resume_storage_key="abc.pdf",
    )
    db.add(cand)
    db.flush()
    prof = StructuredCandidateProfile(
        basic_info=BasicInfo(full_name="Jordan Lee"),
        skills=[SkillItem(name="Python", category="programming_languages")],
    )
    db.add(
        CandidateProfile(
            candidate_id=cand.id,
            extraction_status="extracted",
            source_type="resume_pdf",
            data_origin="demo",
            provider_name="demo",
            warnings=[],
            profile_data=prof.model_dump(mode="json"),
        )
    )
    db.commit()
    return cand


def test_discovery_missing_candidate_and_missing_profile(db_session: Session, test_settings: Settings) -> None:
    with pytest.raises(CandidateNotFoundError):
        run_startup_discovery_pipeline(
            db_session,
            test_settings,
            DiscoveryCriteriaRequest(candidate_id="missing-cand"),
        )

    cand = Candidate(input_source="linkedin_url", linkedin_url="https://www.linkedin.com/in/no-profile")
    db_session.add(cand)
    db_session.commit()

    with pytest.raises(ProfileNotFoundError):
        run_startup_discovery_pipeline(
            db_session,
            test_settings,
            DiscoveryCriteriaRequest(candidate_id=cand.id),
        )


def test_discovery_empty_provider_response_completes_with_warnings(
    db_session: Session,
    test_settings: Settings,
) -> None:
    cand = _create_candidate_with_profile(db_session)

    class EmptyDiscovery(StartupDiscoveryProvider):
        def discover_startups(self, query):
            return []

    resp = run_startup_discovery_pipeline(
        db_session,
        test_settings,
        DiscoveryCriteriaRequest(candidate_id=cand.id),
        discovery_provider=EmptyDiscovery(),
    )
    assert resp.status == "completed_with_warnings"
    assert resp.discovered_count == 0
    assert resp.warnings


def test_discovery_deduplication_and_similar_names_different_domains(db_session: Session) -> None:
    # Same domain -> merged into one company
    c1, created1 = resolve_or_create_company(
        db_session,
        DiscoveredStartupDTO(
            name="Acme AI Inc.",
            official_website="https://www.acme-ai.example.com/about",
            evidence=[_ev("https://acme-ai.example.com", "Acme", "acme-ai.example.com", "Acme AI")],
        ),
    )
    c2, created2 = resolve_or_create_company(
        db_session,
        DiscoveredStartupDTO(
            name="Acme AI",
            official_website="https://acme-ai.example.com",
            industry="AI",
            evidence=[_ev("https://acme-ai.example.com/blog", "Acme Blog", "acme-ai.example.com", "Blog")],
        ),
    )
    assert created1 is True
    assert created2 is False
    assert c1.id == c2.id

    # Similar name but different domain -> NOT merged
    c3, created3 = resolve_or_create_company(
        db_session,
        DiscoveredStartupDTO(
            name="Acme AI",
            official_website="https://acme-robotics.example.com",
        ),
    )
    assert created3 is True
    assert c3.id != c1.id


def test_discovery_provider_failure_and_partial_subprovider_resilience(
    db_session: Session,
    test_settings: Settings,
) -> None:
    cand = _create_candidate_with_profile(db_session)

    class BrokenDiscovery(StartupDiscoveryProvider):
        def discover_startups(self, query):
            raise M4ProviderError("TIMEOUT", "Discovery timed out.", status_code=504)

    with pytest.raises(M4ProviderError):
        run_startup_discovery_pipeline(
            db_session,
            test_settings,
            DiscoveryCriteriaRequest(candidate_id=cand.id),
            discovery_provider=BrokenDiscovery(),
        )

    class BrokenResearch(CompanyResearchProvider):
        def research_company(self, company):
            raise M4ProviderError("UPSTREAM_500", "Research provider failed.")

    resp = run_startup_discovery_pipeline(
        db_session,
        test_settings,
        DiscoveryCriteriaRequest(candidate_id=cand.id, max_companies=2),
        discovery_provider=DemoStartupDiscoveryProvider(),
        research_provider=BrokenResearch(),
        funding_provider=DemoFundingProvider(),
        hiring_provider=DemoHiringSignalProvider(),
        founder_provider=DemoFounderProvider(),
    )
    assert resp.status == "completed_with_warnings"
    assert resp.discovered_count == 2
    assert any("Research failed" in w for w in resp.warnings)


def test_company_research_conflicts_duplicate_evidence_and_repeat_research(db_session: Session) -> None:
    company, _ = resolve_or_create_company(
        db_session,
        DiscoveredStartupDTO(name="ConflictCorp", official_website="https://conflict.example.com"),
    )

    ev1 = _ev("https://conflict.example.com/a", "Source A", "conflict.example.com", "HQ in Austin")
    ev2 = _ev("https://news.example.com/b", "Source B", "news.example.com", "HQ in Miami")

    class ConflictingResearchProvider(CompanyResearchProvider):
        def research_company(self, company_dto):
            return CompanyResearchDTO(
                summary="Conflicting HQ data",
                claims=[
                    ResearchClaimDTO(field_name="headquarters", value="Austin, TX", evidence=ev1),
                    ResearchClaimDTO(field_name="headquarters", value="Miami, FL", evidence=ev2),
                ],
                evidence=[ev1, ev1],  # duplicate evidence
            )

    r1 = run_company_research(db_session, company, ConflictingResearchProvider())
    r2 = run_company_research(db_session, company, DemoCompanyResearchProvider())
    db_session.commit()

    assert r1.status == "requires_review"
    assert len(r1.conflicts) == 1
    assert r1.conflicts[0]["field_name"] == "headquarters"
    assert r2.id != r1.id
    assert db_session.query(SourceEvidence).filter(SourceEvidence.source_url == "https://conflict.example.com/a").count() == 1
    assert len(M4Repository.list_companies(db_session)[0]) == 1
