from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
import re
from typing import Any

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.schemas.m4 import DataOrigin, VerificationStatus
from app.schemas.m5 import RetrievedEvidenceItem
from app.services.evidence_documents import ensure_fts_table


def sanitize_fts5_query(raw_query: str) -> str:
    """Convert arbitrary user/profile text into a safe FTS5 query string.

    Preserves explicit double-quoted phrases when balanced and non-empty,
    and quotes individual alphanumeric tokens joined with OR for lexical recall
    without exposing FTS5 operator syntax errors.
    """
    cleaned = raw_query.strip()
    if not cleaned:
        return ""

    # Extract balanced quoted phrases first
    phrases = [
        p.strip()
        for p in re.findall(r'"([^"]+)"', cleaned)
        if re.search(r"[A-Za-z0-9]", p)
    ]
    remainder = re.sub(r'"[^"]*"', " ", cleaned)

    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9._+-]*", remainder)
    terms: list[str] = []
    seen: set[str] = set()

    for phrase in phrases:
        safe_phrase = phrase.replace('"', " ").strip()
        if safe_phrase:
            key = f'"{safe_phrase}"'
            if key.lower() not in seen:
                seen.add(key.lower())
                terms.append(key)

    for tok in tokens:
        # Quote every token so FTS5 reserved keywords (AND, OR, NOT, NEAR) or punctuation never break syntax
        quoted = f'"{tok}"'
        if quoted.lower() not in seen:
            seen.add(quoted.lower())
            terms.append(quoted)

    return " OR ".join(terms)


class EvidenceRetriever(ABC):
    """Replaceable retriever interface for company evidence."""

    @abstractmethod
    def retrieve(
        self,
        *,
        query: str,
        company_id: str | None = None,
        entity_types: Sequence[str] | None = None,
        verification_status: VerificationStatus | None = None,
        data_origin: DataOrigin | None = None,
        published_after: datetime | None = None,
        limit: int = 12,
    ) -> list[RetrievedEvidenceItem]:
        """Retrieve relevant evidence items matching the query and filters."""


class SQLiteFTSRetriever(EvidenceRetriever):
    """Lexical SQLite FTS5 retriever with metadata filtering and M4 provenance."""

    def __init__(self, db: Session, *, strict_fts_syntax: bool = False) -> None:
        self.db = db
        self.strict_fts_syntax = strict_fts_syntax

    def retrieve(
        self,
        *,
        query: str,
        company_id: str | None = None,
        entity_types: Sequence[str] | None = None,
        verification_status: VerificationStatus | None = None,
        data_origin: DataOrigin | None = None,
        published_after: datetime | None = None,
        limit: int = 12,
    ) -> list[RetrievedEvidenceItem]:
        ensure_fts_table(self.db)
        bounded_limit = max(1, min(limit, 50))

        fts_query = query.strip() if self.strict_fts_syntax else sanitize_fts5_query(query)
        if not fts_query:
            return []

        where_clauses = ["evidence_documents_fts MATCH :fts_query"]
        params: dict[str, Any] = {
            "fts_query": fts_query,
            "limit": bounded_limit,
        }

        if company_id is not None:
            where_clauses.append("ed.company_id = :company_id")
            params["company_id"] = company_id

        if verification_status is not None:
            where_clauses.append("ed.verification_status = :verification_status")
            params["verification_status"] = verification_status

        if data_origin is not None:
            where_clauses.append("ed.data_origin = :data_origin")
            params["data_origin"] = data_origin

        if published_after is not None:
            where_clauses.append("ed.publication_date IS NOT NULL AND ed.publication_date >= :published_after")
            params["published_after"] = published_after

        if entity_types:
            clean_types = [t.strip() for t in entity_types if t and t.strip()]
            if not clean_types:
                return []
            placeholders = []
            for idx, etype in enumerate(clean_types):
                key = f"etype_{idx}"
                placeholders.append(f":{key}")
                params[key] = etype
            where_clauses.append(f"ed.entity_type IN ({', '.join(placeholders)})")

        sql = f"""
            SELECT
                ed.id AS evidence_document_id,
                ed.source_evidence_id AS source_evidence_id,
                ed.company_id AS company_id,
                ed.entity_type AS entity_type,
                ed.document_title AS document_title,
                ed.normalized_content AS content,
                se.source_url AS source_url,
                se.source_title AS source_title,
                ed.publication_date AS publication_date,
                ed.retrieved_at AS retrieved_at,
                ed.verification_status AS verification_status,
                ed.data_origin AS data_origin,
                bm25(evidence_documents_fts) AS bm25_score
            FROM evidence_documents_fts
            JOIN evidence_documents ed ON ed.id = evidence_documents_fts.document_id
            JOIN source_evidence se ON se.id = ed.source_evidence_id
            WHERE {' AND '.join(where_clauses)}
            ORDER BY bm25(evidence_documents_fts) ASC, ed.created_at DESC
            LIMIT :limit
        """

        try:
            rows = self.db.execute(text(sql), params).mappings().all()
        except OperationalError:
            return []

        results: list[RetrievedEvidenceItem] = []
        for row in rows:
            pub_dt = row["publication_date"]
            ret_dt = row["retrieved_at"]
            if isinstance(pub_dt, str):
                pub_dt = datetime.fromisoformat(pub_dt)
            if isinstance(ret_dt, str):
                ret_dt = datetime.fromisoformat(ret_dt)

            results.append(
                RetrievedEvidenceItem(
                    evidence_document_id=row["evidence_document_id"],
                    source_evidence_id=row["source_evidence_id"],
                    company_id=row["company_id"],
                    entity_type=row["entity_type"],
                    document_title=row["document_title"],
                    content=row["content"],
                    source_url=row["source_url"],
                    source_title=row["source_title"],
                    publication_date=pub_dt,
                    retrieved_at=ret_dt,
                    verification_status=row["verification_status"],
                    data_origin=row["data_origin"],
                    bm25_score=float(row["bm25_score"]) if row["bm25_score"] is not None else None,
                )
            )
        return results


class FoundryLangChainRetriever(BaseRetriever):
    """LangChain BaseRetriever adapter delegating to EvidenceRetriever."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    retriever: EvidenceRetriever
    company_id: str | None = None
    entity_types: list[str] | None = None
    verification_status: VerificationStatus | None = None
    data_origin: DataOrigin | None = None
    limit: int = 12

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun | None = None,
    ) -> list[Document]:
        items = self.retriever.retrieve(
            query=query,
            company_id=self.company_id,
            entity_types=self.entity_types,
            verification_status=self.verification_status,
            data_origin=self.data_origin,
            limit=self.limit,
        )
        return [
            Document(
                page_content=item.content,
                metadata={
                    "evidence_document_id": item.evidence_document_id,
                    "source_evidence_id": item.source_evidence_id,
                    "company_id": item.company_id,
                    "entity_type": item.entity_type,
                    "document_title": item.document_title,
                    "source_url": item.source_url,
                    "source_title": item.source_title,
                    "publication_date": item.publication_date.isoformat() if item.publication_date else None,
                    "retrieved_at": item.retrieved_at.isoformat(),
                    "verification_status": item.verification_status,
                    "data_origin": item.data_origin,
                    "bm25_score": item.bm25_score,
                },
            )
            for item in items
        ]
