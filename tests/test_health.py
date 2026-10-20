from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from src.infrastructure.db.session import get_session
from src.main import app


def test_health_returns_ok_when_database_is_available() -> None:
    fake_session = AsyncMock()

    async def override_get_session():
        yield fake_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        with TestClient(app) as client:
            response = client.get("/api/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        fake_session.execute.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()
