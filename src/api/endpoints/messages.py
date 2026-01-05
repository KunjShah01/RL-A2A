"""
Message endpoints - JSON-RPC 2.0 compatible
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from src.core.message import Message
from src.routing.message_router import MessageRouter
from src.protocols.a2a_handler import A2AHandler

router = APIRouter()


def get_message_router(request: Request) -> MessageRouter:
    """Dependency to get message router"""
    return request.app.state.message_router


def get_a2a_handler(request: Request) -> A2AHandler:
    """Dependency to get A2A handler"""
    return request.app.state.a2a_handler


class MessageSendRequest(BaseModel):
    sender_id: str
    receiver_id: str
    content: Any
    message_type: str = "text"
    priority: int = 2


class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Dict[str, Any]
    id: Optional[Any] = None


@router.post("/send")
async def send_message(
    request_data: MessageSendRequest,
    router: MessageRouter = Depends(get_message_router)
):
    """Send a message (REST endpoint)"""
    from src.core.message import Message, MessageType, MessagePriority
    
    message = Message(
        sender_id=request_data.sender_id,
        receiver_id=request_data.receiver_id,
        content=request_data.content,
        message_type=MessageType(request_data.message_type),
        priority=MessagePriority(request_data.priority)
    )
    
    success = await router.route(message)
    
    return {
        "message_id": message.id,
        "status": "sent" if success else "failed"
    }


@router.post("/jsonrpc")
async def jsonrpc_endpoint(
    request_data: JSONRPCRequest,
    a2a_handler: A2AHandler = Depends(get_a2a_handler)
):
    """JSON-RPC 2.0 endpoint"""
    from src.protocols.jsonrpc import JSONRPCResponse
    
    # Handle JSON-RPC request
    response = await a2a_handler.handle_request(request_data.model_dump())
    
    if response:
        return response.to_dict()
    else:
        return {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid request"}, "id": request_data.id}



