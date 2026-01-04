"""
Reward Calculator
Calculates rewards for RL considering cost and latency metrics
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from src.routing.manifest_service import ManifestService


class RewardCalculator:
    """
    Reward Calculator
    
    Calculates rewards for reinforcement learning considering
    performance, cost, and latency metrics from agent manifests
    """
    
    def __init__(self, manifest_service: Optional[ManifestService] = None):
        """
        Initialize reward calculator
        
        Args:
            manifest_service: Manifest service for metrics
        """
        self.manifest_service = manifest_service
        self._logger = logging.getLogger(__name__)
    
    def calculate_reward(
        self,
        agent_id: str,
        success: bool,
        response_time: Optional[float] = None,
        cost: Optional[float] = None,
        base_reward: float = 1.0,
        cost_penalty_weight: float = 0.2,
        latency_penalty_weight: float = 0.1
    ) -> float:
        """
        Calculate reward for an action
        
        Args:
            agent_id: Agent identifier
            success: Whether the action was successful
            response_time: Response time in milliseconds
            cost: Actual cost incurred
            base_reward: Base reward for success (default 1.0)
            cost_penalty_weight: Weight for cost penalty (0-1)
            latency_penalty_weight: Weight for latency penalty (0-1)
            
        Returns:
            Calculated reward
        """
        # Start with base reward/penalty
        reward = base_reward if success else -base_reward
        
        # Get manifest metrics if available
        manifest_metrics = None
        if self.manifest_service:
            manifest = self.manifest_service.get_manifest(agent_id)
            if manifest:
                manifest_metrics = manifest.get("metrics", {})
        
        # Apply cost penalty
        if cost is not None:
            cost_penalty = cost * cost_penalty_weight
            reward -= cost_penalty
        elif manifest_metrics:
            expected_cost = manifest_metrics.get("cost_rate", 0.0)
            cost_penalty = expected_cost * cost_penalty_weight
            reward -= cost_penalty
        
        # Apply latency penalty
        if response_time is not None:
            # Normalize latency (assume max 10 seconds)
            normalized_latency = min(response_time / 10000.0, 1.0)
            latency_penalty = normalized_latency * latency_penalty_weight
            reward -= latency_penalty
        elif manifest_metrics:
            expected_latency = manifest_metrics.get("latency_ms", 1000.0)
            normalized_latency = min(expected_latency / 10000.0, 1.0)
            latency_penalty = normalized_latency * latency_penalty_weight
            reward -= latency_penalty
        
        # Apply success rate bonus if manifest available
        if manifest_metrics and success:
            success_rate = manifest_metrics.get("success_rate", 0.5)
            # Bonus for agents with high success rates
            success_bonus = (success_rate - 0.5) * 0.1
            reward += success_bonus
        
        self._logger.debug(
            f"Calculated reward for agent {agent_id}: {reward:.4f} "
            f"(success: {success}, cost: {cost}, latency: {response_time})"
        )
        
        return reward
    
    def calculate_composite_reward(
        self,
        agent_id: str,
        metrics: Dict[str, Any]
    ) -> float:
        """
        Calculate composite reward from multiple metrics
        
        Args:
            agent_id: Agent identifier
            metrics: Dictionary of metrics (success, response_time, cost, etc.)
            
        Returns:
            Composite reward
        """
        success = metrics.get("success", False)
        response_time = metrics.get("response_time")
        cost = metrics.get("cost")
        
        return self.calculate_reward(
            agent_id=agent_id,
            success=success,
            response_time=response_time,
            cost=cost,
            base_reward=metrics.get("base_reward", 1.0)
        )

