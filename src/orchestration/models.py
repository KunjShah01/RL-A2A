"""
Workflow data models
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import uuid


class StepType(str, Enum):
    """Workflow step type enumeration"""
    AGENT_CALL = "agent_call"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    DELAY = "delay"
    PARALLEL = "parallel"
    WEBHOOK = "webhook"


class WorkflowStatus(str, Enum):
    """Workflow status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """Workflow step definition"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    step_type: StepType = StepType.AGENT_CALL
    name: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    next_steps: List[str] = field(default_factory=list)  # IDs of next steps
    condition: Optional[str] = None  # For conditional steps
    error_handler: Optional[str] = None  # ID of error handling step


@dataclass
class Workflow:
    """Workflow definition"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    steps: List[WorkflowStep] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "steps": [
                {
                    "id": s.id,
                    "step_type": s.step_type.value,
                    "name": s.name,
                    "config": s.config,
                    "next_steps": s.next_steps,
                    "condition": s.condition,
                    "error_handler": s.error_handler,
                }
                for s in self.steps
            ],
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        """Create workflow from dictionary"""
        steps = [
            WorkflowStep(
                id=s["id"],
                step_type=StepType(s["step_type"]),
                name=s["name"],
                config=s.get("config", {}),
                next_steps=s.get("next_steps", []),
                condition=s.get("condition"),
                error_handler=s.get("error_handler"),
            )
            for s in data.get("steps", [])
        ]
        
        created_at = datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else datetime.now()
        updated_at = datetime.fromisoformat(data["updated_at"]) if isinstance(data.get("updated_at"), str) else datetime.now()
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            steps=steps,
            status=WorkflowStatus(data.get("status", "draft")),
            created_at=created_at,
            updated_at=updated_at,
            metadata=data.get("metadata", {}),
        )


@dataclass
class WorkflowExecution:
    """Workflow execution instance"""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    status: WorkflowStatus = WorkflowStatus.RUNNING
    current_step: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    step_results: Dict[str, Any] = field(default_factory=dict)



