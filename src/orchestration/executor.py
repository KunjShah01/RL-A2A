"""
Workflow Step Executor
Executes individual workflow steps
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from src.orchestration.models import WorkflowStep, StepType
from src.core.registry import AgentRegistry
from src.routing.message_router import MessageRouter


class StepExecutor:
    """Executes workflow steps"""
    
    def __init__(
        self,
        agent_registry: AgentRegistry,
        message_router: MessageRouter
    ):
        """
        Initialize step executor
        
        Args:
            agent_registry: Agent registry instance
            message_router: Message router instance
        """
        self.agent_registry = agent_registry
        self.message_router = message_router
        self._logger = logging.getLogger(__name__)
    
    async def execute_step(
        self,
        step: WorkflowStep,
        execution_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a workflow step
        
        Args:
            step: Workflow step to execute
            execution_context: Execution context
            
        Returns:
            Step execution result
        """
        try:
            if step.step_type == StepType.AGENT_CALL:
                return await self._execute_agent_call(step, execution_context)
            elif step.step_type == StepType.CONDITIONAL:
                return await self._execute_conditional(step, execution_context)
            elif step.step_type == StepType.LOOP:
                return await self._execute_loop(step, execution_context)
            elif step.step_type == StepType.DELAY:
                return await self._execute_delay(step, execution_context)
            elif step.step_type == StepType.PARALLEL:
                return await self._execute_parallel(step, execution_context)
            else:
                raise ValueError(f"Unsupported step type: {step.step_type}")
        
        except Exception as e:
            self._logger.error(f"Error executing step {step.id}: {e}", exc_info=True)
            raise
    
    async def _execute_agent_call(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agent call step"""
        config = step.config
        agent_id = config.get("agent_id")
        capability = config.get("capability")
        message_content = config.get("message", {})
        
        if not agent_id and not capability:
            raise ValueError("agent_id or capability required")
        
        # Route message to agent
        from src.core.message import Message, MessageType
        
        message = Message(
            sender_id=context.get("workflow_id", "workflow"),
            receiver_id=agent_id or "",
            content=message_content,
            message_type=MessageType.TASK,
            metadata={"capability": capability, "workflow_step": step.id}
        )
        
        await self.message_router.route(message)
        
        return {
            "step_id": step.id,
            "status": "completed",
            "result": {"message_sent": True}
        }
    
    async def _execute_conditional(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute conditional step"""
        condition = step.condition
        if not condition:
            raise ValueError("Condition required for conditional step")
        
        # Evaluate condition (simplified - in production, use proper expression evaluator)
        result = eval(condition, {"context": context, "__builtins__": {}})
        
        return {
            "step_id": step.id,
            "status": "completed",
            "result": {"condition_result": bool(result)},
            "next_step": step.next_steps[0] if result and step.next_steps else step.next_steps[1] if step.next_steps else None
        }
    
    async def _execute_loop(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute loop step"""
        config = step.config
        iterations = config.get("iterations", 1)
        loop_steps = config.get("steps", [])
        
        results = []
        for i in range(iterations):
            # Execute loop steps (simplified)
            results.append({"iteration": i})
        
        return {
            "step_id": step.id,
            "status": "completed",
            "result": {"iterations": results}
        }
    
    async def _execute_delay(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute delay step"""
        config = step.config
        delay_seconds = config.get("delay_seconds", 1)
        
        await asyncio.sleep(delay_seconds)
        
        return {
            "step_id": step.id,
            "status": "completed",
            "result": {"delayed": delay_seconds}
        }
    
    async def _execute_parallel(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute parallel steps"""
        config = step.config
        parallel_steps = config.get("steps", [])
        
        # Execute steps in parallel (simplified)
        tasks = []
        for sub_step in parallel_steps:
            # In production, create actual step objects and execute
            tasks.append(asyncio.create_task(asyncio.sleep(0.1)))
        
        await asyncio.gather(*tasks)
        
        return {
            "step_id": step.id,
            "status": "completed",
            "result": {"parallel_completed": len(parallel_steps)}
        }



