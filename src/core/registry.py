"""
Agent Registry Service
Central registry for agent management and discovery
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .agent import Agent, AgentStatus
from .events import EventBus, Event, EventType


class AgentRegistry:
    """
    Agent Registry Service
    
    Manages agent registration, discovery, and state tracking
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        Initialize agent registry
        
        Args:
            event_bus: Optional event bus for event emission
        """
        self._agents: Dict[str, Agent] = {}
        self._agents_by_did: Dict[str, Agent] = {}
        self._event_bus = event_bus
        self._logger = logging.getLogger(__name__)
    
    def register(self, agent: Agent) -> None:
        """
        Register an agent
        
        Args:
            agent: Agent to register
        """
        self._agents[agent.id] = agent
        if agent.did:
            self._agents_by_did[agent.did] = agent
        
        self._logger.info(f"Registered agent: {agent.id} ({agent.name})")
        
        # Emit event
        if self._event_bus:
            event = Event(
                event_type=EventType.AGENT_CREATED,
                payload={"agent_id": agent.id, "agent": agent.to_dict()},
                source="registry",
            )
            asyncio.create_task(self._event_bus.emit(event))
    
    def get(self, agent_id: str) -> Optional[Agent]:
        """
        Get agent by ID
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent if found, None otherwise
        """
        return self._agents.get(agent_id)
    
    def get_by_did(self, did: str) -> Optional[Agent]:
        """
        Get agent by DID
        
        Args:
            did: Decentralized Identifier
            
        Returns:
            Agent if found, None otherwise
        """
        return self._agents_by_did.get(did)
    
    def update(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update agent
        
        Args:
            agent_id: Agent identifier
            updates: Dictionary of updates
            
        Returns:
            True if updated, False if agent not found
        """
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        
        # Update agent fields
        for key, value in updates.items():
            if hasattr(agent, key):
                setattr(agent, key, value)
        
        agent.update_last_active()
        
        self._logger.debug(f"Updated agent: {agent_id}")
        
        # Emit event
        if self._event_bus:
            event = Event(
                event_type=EventType.AGENT_UPDATED,
                payload={"agent_id": agent_id, "updates": updates},
                source="registry",
            )
            asyncio.create_task(self._event_bus.emit(event))
        
        return True
    
    def unregister(self, agent_id: str) -> bool:
        """
        Unregister an agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if unregistered, False if agent not found
        """
        agent = self._agents.pop(agent_id, None)
        if not agent:
            return False
        
        if agent.did:
            self._agents_by_did.pop(agent.did, None)
        
        self._logger.info(f"Unregistered agent: {agent_id}")
        
        # Emit event
        if self._event_bus:
            event = Event(
                event_type=EventType.AGENT_DELETED,
                payload={"agent_id": agent_id},
                source="registry",
            )
            asyncio.create_task(self._event_bus.emit(event))
        
        return True
    
    def list_all(self, status: Optional[AgentStatus] = None) -> List[Agent]:
        """
        List all agents, optionally filtered by status
        
        Args:
            status: Optional status filter
            
        Returns:
            List of agents
        """
        agents = list(self._agents.values())
        if status:
            agents = [a for a in agents if a.status == status]
        return agents
    
    def list_by_capability(self, capability: str) -> List[Agent]:
        """
        List agents with a specific capability
        
        Args:
            capability: Capability to filter by
            
        Returns:
            List of agents with the capability
        """
        return [
            agent for agent in self._agents.values()
            if capability in agent.capabilities
        ]
    
    def list_by_role(self, role: str) -> List[Agent]:
        """
        List agents by role
        
        Args:
            role: Role to filter by
            
        Returns:
            List of agents with the role
        """
        return [
            agent for agent in self._agents.values()
            if agent.role == role
        ]
    
    def count(self, status: Optional[AgentStatus] = None) -> int:
        """
        Count agents, optionally filtered by status
        
        Args:
            status: Optional status filter
            
        Returns:
            Number of agents
        """
        if status:
            return sum(1 for a in self._agents.values() if a.status == status)
        return len(self._agents)
    
    def exists(self, agent_id: str) -> bool:
        """
        Check if agent exists
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if agent exists
        """
        return agent_id in self._agents

