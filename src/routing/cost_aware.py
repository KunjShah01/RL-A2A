"""
Cost-Aware Router
Routes messages based on cost and latency metrics from manifests
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

from src.core.message import Message
from src.routing.manifest_service import ManifestService


class RoutingStrategy(str, Enum):
    """Routing strategy enumeration"""
    LOWEST_COST = "lowest_cost"
    LOWEST_LATENCY = "lowest_latency"
    BEST_VALUE = "best_value"  # Balance of cost and latency
    HIGHEST_SUCCESS = "highest_success"


class CostAwareRouter:
    """
    Cost-Aware Router
    
    Routes messages to agents based on cost, latency, and success rate metrics
    """
    
    def __init__(self, manifest_service: ManifestService):
        """
        Initialize cost-aware router
        
        Args:
            manifest_service: Manifest service instance
        """
        self.manifest_service = manifest_service
        self._logger = logging.getLogger(__name__)
        self.strategy = RoutingStrategy.BEST_VALUE
    
    def set_strategy(self, strategy: RoutingStrategy) -> None:
        """
        Set routing strategy
        
        Args:
            strategy: Routing strategy
        """
        self.strategy = strategy
        self._logger.info(f"Routing strategy set to: {strategy.value}")
    
    def select_agent(
        self,
        capability: str,
        strategy: Optional[RoutingStrategy] = None,
        max_cost: Optional[float] = None,
        max_latency: Optional[float] = None
    ) -> Optional[str]:
        """
        Select best agent for a capability based on strategy
        
        Args:
            capability: Required capability
            strategy: Optional routing strategy (uses instance strategy if None)
            max_cost: Optional maximum cost constraint
            max_latency: Optional maximum latency constraint
            
        Returns:
            Selected agent ID or None
        """
        strategy = strategy or self.strategy
        
        # Find agents with the capability
        candidates = self.manifest_service.find_agents_by_capability(capability)
        
        if not candidates:
            self._logger.warning(f"No agents found with capability: {capability}")
            return None
        
        # Apply constraints
        if max_cost or max_latency:
            filtered = []
            for manifest in candidates:
                metrics = manifest.get("metrics", {})
                cost = metrics.get("cost_rate", float('inf'))
                latency = metrics.get("latency_ms", float('inf'))
                
                if max_cost and cost > max_cost:
                    continue
                if max_latency and latency > max_latency:
                    continue
                
                filtered.append(manifest)
            
            candidates = filtered
        
        if not candidates:
            self._logger.warning("No candidates match constraints")
            return None
        
        # Select based on strategy
        if strategy == RoutingStrategy.LOWEST_COST:
            selected = min(candidates, key=lambda m: m.get("metrics", {}).get("cost_rate", float('inf')))
        elif strategy == RoutingStrategy.LOWEST_LATENCY:
            selected = min(candidates, key=lambda m: m.get("metrics", {}).get("latency_ms", float('inf')))
        elif strategy == RoutingStrategy.HIGHEST_SUCCESS:
            selected = max(candidates, key=lambda m: m.get("metrics", {}).get("success_rate", 0.0))
        else:  # BEST_VALUE
            selected = self._select_best_value(candidates)
        
        agent_id = selected.get("agent_id")
        self._logger.info(f"Selected agent {agent_id} for capability {capability} using strategy {strategy.value}")
        
        return agent_id
    
    def _select_best_value(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Select agent with best value (balanced cost and latency)
        
        Args:
            candidates: List of candidate manifests
            
        Returns:
            Selected manifest
        """
        best_score = float('-inf')
        best_candidate = None
        
        for manifest in candidates:
            metrics = manifest.get("metrics", {})
            cost = metrics.get("cost_rate", 1.0)
            latency = metrics.get("latency_ms", 1000.0)
            success = metrics.get("success_rate", 0.5)
            
            # Normalize and combine metrics
            # Lower cost and latency are better, higher success is better
            # Score = success_rate * 0.5 - (cost_rate * 0.25 + latency_ms / 10000 * 0.25)
            normalized_latency = latency / 10000.0  # Normalize to 0-1 range (assuming max 10s)
            score = success * 0.5 - (cost * 0.25 + normalized_latency * 0.25)
            
            if score > best_score:
                best_score = score
                best_candidate = manifest
        
        return best_candidate
    
    def rank_agents(
        self,
        capability: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Rank agents by routing strategy
        
        Args:
            capability: Required capability
            limit: Maximum number of agents to return
            
        Returns:
            List of ranked agent manifests
        """
        candidates = self.manifest_service.find_agents_by_capability(capability)
        
        if not candidates:
            return []
        
        # Sort based on strategy
        if self.strategy == RoutingStrategy.LOWEST_COST:
            candidates.sort(key=lambda m: m.get("metrics", {}).get("cost_rate", float('inf')))
        elif self.strategy == RoutingStrategy.LOWEST_LATENCY:
            candidates.sort(key=lambda m: m.get("metrics", {}).get("latency_ms", float('inf')))
        elif self.strategy == RoutingStrategy.HIGHEST_SUCCESS:
            candidates.sort(key=lambda m: m.get("metrics", {}).get("success_rate", 0.0), reverse=True)
        else:  # BEST_VALUE
            # Calculate scores and sort
            scored = []
            for manifest in candidates:
                metrics = manifest.get("metrics", {})
                cost = metrics.get("cost_rate", 1.0)
                latency = metrics.get("latency_ms", 1000.0)
                success = metrics.get("success_rate", 0.5)
                normalized_latency = latency / 10000.0
                score = success * 0.5 - (cost * 0.25 + normalized_latency * 0.25)
                scored.append((score, manifest))
            
            scored.sort(key=lambda x: x[0], reverse=True)
            candidates = [m for _, m in scored]
        
        return candidates[:limit]



