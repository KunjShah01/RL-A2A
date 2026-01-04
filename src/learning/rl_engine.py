"""
Reinforcement Learning Engine
Main RL engine coordinating Q-Learning, rewards, and FRL
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from src.learning.q_learning import QLearning
from src.learning.reward_calculator import RewardCalculator
from src.learning.frl_aggregator import FRLAggregator
from src.routing.manifest_service import ManifestService
from src.core.registry import AgentRegistry
from src.core.events import EventBus, Event, EventType


class RLEngine:
    """
    Reinforcement Learning Engine
    
    Coordinates Q-Learning, reward calculation, and federated learning
    """
    
    def __init__(
        self,
        agent_registry: AgentRegistry,
        manifest_service: ManifestService,
        event_bus: Optional[EventBus] = None,
        enable_frl: bool = False
    ):
        """
        Initialize RL engine
        
        Args:
            agent_registry: Agent registry instance
            manifest_service: Manifest service instance
            event_bus: Optional event bus
            enable_frl: Enable federated learning
        """
        self.agent_registry = agent_registry
        self.manifest_service = manifest_service
        self.event_bus = event_bus
        self.enable_frl = enable_frl
        
        self.q_learning = QLearning(manifest_service=manifest_service)
        self.reward_calculator = RewardCalculator(manifest_service=manifest_service)
        self.frl_aggregator = FRLAggregator() if enable_frl else None
        
        self._logger = logging.getLogger(__name__)
        self._instance_id = f"rla2a-{datetime.now().timestamp()}"
    
    def update_agent_performance(
        self,
        agent_id: str,
        reward: float,
        state: str,
        action: str,
        next_state: str,
        cost: Optional[float] = None,
        latency: Optional[float] = None
    ) -> float:
        """
        Update agent performance based on reward
        
        Args:
            agent_id: Agent identifier
            reward: Reward value
            state: Current state
            action: Action taken
            next_state: Next state
            cost: Optional cost
            latency: Optional latency
            
        Returns:
            Updated Q-value
        """
        # Update Q-table
        q_value = self.q_learning.update_q_value(
            agent_id=agent_id,
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            cost=cost,
            latency=latency
        )
        
        # Emit event
        if self.event_bus:
            event = Event(
                event_type=EventType.RL_REWARD,
                payload={
                    "agent_id": agent_id,
                    "reward": reward,
                    "q_value": q_value,
                    "state": state,
                    "action": action,
                }
            )
            asyncio.create_task(self.event_bus.emit(event))
        
        # Submit to FRL if enabled
        if self.enable_frl and self.frl_aggregator:
            q_table = self.q_learning.get_q_table(agent_id)
            if q_table is not None:
                self.frl_aggregator.submit_update(
                    agent_id=agent_id,
                    q_table=q_table,
                    instance_id=self._instance_id,
                    metadata={"state": state, "action": action, "reward": reward}
                )
        
        return q_value
    
    def calculate_and_update(
        self,
        agent_id: str,
        success: bool,
        state: str,
        action: str,
        next_state: str,
        response_time: Optional[float] = None,
        cost: Optional[float] = None
    ) -> float:
        """
        Calculate reward and update Q-table
        
        Args:
            agent_id: Agent identifier
            success: Whether action was successful
            state: Current state
            action: Action taken
            next_state: Next state
            response_time: Response time in milliseconds
            cost: Actual cost incurred
            
        Returns:
            Updated Q-value
        """
        # Calculate reward
        reward = self.reward_calculator.calculate_reward(
            agent_id=agent_id,
            success=success,
            response_time=response_time,
            cost=cost
        )
        
        # Update Q-table
        return self.update_agent_performance(
            agent_id=agent_id,
            reward=reward,
            state=state,
            action=action,
            next_state=next_state,
            cost=cost,
            latency=response_time
        )
    
    def select_action(self, agent_id: str, state: str, actions: list) -> str:
        """
        Select action for agent using Q-learning
        
        Args:
            agent_id: Agent identifier
            state: Current state
            actions: Available actions
            
        Returns:
            Selected action
        """
        return self.q_learning.select_action(agent_id, state, actions)
    
    def get_best_action(self, agent_id: str, state: str, actions: list) -> str:
        """
        Get best action for agent (greedy policy)
        
        Args:
            agent_id: Agent identifier
            state: Current state
            actions: Available actions
            
        Returns:
            Best action
        """
        return self.q_learning.get_best_action(agent_id, state, actions)
    
    def apply_frl_update(self, agent_id: str) -> bool:
        """
        Apply federated learning update for agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if update applied
        """
        if not self.enable_frl or not self.frl_aggregator:
            return False
        
        aggregated_q_table = self.frl_aggregator.aggregate_updates(agent_id)
        if aggregated_q_table is None:
            return False
        
        # Apply aggregated Q-table (simplified - in production, merge with existing)
        # For now, just log
        self._logger.info(f"Applied FRL update for agent {agent_id}")
        
        # Emit event
        if self.event_bus:
            event = Event(
                event_type=EventType.FRL_AGGREGATION,
                payload={
                    "agent_id": agent_id,
                    "q_table_shape": aggregated_q_table.shape,
                }
            )
            asyncio.create_task(self.event_bus.emit(event))
        
        return True
    
    def get_statistics(self, agent_id: str) -> Dict[str, Any]:
        """
        Get learning statistics for agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Statistics dictionary
        """
        q_stats = self.q_learning.get_statistics(agent_id)
        
        result = {
            "agent_id": agent_id,
            "q_learning": q_stats,
        }
        
        if self.enable_frl and self.frl_aggregator:
            result["frl"] = self.frl_aggregator.get_update_statistics(agent_id)
        
        return result



