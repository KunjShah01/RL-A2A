"""
Federated Reinforcement Learning endpoints
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional

from src.learning.rl_engine import RLEngine

router = APIRouter()


def get_rl_engine(request: Request) -> RLEngine:
    """Dependency to get RL engine"""
    return request.app.state.rl_engine


@router.get("/stats/{agent_id}")
async def get_agent_stats(
    agent_id: str,
    rl_engine: RLEngine = Depends(get_rl_engine)
):
    """Get RL statistics for an agent"""
    stats = rl_engine.get_statistics(agent_id)
    return stats


@router.post("/aggregate/{agent_id}")
async def aggregate_updates(
    agent_id: str,
    rl_engine: RLEngine = Depends(get_rl_engine)
):
    """Trigger FRL aggregation for an agent"""
    success = rl_engine.apply_frl_update(agent_id)
    return {"status": "aggregated" if success else "no_updates", "agent_id": agent_id}



