"""
Agent Manifest endpoints
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from src.routing.manifest_service import ManifestService
from src.core.registry import AgentRegistry

router = APIRouter()


def get_manifest_service(request: Request) -> ManifestService:
    """Dependency to get manifest service"""
    return request.app.state.manifest_service


def get_agent_registry(request: Request) -> AgentRegistry:
    """Dependency to get agent registry"""
    return request.app.state.agent_registry


class ManifestCreateRequest(BaseModel):
    capabilities: List[str]
    schemas: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, float]] = None
    endpoints: Optional[Dict[str, str]] = None
    version: str = "1.0.0"


@router.get("/{agent_id}")
async def get_manifest(
    agent_id: str,
    manifest_service: ManifestService = Depends(get_manifest_service),
    registry: AgentRegistry = Depends(get_agent_registry)
):
    """Get agent manifest"""
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    manifest = manifest_service.get_manifest(agent_id)
    if not manifest:
        # Return basic manifest from agent data
        return {
            "agent_id": agent_id,
            "did": agent.did,
            "capabilities": agent.capabilities,
            "version": "1.0.0"
        }
    
    return manifest


@router.post("/{agent_id}")
async def create_manifest(
    agent_id: str,
    request_data: ManifestCreateRequest,
    manifest_service: ManifestService = Depends(get_manifest_service),
    registry: AgentRegistry = Depends(get_agent_registry)
):
    """Create or update agent manifest"""
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    manifest_data = {
        "capabilities": request_data.capabilities,
        "schemas": request_data.schemas or {},
        "metrics": request_data.metrics or {},
        "endpoints": request_data.endpoints or {},
        "version": request_data.version
    }
    
    manifest = manifest_service.create_manifest(agent, manifest_data)
    
    return manifest


@router.get("/search/capability/{capability}")
async def search_by_capability(
    capability: str,
    manifest_service: ManifestService = Depends(get_manifest_service)
):
    """Search agents by capability"""
    manifests = manifest_service.find_agents_by_capability(capability)
    return {"capability": capability, "agents": manifests}



