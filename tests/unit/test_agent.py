from src.core.agent import Agent, AgentStatus
from datetime import datetime


def test_agent_to_from_dict_roundtrip():
    a = Agent(id="agent-1", name="TestAgent", did="did:example:123")
    d = a.to_dict()
    assert d["id"] == "agent-1"
    assert d["did"] == "did:example:123"

    a2 = Agent.from_dict(d)
    assert a2.id == a.id
    assert a2.did == a.did
    assert isinstance(a2.created_at, datetime)


def test_update_metrics_and_last_active():
    a = Agent(id="a2", name="A2")
    metrics = {"success_rate": 0.5}
    a.update_metrics(metrics)
    assert a.performance_metrics["success_rate"] == 0.5
    prev = a.last_active
    a.update_last_active()
    assert a.last_active >= prev
