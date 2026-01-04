"""
Message data model with JSON-RPC 2.0 compatibility
Enhanced message representation for RL-A2A v2.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import uuid


class MessageType(str, Enum):
    """Message type enumeration"""
    TEXT = "text"
    TASK = "task"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    QUERY = "query"
    COMMAND = "command"
    JSONRPC = "jsonrpc"


class MessagePriority(int, Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Message:
    """
    Enhanced Message model with JSON-RPC 2.0 compatibility
    
    Attributes:
        id: Unique message identifier
        jsonrpc_id: JSON-RPC 2.0 request ID (if applicable)
        sender_id: Sender agent ID
        sender_did: Sender agent DID
        receiver_id: Receiver agent ID
        receiver_did: Receiver agent DID
        content: Message content
        message_type: Type of message
        priority: Message priority
        metadata: Additional metadata
        timestamp: Message timestamp
        encrypted: Whether message is encrypted
        signature: Message signature for verification
        requires_approval: Whether message requires human approval
        task_id: Task identifier (for A2A tasks)
        correlation_id: Correlation ID for message threading
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    jsonrpc_id: Optional[Union[str, int]] = None
    sender_id: str = ""
    sender_did: Optional[str] = None
    receiver_id: str = ""
    receiver_did: Optional[str] = None
    content: Any = None
    message_type: MessageType = MessageType.TEXT
    priority: MessagePriority = MessagePriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    encrypted: bool = False
    signature: Optional[str] = None
    requires_approval: bool = False
    task_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "id": self.id,
            "jsonrpc_id": self.jsonrpc_id,
            "sender_id": self.sender_id,
            "sender_did": self.sender_did,
            "receiver_id": self.receiver_id,
            "receiver_did": self.receiver_did,
            "content": self.content,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "encrypted": self.encrypted,
            "signature": self.signature,
            "requires_approval": self.requires_approval,
            "task_id": self.task_id,
            "correlation_id": self.correlation_id,
        }
    
    def to_jsonrpc(self) -> Dict[str, Any]:
        """Convert message to JSON-RPC 2.0 format"""
        return {
            "jsonrpc": "2.0",
            "id": self.jsonrpc_id or self.id,
            "method": self.metadata.get("method", "message/send"),
            "params": {
                "sender_id": self.sender_id,
                "receiver_id": self.receiver_id,
                "content": self.content,
                "type": self.message_type.value,
                "priority": self.priority.value,
                "metadata": {k: v for k, v in self.metadata.items() if k != "method"},
            },
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary"""
        data = data.copy()
        if "message_type" in data and isinstance(data["message_type"], str):
            data["message_type"] = MessageType(data["message_type"])
        if "priority" in data:
            if isinstance(data["priority"], str):
                data["priority"] = MessagePriority(int(data["priority"]))
            elif isinstance(data["priority"], int):
                data["priority"] = MessagePriority(data["priority"])
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)
    
    @classmethod
    def from_jsonrpc(cls, jsonrpc_data: Dict[str, Any]) -> "Message":
        """Create message from JSON-RPC 2.0 format"""
        params = jsonrpc_data.get("params", {})
        metadata = params.get("metadata", {})
        metadata["method"] = jsonrpc_data.get("method", "message/send")
        
        return cls(
            id=str(uuid.uuid4()),
            jsonrpc_id=jsonrpc_data.get("id"),
            sender_id=params.get("sender_id", ""),
            receiver_id=params.get("receiver_id", ""),
            content=params.get("content"),
            message_type=MessageType(params.get("type", "text")),
            priority=MessagePriority(params.get("priority", 2)),
            metadata=metadata,
        )



