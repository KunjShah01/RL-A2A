"""
Message Router
Routes messages to agents based on various strategies
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.core.message import Message, MessageType
from src.core.registry import AgentRegistry
from src.core.events import EventBus, Event, EventType
from src.routing.manifest_service import ManifestService
from src.routing.cost_aware import CostAwareRouter, RoutingStrategy


class MessageRouter:
    """
    Message Router
    
    Routes messages to agents using various routing strategies
    """
    
    def __init__(
        self,
        agent_registry: AgentRegistry,
        manifest_service: ManifestService,
        event_bus: Optional[EventBus] = None
    ):
        """
        Initialize message router
        
        Args:
            agent_registry: Agent registry instance
            manifest_service: Manifest service instance
            event_bus: Optional event bus
        """
        self.agent_registry = agent_registry
        self.manifest_service = manifest_service
        self.event_bus = event_bus
        self.cost_aware_router = CostAwareRouter(manifest_service)
        self._logger = logging.getLogger(__name__)
        self._message_queue: List[Message] = []
    
    async def route(self, message: Message) -> bool:
        """
        Route a message to the appropriate agent
        
        Args:
            message: Message to route
            
        Returns:
            True if routed successfully
        """
        try:
            # Check if receiver is specified
            if message.receiver_id:
                return await self._route_to_agent(message, message.receiver_id)
            
            # Otherwise, use routing strategy
            # Check metadata for routing hints
            capability = message.metadata.get("required_capability")
            if capability:
                agent_id = self.cost_aware_router.select_agent(capability)
                if agent_id:
                    message.receiver_id = agent_id
                    return await self._route_to_agent(message, agent_id)
            
            # Default: route to all agents with matching capabilities
            if message.message_type == MessageType.NOTIFICATION:
                return await self._broadcast(message)
            
            self._logger.warning(f"No routing strategy for message: {message.id}")
            return False
        
        except Exception as e:
            self._logger.error(f"Error routing message: {e}", exc_info=True)
            return False
    
    async def _route_to_agent(self, message: Message, agent_id: str) -> bool:
        """
        Route message to a specific agent
        
        Args:
            message: Message to route
            agent_id: Target agent ID
            
        Returns:
            True if routed
        """
        agent = self.agent_registry.get(agent_id)
        if not agent:
            self._logger.warning(f"Agent not found: {agent_id}")
            return False
        
        # Update message receiver
        message.receiver_id = agent_id
        if agent.did:
            message.receiver_did = agent.did
        
        # Emit event
        if self.event_bus:
            event = Event(
                event_type=EventType.MESSAGE_SENT,
                payload={
                    "message_id": message.id,
                    "sender_id": message.sender_id,
                    "receiver_id": agent_id,
                },
                correlation_id=message.correlation_id,
            )
            await self.event_bus.emit(event)
        
        # In production, this would actually deliver the message
        # For now, just log
        self._logger.info(f"Routed message {message.id} to agent {agent_id}")
        
        return True
    
    async def _broadcast(self, message: Message) -> bool:
        """
        Broadcast message to multiple agents
        
        Args:
            message: Message to broadcast
            
        Returns:
            True if broadcast
        """
        capability = message.metadata.get("required_capability")
        if capability:
            agents = self.manifest_service.find_agents_by_capability(capability)
            agent_ids = [a["agent_id"] for a in agents]
        else:
            agents = self.agent_registry.list_all()
            agent_ids = [a.id for a in agents]
        
        success_count = 0
        for agent_id in agent_ids:
            if await self._route_to_agent(message, agent_id):
                success_count += 1
        
        self._logger.info(f"Broadcast message {message.id} to {success_count}/{len(agent_ids)} agents")
        
        return success_count > 0
    
    def set_routing_strategy(self, strategy: RoutingStrategy) -> None:
        """
        Set routing strategy
        
        Args:
            strategy: Routing strategy
        """
        self.cost_aware_router.set_strategy(strategy)
    
    async def route_by_capability(
        self,
        message: Message,
        capability: str,
        strategy: Optional[RoutingStrategy] = None
    ) -> bool:
        """
        Route message to agent with specific capability
        
        Args:
            message: Message to route
            capability: Required capability
            strategy: Optional routing strategy
            
        Returns:
            True if routed
        """
        agent_id = self.cost_aware_router.select_agent(capability, strategy)
        if agent_id:
            message.receiver_id = agent_id
            return await self._route_to_agent(message, agent_id)
        
        return False

