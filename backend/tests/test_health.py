from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import create_app


def test_health_ok(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "foundry-backend",
        "version": "0.1.0",
        "database": "ok",
    }


def test_health_database_unavailable_returns_503_without_leaking_details() -> None:
    app = create_app()

    class BrokenSession:
        def execute(self, *_args, **_kwargs):
            raise OperationalError("SELECT 1", {}, Exception("sensitive sqlite path /secret/db"))

    def _override_broken_db():
        yield BrokenSession()  # type: ignore[misc]

    app.dependency_overrides[get_db] = _override_broken_db
    try:
        with TestClient(app) as test_client:
            response = test_client.get("/api/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["database"] == "unavailable"
    assert "sensitive" not in response.text
    assert "/secret/db" not in response.text
