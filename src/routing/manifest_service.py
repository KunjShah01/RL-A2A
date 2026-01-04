"""
Agent Manifest Service
Manages agent manifests for capability discovery
"""

import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from src.core.agent import Agent
from src.utils.storage import Storage, MemoryStorage


class ManifestService:
    """
    Agent Manifest Service
    
    Manages agent manifests for capability discovery and routing
    """
    
    def __init__(self, storage: Optional[Storage] = None):
        """
        Initialize manifest service
        
        Args:
            storage: Storage backend (defaults to MemoryStorage)
        """
        self.storage = storage or MemoryStorage()
        self._logger = logging.getLogger(__name__)
        self._manifest_cache: Dict[str, Dict[str, Any]] = {}
    
    def create_manifest(self, agent: Agent, manifest_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update agent manifest
        
        Args:
            agent: Agent instance
            manifest_data: Manifest data
            
        Returns:
            Created manifest
        """
        manifest = {
            "agent_id": agent.id,
            "did": agent.did,
            "version": manifest_data.get("version", "1.0.0"),
            "capabilities": manifest_data.get("capabilities", agent.capabilities),
            "schemas": manifest_data.get("schemas", {}),
            "metrics": manifest_data.get("metrics", {}),
            "endpoints": manifest_data.get("endpoints", {}),
            "metadata": manifest_data.get("metadata", {}),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        # Store manifest
        key = f"manifest:{agent.id}"
        self.storage.set(key, manifest)
        self._manifest_cache[agent.id] = manifest
        
        self._logger.info(f"Created manifest for agent: {agent.id}")
        
        return manifest
    
    def get_manifest(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent manifest
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Manifest dictionary or None
        """
        # Check cache
        if agent_id in self._manifest_cache:
            return self._manifest_cache[agent_id]
        
        # Load from storage
        key = f"manifest:{agent_id}"
        manifest = self.storage.get(key)
        
        if manifest:
            self._manifest_cache[agent_id] = manifest
        
        return manifest
    
    def update_manifest(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update agent manifest
        
        Args:
            agent_id: Agent identifier
            updates: Updates to apply
            
        Returns:
            True if updated
        """
        manifest = self.get_manifest(agent_id)
        if not manifest:
            return False
        
        # Apply updates
        manifest.update(updates)
        manifest["updated_at"] = datetime.now().isoformat()
        
        # Store updated manifest
        key = f"manifest:{agent_id}"
        self.storage.set(key, manifest)
        self._manifest_cache[agent_id] = manifest
        
        self._logger.debug(f"Updated manifest for agent: {agent_id}")
        
        return True
    
    def delete_manifest(self, agent_id: str) -> bool:
        """
        Delete agent manifest
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if deleted
        """
        key = f"manifest:{agent_id}"
        deleted = self.storage.delete(key)
        
        if agent_id in self._manifest_cache:
            del self._manifest_cache[agent_id]
        
        if deleted:
            self._logger.info(f"Deleted manifest for agent: {agent_id}")
        
        return deleted
    
    def find_agents_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """
        Find agents with a specific capability
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of manifests with the capability
        """
        manifests = []
        keys = self.storage.list_keys("manifest:")
        
        for key in keys:
            manifest = self.storage.get(key)
            if manifest and capability in manifest.get("capabilities", []):
                manifests.append(manifest)
        
        return manifests
    
    def find_agents_by_metrics(
        self,
        max_cost_rate: Optional[float] = None,
        max_latency_ms: Optional[float] = None,
        min_success_rate: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Find agents matching metric criteria
        
        Args:
            max_cost_rate: Maximum cost rate
            max_latency_ms: Maximum latency in milliseconds
            min_success_rate: Minimum success rate
            
        Returns:
            List of matching manifests
        """
        manifests = []
        keys = self.storage.list_keys("manifest:")
        
        for key in keys:
            manifest = self.storage.get(key)
            if not manifest:
                continue
            
            metrics = manifest.get("metrics", {})
            cost_rate = metrics.get("cost_rate", float('inf'))
            latency_ms = metrics.get("latency_ms", float('inf'))
            success_rate = metrics.get("success_rate", 0.0)
            
            # Check criteria
            if max_cost_rate and cost_rate > max_cost_rate:
                continue
            if max_latency_ms and latency_ms > max_latency_ms:
                continue
            if min_success_rate and success_rate < min_success_rate:
                continue
            
            manifests.append(manifest)
        
        return manifests
    
    def list_all_manifests(self) -> List[Dict[str, Any]]:
        """
        List all agent manifests
        
        Returns:
            List of all manifests
        """
        manifests = []
        keys = self.storage.list_keys("manifest:")
        
        for key in keys:
            manifest = self.storage.get(key)
            if manifest:
                manifests.append(manifest)
        
        return manifests



