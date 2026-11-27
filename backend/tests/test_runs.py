from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.candidate import Candidate
from app.models.research_run import ResearchRun
from app.repositories.run_repository import RunRepository

VALID_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"


def test_create_run_with_valid_linkedin_url(client: TestClient) -> None:
    response = client.post(
        "/api/runs",
        data={"linkedin_url": "  https://www.linkedin.com/in/jane-doe/  "},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["started_at"] is None
    assert body["completed_at"] is None
    assert body["error"] is None
    assert body["candidate"]["input_source"] == "linkedin_url"
    assert body["candidate"]["linkedin_url"] == "https://www.linkedin.com/in/jane-doe"
    assert body["candidate"]["resume_filename"] is None
    assert body["candidate"]["resume_size_bytes"] is None


@pytest.mark.parametrize(
    "bad_url",
    [
        "http://www.linkedin.com/in/jane-doe",
        "https://example.com/in/jane-doe",
        "https://notlinkedin.com/in/jane-doe",
        "https://www.linkedin.com/company/acme",
        "https://www.linkedin.com/in/",
        "https://www.linkedin.com/in",
        "   ",
        "",
        "not-a-url",
    ],
)
def test_create_run_invalid_linkedin_url_rejected(client: TestClient, bad_url: str) -> None:
    response = client.post("/api/runs", data={"linkedin_url": bad_url})
    assert response.status_code == 422
    assert "code" in response.json()
    assert "detail" in response.json()


def test_create_run_with_valid_pdf_persists_file_and_metadata(
    client: TestClient,
    test_settings: Settings,
    db_session: Session,
) -> None:
    response = client.post(
        "/api/runs",
        files={"resume_file": ("../../candidate_resume.pdf", VALID_PDF_BYTES, "application/pdf")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["candidate"]["input_source"] == "resume_pdf"
    assert body["candidate"]["linkedin_url"] is None
    assert body["candidate"]["resume_filename"] == "candidate_resume.pdf"
    assert body["candidate"]["resume_size_bytes"] == len(VALID_PDF_BYTES)
    assert "resume_storage_key" not in body["candidate"]
    assert str(test_settings.upload_dir) not in response.text

    stored_files = list(test_settings.upload_dir.iterdir())
    assert len(stored_files) == 1
    assert stored_files[0].read_bytes() == VALID_PDF_BYTES

    candidate = db_session.get(Candidate, body["candidate"]["id"])
    assert candidate is not None
    assert candidate.resume_storage_key == stored_files[0].name


def test_create_run_invalid_extension_rejected(client: TestClient, test_settings: Settings) -> None:
    response = client.post(
        "/api/runs",
        files={"resume_file": ("resume.txt", VALID_PDF_BYTES, "application/pdf")},
    )
    assert response.status_code == 422
    assert list(test_settings.upload_dir.iterdir()) == []


def test_create_run_invalid_mime_type_rejected(client: TestClient, test_settings: Settings) -> None:
    response = client.post(
        "/api/runs",
        files={"resume_file": ("resume.pdf", VALID_PDF_BYTES, "text/plain")},
    )
    assert response.status_code == 422
    assert list(test_settings.upload_dir.iterdir()) == []


def test_create_run_invalid_magic_bytes_rejected_and_cleaned_up(
    client: TestClient,
    test_settings: Settings,
) -> None:
    response = client.post(
        "/api/runs",
        files={"resume_file": ("fake.pdf", b"NOT_A_PDF_FILE", "application/pdf")},
    )
    assert response.status_code == 422
    assert list(test_settings.upload_dir.iterdir()) == []


def test_create_run_empty_pdf_rejected_and_cleaned_up(
    client: TestClient,
    test_settings: Settings,
) -> None:
    response = client.post(
        "/api/runs",
        files={"resume_file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 422
    assert list(test_settings.upload_dir.iterdir()) == []


def test_create_run_oversized_pdf_returns_413_and_cleans_up_partial_file(
    client: TestClient,
    test_settings: Settings,
) -> None:
    oversized = b"%PDF-1.4\n" + (b"A" * (test_settings.max_resume_size_bytes + 1024))
    response = client.post(
        "/api/runs",
        files={"resume_file": ("big.pdf", oversized, "application/pdf")},
    )
    assert response.status_code == 413
    assert response.json()["code"] == "RESUME_TOO_LARGE"
    assert list(test_settings.upload_dir.iterdir()) == []


def test_create_run_cleans_up_file_when_db_persistence_fails(
    client: TestClient,
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _boom(*_args, **_kwargs):
        raise RuntimeError("db failure")

    monkeypatch.setattr(RunRepository, "create_resume_candidate_and_run", _boom)

    with pytest.raises(RuntimeError, match="db failure"):
        client.post(
            "/api/runs",
            files={"resume_file": ("resume.pdf", VALID_PDF_BYTES, "application/pdf")},
        )

    assert list(test_settings.upload_dir.iterdir()) == []


def test_create_run_both_inputs_rejected(client: TestClient, test_settings: Settings) -> None:
    response = client.post(
        "/api/runs",
        data={"linkedin_url": "https://www.linkedin.com/in/jane-doe"},
        files={"resume_file": ("resume.pdf", VALID_PDF_BYTES, "application/pdf")},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "MULTIPLE_INPUT_METHODS"
    assert list(test_settings.upload_dir.iterdir()) == []


def test_create_run_neither_input_rejected(client: TestClient) -> None:
    response = client.post("/api/runs")
    assert response.status_code == 422
    assert response.json()["code"] == "MISSING_CANDIDATE_INPUT"


def test_get_run_returns_persisted_run(client: TestClient) -> None:
    create_resp = client.post(
        "/api/runs",
        data={"linkedin_url": "https://linkedin.com/in/alex-smith"},
    )
    assert create_resp.status_code == 201
    created = create_resp.json()

    get_resp = client.get(f"/api/runs/{created['run_id']}")
    assert get_resp.status_code == 200
    assert get_resp.json() == created


def test_get_run_unknown_id_returns_404(client: TestClient) -> None:
    response = client.get("/api/runs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json() == {
        "code": "RUN_NOT_FOUND",
        "detail": "Research run not found.",
    }


def test_candidate_multiple_runs_relationship_and_constraints(db_session: Session) -> None:
    candidate = Candidate(
        input_source="linkedin_url",
        linkedin_url="https://www.linkedin.com/in/multi-run",
    )
    db_session.add(candidate)
    db_session.flush()

    run1 = ResearchRun(candidate_id=candidate.id, status="pending")
    run2 = ResearchRun(candidate_id=candidate.id, status="pending")
    db_session.add_all([run1, run2])
    db_session.commit()
    db_session.refresh(candidate)

    assert len(candidate.research_runs) == 2

    invalid_status_run = ResearchRun(candidate_id=candidate.id, status="invalid_status")
    db_session.add(invalid_status_run)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    orphan_run = ResearchRun(candidate_id="missing-candidate-id", status="pending")
    db_session.add(orphan_run)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_database_isolation_step_1_create(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/api/runs",
        data={"linkedin_url": "https://www.linkedin.com/in/isolation-check"},
    )
    assert response.status_code == 201
    assert db_session.query(ResearchRun).count() == 1


def test_database_isolation_step_2_verify_empty(db_session: Session) -> None:
    assert db_session.query(ResearchRun).count() == 0
    assert db_session.query(Candidate).count() == 0
