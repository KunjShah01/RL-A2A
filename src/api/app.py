"""
FastAPI Application
Main application setup and configuration
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.utils.config import Config
from src.utils.logger import get_logger
from src.core.events import EventBus
from src.core.registry import AgentRegistry
from src.routing.manifest_service import ManifestService
from src.routing.message_router import MessageRouter
from src.learning.rl_engine import RLEngine
from src.middleware.hitl import ApprovalQueue, HITLMiddleware
from src.protocols.router import ProtocolRouter
from src.protocols.a2a_handler import A2AHandler
from src.protocols.mcp_handler import MCPHandler

from .endpoints import agents, messages, manifests, workflows, frl, hitl

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="RL-A2A v2.0",
        description="Reinforcement Learning Agent-to-Agent Communication Platform",
        version=Config.VERSION,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize core components
    event_bus = EventBus()
    agent_registry = AgentRegistry(event_bus=event_bus)
    manifest_service = ManifestService()
    message_router = MessageRouter(
        agent_registry=agent_registry,
        manifest_service=manifest_service,
        event_bus=event_bus
    )
    rl_engine = RLEngine(
        agent_registry=agent_registry,
        manifest_service=manifest_service,
        event_bus=event_bus,
        enable_frl=Config.FRL_ENABLED
    )
    
    # Protocol handlers
    protocol_router = ProtocolRouter()
    a2a_handler = A2AHandler(message_router=message_router)
    from src.protocols.router import ProtocolType
    protocol_router.register_handler(ProtocolType.A2A, a2a_handler)
    
    # HITL middleware
    approval_queue = ApprovalQueue()
    hitl_middleware = HITLMiddleware(
        approval_queue=approval_queue,
        event_bus=event_bus
    )
    
    # Store in app state
    app.state.event_bus = event_bus
    app.state.agent_registry = agent_registry
    app.state.manifest_service = manifest_service
    app.state.message_router = message_router
    app.state.rl_engine = rl_engine
    app.state.protocol_router = protocol_router
    app.state.a2a_handler = a2a_handler
    app.state.approval_queue = approval_queue
    app.state.hitl_middleware = hitl_middleware
    
    # Initialize MCP handler if available
    try:
        mcp_handler = MCPHandler(
            agent_registry=agent_registry,
            event_bus=event_bus
        )
        app.state.mcp_handler = mcp_handler
        protocol_router.register_handler(ProtocolType.MCP, mcp_handler)
    except ImportError:
        logger.warning("MCP not available, skipping MCP handler")
        app.state.mcp_handler = None
    
    # Include routers
    app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
    app.include_router(messages.router, prefix="/api/v1/messages", tags=["messages"])
    app.include_router(manifests.router, prefix="/api/v1/manifests", tags=["manifests"])
    app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])
    app.include_router(frl.router, prefix="/api/v1/frl", tags=["frl"])
    app.include_router(hitl.router, prefix="/api/v1/hitl", tags=["hitl"])
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": Config.SYSTEM_NAME,
            "version": Config.VERSION,
            "status": "operational",
            "docs": "/docs"
        }
    
    # Health check
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "agents_count": agent_registry.count(),
            "version": Config.VERSION
        }
    
    logger.info("FastAPI application created successfully")
    
    return app

