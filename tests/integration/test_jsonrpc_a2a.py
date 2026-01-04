from fastapi.testclient import TestClient
from src.api.app import create_app


def test_jsonrpc_tasks_send_returns_task_id():
    app = create_app()
    client = TestClient(app)

    payload = {
        "jsonrpc": "2.0",
        "method": "tasks/send",
        "params": {"task": {"do": "something"}, "target_agent": "agent-unknown", "priority": 2},
        "id": 1,
    }

    r = client.post("/api/v1/messages/jsonrpc", json=payload)
    assert r.status_code == 200
    data = r.json()
    # JSON-RPC response should contain result with task_id
    assert data.get("result") is not None
    assert "task_id" in data["result"]
