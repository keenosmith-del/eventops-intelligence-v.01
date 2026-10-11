"""Deployment safety checks; no external provider calls."""
from concurrent.futures import ThreadPoolExecutor
import time

import pytest
from fastapi.testclient import TestClient

from app.core import environment
from app.main import app


def test_production_never_reads_developer_dotenv(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setattr(environment, "load_dotenv", lambda *a, **kw: pytest.fail("dotenv read in production"))
    environment.load_local_environment()


@pytest.fixture
def production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:example@db.example.invalid/eventops?sslmode=require")
    monkeypatch.delenv("POSTGRES_SSLMODE", raising=False)
    monkeypatch.setenv("FRONTEND_ORIGINS", "https://frontend.example.invalid")
    return monkeypatch


def test_valid_production_configuration(production):
    environment.validate_production_environment()


@pytest.mark.parametrize("name,value", [
    ("DEMO_MODE", "false"),
    ("DATABASE_URL", ""),
    ("DATABASE_URL", "postgresql://user:example@localhost/eventops?sslmode=require"),
    ("POSTGRES_SSLMODE", "disable"),
    ("FRONTEND_ORIGINS", "*"),
    ("FRONTEND_ORIGINS", "http://frontend.example.invalid"),
    ("FRONTEND_ORIGINS", "https://frontend.example.invalid/path"),
    ("FRONTEND_ORIGINS", ""),
])
def test_unsafe_production_configuration_fails_closed(production, name, value):
    production.setenv(name, value)
    with pytest.raises(RuntimeError) as error:
        environment.validate_production_environment()
    assert "postgresql://" not in str(error.value)


def test_concurrent_first_requests_initialize_only_one_model(monkeypatch):
    from app.api import rag
    count = []
    def initialize():
        count.append(1)
        time.sleep(0.02)
        return object()
    rag._cached_embedding_model.cache_clear()
    monkeypatch.setattr(rag, "LocalEmbeddingModel", initialize)
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            models = list(pool.map(lambda _: rag.get_embedding_model(), range(4)))
        assert len(count) == 1
        assert all(model is models[0] for model in models)
    finally:
        rag._cached_embedding_model.cache_clear()


def test_readiness_does_not_leak_database_failure(monkeypatch):
    from app.core import database
    def fail():
        raise RuntimeError("credential-bearing failure must stay private")
    monkeypatch.setattr(database, "connect_db", fail)
    response = TestClient(app).get("/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}


def test_session_unavailable_logs_category_without_provider_secret(monkeypatch, caplog):
    from app.core import demo
    from psycopg import OperationalError
    from fastapi.testclient import TestClient
    from app.main import app
    def failed_connection():
        raise OperationalError("private-provider-credential-must-not-appear")
    monkeypatch.setattr(demo, "connect_db", failed_connection)
    response = TestClient(app).post("/api/demo/session")
    assert response.status_code == 503
    assert "category=OperationalError" in caplog.text
    assert "private-provider-credential" not in caplog.text + response.text
