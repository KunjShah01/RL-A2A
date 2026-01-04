from fastapi.testclient import TestClient
from src.api.app import create_app


def test_root_and_health_endpoints():
    app = create_app()
    client = TestClient(app)

    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "version" in data

    h = client.get("/health")
    assert h.status_code == 200
    hd = h.json()
    assert "status" in hd
