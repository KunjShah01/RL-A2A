"""
Protocol Router - Routes messages between protocols
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum

from src.core.message import Message
from src.protocols.jsonrpc import JSONRPCHandler
from src.protocols.a2a_handler import A2AHandler


class ProtocolType(str, Enum):
    """Protocol type enumeration"""
    JSONRPC = "jsonrpc"
    A2A = "a2a"
    MCP = "mcp"
    INTERNAL = "internal"
    REST = "rest"
    WEBSOCKET = "websocket"


class ProtocolRouter:
    """
    Protocol Router
    
    Routes messages between different protocols (JSON-RPC, A2A, MCP, internal)
    """
    
    def __init__(self):
        """Initialize protocol router"""
        self._handlers: Dict[ProtocolType, Any] = {}
        self._logger = logging.getLogger(__name__)
        self.jsonrpc_handler = JSONRPCHandler()
        self.a2a_handler = A2AHandler()
    
    def register_handler(self, protocol: ProtocolType, handler: Any) -> None:
        """
        Register a protocol handler
        
        Args:
            protocol: Protocol type
            handler: Protocol handler instance
        """
        self._handlers[protocol] = handler
        self._logger.debug(f"Registered protocol handler: {protocol.value}")
    
    def get_handler(self, protocol: ProtocolType) -> Optional[Any]:
        """
        Get protocol handler
        
        Args:
            protocol: Protocol type
            
        Returns:
            Protocol handler or None
        """
        return self._handlers.get(protocol)
    
    async def route_message(self, message: Message, target_protocol: Optional[ProtocolType] = None) -> Any:
        """
        Route a message to the appropriate protocol handler
        
        Args:
            message: Message to route
            target_protocol: Optional target protocol (auto-detect if None)
            
        Returns:
            Response from protocol handler
        """
        # Determine target protocol
        if not target_protocol:
            target_protocol = self._detect_protocol(message)
        
        handler = self._handlers.get(target_protocol)
        if not handler:
            self._logger.warning(f"No handler for protocol: {target_protocol}")
            return None
        
        try:
            # Route based on protocol type
            if target_protocol == ProtocolType.A2A:
                return await self._route_to_a2a(message, handler)
            elif target_protocol == ProtocolType.JSONRPC:
                return await self._route_to_jsonrpc(message, handler)
            elif target_protocol == ProtocolType.MCP:
                return await self._route_to_mcp(message, handler)
            else:
                # Internal routing
                return await handler.handle(message)
        
        except Exception as e:
            self._logger.error(f"Error routing message: {e}", exc_info=True)
            return None
    
    def _detect_protocol(self, message: Message) -> ProtocolType:
        """
        Detect protocol from message
        
        Args:
            message: Message to analyze
            
        Returns:
            Detected protocol type
        """
        # Check metadata for protocol hint
        metadata = message.metadata
        if "protocol" in metadata:
            try:
                return ProtocolType(metadata["protocol"])
            except ValueError:
                pass
        
        # Check message type
        if message.jsonrpc_id is not None:
            return ProtocolType.JSONRPC
        
        if message.task_id:
            return ProtocolType.A2A
        
        # Default to internal
        return ProtocolType.INTERNAL
    
    async def _route_to_a2a(self, message: Message, handler: A2AHandler) -> Any:
        """Route message to A2A handler"""
        # Convert message to A2A format
        request_data = message.to_jsonrpc()
        return await handler.handle_request(request_data)
    
    async def _route_to_jsonrpc(self, message: Message, handler: JSONRPCHandler) -> Any:
        """Route message to JSON-RPC handler"""
        request_data = message.to_jsonrpc()
        return await handler.handle_request(request_data)
    
    async def _route_to_mcp(self, message: Message, handler: Any) -> Any:
        """Route message to MCP handler"""
        # MCP routing would convert message to MCP format
        # For now, return None as MCP is primarily server-side
        return None
    
    def convert_message(self, message: Message, target_protocol: ProtocolType) -> Any:
        """
        Convert message to target protocol format
        
        Args:
            message: Source message
            target_protocol: Target protocol type
            
        Returns:
            Converted message in target protocol format
        """
        if target_protocol == ProtocolType.JSONRPC or target_protocol == ProtocolType.A2A:
            return message.to_jsonrpc()
        elif target_protocol == ProtocolType.INTERNAL:
            return message.to_dict()
        else:
            return message.to_dict()

