import io
from pathlib import Path

from alembic import command
from alembic.config import Config
import pymupdf
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.candidate import Candidate
from app.models.candidate_profile import CandidateProfile
from app.models.research_run import ResearchRun


def _build_pdf_bytes(text_content: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text_content)
    data = doc.tobytes()
    doc.close()
    return data


def test_api_process_and_retrieve_candidate_profile(
    client: TestClient,
    test_settings: Settings,
) -> None:
    pdf_bytes = _build_pdf_bytes("Elena Vance\nFounding Engineer\nPython, FastAPI, Docker, SQLite")
    create_resp = client.post(
        "/api/runs",
        files={"resume_file": ("elena_resume.pdf", pdf_bytes, "application/pdf")},
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    run_id = created["run_id"]
    candidate_id = created["candidate"]["id"]

    # Profile not yet generated -> 404
    pre_profile_resp = client.get(f"/api/candidates/{candidate_id}/profile")
    assert pre_profile_resp.status_code == 404
    assert pre_profile_resp.json()["code"] == "PROFILE_NOT_FOUND"

    # Process run
    proc_resp = client.post(f"/api/runs/{run_id}/process")
    assert proc_resp.status_code == 200
    proc_body = proc_resp.json()
    assert proc_body["run_id"] == run_id
    assert proc_body["candidate_id"] == candidate_id
    assert proc_body["status"] == "completed"
    assert proc_body["profile_id"] is not None
    assert str(test_settings.upload_dir) not in proc_resp.text

    # Retrieve run status includes profile_extraction_status
    run_resp = client.get(f"/api/runs/{run_id}")
    assert run_resp.status_code == 200
    assert run_resp.json()["status"] == "completed"
    assert run_resp.json()["profile_extraction_status"] is not None

    # Retrieve candidate profile
    profile_resp = client.get(f"/api/candidates/{candidate_id}/profile")
    assert profile_resp.status_code == 200
    profile_body = profile_resp.json()
    assert profile_body["candidate_id"] == candidate_id
    assert profile_body["data_origin"] == "demo"
    assert profile_body["provider_name"] == "demo"
    assert profile_body["profile"]["basic_info"]["full_name"] == "Elena Vance"
    assert "resume_storage_key" not in profile_resp.text
    assert str(test_settings.upload_dir) not in profile_resp.text


def test_api_process_unknown_run_returns_404(client: TestClient) -> None:
    resp = client.post("/api/runs/00000000-0000-0000-0000-000000000000/process")
    assert resp.status_code == 404
    assert resp.json()["code"] == "RUN_NOT_FOUND"


def test_api_process_linkedin_run_rejected_without_fabrication(client: TestClient) -> None:
    create_resp = client.post(
        "/api/runs",
        data={"linkedin_url": "https://www.linkedin.com/in/elena-vance"},
    )
    assert create_resp.status_code == 201
    run_id = create_resp.json()["run_id"]
    candidate_id = create_resp.json()["candidate"]["id"]

    proc_resp = client.post(f"/api/runs/{run_id}/process")
    assert proc_resp.status_code == 422
    assert proc_resp.json()["code"] == "LINKEDIN_EXTRACTION_UNSUPPORTED"

    run_resp = client.get(f"/api/runs/{run_id}")
    assert run_resp.status_code == 200
    assert run_resp.json()["status"] == "failed"

    profile_resp = client.get(f"/api/candidates/{candidate_id}/profile")
    assert profile_resp.status_code == 404


def test_api_duplicate_processing_prevented_when_status_is_processing(
    client: TestClient,
    db_session: Session,
) -> None:
    candidate = Candidate(
        input_source="resume_pdf",
        resume_filename="test.pdf",
        resume_content_type="application/pdf",
        resume_size_bytes=100,
        resume_storage_key="nonexistent.pdf",
    )
    db_session.add(candidate)
    db_session.flush()
    run = ResearchRun(candidate_id=candidate.id, status="processing")
    db_session.add(run)
    db_session.commit()

    resp = client.post(f"/api/runs/{run.id}/process")
    assert resp.status_code == 409
    assert resp.json()["code"] == "RUN_ALREADY_PROCESSING"


def test_api_invalid_candidate_id_returns_404(client: TestClient) -> None:
    resp = client.get("/api/candidates/00000000-0000-0000-0000-000000000000/profile")
    assert resp.status_code == 404
    assert resp.json()["code"] == "CANDIDATE_NOT_FOUND"


def test_db_unique_profile_constraint_and_relationship(db_session: Session) -> None:
    candidate = Candidate(
        input_source="linkedin_url",
        linkedin_url="https://www.linkedin.com/in/unique-check",
    )
    db_session.add(candidate)
    db_session.flush()

    p1 = CandidateProfile(
        candidate_id=candidate.id,
        extraction_status="extracted",
        source_type="linkedin_url",
        data_origin="demo",
        provider_name="demo",
        warnings=[],
    )
    db_session.add(p1)
    db_session.commit()
    db_session.refresh(candidate)
    assert candidate.profile is not None
    assert candidate.profile.id == p1.id

    p2 = CandidateProfile(
        candidate_id=candidate.id,
        extraction_status="extracted",
        source_type="linkedin_url",
        data_origin="demo",
        provider_name="demo",
        warnings=[],
    )
    db_session.add(p2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_alembic_upgrade_from_m2_preserves_existing_records_and_supports_downgrade(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_file = tmp_path / "migration_test.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    from app.core.config import get_settings
    get_settings.cache_clear()

    backend_dir = Path(__file__).resolve().parents[1]
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))

    try:
        # Upgrade to M2 revision
        command.upgrade(alembic_cfg, "20261127_0001")

        engine = create_engine(db_url)
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO candidates (id, input_source, linkedin_url, created_at, updated_at) "
                    "VALUES ('cand-1', 'linkedin_url', 'https://www.linkedin.com/in/m2-user', "
                    "'2026-11-27T00:00:00Z', '2026-11-27T00:00:00Z')"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO research_runs (id, candidate_id, status, created_at) "
                    "VALUES ('run-1', 'cand-1', 'pending', '2026-11-27T00:00:00Z')"
                )
            )

        # Upgrade to M3 head
        command.upgrade(alembic_cfg, "head")

        with engine.connect() as conn:
            cand_count = conn.execute(text("SELECT COUNT(*) FROM candidates WHERE id = 'cand-1'")).scalar_one()
            run_count = conn.execute(text("SELECT COUNT(*) FROM research_runs WHERE id = 'run-1'")).scalar_one()
            tables = {
                row[0]
                for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                ).fetchall()
            }
            assert cand_count == 1
            assert run_count == 1
            assert "candidate_profiles" in tables

        # Downgrade back to M2
        command.downgrade(alembic_cfg, "20261127_0001")
        with engine.connect() as conn:
            tables_after = {
                row[0]
                for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                ).fetchall()
            }
            assert "candidate_profiles" not in tables_after
            assert conn.execute(text("SELECT COUNT(*) FROM candidates WHERE id = 'cand-1'")).scalar_one() == 1
        engine.dispose()
    finally:
        get_settings.cache_clear()
