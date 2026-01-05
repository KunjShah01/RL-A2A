"""
MCP Handler - Model Context Protocol handler
Enhanced MCP protocol handler for RL-A2A v2.0
"""

import logging
from typing import Dict, Any, Optional, List

from src.utils.config import Config
try:
    from mcp.server import Server
    from mcp.types import Tool, Resource, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    Server = None
    Tool = None
    Resource = None
    TextContent = None
    types = None

from ..core.registry import AgentRegistry
from ..core.events import EventBus


class MCPHandler:
    """
    MCP Protocol Handler
    
    Handles MCP protocol for AI assistant integration
    """
    
    def __init__(self, agent_registry: Optional[AgentRegistry] = None, event_bus: Optional[EventBus] = None):
        """
        Initialize MCP handler
        
        Args:
            agent_registry: Agent registry instance
            event_bus: Event bus instance
        """
        if not MCP_AVAILABLE:
            raise ImportError("MCP library not available. Install with: pip install mcp")
        
        self.agent_registry = agent_registry
        self.event_bus = event_bus
        self._logger = logging.getLogger(__name__)
        self.server = Server("rl-a2a-v2")
        
        # Register MCP handlers
        self._setup_tools()
        self._setup_resources()
    
    def _setup_tools(self) -> None:
        """Setup MCP tools"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available MCP tools"""
            return [
                Tool(
                    name="create_agent",
                    description="Create a new AI agent with specified role and capabilities",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Agent name"},
                            "role": {"type": "string", "description": "Agent role"},
                            "ai_provider": {"type": "string", "description": "AI provider (openai, anthropic, google)"}
                        },
                        "required": ["name", "role"]
                    }
                ),
                Tool(
                    name="list_agents",
                    description="List all active agents in the system",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="send_message",
                    description="Send a message between agents",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sender_id": {"type": "string"},
                            "receiver_id": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["sender_id", "receiver_id", "content"]
                    }
                ),
                Tool(
                    name="get_system_status",
                    description="Get comprehensive system status and metrics",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="get_agent_manifest",
                    description="Get agent manifest for capability discovery",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "string"}
                        },
                        "required": ["agent_id"]
                    }
                ),
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle MCP tool calls"""
            try:
                if name == "create_agent":
                    result = await self._handle_create_agent(arguments)
                elif name == "list_agents":
                    result = await self._handle_list_agents(arguments)
                elif name == "send_message":
                    result = await self._handle_send_message(arguments)
                elif name == "get_system_status":
                    result = await self._handle_get_system_status(arguments)
                elif name == "get_agent_manifest":
                    result = await self._handle_get_agent_manifest(arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}
                
                import json
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            except Exception as e:
                self._logger.error(f"Error handling MCP tool {name}: {e}", exc_info=True)
                import json
                return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]
    
    def _setup_resources(self) -> None:
        """Setup MCP resources"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available MCP resources"""
            return [
                Resource(
                    uri="rl-a2a://system/config",
                    name="System Configuration",
                    description="System configuration and settings",
                    mimeType="application/json"
                ),
                Resource(
                    uri="rl-a2a://agents/list",
                    name="Agents List",
                    description="List of all agents",
                    mimeType="application/json"
                ),
                Resource(
                    uri="rl-a2a://system/logs",
                    name="System Logs",
                    description="Recent system logs",
                    mimeType="text/plain"
                ),
            ]
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Handle resource read requests"""
            if uri == "rl-a2a://system/config":
                import json
                return json.dumps(Config.to_dict(), indent=2)
            
            elif uri == "rl-a2a://agents/list":
                if self.agent_registry:
                    agents = self.agent_registry.list_all()
                    import json
                    return json.dumps([agent.to_dict() for agent in agents], indent=2, default=str)
                return "[]"
            
            elif uri == "rl-a2a://system/logs":
                # Read recent logs
                from src.utils.logger import get_logger
                import logging
                logger = get_logger("rla2a")
                # This is a simplified implementation - in production, read from log file
                return "System logs available"
            
            else:
                raise ValueError(f"Unknown resource: {uri}")
    
    async def _handle_create_agent(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create_agent tool"""
        if not self.agent_registry:
            return {"error": "Agent registry not available"}
        
        import uuid
        from src.core.agent import Agent, AgentStatus
        from src.identity.key_manager import KeyManager
        
        name = arguments.get("name", "Unknown")
        role = arguments.get("role", "general")
        ai_provider = arguments.get("ai_provider", "openai")
        
        # Generate DID and keys
        key_manager = KeyManager()
        private_key, public_key = key_manager.generate_ed25519_keypair()
        did = f"did:key:{key_manager.key_to_base64(public_key)[:32]}"
        
        # Create agent
        agent = Agent(
            id=str(uuid.uuid4()),
            did=did,
            name=name,
            role=role,
            status=AgentStatus.ACTIVE,
            public_key=key_manager.key_to_pem(public_key),
            ai_provider=ai_provider,
        )
        
        self.agent_registry.register(agent)
        
        return {
            "agent_id": agent.id,
            "did": agent.did,
            "name": agent.name,
            "status": "created"
        }
    
    async def _handle_list_agents(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list_agents tool"""
        if not self.agent_registry:
            return {"agents": []}
        
        agents = self.agent_registry.list_all()
        return {
            "agents": [agent.to_dict() for agent in agents],
            "count": len(agents)
        }
    
    async def _handle_send_message(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle send_message tool"""
        sender_id = arguments.get("sender_id")
        receiver_id = arguments.get("receiver_id")
        content = arguments.get("content")
        
        if not sender_id or not receiver_id or not content:
            return {"error": "Missing required parameters"}
        
        # Emit event for message sending
        if self.event_bus:
            from src.core.events import Event, EventType
            event = Event(
                event_type=EventType.MESSAGE_SENT,
                payload={
                    "sender_id": sender_id,
                    "receiver_id": receiver_id,
                    "content": content
                }
            )
            await self.event_bus.emit(event)
        
        return {
            "status": "sent",
            "sender_id": sender_id,
            "receiver_id": receiver_id
        }
    
    async def _handle_get_system_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_system_status tool"""
        # use top-level Config imported at module level
        agent_count = 0
        if self.agent_registry:
            agent_count = self.agent_registry.count()

        return {
            "version": Config.VERSION,
            "system_name": Config.SYSTEM_NAME,
            "agents_count": agent_count,
            "status": "operational"
        }
    
    async def _handle_get_agent_manifest(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_agent_manifest tool"""
        agent_id = arguments.get("agent_id")
        if not agent_id or not self.agent_registry:
            return {"error": "Agent ID required"}
        
        agent = self.agent_registry.get(agent_id)
        if not agent:
            return {"error": f"Agent not found: {agent_id}"}
        
        # Return basic manifest structure
        # Full manifest service will be implemented in Phase 3
        return {
            "agent_id": agent.id,
            "did": agent.did,
            "capabilities": agent.capabilities,
            "role": agent.role,
            "status": agent.status.value
        }
    
    async def run(self):
        """Run MCP server"""
        await self.server.run()
