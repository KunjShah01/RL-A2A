import asyncio
from src.core.registry import AgentRegistry
from src.core.agent import Agent, AgentStatus


def test_registry_register_get_update_unregister():
    ev = None
    reg = AgentRegistry(event_bus=ev)
    a = Agent(id="r1", name="RegAgent", did="did:ex:r1")
    reg.register(a)
    assert reg.exists("r1")
    fetched = reg.get("r1")
    assert fetched.name == "RegAgent"

    # Update
    ok = reg.update("r1", {"name": "RegAgent2", "status": AgentStatus.ACTIVE})
    assert ok
    assert reg.get("r1").name == "RegAgent2"

    # Count and list
    assert reg.count() == 1
    assert len(reg.list_all()) == 1

    # Unregister
    assert reg.unregister("r1")
    assert not reg.exists("r1")
