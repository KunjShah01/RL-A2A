"""
Workflow endpoints
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from src.orchestration.workflow_engine import WorkflowEngine
from src.orchestration.models import Workflow, WorkflowStatus

router = APIRouter()


def get_workflow_engine(request: Request) -> WorkflowEngine:
    """Dependency to get workflow engine"""
    if not hasattr(request.app.state, 'workflow_engine'):
        # Initialize workflow engine if not exists
        from src.orchestration.executor import StepExecutor
        from src.utils.storage import MemoryStorage
        
        executor = StepExecutor(
            agent_registry=request.app.state.agent_registry,
            message_router=request.app.state.message_router
        )
        
        engine = WorkflowEngine(
            step_executor=executor,
            storage=MemoryStorage(),
            event_bus=request.app.state.event_bus
        )
        request.app.state.workflow_engine = engine
    
    return request.app.state.workflow_engine


class WorkflowCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    steps: List[Dict[str, Any]]


@router.post("", response_model=Dict[str, Any])
async def create_workflow(
    request_data: WorkflowCreateRequest,
    engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """Create a workflow"""
    from src.orchestration.models import WorkflowStep, StepType
    
    steps = [
        WorkflowStep(
            id=step.get("id", ""),
            step_type=StepType(step.get("step_type", "agent_call")),
            name=step.get("name", ""),
            config=step.get("config", {}),
            next_steps=step.get("next_steps", [])
        )
        for step in request_data.steps
    ]
    
    workflow = Workflow(
        name=request_data.name,
        description=request_data.description or "",
        steps=steps,
        status=WorkflowStatus.DRAFT
    )
    
    engine.register_workflow(workflow)
    
    return workflow.to_dict()


@router.get("", response_model=List[Dict[str, Any]])
async def list_workflows(
    engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """List all workflows"""
    workflows = engine.list_workflows()
    return [w.to_dict() for w in workflows]


@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    initial_context: Optional[Dict[str, Any]] = None,
    engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """Execute a workflow"""
    execution = await engine.execute_workflow(workflow_id, initial_context or {})
    
    return {
        "execution_id": execution.execution_id,
        "workflow_id": workflow_id,
        "status": execution.status.value,
        "error": execution.error
    }

