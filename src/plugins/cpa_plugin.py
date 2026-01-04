"""
Cross-Protocol Adapter Plugin
Translates between A2A, MCP, and internal message formats
"""

import logging
from typing import Dict, Any, Optional
import json

from src.plugins.base import PluginInterface, PluginMetadata
from src.core.message import Message, MessageType
from src.protocols.router import ProtocolRouter, ProtocolType


class CrossProtocolAdapterPlugin(PluginInterface):
    """
    Cross-Protocol Adapter Plugin
    
    Provides protocol translation between A2A, MCP, and internal message formats
    """
    
    def __init__(self):
        """Initialize CPA plugin"""
        self._metadata = PluginMetadata(
            name="cross_protocol_adapter",
            version="1.0.0",
            description="Cross-Protocol Adapter for translating between A2A, MCP, and internal formats",
            author="RL-A2A Team",
            dependencies=[],
            entry_point="cpa_plugin",
            permissions=["read", "write"],
            category="protocol",
            tags=["adapter", "protocol", "a2a", "mcp"],
            min_rla2a_version="2.0.0",
            enabled=True
        )
        self.context = None
        self.protocol_router: Optional[ProtocolRouter] = None
        self._logger = logging.getLogger(__name__)
    
    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata"""
        return self._metadata
    
    async def initialize(self, context: Dict[str, Any]) -> bool:
        """
        Initialize the plugin
        
        Args:
            context: Plugin context
            
        Returns:
            True if initialized successfully
        """
        self.context = context
        
        # Initialize protocol router if available
        if "protocol_router" in context:
            self.protocol_router = context["protocol_router"]
        
        self._logger.info("Cross-Protocol Adapter plugin initialized")
        return True
    
    async def execute(self, *args, **kwargs) -> Any:
        """
        Execute plugin functionality
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Execution result
        """
        action = kwargs.get("action", "translate")
        
        if action == "translate":
            return await self._translate(**kwargs)
        elif action == "convert":
            return await self._convert(**kwargs)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    async def _translate(self, message: Dict[str, Any], source_protocol: str, target_protocol: str, **kwargs) -> Dict[str, Any]:
        """
        Translate message from source protocol to target protocol
        
        Args:
            message: Message data
            source_protocol: Source protocol (a2a, mcp, internal)
            target_protocol: Target protocol (a2a, mcp, internal)
            **kwargs: Additional parameters
            
        Returns:
            Translated message
        """
        try:
            # Convert source protocol to internal format
            internal_message = await self._from_protocol(message, source_protocol)
            
            # Convert internal format to target protocol
            target_message = await self._to_protocol(internal_message, target_protocol)
            
            self._logger.debug(f"Translated message from {source_protocol} to {target_protocol}")
            
            return {
                "success": True,
                "source_protocol": source_protocol,
                "target_protocol": target_protocol,
                "message": target_message
            }
        
        except Exception as e:
            self._logger.error(f"Translation error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _convert(self, message: Any, protocol: str, **kwargs) -> Dict[str, Any]:
        """
        Convert message to/from protocol format
        
        Args:
            message: Message data
            protocol: Protocol type
            **kwargs: Additional parameters
            
        Returns:
            Converted message
        """
        if isinstance(message, Message):
            # Convert from internal to protocol
            return await self._to_protocol(message, protocol)
        else:
            # Convert from protocol to internal
            return await self._from_protocol(message, protocol)
    
    async def _from_protocol(self, message_data: Any, protocol: str) -> Message:
        """
        Convert from protocol format to internal Message
        
        Args:
            message_data: Protocol-specific message data
            protocol: Protocol type
            
        Returns:
            Internal Message object
        """
        if protocol == "a2a" or protocol == "jsonrpc":
            # JSON-RPC 2.0 / A2A format
            if isinstance(message_data, dict):
                params = message_data.get("params", {})
                return Message(
                    jsonrpc_id=message_data.get("id"),
                    sender_id=params.get("sender_id", ""),
                    receiver_id=params.get("receiver_id", ""),
                    content=params.get("content"),
                    message_type=MessageType(params.get("type", "text")),
                    metadata={"method": message_data.get("method"), "protocol": protocol}
                )
            else:
                raise ValueError("Invalid A2A/JSON-RPC message format")
        
        elif protocol == "mcp":
            # MCP format (simplified)
            if isinstance(message_data, dict):
                return Message(
                    sender_id=message_data.get("sender_id", ""),
                    receiver_id=message_data.get("receiver_id", ""),
                    content=message_data.get("content"),
                    message_type=MessageType.TEXT,
                    metadata={"protocol": "mcp", **message_data.get("metadata", {})}
                )
            else:
                raise ValueError("Invalid MCP message format")
        
        elif protocol == "internal":
            # Already internal format
            if isinstance(message_data, Message):
                return message_data
            elif isinstance(message_data, dict):
                return Message.from_dict(message_data)
            else:
                raise ValueError("Invalid internal message format")
        
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")
    
    async def _to_protocol(self, message: Message, protocol: str) -> Dict[str, Any]:
        """
        Convert from internal Message to protocol format
        
        Args:
            message: Internal Message object
            protocol: Target protocol type
            
        Returns:
            Protocol-specific message format
        """
        if protocol == "a2a" or protocol == "jsonrpc":
            # JSON-RPC 2.0 / A2A format
            return message.to_jsonrpc()
        
        elif protocol == "mcp":
            # MCP format (simplified)
            return {
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id,
                "content": message.content,
                "type": message.message_type.value,
                "metadata": message.metadata
            }
        
        elif protocol == "internal":
            # Internal format
            return message.to_dict()
        
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")
    
    async def cleanup(self) -> bool:
        """
        Cleanup plugin resources
        
        Returns:
            True if cleaned up successfully
        """
        self.protocol_router = None
        self._logger.info("Cross-Protocol Adapter plugin cleaned up")
        return True



