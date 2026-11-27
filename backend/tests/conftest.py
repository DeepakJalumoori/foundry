from collections.abc import Generator
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings
from app.core.database import Base, create_engine_from_url, get_db
from app.main import create_app


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    db_path = tmp_path / "test_foundry.db"
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        app_name="Foundry Test",
        app_version="0.1.0",
        database_url=f"sqlite:///{db_path.as_posix()}",
        cors_origins="http://localhost:3000",
        max_resume_size_mb=1,
        upload_dir=upload_dir,
    )


@pytest.fixture
def db_session(test_settings: Settings) -> Generator[Session, None, None]:
    engine = create_engine_from_url(test_settings.database_url)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(test_settings: Settings, db_session: Session) -> Generator[TestClient, None, None]:
    app = create_app()

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_settings] = lambda: test_settings

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
