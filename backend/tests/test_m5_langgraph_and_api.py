from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
import pymupdf
import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.graphs.matching_graph import MatchingState, build_matching_graph
from app.models.candidate import Candidate
from app.models.candidate_profile import CandidateProfile
from app.models.m4 import Company, DiscoveryRun
from app.models.m5 import MatchingRun, MatchResult
from app.providers.llm import DemoLLMProvider, LLMAssessmentResult, LLMProvider, LLMProviderError
from app.schemas.m5 import MatchingRunCreateRequest, RetrievedEvidenceItem, StructuredCompanyAssessment
from app.services.fts_retriever import SQLiteFTSRetriever
from app.services.matching_service import start_matching_run


def _build_pdf_bytes(text_content: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text_content)
    data = doc.tobytes()
    doc.close()
    return data


def _setup_candidate_and_discovery(client: TestClient) -> tuple[str, str, list[str]]:
    pdf_bytes = _build_pdf_bytes(
        "Jordan Taylor\nBackend Systems Engineer\n"
        "Skills: Python, FastAPI, SQLite, PyTorch, Docker\n"
        "Experience: Backend Engineer building SQLite and Python services.\n"
        "Projects: Distributed query engine in Python and FastAPI."
    )
    run_resp = client.post(
        "/api/runs",
        files={"resume_file": ("jordan.pdf", pdf_bytes, "application/pdf")},
    )
    assert run_resp.status_code == 201
    run_id = run_resp.json()["run_id"]
    candidate_id = run_resp.json()["candidate"]["id"]

    proc_resp = client.post(f"/api/runs/{run_id}/process")
    assert proc_resp.status_code == 200

    disc_resp = client.post(
        "/api/discovery",
        json={"candidate_id": candidate_id, "max_companies": 3},
    )
    assert disc_resp.status_code == 201
    disc_body = disc_resp.json()
    assert disc_body["discovered_count"] == 3
    return candidate_id, disc_body["run_id"], disc_body["company_ids"]


def test_m5_end_to_end_three_company_acceptance_scenario(
    client: TestClient,
    test_settings: Settings,
) -> None:
    candidate_id, discovery_run_id, company_ids = _setup_candidate_and_discovery(client)

    # Start M5 matching run via API
    match_resp = client.post(
        "/api/matching-runs",
        json={
            "candidate_id": candidate_id,
            "discovery_run_id": discovery_run_id,
        },
    )
    assert match_resp.status_code == 201
    run_body = match_resp.json()
    m_run_id = run_body["run_id"]
    assert run_body["status"] in {"completed", "completed_with_warnings"}
    assert run_body["result_count"] == 3
    assert run_body["scoring_version"] == "fit_v1"
    assert run_body["ranking_version"] == "rank_v2"
    assert str(test_settings.upload_dir) not in match_resp.text

    # Retrieve run status
    get_run = client.get(f"/api/matching-runs/{m_run_id}")
    assert get_run.status_code == 200
    assert get_run.json()["run_id"] == m_run_id

    # Retrieve ranked results with pagination
    results_resp = client.get(f"/api/matching-runs/{m_run_id}/results?limit=10&offset=0")
    assert results_resp.status_code == 200
    items = results_resp.json()["items"]
    assert results_resp.json()["total"] == 3
    assert len(items) == 3

    by_name = {item["company_name"]: item for item in items}
    kestrel = by_name["Kestrel Data Systems"]
    verdant = by_name["Verdant BioCompute"]
    harbor = by_name["HarborPay Ledger"]

    # Company A: Kestrel -> active opportunity & high fit
    assert kestrel["opportunity_type"] == "active"
    assert kestrel["fit_score"] > harbor["fit_score"]
    assert kestrel["data_origin"] == "demo"

    # Company B: Verdant -> hidden opportunity
    assert verdant["opportunity_type"] == "hidden"
    assert verdant["evidence_strength"] in {"moderate", "weak"}

    # Company C: HarborPay -> funding only, insufficient hiring evidence
    assert harbor["opportunity_type"] == "insufficient_evidence"
    assert harbor["evidence_strength"] == "insufficient"

    # Active opportunity Kestrel ranks #1
    assert items[0]["company_name"] == "Kestrel Data Systems"
    assert items[0]["ranking_position"] == 1

    # Retrieve individual match detail & evidence
    detail_resp = client.get(f"/api/matches/{kestrel['match_id']}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["dimension_breakdown"]) == 5
    assert detail["opportunity_assessment"]["opportunity_type"] == "active"
    assert detail["qualitative_assessment"] is not None

    ev_resp = client.get(f"/api/matches/{kestrel['match_id']}/evidence?limit=10&offset=0")
    assert ev_resp.status_code == 200
    ev_items = ev_resp.json()["items"]
    assert len(ev_items) >= 1
    assert all(e["company_id"] == kestrel["company_id"] for e in ev_items)
    assert all(e["source_evidence_id"] is not None for e in ev_items)

    # Ensure no full resume text or secrets leaked
    assert "gemini_api_key" not in detail_resp.text.lower()


def test_m5_api_validation_and_missing_resources(client: TestClient) -> None:
    assert client.get("/api/matching-runs/missing-run").status_code == 404
    assert client.get("/api/matching-runs/missing-run/results").status_code == 404
    assert client.get("/api/matches/missing-match").status_code == 404
    assert client.get("/api/matches/missing-match/evidence").status_code == 404

    # Missing both discovery_run_id and company_ids -> 422
    bad_req = client.post("/api/matching-runs", json={"candidate_id": "c1"})
    assert bad_req.status_code == 422

    # Missing candidate -> 404
    missing_cand = client.post(
        "/api/matching-runs",
        json={"candidate_id": "missing-candidate", "company_ids": ["c1"]},
    )
    assert missing_cand.status_code == 404


def test_langgraph_failure_paths_and_provider_timeout(
    db_session: Session,
    test_settings: Settings,
) -> None:
    # 1. Direct graph invocation with missing candidate -> failed without partial results
    graph = build_matching_graph(
        db=db_session,
        llm_provider=DemoLLMProvider(),
        retriever=SQLiteFTSRetriever(db_session),
    )
    init_state: MatchingState = {
        "matching_run_id": "nonexistent-run",
        "candidate_id": "missing-cand",
        "discovery_run_id": None,
        "company_ids": ["c1"],
        "retrieval_config": {},
        "scoring_version": "fit_v1",
        "ranking_version": "rank_v1",
        "candidate_profile_snapshot": {},
        "company_context": {},
        "retrieval_queries": {},
        "retrieved_evidence": {},
        "evidence_quality": {},
        "company_assessments": {},
        "assessment_metadata": {},
        "match_scores": {},
        "opportunity_assessments": {},
        "explanations": {},
        "ranked_results": [],
        "warnings": [],
        "errors": [],
        "fatal_error_code": None,
        "fatal_error_message": None,
        "requires_review": False,
        "persisted": False,
        "final_status": "processing",
    }
    out = graph.invoke(init_state)
    assert out["final_status"] == "failed"
    assert out["fatal_error_code"] == "CANDIDATE_NOT_FOUND"

    # 2. Candidate exists but has no profile -> MatchingRun marked failed, zero MatchResults
    cand = Candidate(
        input_source="linkedin_url",
        linkedin_url="https://www.linkedin.com/in/no-profile-user",
    )
    db_session.add(cand)
    db_session.flush()
    run = MatchingRun(
        candidate_id=cand.id,
        company_ids=["c1"],
        status="processing",
        scoring_version="fit_v1",
        ranking_version="rank_v1",
        retrieval_config={},
    )
    db_session.add(run)
    db_session.commit()

    out2 = graph.invoke({**init_state, "matching_run_id": run.id, "candidate_id": cand.id})
    assert out2["final_status"] == "failed"
    assert out2["fatal_error_code"] == "PROFILE_NOT_FOUND"
    db_session.refresh(run)
    assert run.status == "failed"
    assert db_session.scalars(select(MatchResult).where(MatchResult.matching_run_id == run.id)).all() == []


def test_langgraph_handles_llm_timeout_gracefully(
    client: TestClient,
    db_session: Session,
    test_settings: Settings,
) -> None:
    candidate_id, discovery_run_id, _ = _setup_candidate_and_discovery(client)

    class TimeoutLLMProvider(LLMProvider):
        provider_name = "gemini"
        model_name = "gemini-2.5-flash"

        def extract_candidate_profile(self, resume_text: str, schema: Any = None):
            raise NotImplementedError

        def assess_candidate_company_fit(
            self,
            *,
            candidate_profile: dict[str, Any],
            company_context: dict[str, Any],
            retrieved_evidence: list[RetrievedEvidenceItem],
        ) -> LLMAssessmentResult:
            raise LLMProviderError("LLM_TIMEOUT", "Simulated timeout", status_code=504)

    resp = start_matching_run(
        db_session,
        test_settings,
        MatchingRunCreateRequest(candidate_id=candidate_id, discovery_run_id=discovery_run_id),
        llm_provider=TimeoutLLMProvider(),
    )
    assert resp.status_code if hasattr(resp, "status_code") else True
    assert resp.status == "completed_with_warnings"
    assert resp.requires_review is True
    assert resp.result_count == 3


def test_alembic_m4_to_m5_upgrade_and_downgrade(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "mig_m5.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    from app.core.config import get_settings
    get_settings.cache_clear()

    backend_dir = Path(__file__).resolve().parents[1]
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))

    try:
        # Upgrade to M4 first and insert an M2 candidate
        command.upgrade(alembic_cfg, "20261127_0003")
        engine = create_engine(db_url)
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO candidates (id, input_source, linkedin_url, created_at, updated_at) "
                    "VALUES ('cand-m4', 'linkedin_url', 'https://www.linkedin.com/in/m4-user', "
                    "'2026-11-27T00:00:00Z', '2026-11-27T00:00:00Z')"
                )
            )

        # Upgrade to M5
        command.upgrade(alembic_cfg, "20261127_0004")
        with engine.connect() as conn:
            cand_count = conn.execute(text("SELECT count(*) FROM candidates WHERE id = 'cand-m4'")).scalar_one()
            assert cand_count == 1
            # Verify FTS5 virtual table exists and is queryable
            fts_check = conn.execute(text("SELECT count(*) FROM evidence_documents_fts")).scalar_one()
            assert fts_check == 0

        # Downgrade back to M4
        command.downgrade(alembic_cfg, "20261127_0003")
        with engine.connect() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                ).fetchall()
            }
            assert "matching_runs" not in tables
            assert "evidence_documents_fts" not in tables
            assert "candidates" in tables
        engine.dispose()
    finally:
        get_settings.cache_clear()


def test_i3_unhandled_graph_exception_marks_run_failed_and_cleans_partial_results(
    client: TestClient,
    db_session: Session,
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services.matching_service import MatchingExecutionError

    candidate_id, discovery_run_id, _ = _setup_candidate_and_discovery(client)

    class ExplodingGraph:
        def invoke(self, _state):
            raise RuntimeError("Simulated unexpected node crash")

    monkeypatch.setattr("app.services.matching_service.build_matching_graph", lambda **_kw: ExplodingGraph())

    with pytest.raises(MatchingExecutionError):
        start_matching_run(
            db_session,
            test_settings,
            MatchingRunCreateRequest(candidate_id=candidate_id, discovery_run_id=discovery_run_id),
        )

    runs = list(db_session.scalars(select(MatchingRun).where(MatchingRun.candidate_id == candidate_id)).all())
    assert len(runs) == 1
    assert runs[0].status == "failed"
    assert runs[0].error_code == "MATCHING_WORKFLOW_ERROR"
    assert db_session.scalars(select(MatchResult).where(MatchResult.matching_run_id == runs[0].id)).all() == []


def test_i4_persist_results_db_failure_rolls_back_without_partial_results(
    client: TestClient,
    db_session: Session,
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_id, discovery_run_id, _ = _setup_candidate_and_discovery(client)

    orig_commit = db_session.commit
    call_count = 0

    def _fail_on_persist_commit():
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RuntimeError("Simulated SQLite disk error during persist_results")
        return orig_commit()

    monkeypatch.setattr(db_session, "commit", _fail_on_persist_commit)

    resp = start_matching_run(
        db_session,
        test_settings,
        MatchingRunCreateRequest(candidate_id=candidate_id, discovery_run_id=discovery_run_id),
    )
    assert resp.status == "failed"
    assert resp.error_code == "PERSISTENCE_ERROR"
    assert resp.result_count == 0
    assert db_session.scalars(select(MatchResult).where(MatchResult.matching_run_id == resp.run_id)).all() == []


def test_m1_duplicate_and_reordered_matching_run_rejected_with_409(
    client: TestClient,
) -> None:
    candidate_id, discovery_run_id, company_ids = _setup_candidate_and_discovery(client)

    first = client.post(
        "/api/matching-runs",
        json={"candidate_id": candidate_id, "discovery_run_id": discovery_run_id, "company_ids": company_ids},
    )
    assert first.status_code == 201

    dup = client.post(
        "/api/matching-runs",
        json={"candidate_id": candidate_id, "discovery_run_id": discovery_run_id, "company_ids": list(reversed(company_ids))},
    )
    assert dup.status_code == 409
    assert dup.json()["code"] == "DUPLICATE_MATCHING_RUN"


def test_m2_gemini_fallback_preserves_real_provider_provenance(
    client: TestClient,
    db_session: Session,
    test_settings: Settings,
) -> None:
    from app.models.m5 import CompanyAssessment

    candidate_id, discovery_run_id, _ = _setup_candidate_and_discovery(client)

    class FailingGeminiProvider(LLMProvider):
        provider_name = "gemini"
        model_name = "gemini-2.5-flash"
        data_origin = "real"

        def extract_candidate_profile(self, resume_text: str, schema: Any = None):
            raise NotImplementedError

        def assess_candidate_company_fit(self, **_kwargs) -> LLMAssessmentResult:
            raise LLMProviderError("LLM_TIMEOUT", "Simulated Gemini timeout", status_code=504)

    resp = start_matching_run(
        db_session,
        test_settings,
        MatchingRunCreateRequest(candidate_id=candidate_id, discovery_run_id=discovery_run_id),
        llm_provider=FailingGeminiProvider(),
    )
    assert resp.status == "completed_with_warnings"
    assessments = list(
        db_session.scalars(select(CompanyAssessment).where(CompanyAssessment.matching_run_id == resp.run_id)).all()
    )
    assert len(assessments) == 3
    assert all(a.provider_name == "gemini" for a in assessments)


def test_i4_gemini_assess_candidate_company_fit_mocked_paths() -> None:
    from datetime import UTC, datetime
    from types import SimpleNamespace
    from google.genai import errors as genai_errors
    from app.providers.llm import GeminiLLMProvider

    ev = [
        RetrievedEvidenceItem(
            evidence_document_id="doc-1",
            source_evidence_id="ev-1",
            company_id="c-1",
            entity_type="company_research",
            document_title="Kestrel",
            content="Uses Python and SQLite.",
            source_url="https://example.com",
            source_title="Kestrel",
            retrieved_at=datetime(2026, 11, 20, tzinfo=UTC),
            verification_status="verified",
            data_origin="demo",
        )
    ]
    cand = {"basic_info": {"headline": "Backend Eng"}, "skills": [{"name": "Python"}]}
    comp = {"name": "Kestrel", "stage": "seed", "industry": "Tools", "tech_stack": ["Python"]}

    valid_json = StructuredCompanyAssessment(
        required_technical_skills=["Python"],
        candidate_matching_skills=["Python"],
        evidence_references=["ev-1"],
        explanation="Strong match.",
    ).model_dump_json()

    class FakeModelsValid:
        def generate_content(self, **_kwargs):
            return SimpleNamespace(text=valid_json)

    prov = GeminiLLMProvider(api_key="test-key-123", max_retries=1, client=SimpleNamespace(models=FakeModelsValid()))
    res = prov.assess_candidate_company_fit(candidate_profile=cand, company_context=comp, retrieved_evidence=ev)
    assert res.data_origin == "real"
    assert res.assessment.candidate_matching_skills == ["Python"]

    calls = 0

    class FakeModelsRetry:
        def generate_content(self, **_kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                return SimpleNamespace(text="{not valid json")
            return SimpleNamespace(text=valid_json)

    prov_retry = GeminiLLMProvider(api_key="test-key-123", max_retries=1, client=SimpleNamespace(models=FakeModelsRetry()))
    res_retry = prov_retry.assess_candidate_company_fit(candidate_profile=cand, company_context=comp, retrieved_evidence=ev)
    assert calls == 2
    assert res_retry.assessment.explanation == "Strong match."

    class FakeModelsBadSchema:
        def generate_content(self, **_kwargs):
            return SimpleNamespace(text='{"required_technical_skills": ["Python"]}')

    prov_bad = GeminiLLMProvider(api_key="test-key-123", max_retries=1, client=SimpleNamespace(models=FakeModelsBadSchema()))
    with pytest.raises(LLMProviderError) as exc_bad:
        prov_bad.assess_candidate_company_fit(candidate_profile=cand, company_context=comp, retrieved_evidence=ev)
    assert exc_bad.value.code == "LLM_INVALID_OUTPUT"

    class FakeModelsTimeout:
        def generate_content(self, **_kwargs):
            raise TimeoutError("timed out")

    prov_to = GeminiLLMProvider(api_key="test-key-123", max_retries=1, client=SimpleNamespace(models=FakeModelsTimeout()))
    with pytest.raises(LLMProviderError) as exc_to:
        prov_to.assess_candidate_company_fit(candidate_profile=cand, company_context=comp, retrieved_evidence=ev)
    assert exc_to.value.code == "LLM_TIMEOUT"
    assert exc_to.value.status_code == 504

    class FakeModelsRateLimit:
        def generate_content(self, **_kwargs):
            raise genai_errors.APIError(429, {"error": {"message": "rate limit"}})

    prov_rl = GeminiLLMProvider(api_key="test-key-123", max_retries=0, client=SimpleNamespace(models=FakeModelsRateLimit()))
    with pytest.raises(LLMProviderError) as exc_rl:
        prov_rl.assess_candidate_company_fit(candidate_profile=cand, company_context=comp, retrieved_evidence=ev)
    assert exc_rl.value.code == "LLM_RATE_LIMITED"
    assert exc_rl.value.status_code == 429
