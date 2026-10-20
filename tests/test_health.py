from fastapi.testclient import TestClient
from src.main import main_app

client = TestClient(main_app)


def test_health_returns_ok():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
