import asyncio
from src.core.events import EventBus, Event, EventType


def test_eventbus_subscribe_emit_sync():
    bus = EventBus()
    received = []

    def callback(e: Event):
        received.append(e.event_type)

    bus.subscribe(EventType.AGENT_CREATED, callback)
    e = Event(event_type=EventType.AGENT_CREATED, payload={"x": 1})
    bus.emit_sync(e)
    assert received and received[0] == EventType.AGENT_CREATED


def test_eventbus_async_emit():
    bus = EventBus()
    results = []

    async def cb(e: Event):
        results.append(e.payload.get("val"))

    bus.subscribe(EventType.TASK_CREATED, cb)

    async def runner():
        await bus.emit(Event(event_type=EventType.TASK_CREATED, payload={"val": 7}))

    import asyncio as _asyncio
    _asyncio.run(runner())
    assert results == [7]
