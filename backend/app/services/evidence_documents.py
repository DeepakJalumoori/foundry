from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime
import hashlib
import re
from typing import Any

from langchain_core.documents import Document
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.m4 import (
    Company,
    CompanyResearch,
    EvidenceLink,
    Founder,
    FundingEvent,
    HiringSignal,
    JobOpportunity,
    SourceEvidence,
)
from app.models.m5 import EvidenceDocument, FTS5_CREATE_SQL

MAX_CHUNK_CHARS = 1500
CHUNK_OVERLAP = 150


def normalize_text(value: str | None) -> str:
    """Collapse excessive whitespace while preserving readable text."""
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def compute_document_hash(
    *,
    document_title: str,
    normalized_content: str,
    source_evidence_id: str,
    verification_status: str,
    data_origin: str,
) -> str:
    payload = "|".join(
        [
            source_evidence_id,
            verification_status,
            data_origin,
            document_title,
            normalized_content,
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def chunk_text(content: str, max_chars: int = MAX_CHUNK_CHARS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split long content into bounded chunks without losing provenance."""
    cleaned = normalize_text(content)
    if not cleaned:
        return []
    if len(cleaned) <= max_chars:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    step = max(1, max_chars - overlap)
    while start < len(cleaned):
        end = min(len(cleaned), start + max_chars)
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(cleaned):
            break
        start += step
    return chunks


def ensure_fts_table(db: Session) -> None:
    """Ensure the SQLite FTS5 virtual table exists."""
    db.execute(text(FTS5_CREATE_SQL))


def sync_fts_upsert(db: Session, doc: EvidenceDocument) -> None:
    """Insert or replace a single EvidenceDocument row in the FTS5 index."""
    ensure_fts_table(db)
    db.execute(
        text("DELETE FROM evidence_documents_fts WHERE document_id = :document_id"),
        {"document_id": doc.id},
    )
    db.execute(
        text(
            """
            INSERT INTO evidence_documents_fts (
                document_id,
                source_evidence_id,
                company_id,
                entity_type,
                verification_status,
                data_origin,
                document_title,
                normalized_content
            ) VALUES (
                :document_id,
                :source_evidence_id,
                :company_id,
                :entity_type,
                :verification_status,
                :data_origin,
                :document_title,
                :normalized_content
            )
            """
        ),
        {
            "document_id": doc.id,
            "source_evidence_id": doc.source_evidence_id,
            "company_id": doc.company_id,
            "entity_type": doc.entity_type,
            "verification_status": doc.verification_status,
            "data_origin": doc.data_origin,
            "document_title": doc.document_title,
            "normalized_content": doc.normalized_content,
        },
    )


def sync_fts_delete(db: Session, document_id: str) -> None:
    """Remove a document row from the FTS5 index."""
    ensure_fts_table(db)
    db.execute(
        text("DELETE FROM evidence_documents_fts WHERE document_id = :document_id"),
        {"document_id": document_id},
    )


def delete_evidence_document(db: Session, document_id: str) -> bool:
    """Delete an EvidenceDocument and remove it from the FTS5 index."""
    doc = db.get(EvidenceDocument, document_id)
    if doc is None:
        sync_fts_delete(db, document_id)
        return False
    sync_fts_delete(db, document_id)
    db.delete(doc)
    db.flush()
    return True


def rebuild_fts_index(db: Session) -> int:
    """Idempotently rebuild the entire FTS5 index from evidence_documents."""
    ensure_fts_table(db)
    db.execute(text("DELETE FROM evidence_documents_fts"))
    docs = list(db.scalars(select(EvidenceDocument)).all())
    for doc in docs:
        db.execute(
            text(
                """
                INSERT INTO evidence_documents_fts (
                    document_id,
                    source_evidence_id,
                    company_id,
                    entity_type,
                    verification_status,
                    data_origin,
                    document_title,
                    normalized_content
                ) VALUES (
                    :document_id,
                    :source_evidence_id,
                    :company_id,
                    :entity_type,
                    :verification_status,
                    :data_origin,
                    :document_title,
                    :normalized_content
                )
                """
            ),
            {
                "document_id": doc.id,
                "source_evidence_id": doc.source_evidence_id,
                "company_id": doc.company_id,
                "entity_type": doc.entity_type,
                "verification_status": doc.verification_status,
                "data_origin": doc.data_origin,
                "document_title": doc.document_title,
                "normalized_content": doc.normalized_content,
            },
        )
    db.flush()
    return len(docs)


def to_langchain_documents(docs: Sequence[EvidenceDocument]) -> list[Document]:
    """Convert EvidenceDocument ORM records into LangChain Document objects."""
    lc_docs: list[Document] = []
    for doc in docs:
        meta = dict(doc.metadata_json or {})
        meta.update(
            {
                "evidence_document_id": doc.id,
                "source_evidence_id": doc.source_evidence_id,
                "company_id": doc.company_id,
                "entity_type": doc.entity_type,
                "entity_id": doc.entity_id,
                "chunk_index": doc.chunk_index,
                "document_title": doc.document_title,
                "verification_status": doc.verification_status,
                "data_origin": doc.data_origin,
            }
        )
        lc_docs.append(Document(page_content=doc.normalized_content, metadata=meta))
    return lc_docs


class EvidenceDocumentNormalizer:
    """Normalizes M4 company intelligence and SourceEvidence into EvidenceDocuments."""

    @staticmethod
    def _load_evidence_by_entity(
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
        grouped: dict[str, list[SourceEvidence]] = defaultdict(list)
        for ent_id, ev in db.execute(stmt).all():
            grouped[ent_id].append(ev)
        return grouped

    def _upsert_entity_documents(
        self,
        db: Session,
        *,
        company: Company,
        entity_type: str,
        entity_id: str,
        title: str,
        raw_content: str,
        evidence_items: list[SourceEvidence],
        extra_metadata: dict[str, Any] | None = None,
    ) -> list[EvidenceDocument]:
        if not evidence_items:
            return []
        primary_ev = evidence_items[0]
        chunks = chunk_text(raw_content)
        if not chunks:
            return []

        now = datetime.now(UTC)
        persisted: list[EvidenceDocument] = []

        existing_rows = list(
            db.scalars(
                select(EvidenceDocument).where(
                    EvidenceDocument.company_id == company.id,
                    EvidenceDocument.entity_type == entity_type,
                    EvidenceDocument.entity_id == entity_id,
                )
            ).all()
        )
        existing_by_chunk = {row.chunk_index: row for row in existing_rows}

        for idx, chunk in enumerate(chunks):
            doc_title = normalize_text(title)[:500] or f"{company.name} ({entity_type})"
            if len(chunks) > 1:
                doc_title = f"{doc_title[:485]} [part {idx + 1}]"

            verification_status = primary_ev.verification_status
            data_origin = primary_ev.data_origin
            content_hash = compute_document_hash(
                document_title=doc_title,
                normalized_content=chunk,
                source_evidence_id=primary_ev.id,
                verification_status=verification_status,
                data_origin=data_origin,
            )
            metadata_json: dict[str, Any] = {
                "company_name": company.name,
                "company_stage": company.stage,
                "company_industry": company.industry,
                "source_url": primary_ev.source_url,
                "source_title": primary_ev.source_title,
                "source_domain": primary_ev.source_domain,
                "source_type": primary_ev.source_type,
                "publication_date": primary_ev.publication_date.isoformat() if primary_ev.publication_date else None,
                "retrieved_at": primary_ev.retrieved_at.isoformat() if primary_ev.retrieved_at else now.isoformat(),
                "linked_evidence_ids": [ev.id for ev in evidence_items],
            }
            if extra_metadata:
                metadata_json.update(extra_metadata)

            existing = existing_by_chunk.pop(idx, None)
            if existing is not None:
                if (
                    existing.content_hash == content_hash
                    and existing.metadata_json == metadata_json
                ):
                    persisted.append(existing)
                    continue
                existing.source_evidence_id = primary_ev.id
                existing.document_title = doc_title
                existing.normalized_content = chunk
                existing.metadata_json = metadata_json
                existing.verification_status = verification_status
                existing.data_origin = data_origin
                existing.publication_date = primary_ev.publication_date
                existing.retrieved_at = primary_ev.retrieved_at
                existing.content_hash = content_hash
                existing.updated_at = now
                db.flush()
                sync_fts_upsert(db, existing)
                persisted.append(existing)
            else:
                doc = EvidenceDocument(
                    source_evidence_id=primary_ev.id,
                    company_id=company.id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    chunk_index=idx,
                    document_title=doc_title,
                    normalized_content=chunk,
                    metadata_json=metadata_json,
                    verification_status=verification_status,
                    data_origin=data_origin,
                    publication_date=primary_ev.publication_date,
                    retrieved_at=primary_ev.retrieved_at,
                    content_hash=content_hash,
                )
                db.add(doc)
                db.flush()
                sync_fts_upsert(db, doc)
                persisted.append(doc)

        # Clean up obsolete chunks if content shrank
        for stale in existing_by_chunk.values():
            sync_fts_delete(db, stale.id)
            db.delete(stale)
        db.flush()

        return persisted

    def index_company(self, db: Session, company: Company) -> list[EvidenceDocument]:
        """Normalize and index all eligible M4 records for a single company."""
        ensure_fts_table(db)
        docs: list[EvidenceDocument] = []

        # 1. Company profile + linked SourceEvidence
        company_ev = self._load_evidence_by_entity(db, "company", [company.id]).get(company.id, [])
        if company_ev:
            tech = ", ".join(company.tech_stack or [])
            profile_text = " ".join(
                part
                for part in [
                    f"Company: {company.name}.",
                    f"Stage: {company.stage}." if company.stage else "",
                    f"Industry: {company.industry}." if company.industry else "",
                    f"Description: {company.description}" if company.description else "",
                    f"Product: {company.product_or_service}" if company.product_or_service else "",
                    f"Tech stack: {tech}." if tech else "",
                    f"Headquarters: {company.headquarters}." if company.headquarters else "",
                ]
                if part
            )
            docs.extend(
                self._upsert_entity_documents(
                    db,
                    company=company,
                    entity_type="company",
                    entity_id=company.id,
                    title=f"{company.name} — Company Overview",
                    raw_content=profile_text,
                    evidence_items=company_ev,
                )
            )

        # 2. CompanyResearch
        research_rows = list(
            db.scalars(select(CompanyResearch).where(CompanyResearch.company_id == company.id)).all()
        )
        research_ev_map = self._load_evidence_by_entity(
            db, "company_research", [r.id for r in research_rows]
        )
        for res in research_rows:
            ev_list = research_ev_map.get(res.id, []) or company_ev
            claims_text = " ".join(
                str(c.get("claim", "")) for c in (res.raw_claims or []) if isinstance(c, dict)
            )
            body = " ".join(part for part in [res.summary or "", claims_text] if part)
            docs.extend(
                self._upsert_entity_documents(
                    db,
                    company=company,
                    entity_type="company_research",
                    entity_id=res.id,
                    title=f"{company.name} — Company Research",
                    raw_content=body,
                    evidence_items=ev_list,
                )
            )

        # 3. FundingEvent
        funding_rows = list(
            db.scalars(select(FundingEvent).where(FundingEvent.company_id == company.id)).all()
        )
        funding_ev_map = self._load_evidence_by_entity(
            db, "funding_event", [f.id for f in funding_rows]
        )
        for fe in funding_rows:
            ev_list = funding_ev_map.get(fe.id, []) or company_ev
            investors = ", ".join(fe.investors or [])
            amount_str = f"{fe.amount} {fe.currency or ''}".strip() if fe.amount is not None else "undisclosed"
            body = " ".join(
                part
                for part in [
                    f"Funding round: {fe.round_type}, amount: {amount_str}.",
                    f"Lead investor: {fe.lead_investor}." if fe.lead_investor else "",
                    f"Investors: {investors}." if investors else "",
                    fe.normalized_summary or fe.original_claim or "",
                ]
                if part
            )
            docs.extend(
                self._upsert_entity_documents(
                    db,
                    company=company,
                    entity_type="funding_event",
                    entity_id=fe.id,
                    title=f"{company.name} — Funding ({fe.round_type})",
                    raw_content=body,
                    evidence_items=ev_list,
                    extra_metadata={"round_type": fe.round_type},
                )
            )

        # 4. HiringSignal
        signal_rows = list(
            db.scalars(select(HiringSignal).where(HiringSignal.company_id == company.id)).all()
        )
        signal_ev_map = self._load_evidence_by_entity(
            db, "hiring_signal", [s.id for s in signal_rows]
        )
        for sig in signal_rows:
            ev_list = signal_ev_map.get(sig.id, []) or company_ev
            roles = ", ".join(sig.role_titles or [])
            body = " ".join(
                part
                for part in [
                    f"Hiring signal ({sig.opportunity_category}, {sig.signal_type}): {sig.title}.",
                    f"Observed fact: {sig.observed_fact}",
                    f"Description: {sig.description}" if sig.description else "",
                    f"Roles: {roles}." if roles else "",
                    f"Department: {sig.department}." if sig.department else "",
                ]
                if part
            )
            docs.extend(
                self._upsert_entity_documents(
                    db,
                    company=company,
                    entity_type="hiring_signal",
                    entity_id=sig.id,
                    title=f"{company.name} — {sig.title}",
                    raw_content=body,
                    evidence_items=ev_list,
                    extra_metadata={"opportunity_category": sig.opportunity_category},
                )
            )

        # 5. JobOpportunity
        job_rows = list(
            db.scalars(select(JobOpportunity).where(JobOpportunity.company_id == company.id)).all()
        )
        job_ev_map = self._load_evidence_by_entity(
            db, "job_opportunity", [j.id for j in job_rows]
        )
        for job in job_rows:
            ev_list = job_ev_map.get(job.id, []) or company_ev
            body = " ".join(
                part
                for part in [
                    f"Job opening: {job.title}.",
                    f"Location: {job.location}." if job.location else "",
                    f"Employment type: {job.employment_type}." if job.employment_type else "",
                    f"Active: {'yes' if job.is_active else 'no'}.",
                    f"URL: {job.job_url}",
                ]
                if part
            )
            docs.extend(
                self._upsert_entity_documents(
                    db,
                    company=company,
                    entity_type="job_opportunity",
                    entity_id=job.id,
                    title=f"{company.name} — Job: {job.title}",
                    raw_content=body,
                    evidence_items=ev_list,
                    extra_metadata={"is_active": job.is_active, "job_url": job.job_url},
                )
            )

        # 6. Founder
        founder_rows = list(
            db.scalars(select(Founder).where(Founder.company_id == company.id)).all()
        )
        founder_ev_map = self._load_evidence_by_entity(
            db, "founder", [f.id for f in founder_rows]
        )
        for fnd in founder_rows:
            ev_list = founder_ev_map.get(fnd.id, []) or company_ev
            body = " ".join(
                part
                for part in [
                    f"Founder: {fnd.full_name}",
                    f"Role: {fnd.role_title}." if fnd.role_title else "",
                    f"Bio: {fnd.biography}" if fnd.biography else "",
                ]
                if part
            )
            docs.extend(
                self._upsert_entity_documents(
                    db,
                    company=company,
                    entity_type="founder",
                    entity_id=fnd.id,
                    title=f"{company.name} — Founder: {fnd.full_name}",
                    raw_content=body,
                    evidence_items=ev_list,
                )
            )

        return docs
