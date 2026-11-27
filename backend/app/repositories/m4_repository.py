from collections import defaultdict
from datetime import UTC, datetime
import hashlib
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.m4 import (
    Company,
    CompanyResearch,
    DiscoveryRun,
    EvidenceLink,
    Founder,
    FundingEvent,
    HiringSignal,
    JobOpportunity,
    SourceEvidence,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def compute_excerpt_hash(excerpt: str | None) -> str:
    text = (excerpt or "").strip()
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class M4Repository:
    """Persistence operations for M4 startup discovery and intelligence entities."""

    @staticmethod
    def get_or_create_evidence(
        db: Session,
        *,
        source_url: str,
        source_title: str,
        source_domain: str,
        source_type: str,
        publication_date: datetime | None,
        retrieved_at: datetime,
        excerpt: str | None,
        verification_status: str,
        data_origin: str,
    ) -> SourceEvidence:
        excerpt_hash = compute_excerpt_hash(excerpt)
        stmt = select(SourceEvidence).where(
            SourceEvidence.source_url == source_url,
            SourceEvidence.excerpt_hash == excerpt_hash,
        )
        existing = db.scalar(stmt)
        if existing is not None:
            return existing

        ev = SourceEvidence(
            source_url=source_url,
            source_title=source_title,
            source_domain=source_domain,
            source_type=source_type,
            publication_date=publication_date,
            retrieved_at=retrieved_at,
            excerpt=excerpt,
            excerpt_hash=excerpt_hash,
            verification_status=verification_status,
            data_origin=data_origin,
        )
        db.add(ev)
        db.flush()
        return ev

    @staticmethod
    def link_evidence(db: Session, entity_type: str, entity_id: str, evidence_id: str) -> None:
        stmt = select(EvidenceLink).where(
            EvidenceLink.entity_type == entity_type,
            EvidenceLink.entity_id == entity_id,
            EvidenceLink.evidence_id == evidence_id,
        )
        if db.scalar(stmt) is None:
            db.add(EvidenceLink(entity_type=entity_type, entity_id=entity_id, evidence_id=evidence_id))
            db.flush()

    @staticmethod
    def get_evidence_map(
        db: Session,
        entity_type: str,
        entity_ids: list[str],
    ) -> dict[str, list[SourceEvidence]]:
        if not entity_ids:
            return {}
        stmt = (
            select(EvidenceLink.entity_id, SourceEvidence)
            .join(SourceEvidence, SourceEvidence.id == EvidenceLink.evidence_id)
            .where(
                EvidenceLink.entity_type == entity_type,
                EvidenceLink.entity_id.in_(entity_ids),
            )
        )
        result: dict[str, list[SourceEvidence]] = defaultdict(list)
        for entity_id, ev in db.execute(stmt).all():
            result[entity_id].append(ev)
        return result

    @staticmethod
    def create_discovery_run(db: Session, candidate_id: str, criteria: dict[str, Any]) -> DiscoveryRun:
        run = DiscoveryRun(
            candidate_id=candidate_id,
            status="pending",
            criteria=criteria,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def get_discovery_run(db: Session, run_id: str) -> DiscoveryRun | None:
        return db.get(DiscoveryRun, run_id)

    @staticmethod
    def mark_discovery_processing(db: Session, run: DiscoveryRun) -> DiscoveryRun:
        run.status = "processing"
        run.started_at = _utc_now()
        run.completed_at = None
        run.error_code = None
        run.error_message = None
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def mark_discovery_completed(
        db: Session,
        run: DiscoveryRun,
        *,
        company_ids: list[str],
        warnings: list[str],
    ) -> DiscoveryRun:
        run.status = "completed_with_warnings" if warnings else "completed"
        run.discovered_count = len(company_ids)
        run.company_ids = company_ids
        run.warnings = warnings
        run.completed_at = _utc_now()
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def mark_discovery_failed(
        db: Session,
        run: DiscoveryRun,
        *,
        error_code: str,
        error_message: str,
    ) -> DiscoveryRun:
        if run.started_at is None:
            run.started_at = _utc_now()
        run.status = "failed"
        run.error_code = error_code[:64]
        run.error_message = error_message
        run.completed_at = _utc_now()
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def get_company_by_id(db: Session, company_id: str) -> Company | None:
        return db.get(Company, company_id)

    @staticmethod
    def get_company_by_domain(db: Session, normalized_domain: str) -> Company | None:
        return db.scalar(select(Company).where(Company.normalized_domain == normalized_domain))

    @staticmethod
    def get_company_by_external_id(db: Session, external_id: str) -> Company | None:
        return db.scalar(select(Company).where(Company.external_id == external_id))

    @staticmethod
    def get_companies_by_normalized_name(db: Session, normalized_name: str) -> list[Company]:
        return list(db.scalars(select(Company).where(Company.normalized_name == normalized_name)).all())

    @staticmethod
    def list_companies(
        db: Session,
        *,
        limit: int = 20,
        offset: int = 0,
        stage: str | None = None,
        opportunity_type: str | None = None,
        industry: str | None = None,
    ) -> tuple[list[Company], int]:
        filters = []
        if stage:
            filters.append(Company.stage == stage)
        if opportunity_type:
            filters.append(Company.opportunity_type == opportunity_type)
        if industry:
            filters.append(func.lower(Company.industry) == industry.strip().lower())

        count_stmt = select(func.count()).select_from(Company).where(*filters)
        total = db.scalar(count_stmt) or 0

        stmt = (
            select(Company)
            .where(*filters)
            .order_by(Company.created_at.desc(), Company.name.asc())
            .limit(limit)
            .offset(offset)
        )
        items = list(db.scalars(stmt).all())
        return items, total

    @staticmethod
    def get_latest_research(db: Session, company_id: str) -> CompanyResearch | None:
        stmt = (
            select(CompanyResearch)
            .where(CompanyResearch.company_id == company_id)
            .order_by(CompanyResearch.researched_at.desc())
            .limit(1)
        )
        return db.scalar(stmt)

    @staticmethod
    def list_funding_events(db: Session, company_id: str) -> list[FundingEvent]:
        stmt = (
            select(FundingEvent)
            .where(FundingEvent.company_id == company_id)
            .order_by(FundingEvent.announced_date.desc().nullslast(), FundingEvent.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def list_hiring_signals(db: Session, company_id: str) -> list[HiringSignal]:
        stmt = (
            select(HiringSignal)
            .where(HiringSignal.company_id == company_id)
            .order_by(HiringSignal.publication_date.desc().nullslast(), HiringSignal.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def list_job_opportunities(db: Session, company_id: str) -> list[JobOpportunity]:
        stmt = (
            select(JobOpportunity)
            .where(JobOpportunity.company_id == company_id)
            .order_by(JobOpportunity.posting_date.desc().nullslast(), JobOpportunity.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def list_founders(db: Session, company_id: str) -> list[Founder]:
        stmt = (
            select(Founder)
            .where(Founder.company_id == company_id)
            .order_by(Founder.created_at.asc())
        )
        return list(db.scalars(stmt).all())
