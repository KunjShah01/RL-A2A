from src.core.message import Message, MessageType, MessagePriority


def test_message_to_jsonrpc_and_back():
    msg = Message(sender_id="s1", receiver_id="r1", content={"foo": "bar"}, message_type=MessageType.TASK, priority=MessagePriority.HIGH)
    jr = msg.to_jsonrpc()
    assert jr["jsonrpc"] == "2.0"
    assert jr["params"]["content"]["foo"] == "bar"

    # Build from jsonrpc
    from_dict = {
        "jsonrpc": "2.0",
        "method": "tasks/send",
        "params": {"sender_id": "s1", "receiver_id": "r1", "content": {"foo": "bar"}, "type": "task", "priority": 3},
        "id": 42
    }

    m2 = Message.from_jsonrpc(from_dict)
    assert m2.sender_id == "s1"
    assert m2.message_type == MessageType.TASK
    assert m2.priority == MessagePriority(3)
