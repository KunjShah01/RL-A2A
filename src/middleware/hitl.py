"""
Human-in-the-Loop (HITL) Middleware
Intercepts messages requiring human approval
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

from src.core.message import Message
from src.core.events import EventBus, Event, EventType
from src.utils.config import Config


class ApprovalStatus(str, Enum):
    """Approval status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"


@dataclass
class ApprovalRequest:
    """Approval request data structure"""
    request_id: str
    message_id: str
    message: Message
    reason: str
    requester_id: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    timeout_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if approval request is expired"""
        if self.timeout_at:
            return datetime.now() > self.timeout_at
        return False


class ApprovalQueue:
    """Approval queue for HITL requests"""
    
    def __init__(self, timeout_seconds: int = None):
        """
        Initialize approval queue
        
        Args:
            timeout_seconds: Default timeout in seconds
        """
        self._queue: Dict[str, ApprovalRequest] = {}
        self._logger = logging.getLogger(__name__)
        self.default_timeout = timeout_seconds or Config.HITL_TIMEOUT_SECONDS
    
    def add_request(
        self,
        request_id: str,
        message: Message,
        reason: str,
        requester_id: str,
        timeout_seconds: Optional[int] = None
    ) -> ApprovalRequest:
        """
        Add approval request to queue
        
        Args:
            request_id: Request identifier
            message: Message requiring approval
            reason: Reason for approval requirement
            requester_id: Requester identifier
            timeout_seconds: Optional timeout in seconds
            
        Returns:
            Approval request
        """
        timeout = timeout_seconds or self.default_timeout
        timeout_at = datetime.now() + timedelta(seconds=timeout) if timeout > 0 else None
        
        request = ApprovalRequest(
            request_id=request_id,
            message_id=message.id,
            message=message,
            reason=reason,
            requester_id=requester_id,
            timeout_at=timeout_at
        )
        
        self._queue[request_id] = request
        self._logger.info(f"Added approval request {request_id} for message {message.id}")
        
        return request
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """
        Get approval request
        
        Args:
            request_id: Request identifier
            
        Returns:
            Approval request or None
        """
        return self._queue.get(request_id)
    
    def approve(self, request_id: str, approved_by: str) -> bool:
        """
        Approve a request
        
        Args:
            request_id: Request identifier
            approved_by: Approver identifier
            
        Returns:
            True if approved
        """
        request = self._queue.get(request_id)
        if not request:
            return False
        
        if request.status != ApprovalStatus.PENDING:
            self._logger.warning(f"Request {request_id} is not pending (status: {request.status})")
            return False
        
        request.status = ApprovalStatus.APPROVED
        request.approved_by = approved_by
        request.metadata["approved_at"] = datetime.now().isoformat()
        
        self._logger.info(f"Approved request {request_id} by {approved_by}")
        
        return True
    
    def reject(self, request_id: str, rejected_by: str, reason: str) -> bool:
        """
        Reject a request
        
        Args:
            request_id: Request identifier
            rejected_by: Rejector identifier
            reason: Rejection reason
            
        Returns:
            True if rejected
        """
        request = self._queue.get(request_id)
        if not request:
            return False
        
        if request.status != ApprovalStatus.PENDING:
            return False
        
        request.status = ApprovalStatus.REJECTED
        request.rejection_reason = reason
        request.metadata["rejected_by"] = rejected_by
        request.metadata["rejected_at"] = datetime.now().isoformat()
        
        self._logger.info(f"Rejected request {request_id} by {rejected_by}: {reason}")
        
        return True
    
    def list_pending(self) -> List[ApprovalRequest]:
        """List all pending requests"""
        return [r for r in self._queue.values() if r.status == ApprovalStatus.PENDING]
    
    def cleanup_expired(self) -> List[str]:
        """
        Clean up expired requests
        
        Returns:
            List of expired request IDs
        """
        expired_ids = []
        now = datetime.now()
        
        for request_id, request in list(self._queue.items()):
            if request.is_expired():
                request.status = ApprovalStatus.EXPIRED
                expired_ids.append(request_id)
                self._logger.info(f"Request {request_id} expired")
        
        return expired_ids


class HITLMiddleware:
    """
    Human-in-the-Loop Middleware
    
    Intercepts messages requiring human approval before processing
    """
    
    def __init__(
        self,
        approval_queue: ApprovalQueue,
        event_bus: Optional[EventBus] = None,
        auto_approve: bool = False
    ):
        """
        Initialize HITL middleware
        
        Args:
            approval_queue: Approval queue instance
            event_bus: Optional event bus
            auto_approve: Auto-approve if no timeout (for testing)
        """
        self.approval_queue = approval_queue
        self.event_bus = event_bus
        self.auto_approve = auto_approve
        self._logger = logging.getLogger(__name__)
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """
        Process message through HITL middleware
        
        Args:
            message: Message to process
            
        Returns:
            Message if approved, None if pending/rejected
        """
        # Check if message requires approval
        if not message.requires_approval:
            return message
        
        # Check metadata for approval flags
        metadata = message.metadata
        if metadata.get("sensitive_transaction") or metadata.get("requires_approval"):
            message.requires_approval = True
        
        if not message.requires_approval:
            return message
        
        # Create approval request
        import uuid
        request_id = str(uuid.uuid4())
        reason = metadata.get("approval_reason", "Message flagged for human approval")
        
        request = self.approval_queue.add_request(
            request_id=request_id,
            message=message,
            reason=reason,
            requester_id=message.sender_id or "system"
        )
        
        # Emit event
        if self.event_bus:
            event = Event(
                event_type=EventType.HITL_APPROVAL_REQUIRED,
                payload={
                    "request_id": request_id,
                    "message_id": message.id,
                    "reason": reason,
                },
                correlation_id=message.correlation_id
            )
            await self.event_bus.emit(event)
        
        # Auto-approve if enabled (for testing)
        if self.auto_approve:
            self.approval_queue.approve(request_id, "system")
            return message
        
        # Wait for approval (with timeout)
        return await self._wait_for_approval(request_id, message)
    
    async def _wait_for_approval(self, request_id: str, message: Message) -> Optional[Message]:
        """
        Wait for approval with timeout
        
        Args:
            request_id: Request identifier
            message: Original message
            
        Returns:
            Message if approved, None otherwise
        """
        timeout = Config.HITL_TIMEOUT_SECONDS
        start_time = datetime.now()
        
        while True:
            request = self.approval_queue.get_request(request_id)
            if not request:
                return None
            
            # Check status
            if request.status == ApprovalStatus.APPROVED:
                # Emit approval event
                if self.event_bus:
                    event = Event(
                        event_type=EventType.HITL_APPROVED,
                        payload={
                            "request_id": request_id,
                            "message_id": message.id,
                            "approved_by": request.approved_by,
                        }
                    )
                    await self.event_bus.emit(event)
                
                return message
            
            elif request.status == ApprovalStatus.REJECTED:
                # Emit rejection event
                if self.event_bus:
                    event = Event(
                        event_type=EventType.HITL_REJECTED,
                        payload={
                            "request_id": request_id,
                            "message_id": message.id,
                            "reason": request.rejection_reason,
                        }
                    )
                    await self.event_bus.emit(event)
                
                return None
            
            elif request.is_expired():
                return None
            
            # Check timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if timeout > 0 and elapsed > timeout:
                self._logger.warning(f"Approval timeout for request {request_id}")
                return None
            
            # Wait before checking again
            await asyncio.sleep(1)
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """
        Get list of pending approvals (for API/dashboard)
        
        Returns:
            List of approval request dictionaries
        """
        pending = self.approval_queue.list_pending()
        return [
            {
                "request_id": r.request_id,
                "message_id": r.message_id,
                "reason": r.reason,
                "requester_id": r.requester_id,
                "created_at": r.created_at.isoformat(),
                "timeout_at": r.timeout_at.isoformat() if r.timeout_at else None,
                "metadata": r.metadata,
            }
            for r in pending
        ]

