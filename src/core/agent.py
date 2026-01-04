"""
Agent data model with DID support
Enhanced agent representation for RL-A2A v2.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class AgentStatus(str, Enum):
    """Agent status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


@dataclass
class Agent:
    """
    Enhanced Agent model with DID support and comprehensive metadata
    
    Attributes:
        id: Unique agent identifier (UUID)
        did: Decentralized Identifier for the agent
        name: Human-readable agent name
        role: Agent role/type
        status: Current agent status
        capabilities: List of agent capabilities
        public_key: Public key for message signing/verification
        state: Agent state dictionary
        memory: Agent memory/context
        performance_metrics: Performance tracking metrics
        security_level: Security classification
        ai_provider: Preferred AI provider
        created_at: Creation timestamp
        last_active: Last activity timestamp
        manifest_version: Version of agent manifest
    """
    
    id: str
    name: str
    did: Optional[str] = None
    role: str = "general"
    status: AgentStatus = AgentStatus.PENDING
    capabilities: List[str] = field(default_factory=list)
    public_key: Optional[str] = None
    state: Dict[str, Any] = field(default_factory=dict)
    memory: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    security_level: str = "standard"
    ai_provider: str = "openai"
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    manifest_version: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default values"""
        if not self.capabilities:
            self.capabilities = ["communication", "learning", "reasoning"]
        if not self.performance_metrics:
            self.performance_metrics = {
                "success_rate": 0.0,
                "response_time": 0.0,
                "learning_rate": 0.0,
                "collaboration_score": 0.0,
                "cost_efficiency": 0.0,
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary"""
        return {
            "id": self.id,
            "did": self.did,
            "name": self.name,
            "role": self.role,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "public_key": self.public_key,
            "state": self.state,
            "performance_metrics": self.performance_metrics,
            "security_level": self.security_level,
            "ai_provider": self.ai_provider,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "manifest_version": self.manifest_version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Agent":
        """Create agent from dictionary"""
        data = data.copy()
        if "status" in data and isinstance(data["status"], str):
            data["status"] = AgentStatus(data["status"])
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "last_active" in data and isinstance(data["last_active"], str):
            data["last_active"] = datetime.fromisoformat(data["last_active"])
        return cls(**data)
    
    def update_last_active(self):
        """Update last active timestamp"""
        self.last_active = datetime.now()
    
    def update_metrics(self, metrics: Dict[str, float]):
        """Update performance metrics"""
        self.performance_metrics.update(metrics)



