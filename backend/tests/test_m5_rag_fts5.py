from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.m4 import Company, CompanyResearch, EvidenceLink, HiringSignal, JobOpportunity, SourceEvidence
from app.models.m5 import EvidenceDocument
from app.repositories.m4_repository import M4Repository
from app.services.evidence_documents import (
    EvidenceDocumentNormalizer,
    delete_evidence_document,
    rebuild_fts_index,
)
from app.services.fts_retriever import FoundryLangChainRetriever, SQLiteFTSRetriever


def _seed_two_companies(db: Session) -> tuple[Company, Company, SourceEvidence, SourceEvidence]:
    now = datetime(2026, 11, 20, 12, 0, 0, tzinfo=UTC)

    c1 = Company(
        name="Kestrel Data Systems",
        normalized_name="kestrel data systems",
        normalized_domain="kestreldata.example.com",
        description="Real-time SQLite and DuckDB edge analytics engine.",
        industry="Developer Tools",
        stage="seed",
        tech_stack=["Python", "SQLite", "FastAPI"],
        opportunity_type="active",
        research_status="completed",
        data_origin="demo",
    )
    c2 = Company(
        name="HarborPay Ledger",
        normalized_name="harborpay ledger",
        normalized_domain="harborpay.example.com",
        description="Cross-border treasury reconciliation API.",
        industry="FinTech",
        stage="series_b",
        tech_stack=["Go", "TypeScript", "PostgreSQL"],
        opportunity_type="unknown",
        research_status="completed",
        data_origin="demo",
    )
    db.add_all([c1, c2])
    db.flush()

    ev1 = M4Repository.get_or_create_evidence(
        db,
        source_url="https://kestreldata.example.com/careers/backend",
        source_title="Kestrel Careers (Demo)",
        source_domain="kestreldata.example.com",
        source_type="demo",
        publication_date=now - timedelta(days=5),
        retrieved_at=now,
        excerpt="Hiring Backend Systems Engineer with Python and SQLite expertise.",
        verification_status="verified",
        data_origin="demo",
    )
    ev2 = M4Repository.get_or_create_evidence(
        db,
        source_url="https://harborpay.example.com/news/series-b",
        source_title="HarborPay News (Demo)",
        source_domain="harborpay.example.com",
        source_type="demo",
        publication_date=now - timedelta(days=30),
        retrieved_at=now,
        excerpt="HarborPay raised Series B for Go treasury settlement API.",
        verification_status="unverified",
        data_origin="demo",
    )
    M4Repository.link_evidence(db, "company", c1.id, ev1.id)
    M4Repository.link_evidence(db, "company", c2.id, ev2.id)

    job1 = JobOpportunity(
        company_id=c1.id,
        title="Backend Systems Engineer",
        job_url="https://kestreldata.example.com/careers/backend",
        location="San Francisco, CA",
        employment_type="Full-time",
        posting_date=now - timedelta(days=5),
        verification_status="verified",
        is_active=True,
        data_origin="demo",
    )
    db.add(job1)
    db.flush()
    M4Repository.link_evidence(db, "job_opportunity", job1.id, ev1.id)

    res2 = CompanyResearch(
        company_id=c2.id,
        summary="HarborPay builds multi-currency treasury settlement in Go.",
        status="completed",
        data_origin="demo",
    )
    db.add(res2)
    db.flush()
    M4Repository.link_evidence(db, "company_research", res2.id, ev2.id)
    db.commit()

    return c1, c2, ev1, ev2


def test_fts5_keyword_phrase_company_isolation_and_filters(db_session: Session) -> None:
    c1, c2, ev1, ev2 = _seed_two_companies(db_session)
    normalizer = EvidenceDocumentNormalizer()
    docs1 = normalizer.index_company(db_session, c1)
    docs2 = normalizer.index_company(db_session, c2)
    db_session.commit()

    assert len(docs1) >= 2
    assert len(docs2) >= 2

    retriever = SQLiteFTSRetriever(db_session)

    # Exact keyword retrieval
    python_hits = retriever.retrieve(query="Python SQLite", company_id=c1.id)
    assert len(python_hits) >= 1
    assert all(hit.company_id == c1.id for hit in python_hits)
    assert all(hit.source_evidence_id == ev1.id for hit in python_hits)
    assert all(hit.data_origin == "demo" for hit in python_hits)

    # Phrase retrieval
    phrase_hits = retriever.retrieve(query='"Backend Systems Engineer"', company_id=c1.id)
    assert len(phrase_hits) >= 1
    assert any("Backend Systems Engineer" in hit.content or "Backend Systems Engineer" in hit.document_title for hit in phrase_hits)

    # Company isolation
    cross_hits = retriever.retrieve(query="Python SQLite", company_id=c2.id)
    assert cross_hits == []

    # Entity type filter
    job_only = retriever.retrieve(query="Backend", company_id=c1.id, entity_types=["job_opportunity"])
    assert len(job_only) == 1
    assert job_only[0].entity_type == "job_opportunity"

    # Verification status filter
    verified_c2 = retriever.retrieve(query="treasury", company_id=c2.id, verification_status="verified")
    assert verified_c2 == []
    unverified_c2 = retriever.retrieve(query="treasury", company_id=c2.id, verification_status="unverified")
    assert len(unverified_c2) >= 1

    # Demo-data filter
    real_only = retriever.retrieve(query="Python", company_id=c1.id, data_origin="real")
    assert real_only == []
    demo_only = retriever.retrieve(query="Python", company_id=c1.id, data_origin="demo")
    assert len(demo_only) >= 1


def test_fts5_invalid_syntax_empty_and_langchain_retriever(db_session: Session) -> None:
    c1, _c2, _ev1, _ev2 = _seed_two_companies(db_session)
    normalizer = EvidenceDocumentNormalizer()
    normalizer.index_company(db_session, c1)
    db_session.commit()

    # Strict syntax mode should catch OperationalError safely and return []
    strict_retriever = SQLiteFTSRetriever(db_session, strict_fts_syntax=True)
    assert strict_retriever.retrieve(query='AND OR "unclosed') == []
    assert strict_retriever.retrieve(query="***:::") == []

    # Sanitized mode handles messy input safely without raising
    safe_retriever = SQLiteFTSRetriever(db_session)
    assert safe_retriever.retrieve(query="   ") == []
    assert safe_retriever.retrieve(query="nonexistent_token_xyz") == []
    messy_hits = safe_retriever.retrieve(query='Python (AND) "unclosed', company_id=c1.id)
    assert len(messy_hits) >= 1

    # LangChain BaseRetriever adapter
    lc_retriever = FoundryLangChainRetriever(retriever=safe_retriever, company_id=c1.id, limit=5)
    lc_docs = lc_retriever.invoke("Python SQLite")
    assert len(lc_docs) >= 1
    assert lc_docs[0].metadata["company_id"] == c1.id
    assert "source_evidence_id" in lc_docs[0].metadata


def test_fts5_dedup_update_delete_and_rebuild(db_session: Session) -> None:
    c1, _c2, _ev1, _ev2 = _seed_two_companies(db_session)
    normalizer = EvidenceDocumentNormalizer()

    # Indexing twice does not create duplicate EvidenceDocuments or FTS rows
    normalizer.index_company(db_session, c1)
    normalizer.index_company(db_session, c1)
    db_session.commit()

    doc_count = len(list(db_session.scalars(select(EvidenceDocument).where(EvidenceDocument.company_id == c1.id)).all()))
    fts_count = db_session.execute(
        text("SELECT count(*) FROM evidence_documents_fts WHERE company_id = :cid"),
        {"cid": c1.id},
    ).scalar_one()
    assert doc_count == fts_count

    # Update company description and re-index
    c1.description = "Updated edge analytics with DuckDB and Arrow."
    db_session.flush()
    normalizer.index_company(db_session, c1)
    db_session.commit()

    retriever = SQLiteFTSRetriever(db_session)
    assert len(retriever.retrieve(query="Arrow", company_id=c1.id)) >= 1

    # Rebuild index is idempotent
    rebuilt = rebuild_fts_index(db_session)
    db_session.commit()
    assert rebuilt == doc_count
    fts_after_rebuild = db_session.execute(
        text("SELECT count(*) FROM evidence_documents_fts WHERE company_id = :cid"),
        {"cid": c1.id},
    ).scalar_one()
    assert fts_after_rebuild == doc_count

    # Delete a document and verify FTS removal
    first_doc = db_session.scalars(select(EvidenceDocument).where(EvidenceDocument.company_id == c1.id)).first()
    assert first_doc is not None
    deleted = delete_evidence_document(db_session, first_doc.id)
    db_session.commit()
    assert deleted is True
    fts_after_delete = db_session.execute(
        text("SELECT count(*) FROM evidence_documents_fts WHERE document_id = :did"),
        {"did": first_doc.id},
    ).scalar_one()
    assert fts_after_delete == 0
