"""
Q-Learning Implementation with Cost Awareness
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple
from collections import defaultdict

from src.routing.manifest_service import ManifestService


class QLearning:
    """
    Q-Learning with cost and latency awareness
    
    Uses agent manifest metrics in Q-value calculations
    """
    
    def __init__(
        self,
        manifest_service: Optional[ManifestService] = None,
        learning_rate: float = 0.1,
        discount_factor: float = 0.9,
        exploration_rate: float = 0.1,
        cost_weight: float = 0.3,
        latency_weight: float = 0.2,
        reward_weight: float = 0.5
    ):
        """
        Initialize Q-Learning
        
        Args:
            manifest_service: Manifest service for cost/latency data
            learning_rate: Learning rate (alpha)
            discount_factor: Discount factor (gamma)
            exploration_rate: Exploration rate (epsilon)
            cost_weight: Weight for cost in Q-value calculation
            latency_weight: Weight for latency in Q-value calculation
            reward_weight: Weight for reward in Q-value calculation
        """
        self.manifest_service = manifest_service
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.cost_weight = cost_weight
        self.latency_weight = latency_weight
        self.reward_weight = reward_weight
        
        # Q-tables per agent
        self.q_tables: Dict[str, np.ndarray] = {}
        self.state_spaces: Dict[str, Dict[str, int]] = {}
        self.action_spaces: Dict[str, Dict[str, int]] = {}
        self._logger = logging.getLogger(__name__)
    
    def initialize_agent(self, agent_id: str, num_states: int, num_actions: int) -> None:
        """
        Initialize Q-table for an agent
        
        Args:
            agent_id: Agent identifier
            num_states: Number of states
            num_actions: Number of actions
        """
        self.q_tables[agent_id] = np.zeros((num_states, num_actions))
        self.state_spaces[agent_id] = {}
        self.action_spaces[agent_id] = {}
        self._logger.debug(f"Initialized Q-table for agent {agent_id}: {num_states}x{num_actions}")
    
    def get_state_index(self, agent_id: str, state: str) -> int:
        """
        Get state index (create if not exists)
        
        Args:
            agent_id: Agent identifier
            state: State identifier
            
        Returns:
            State index
        """
        if agent_id not in self.state_spaces:
            self.state_spaces[agent_id] = {}
        
        if state not in self.state_spaces[agent_id]:
            self.state_spaces[agent_id][state] = len(self.state_spaces[agent_id])
        
        return self.state_spaces[agent_id][state]
    
    def get_action_index(self, agent_id: str, action: str) -> int:
        """
        Get action index (create if not exists)
        
        Args:
            agent_id: Agent identifier
            action: Action identifier
            
        Returns:
            Action index
        """
        if agent_id not in self.action_spaces:
            self.action_spaces[agent_id] = {}
        
        if action not in self.action_spaces[agent_id]:
            self.action_spaces[agent_id][action] = len(self.action_spaces[agent_id])
        
        return self.action_spaces[agent_id][action]
    
    def get_q_value(self, agent_id: str, state: str, action: str) -> float:
        """
        Get Q-value for state-action pair
        
        Args:
            agent_id: Agent identifier
            state: State identifier
            action: Action identifier
            
        Returns:
            Q-value
        """
        if agent_id not in self.q_tables:
            return 0.0
        
        state_idx = self.get_state_index(agent_id, state)
        action_idx = self.get_action_index(agent_id, action)
        
        # Ensure Q-table is large enough
        q_table = self.q_tables[agent_id]
        if state_idx >= q_table.shape[0] or action_idx >= q_table.shape[1]:
            self._resize_q_table(agent_id, state_idx + 1, action_idx + 1)
            q_table = self.q_tables[agent_id]
        
        return float(q_table[state_idx, action_idx])
    
    def update_q_value(
        self,
        agent_id: str,
        state: str,
        action: str,
        reward: float,
        next_state: str,
        cost: Optional[float] = None,
        latency: Optional[float] = None
    ) -> float:
        """
        Update Q-value using Q-learning algorithm with cost/latency awareness
        
        Args:
            agent_id: Agent identifier
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
            cost: Optional cost from manifest
            latency: Optional latency from manifest
            
        Returns:
            Updated Q-value
        """
        if agent_id not in self.q_tables:
            self.initialize_agent(agent_id, 10, 10)
        
        state_idx = self.get_state_index(agent_id, state)
        action_idx = self.get_action_index(agent_id, action)
        next_state_idx = self.get_state_index(agent_id, next_state)
        
        # Ensure Q-table is large enough
        max_state = max(state_idx, next_state_idx) + 1
        max_action = action_idx + 1
        if (max_state > self.q_tables[agent_id].shape[0] or
            max_action > self.q_tables[agent_id].shape[1]):
            self._resize_q_table(agent_id, max_state, max_action)
        
        q_table = self.q_tables[agent_id]
        
        # Get current Q-value
        current_q = q_table[state_idx, action_idx]
        
        # Get max Q-value for next state
        max_next_q = np.max(q_table[next_state_idx, :]) if next_state_idx < q_table.shape[0] else 0.0
        
        # Calculate adjusted reward (incorporate cost and latency)
        adjusted_reward = self._calculate_adjusted_reward(reward, cost, latency)
        
        # Q-learning update: Q(s,a) = Q(s,a) + α * (r + γ * max(Q(s',a')) - Q(s,a))
        new_q = current_q + self.learning_rate * (
            adjusted_reward + self.discount_factor * max_next_q - current_q
        )
        
        q_table[state_idx, action_idx] = new_q
        
        self._logger.debug(
            f"Updated Q-value for agent {agent_id}: "
            f"Q({state}, {action}) = {current_q:.4f} -> {new_q:.4f} "
            f"(reward: {reward:.4f}, adjusted: {adjusted_reward:.4f})"
        )
        
        return float(new_q)
    
    def _calculate_adjusted_reward(
        self,
        reward: float,
        cost: Optional[float],
        latency: Optional[float]
    ) -> float:
        """
        Calculate adjusted reward incorporating cost and latency
        
        Args:
            reward: Base reward
            cost: Cost from manifest
            latency: Latency from manifest
            
        Returns:
            Adjusted reward
        """
        adjusted = reward * self.reward_weight
        
        if cost is not None:
            # Penalize high cost (normalize to 0-1 range, assume max cost 1.0)
            cost_penalty = -min(cost, 1.0) * self.cost_weight
            adjusted += cost_penalty
        
        if latency is not None:
            # Penalize high latency (normalize to 0-1 range, assume max 10000ms)
            latency_penalty = -min(latency / 10000.0, 1.0) * self.latency_weight
            adjusted += latency_penalty
        
        return adjusted
    
    def select_action(self, agent_id: str, state: str, actions: list) -> str:
        """
        Select action using epsilon-greedy policy
        
        Args:
            agent_id: Agent identifier
            state: Current state
            actions: Available actions
            
        Returns:
            Selected action
        """
        import random
        
        if random.random() < self.exploration_rate:
            # Explore: random action
            return random.choice(actions)
        else:
            # Exploit: best action
            return self.get_best_action(agent_id, state, actions)
    
    def get_best_action(self, agent_id: str, state: str, actions: list) -> str:
        """
        Get best action for state (greedy policy)
        
        Args:
            agent_id: Agent identifier
            state: Current state
            actions: Available actions
            
        Returns:
            Best action
        """
        if not actions:
            return None
        
        if agent_id not in self.q_tables:
            return actions[0]
        
        state_idx = self.get_state_index(agent_id, state)
        q_table = self.q_tables[agent_id]
        
        if state_idx >= q_table.shape[0]:
            return actions[0]
        
        # Get Q-values for all actions
        action_q_values = []
        for action in actions:
            action_idx = self.get_action_index(agent_id, action)
            if action_idx < q_table.shape[1]:
                action_q_values.append((action, q_table[state_idx, action_idx]))
            else:
                action_q_values.append((action, 0.0))
        
        # Return action with highest Q-value
        best_action = max(action_q_values, key=lambda x: x[1])[0]
        return best_action
    
    def _resize_q_table(self, agent_id: str, num_states: int, num_actions: int) -> None:
        """Resize Q-table if needed"""
        old_table = self.q_tables[agent_id]
        new_table = np.zeros((num_states, num_actions))
        
        # Copy old values
        old_states, old_actions = old_table.shape
        new_table[:old_states, :old_actions] = old_table
        
        self.q_tables[agent_id] = new_table
        self._logger.debug(f"Resized Q-table for agent {agent_id} to {num_states}x{num_actions}")
    
    def get_q_table(self, agent_id: str) -> Optional[np.ndarray]:
        """
        Get Q-table for agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Q-table or None
        """
        return self.q_tables.get(agent_id)
    
    def get_statistics(self, agent_id: str) -> Dict[str, Any]:
        """
        Get learning statistics for agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Statistics dictionary
        """
        if agent_id not in self.q_tables:
            return {}
        
        q_table = self.q_tables[agent_id]
        
        return {
            "num_states": q_table.shape[0],
            "num_actions": q_table.shape[1],
            "max_q_value": float(np.max(q_table)),
            "min_q_value": float(np.min(q_table)),
            "mean_q_value": float(np.mean(q_table)),
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor,
            "exploration_rate": self.exploration_rate,
        }



