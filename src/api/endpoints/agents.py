"""
Agent endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Optional
from pydantic import BaseModel

from src.core.registry import AgentRegistry
from src.core.agent import Agent
from src.identity.key_manager import KeyManager
import uuid

router = APIRouter()


def get_agent_registry(request: Request) -> AgentRegistry:
    """Dependency to get agent registry"""
    return request.app.state.agent_registry


class AgentCreateRequest(BaseModel):
    name: str
    role: str = "general"
    ai_provider: str = "openai"
    capabilities: Optional[List[str]] = None


class AgentResponse(BaseModel):
    id: str
    did: Optional[str]
    name: str
    role: str
    status: str
    capabilities: List[str]
    ai_provider: str


@router.post("", response_model=AgentResponse)
async def create_agent(
    request_data: AgentCreateRequest,
    registry: AgentRegistry = Depends(get_agent_registry)
):
    """Create a new agent"""
    from src.core.agent import AgentStatus
    from src.identity.key_manager import KeyManager
    
    # Generate DID and keys
    key_manager = KeyManager()
    private_key, public_key = key_manager.generate_ed25519_keypair()
    did = f"did:key:{key_manager.key_to_base64(public_key)[:32]}"
    
    # Create agent
    agent = Agent(
        id=str(uuid.uuid4()),
        did=did,
        name=request_data.name,
        role=request_data.role,
        status=AgentStatus.ACTIVE,
        capabilities=request_data.capabilities or [],
        public_key=key_manager.key_to_pem(public_key),
        ai_provider=request_data.ai_provider
    )
    
    registry.register(agent)
    
    return AgentResponse(
        id=agent.id,
        did=agent.did,
        name=agent.name,
        role=agent.role,
        status=agent.status.value,
        capabilities=agent.capabilities,
        ai_provider=agent.ai_provider
    )


@router.get("", response_model=List[AgentResponse])
async def list_agents(registry: AgentRegistry = Depends(get_agent_registry)):
    """List all agents"""
    agents = registry.list_all()
    return [
        AgentResponse(
            id=a.id,
            did=a.did,
            name=a.name,
            role=a.role,
            status=a.status.value,
            capabilities=a.capabilities,
            ai_provider=a.ai_provider
        )
        for a in agents
    ]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    registry: AgentRegistry = Depends(get_agent_registry)
):
    """Get agent by ID"""
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentResponse(
        id=agent.id,
        did=agent.did,
        name=agent.name,
        role=agent.role,
        status=agent.status.value,
        capabilities=agent.capabilities,
        ai_provider=agent.ai_provider
    )


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    registry: AgentRegistry = Depends(get_agent_registry)
):
    """Delete an agent"""
    success = registry.unregister(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"status": "deleted", "agent_id": agent_id}

