"""
Human-in-the-Loop endpoints
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from src.middleware.hitl import ApprovalQueue, HITLMiddleware

router = APIRouter()


def get_approval_queue(request: Request) -> ApprovalQueue:
    """Dependency to get approval queue"""
    return request.app.state.approval_queue


def get_hitl_middleware(request: Request) -> HITLMiddleware:
    """Dependency to get HITL middleware"""
    return request.app.state.hitl_middleware


class ApprovalActionRequest(BaseModel):
    request_id: str
    action: str  # "approve" or "reject"
    reason: Optional[str] = None
    approver_id: str


@router.get("/pending")
async def list_pending_approvals(
    middleware: HITLMiddleware = Depends(get_hitl_middleware)
):
    """List pending approval requests"""
    pending = middleware.get_pending_approvals()
    return {"pending": pending}


@router.post("/approve")
async def approve_request(
    request_data: ApprovalActionRequest,
    queue: ApprovalQueue = Depends(get_approval_queue)
):
    """Approve or reject a request"""
    if request_data.action == "approve":
        success = queue.approve(request_data.request_id, request_data.approver_id)
    elif request_data.action == "reject":
        success = queue.reject(
            request_data.request_id,
            request_data.approver_id,
            request_data.reason or "Rejected"
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    if not success:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return {"status": request_data.action, "request_id": request_data.request_id}



