from pathlib import Path

from alembic import command
from alembic.config import Config
import pymupdf
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, text

from app.core.config import Settings


def _build_pdf_bytes(text_content: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text_content)
    data = doc.tobytes()
    doc.close()
    return data


def test_m4_api_end_to_end_discovery_and_company_endpoints(
    client: TestClient,
    test_settings: Settings,
) -> None:
    pdf_bytes = _build_pdf_bytes("Morgan Reid\nBackend Engineer\nPython, FastAPI, SQLite, Docker")
    create_resp = client.post(
        "/api/runs",
        files={"resume_file": ("morgan.pdf", pdf_bytes, "application/pdf")},
    )
    assert create_resp.status_code == 201
    run_id = create_resp.json()["run_id"]
    candidate_id = create_resp.json()["candidate"]["id"]

    proc_resp = client.post(f"/api/runs/{run_id}/process")
    assert proc_resp.status_code == 200

    # Trigger M4 discovery
    disc_resp = client.post(
        "/api/discovery",
        json={"candidate_id": candidate_id, "max_companies": 2},
    )
    assert disc_resp.status_code == 201
    disc_body = disc_resp.json()
    assert disc_body["status"] == "completed"
    assert disc_body["discovered_count"] == 2
    assert len(disc_body["company_ids"]) == 2
    assert str(test_settings.upload_dir) not in disc_resp.text

    # Retrieve discovery run
    get_disc = client.get(f"/api/discovery/{disc_body['run_id']}")
    assert get_disc.status_code == 200
    assert get_disc.json()["discovered_count"] == 2

    # List companies with pagination and filtering
    list_resp = client.get("/api/companies?limit=1&offset=0")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 2
    assert len(list_resp.json()["items"]) == 1

    active_resp = client.get("/api/companies?opportunity_type=active")
    assert active_resp.status_code == 200
    assert active_resp.json()["total"] == 1
    active_company_id = active_resp.json()["items"][0]["id"]

    # Company detail
    detail_resp = client.get(f"/api/companies/{active_company_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["data_origin"] == "demo"
    assert detail_resp.json()["latest_research"] is not None
    assert len(detail_resp.json()["evidence"]) >= 1

    # Refresh company research
    refresh_resp = client.post(f"/api/companies/{active_company_id}/research")
    assert refresh_resp.status_code == 200

    # Funding, hiring signals, and founders
    funding_resp = client.get(f"/api/companies/{active_company_id}/funding")
    assert funding_resp.status_code == 200
    assert len(funding_resp.json()["items"]) >= 1

    hiring_resp = client.get(f"/api/companies/{active_company_id}/hiring-signals")
    assert hiring_resp.status_code == 200
    assert hiring_resp.json()["opportunity_type"] == "active"
    assert len(hiring_resp.json()["job_opportunities"]) >= 1

    founders_resp = client.get(f"/api/companies/{active_company_id}/founders")
    assert founders_resp.status_code == 200
    assert len(founders_resp.json()["items"]) >= 1


def test_m4_api_missing_resources_return_404(client: TestClient) -> None:
    assert client.get("/api/discovery/missing-id").status_code == 404
    assert client.get("/api/companies/missing-id").status_code == 404
    assert client.post("/api/companies/missing-id/research").status_code == 404
    assert client.get("/api/companies/missing-id/funding").status_code == 404
    assert client.get("/api/companies/missing-id/hiring-signals").status_code == 404
    assert client.get("/api/companies/missing-id/founders").status_code == 404


def test_alembic_m3_to_m4_upgrade_preserves_data_and_supports_downgrade(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_file = tmp_path / "m4_migration_test.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    from app.core.config import get_settings
    get_settings.cache_clear()

    backend_dir = Path(__file__).resolve().parents[1]
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))

    try:
        command.upgrade(alembic_cfg, "20261127_0002")
        engine = create_engine(db_url)
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO candidates (id, input_source, linkedin_url, created_at, updated_at) "
                    "VALUES ('cand-m3', 'linkedin_url', 'https://www.linkedin.com/in/m3-user', "
                    "'2026-11-27T00:00:00Z', '2026-11-27T00:00:00Z')"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO candidate_profiles (id, candidate_id, extraction_status, source_type, "
                    "data_origin, provider_name, warnings, created_at, updated_at) "
                    "VALUES ('prof-m3', 'cand-m3', 'extracted', 'linkedin_url', 'demo', 'demo', '[]', "
                    "'2026-11-27T00:00:00Z', '2026-11-27T00:00:00Z')"
                )
            )

        command.upgrade(alembic_cfg, "head")
        with engine.connect() as conn:
            tables = {
                row[0]
                for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            }
            assert {"companies", "company_research", "funding_events", "hiring_signals", "job_opportunities", "founders", "source_evidence", "evidence_links", "discovery_runs"}.issubset(tables)
            assert conn.execute(text("SELECT COUNT(*) FROM candidate_profiles WHERE id = 'prof-m3'")).scalar_one() == 1

        command.downgrade(alembic_cfg, "20261127_0002")
        with engine.connect() as conn:
            tables_after = {
                row[0]
                for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            }
            assert "companies" not in tables_after
            assert conn.execute(text("SELECT COUNT(*) FROM candidate_profiles WHERE id = 'prof-m3'")).scalar_one() == 1
        engine.dispose()
    finally:
        get_settings.cache_clear()
