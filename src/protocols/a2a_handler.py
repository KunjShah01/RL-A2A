"""
A2A Protocol Handler
Agent-to-Agent protocol methods (tasks/send, tasks/status, tasks/cancel)
"""

import uuid
import logging
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime

from .jsonrpc import JSONRPCHandler, JSONRPCRequest, JSONRPCResponse


class A2AMethod(str, Enum):
    """A2A protocol methods"""
    TASKS_SEND = "tasks/send"
    TASKS_STATUS = "tasks/status"
    TASKS_CANCEL = "tasks/cancel"


class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class A2AHandler:
    """
    A2A Protocol Handler
    
    Implements Agent-to-Agent protocol methods using JSON-RPC 2.0
    """
    
    def __init__(self, message_router=None, task_store=None):
        """
        Initialize A2A handler
        
        Args:
            message_router: Message router for sending messages
            task_store: Task store for tracking tasks
        """
        self.message_router = message_router
        self.task_store = task_store or {}
        self._logger = logging.getLogger(__name__)
        self.jsonrpc_handler = JSONRPCHandler()
        
        # Register A2A methods
        self.jsonrpc_handler.register_method(A2AMethod.TASKS_SEND, self._handle_tasks_send)
        self.jsonrpc_handler.register_method(A2AMethod.TASKS_STATUS, self._handle_tasks_status)
        self.jsonrpc_handler.register_method(A2AMethod.TASKS_CANCEL, self._handle_tasks_cancel)
    
    async def _handle_tasks_send(
        self,
        task: Dict[str, Any],
        target_agent: str,
        priority: int = 2,
        sender_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Handle tasks/send method
        
        Args:
            task: Task data
            target_agent: Target agent ID or DID
            priority: Task priority (1-4)
            sender_id: Optional sender agent ID
            **kwargs: Additional parameters
            
        Returns:
            Task creation result with task_id
        """
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Create task record
        task_record = {
            "task_id": task_id,
            "task": task,
            "target_agent": target_agent,
            "sender_id": sender_id,
            "priority": priority,
            "status": TaskStatus.PENDING.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        # Store task
        self.task_store[task_id] = task_record
        
        # Route message if router is available
        if self.message_router:
            from src.core.message import Message, MessageType, MessagePriority
            
            message = Message(
                id=str(uuid.uuid4()),
                sender_id=sender_id or "",
                receiver_id=target_agent,
                content=task,
                message_type=MessageType.TASK,
                priority=MessagePriority(min(max(priority, 1), 4)),
                task_id=task_id,
                metadata={"a2a_method": A2AMethod.TASKS_SEND},
            )
            
            try:
                await self.message_router.route(message)
            except Exception as e:
                self._logger.error(f"Error routing task message: {e}", exc_info=True)
                task_record["status"] = TaskStatus.FAILED.value
                task_record["error"] = str(e)
        
        self._logger.info(f"Created task {task_id} for agent {target_agent}")
        
        return {
            "task_id": task_id,
            "status": task_record["status"],
        }
    
    async def _handle_tasks_status(self, task_id: str) -> Dict[str, Any]:
        """
        Handle tasks/status method
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status information
        """
        task_record = self.task_store.get(task_id)
        if not task_record:
            raise ValueError(f"Task not found: {task_id}")
        
        return {
            "task_id": task_id,
            "status": task_record["status"],
            "created_at": task_record["created_at"],
            "updated_at": task_record.get("updated_at"),
            "result": task_record.get("result"),
            "error": task_record.get("error"),
        }
    
    async def _handle_tasks_cancel(self, task_id: str) -> Dict[str, Any]:
        """
        Handle tasks/cancel method
        
        Args:
            task_id: Task identifier
            
        Returns:
            Cancellation result
        """
        task_record = self.task_store.get(task_id)
        if not task_record:
            raise ValueError(f"Task not found: {task_id}")
        
        if task_record["status"] in [TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value]:
            raise ValueError(f"Cannot cancel task in status: {task_record['status']}")
        
        # Update task status
        task_record["status"] = TaskStatus.CANCELLED.value
        task_record["updated_at"] = datetime.now().isoformat()
        
        self._logger.info(f"Cancelled task {task_id}")
        
        return {
            "task_id": task_id,
            "status": task_record["status"],
        }
    
    def update_task_status(self, task_id: str, status: TaskStatus, result: Any = None, error: str = None) -> bool:
        """
        Update task status (called by message router/processor)
        
        Args:
            task_id: Task identifier
            status: New status
            result: Optional result data
            error: Optional error message
            
        Returns:
            True if updated
        """
        task_record = self.task_store.get(task_id)
        if not task_record:
            return False
        
        task_record["status"] = status.value
        task_record["updated_at"] = datetime.now().isoformat()
        if result is not None:
            task_record["result"] = result
        if error:
            task_record["error"] = error
        
        return True
    
    async def handle_request(self, request_data: Dict[str, Any]) -> JSONRPCResponse:
        """
        Handle JSON-RPC request (delegates to JSON-RPC handler)
        
        Args:
            request_data: JSON-RPC request data
            
        Returns:
            JSON-RPC response
        """
        return await self.jsonrpc_handler.handle_request(request_data)



