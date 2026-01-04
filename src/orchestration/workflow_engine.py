"""
Workflow Engine
Executes and manages workflows
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.orchestration.models import Workflow, WorkflowExecution, WorkflowStatus
from src.orchestration.executor import StepExecutor
from src.core.events import EventBus, Event, EventType
from src.utils.storage import Storage, MemoryStorage


class WorkflowEngine:
    """Workflow execution engine"""
    
    def __init__(
        self,
        step_executor: StepExecutor,
        storage: Optional[Storage] = None,
        event_bus: Optional[EventBus] = None
    ):
        """
        Initialize workflow engine
        
        Args:
            step_executor: Step executor instance
            storage: Storage backend
            event_bus: Optional event bus
        """
        self.step_executor = step_executor
        self.storage = storage or MemoryStorage()
        self.event_bus = event_bus
        self._logger = logging.getLogger(__name__)
        self._executions: Dict[str, WorkflowExecution] = {}
    
    def register_workflow(self, workflow: Workflow) -> None:
        """
        Register a workflow
        
        Args:
            workflow: Workflow to register
        """
        key = f"workflow:{workflow.id}"
        self.storage.set(key, workflow.to_dict())
        self._logger.info(f"Registered workflow: {workflow.id} ({workflow.name})")
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """
        Get workflow by ID
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Workflow or None
        """
        key = f"workflow:{workflow_id}"
        data = self.storage.get(key)
        if data:
            return Workflow.from_dict(data)
        return None
    
    async def execute_workflow(
        self,
        workflow_id: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """
        Execute a workflow
        
        Args:
            workflow_id: Workflow identifier
            initial_context: Initial execution context
            
        Returns:
            Workflow execution instance
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Create execution
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            context=initial_context or {}
        )
        
        self._executions[execution.execution_id] = execution
        
        # Emit event
        if self.event_bus:
            event = Event(
                event_type=EventType.WORKFLOW_STARTED,
                payload={
                    "execution_id": execution.execution_id,
                    "workflow_id": workflow_id,
                }
            )
            await self.event_bus.emit(event)
        
        try:
            # Execute workflow steps
            await self._execute_steps(workflow, execution)
            
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.now()
            
            # Emit completion event
            if self.event_bus:
                event = Event(
                    event_type=EventType.WORKFLOW_COMPLETED,
                    payload={
                        "execution_id": execution.execution_id,
                        "workflow_id": workflow_id,
                    }
                )
                await self.event_bus.emit(event)
        
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.now()
            self._logger.error(f"Workflow execution failed: {e}", exc_info=True)
        
        return execution
    
    async def _execute_steps(self, workflow: Workflow, execution: WorkflowExecution) -> None:
        """Execute workflow steps"""
        # Find start step (first step or step with no dependencies)
        if not workflow.steps:
            return
        
        # Simple sequential execution (in production, handle branching, loops, etc.)
        current_step = workflow.steps[0]
        
        while current_step:
            execution.current_step = current_step.id
            
            # Execute step
            result = await self.step_executor.execute_step(current_step, execution.context)
            execution.step_results[current_step.id] = result
            
            # Update context
            execution.context.update(result.get("result", {}))
            
            # Get next step
            next_step_id = result.get("next_step")
            if next_step_id:
                current_step = next((s for s in workflow.steps if s.id == next_step_id), None)
            elif current_step.next_steps:
                current_step = next((s for s in workflow.steps if s.id == current_step.next_steps[0]), None)
            else:
                break
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution by ID"""
        return self._executions.get(execution_id)
    
    def list_workflows(self) -> List[Workflow]:
        """List all workflows"""
        keys = self.storage.list_keys("workflow:")
        workflows = []
        for key in keys:
            data = self.storage.get(key)
            if data:
                workflows.append(Workflow.from_dict(data))
        return workflows



