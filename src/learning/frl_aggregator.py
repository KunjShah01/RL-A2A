"""
Federated Reinforcement Learning Aggregator
Aggregates model updates from multiple RL-A2A instances
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import json

from src.utils.config import Config


class FRLAggregator:
    """
    Federated RL Aggregator
    
    Aggregates Q-table updates from multiple RL-A2A instances
    Uses secure aggregation without sharing raw data
    """
    
    def __init__(self, aggregation_server: Optional[str] = None):
        """
        Initialize FRL aggregator
        
        Args:
            aggregation_server: Optional aggregation server URL
        """
        self.aggregation_server = aggregation_server or Config.FRL_AGGREGATION_SERVER
        self._logger = logging.getLogger(__name__)
        self._update_buffer: Dict[str, List[Dict[str, Any]]] = {}
        self._aggregation_interval = Config.FRL_AGGREGATION_INTERVAL
    
    def submit_update(
        self,
        agent_id: str,
        q_table: np.ndarray,
        instance_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Submit Q-table update for aggregation
        
        Args:
            agent_id: Agent identifier
            q_table: Q-table numpy array
            instance_id: RL-A2A instance identifier
            metadata: Optional metadata
            
        Returns:
            Update ID
        """
        # Create update record
        update_id = hashlib.sha256(
            f"{agent_id}:{instance_id}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        update = {
            "update_id": update_id,
            "agent_id": agent_id,
            "instance_id": instance_id,
            "q_table": q_table.tolist(),  # Convert to list for JSON serialization
            "shape": q_table.shape,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        
        # Buffer update
        if agent_id not in self._update_buffer:
            self._update_buffer[agent_id] = []
        
        self._update_buffer[agent_id].append(update)
        
        self._logger.info(f"Submitted FRL update {update_id} for agent {agent_id} from instance {instance_id}")
        
        return update_id
    
    def aggregate_updates(self, agent_id: str) -> Optional[np.ndarray]:
        """
        Aggregate Q-table updates for an agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Aggregated Q-table or None
        """
        if agent_id not in self._update_buffer or not self._update_buffer[agent_id]:
            return None
        
        updates = self._update_buffer[agent_id]
        
        if len(updates) < 2:
            # Need at least 2 updates for aggregation
            self._logger.debug(f"Insufficient updates for aggregation: {len(updates)}")
            return None
        
        # Get first update shape
        first_shape = updates[0]["shape"]
        
        # Convert all updates to numpy arrays
        q_tables = []
        for update in updates:
            q_table = np.array(update["q_table"])
            if q_table.shape != first_shape:
                self._logger.warning(f"Q-table shape mismatch: {q_table.shape} vs {first_shape}")
                # Resize to match first shape
                resized = np.zeros(first_shape)
                min_shape = (min(q_table.shape[0], first_shape[0]),
                           min(q_table.shape[1], first_shape[1]))
                resized[:min_shape[0], :min_shape[1]] = q_table[:min_shape[0], :min_shape[1]]
                q_table = resized
            q_tables.append(q_table)
        
        # Federated averaging
        aggregated = np.mean(q_tables, axis=0)
        
        self._logger.info(f"Aggregated {len(updates)} updates for agent {agent_id}")
        
        # Clear buffer
        self._update_buffer[agent_id] = []
        
        return aggregated
    
    def apply_differential_privacy(
        self,
        q_table: np.ndarray,
        epsilon: float = 1.0,
        sensitivity: float = 1.0
    ) -> np.ndarray:
        """
        Apply differential privacy to Q-table
        
        Args:
            q_table: Q-table to privatize
            epsilon: Privacy budget (epsilon)
            sensitivity: Sensitivity of the function
            
        Returns:
            Privatized Q-table
        """
        # Add Laplacian noise
        noise_scale = sensitivity / epsilon
        noise = np.random.laplace(0, noise_scale, q_table.shape)
        privatized = q_table + noise
        
        self._logger.debug(f"Applied differential privacy (epsilon={epsilon})")
        
        return privatized
    
    def get_update_statistics(self, agent_id: str) -> Dict[str, Any]:
        """
        Get statistics about pending updates
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Statistics dictionary
        """
        updates = self._update_buffer.get(agent_id, [])
        
        return {
            "agent_id": agent_id,
            "pending_updates": len(updates),
            "instances": list(set(u["instance_id"] for u in updates)),
            "oldest_update": updates[0]["timestamp"] if updates else None,
            "newest_update": updates[-1]["timestamp"] if updates else None,
        }
    
    def clear_updates(self, agent_id: Optional[str] = None) -> None:
        """
        Clear update buffer
        
        Args:
            agent_id: Optional agent ID (clear all if None)
        """
        if agent_id:
            if agent_id in self._update_buffer:
                del self._update_buffer[agent_id]
        else:
            self._update_buffer.clear()
        
        self._logger.debug(f"Cleared updates for agent: {agent_id or 'all'}")



