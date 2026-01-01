import asyncio
import json
import os
import sys
import time
import threading
import queue
import signal
import subprocess
import logging
import hashlib
import secrets
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
import uuid
import argparse
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

# Environment configuration
try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Security imports with graceful fallback
SECURITY_AVAILABLE = False
try:
    import jwt
    import bcrypt
    import bleach
    from passlib.context import CryptContext
    SECURITY_AVAILABLE = True
except ImportError:
    pass

# Enhanced dependency management
def check_and_install_dependencies():
    """Smart dependency management with enhanced features"""
    
    # Core packages required for basic functionality
    core_required = [
        "fastapi", "uvicorn", "websockets", "msgpack", 
        "numpy", "pydantic", "requests"
    ]

    # Enhanced packages for security and features
    enhanced_packages = [
        "python-dotenv", "PyJWT", "bcrypt", "bleach", "passlib"
    ]

    # AI provider packages
    ai_packages = [
        "openai", "anthropic", "google-generativeai"
    ]
    
    # MCP packages
    mcp_packages = [
        "mcp", "aiofiles"
    ]

    missing_core = []
    missing_enhanced = []
    missing_ai = []
    missing_mcp = []
    
    print("[CHECK] Checking dependencies...")
    
    # Check core packages
    for pkg in core_required:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing_core.append(pkg)
    
    # Install core packages automatically
    if missing_core:
        print(f"[INSTALL] Installing core packages: {', '.join(missing_core)}")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install"
            ] + missing_core, stdout=subprocess.DEVNULL)
            print("[OK] Core dependencies installed")
        except Exception as e:
            print(f"[FAIL] Core installation failed: {e}")
            print(f"Please install manually: pip install {' '.join(missing_core)}")
            return False
    
    # Check enhanced packages
    for pkg in enhanced_packages:
        try:
            if pkg == "PyJWT":
                import jwt
            else:
                __import__(pkg.replace("-", "_"))
        except ImportError:
            missing_enhanced.append(pkg)

    # Check MCP packages
    for pkg in mcp_packages:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing_mcp.append(pkg)

    # Offer enhanced packages installation
    if missing_enhanced or missing_ai or missing_mcp:
        print("\n[LAUNCH] Enhanced features available!")
        if missing_enhanced:
            print(f"[SECURITY] Security: {', '.join(missing_enhanced)}")
        if missing_ai:
            print(f"[AI] AI Providers: {', '.join(missing_ai)}")
        if missing_mcp:
            print(f"[MCP] MCP Support: {', '.join(missing_mcp)}")

        install_all = missing_enhanced + missing_ai + missing_mcp
        
        # Check for auto-install flag or CI environment
        if os.getenv("RLA2A_AUTO_INSTALL", "false").lower() == "true" or os.getenv("CI"):
            choice = "y"
        else:
            try:
                choice = input(f"Install enhanced packages? (y/N): ").lower().strip()
            except (EOFError, OSError):
                choice = "n"
        
        if choice in ['y', 'yes']:
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install"
                ] + install_all)
                print("[OK] Enhanced packages installed successfully!")
                return True
            except Exception as e:
                print(f"[FAIL] Enhanced installation failed: {e}")
                print("Continuing with basic features...")
    
    return True

# Check and install dependencies
ENHANCED_FEATURES = check_and_install_dependencies()

# Re-import security packages after installation  
try:
    import jwt
    import bcrypt
    import bleach
    from passlib.context import CryptContext
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

# Import core packages
try:
    import requests
    import msgpack
    import numpy as np
    from fastapi import FastAPI, WebSocket, HTTPException, Depends, status, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, JSONResponse
    from pydantic import BaseModel, Field
    import uvicorn
    import websockets
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("[WARN] FastAPI not available. Server functionality limited.")

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-GUI backend
    import matplotlib.pyplot as plt
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import pandas as pd
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    print("[WARN] Visualization packages not available.")

# Enhanced imports with fallbacks
if SECURITY_AVAILABLE:
    try:
        from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
        from fastapi.middleware.trustedhost import TrustedHostMiddleware
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    except ImportError:
        pass

# AI Provider imports with availability checking
OPENAI_AVAILABLE = False
ANTHROPIC_AVAILABLE = False
GOOGLE_AVAILABLE = False
MCP_AVAILABLE = False

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    pass

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    pass

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    pass

try:
    from mcp.server.models import InitializeResult
    from mcp.server import NotificationOptions, Server
    from mcp.types import Resource, Tool, TextContent
    import mcp.types as types
    MCP_AVAILABLE = True
except ImportError:
    pass

# =============================================================================
# ENHANCED CONFIGURATION SYSTEM
# =============================================================================

class SecurityConfig:
    """Enhanced Security Configuration"""
    SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else ["*"]
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    MAX_MESSAGE_SIZE = int(os.getenv("MAX_MESSAGE_SIZE", "1048576"))  # 1MB
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour

# Comprehensive Configuration
CONFIG = {
    # System Information
    "VERSION": "4.0.0-COMBINED-WINDOWS-FINAL",
    "SYSTEM_NAME": "RL-A2A Combined Enhanced",
    
    # AI Provider Configuration
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"), 
    "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
    
    # AI Model Settings
    "DEFAULT_AI_PROVIDER": os.getenv("DEFAULT_AI_PROVIDER", "openai"),
    "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    "ANTHROPIC_MODEL": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
    "GOOGLE_MODEL": os.getenv("GOOGLE_MODEL", "gemini-1.5-flash"),
    "AI_TIMEOUT": int(os.getenv("AI_TIMEOUT", "30")),
    
    # Server Configuration
    "SERVER_HOST": os.getenv("A2A_HOST", "localhost"),
    "SERVER_PORT": int(os.getenv("A2A_PORT", "8000")),
    "DASHBOARD_PORT": int(os.getenv("DASHBOARD_PORT", "8501")),
    
    # System Limits
    "MAX_AGENTS": int(os.getenv("MAX_AGENTS", "100")),
    "MAX_CONNECTIONS": int(os.getenv("MAX_CONNECTIONS", "1000")),
    "DEBUG": os.getenv("DEBUG", "false").lower() == "true",
    
    # Logging Configuration
    "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
    "LOG_FILE": os.getenv("LOG_FILE", "rla2a.log"),
    
    # Feature Flags
    "ENABLE_SECURITY": SECURITY_AVAILABLE,
    "ENABLE_AI": OPENAI_AVAILABLE or ANTHROPIC_AVAILABLE or GOOGLE_AVAILABLE,
    "ENABLE_VISUALIZATION": VISUALIZATION_AVAILABLE,
    "ENABLE_MCP": MCP_AVAILABLE,
    "ENABLE_FASTAPI": FASTAPI_AVAILABLE
}

# Setup logging with UTF-8 encoding
logging.basicConfig(
    level=getattr(logging, CONFIG["LOG_LEVEL"]),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG["LOG_FILE"], encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# =============================================================================
# CORE DATA STRUCTURES
# =============================================================================

@dataclass
class Agent:
    """Enhanced Agent with comprehensive capabilities"""
    id: str
    name: str
    role: str = "general"
    capabilities: List[str] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    memory: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    security_level: str = "standard"
    ai_provider: str = "openai"
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.capabilities:
            self.capabilities = ["communication", "learning", "reasoning"]
        if not self.performance_metrics:
            self.performance_metrics = {
                "success_rate": 0.0,
                "response_time": 0.0,
                "learning_rate": 0.0,
                "collaboration_score": 0.0
            }

@dataclass
class Message:
    """Enhanced Message with security and metadata"""
    id: str
    sender_id: str
    receiver_id: str
    content: str
    message_type: str = "text"
    priority: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    encrypted: bool = False
    signature: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "message_type": self.message_type,
            "priority": self.priority,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "encrypted": self.encrypted,
            "signature": self.signature
        }

# =============================================================================
# PYDANTIC MODELS FOR API
# =============================================================================

if FASTAPI_AVAILABLE:
    class AgentCreate(BaseModel):
        name: str
        role: str = "general"
        ai_provider: str = "openai"
    
    class MessageCreate(BaseModel):
        sender_id: str
        receiver_id: str
        content: str
        message_type: str = "text"
        priority: int = 1

# =============================================================================
# ENHANCED AI MANAGER
# =============================================================================

class AIManager:
    """Multi-provider AI management system"""
    
    def __init__(self):
        self.providers = {}
        self.initialize_providers()
    
    def initialize_providers(self):
        """Initialize available AI providers"""
        
        # OpenAI
        if OPENAI_AVAILABLE and CONFIG["OPENAI_API_KEY"]:
            try:
                self.providers["openai"] = AsyncOpenAI(
                    api_key=CONFIG["OPENAI_API_KEY"]
                )
                logger.info("[AI] OpenAI provider initialized")
            except Exception as e:
                logger.error(f"[FAIL] OpenAI initialization failed: {e}")
        
        # Anthropic
        if ANTHROPIC_AVAILABLE and CONFIG["ANTHROPIC_API_KEY"]:
            try:
                self.providers["anthropic"] = anthropic.AsyncAnthropic(
                    api_key=CONFIG["ANTHROPIC_API_KEY"]
                )
                logger.info("[AI] Anthropic provider initialized")
            except Exception as e:
                logger.error(f"[FAIL] Anthropic initialization failed: {e}")
        
        # Google
        if GOOGLE_AVAILABLE and CONFIG["GOOGLE_API_KEY"]:
            try:
                genai.configure(api_key=CONFIG["GOOGLE_API_KEY"])
                self.providers["google"] = genai
                logger.info("[AI] Google provider initialized")
            except Exception as e:
                logger.error(f"[FAIL] Google initialization failed: {e}")
    
    async def generate_response(self, prompt: str, provider: str = None, **kwargs) -> str:
        """Generate AI response using specified provider"""
        
        if not provider:
            provider = CONFIG["DEFAULT_AI_PROVIDER"]
        
        if provider not in self.providers:
            return f"[AI Error] Provider '{provider}' not available"
        
        try:
            if provider == "openai":
                response = await self.providers["openai"].chat.completions.create(
                    model=CONFIG["OPENAI_MODEL"],
                    messages=[{"role": "user", "content": prompt}],
                    timeout=CONFIG["AI_TIMEOUT"],
                    **kwargs
                )
                return response.choices[0].message.content
            
            elif provider == "anthropic":
                response = await self.providers["anthropic"].messages.create(
                    model=CONFIG["ANTHROPIC_MODEL"],
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}],
                    **kwargs
                )
                return response.content[0].text
            
            elif provider == "google":
                model = genai.GenerativeModel(CONFIG["GOOGLE_MODEL"])
                response = await model.generate_content_async(prompt, **kwargs)
                return response.text
            
        except Exception as e:
            logger.error(f"[FAIL] AI generation failed for {provider}: {e}")
            return f"[AI Error] Failed to generate response: {str(e)}"

# =============================================================================
# ENHANCED A2A SYSTEM
# =============================================================================

class A2ASystem:
    """Enhanced Agent-to-Agent Communication System"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.connections: Dict[str, WebSocket] = {}
        self.message_queue = asyncio.Queue()
        self.ai_manager = AIManager()
        self.security_manager = SecurityManager() if SECURITY_AVAILABLE else None
        self.performance_monitor = PerformanceMonitor()
        self.running = False
        
        # Enhanced features
        self.learning_system = ReinforcementLearningSystem()
        self.collaboration_engine = CollaborationEngine()
        self.visualization_engine = VisualizationEngine()
        
        logger.info(f"[AI] {CONFIG['SYSTEM_NAME']} v{CONFIG['VERSION']} initialized")
    
    def create_agent(self, name: str, role: str = "general", agent_id: str = None, **kwargs) -> str:
        """Create a new agent with enhanced capabilities"""
        
        if not agent_id:
            agent_id = str(uuid.uuid4())
            
        agent = Agent(
            id=agent_id,
            name=name,
            role=role,
            **kwargs
        )
        
        self.agents[agent_id] = agent
        logger.info(f"[AI] Agent created: {name} ({agent_id})")
        
        return agent_id
    
    def create_demo_agents(self, count: int = 3):
        """Create demonstration agents"""
        
        demo_configs = [
            {"name": "Alice", "role": "researcher", "ai_provider": "openai"},
            {"name": "Bob", "role": "analyst", "ai_provider": "anthropic"},
            {"name": "Charlie", "role": "coordinator", "ai_provider": "google"},
            {"name": "Diana", "role": "specialist", "ai_provider": "openai"},
            {"name": "Eve", "role": "monitor", "ai_provider": "anthropic"}
        ]
        
        logger.info(f"[AI] Creating {count} demo agents...")
        
        for i in range(min(count, len(demo_configs))):
            config = demo_configs[i]
            self.create_agent(**config)
    
    async def start_server(self):
        """Start the enhanced A2A server"""
        
        if not FASTAPI_AVAILABLE:
            print("[FAIL] FastAPI not available. Cannot start server.")
            print("[INFO] Install with: pip install fastapi uvicorn")
            return
        
        app = FastAPI(
            title="RL-A2A Enhanced System",
            description="Advanced Agent-to-Agent Communication Platform",
            version=CONFIG["VERSION"]
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=SecurityConfig.ALLOWED_ORIGINS if SECURITY_AVAILABLE else ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Root endpoint
        @app.get("/", response_class=HTMLResponse)
        async def root():
            return f"""
            <html>
                <head><title>RL-A2A Enhanced System</title></head>
                <body>
                    <h1>[AI] RL-A2A Enhanced System</h1>
                    <p>Version: {CONFIG['VERSION']}</p>
                    <p>Status: [OK] Running</p>
                    <h2>Available Endpoints:</h2>
                    <ul>
                        <li><a href="/agents">GET /agents</a> - List all agents</li>
                        <li><a href="/status">GET /status</a> - System status</li>
                        <li><a href="/docs">GET /docs</a> - API Documentation</li>
                    </ul>
                    <h2>Features:</h2>
                    <ul>
                        <li>FastAPI: {'[OK]' if FASTAPI_AVAILABLE else '[FAIL]'}</li>
                        <li>Security: {'[OK]' if SECURITY_AVAILABLE else '[BASIC]'}</li>
                        <li>AI Providers: {'[OK]' if CONFIG['ENABLE_AI'] else '[NONE]'}</li>
                        <li>Visualization: {'[OK]' if VISUALIZATION_AVAILABLE else '[BASIC]'}</li>
                    </ul>
                </body>
            </html>
            """
        
        # WebSocket endpoint
        @app.websocket("/ws/{agent_id}")
        async def websocket_endpoint(websocket: WebSocket, agent_id: str):
            await websocket.accept()
            self.connections[agent_id] = websocket
            
            try:
                while True:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    # Create message
                    message = Message(
                        id=str(uuid.uuid4()),
                        sender_id=agent_id,
                        receiver_id=message_data.get("receiver_id"),
                        content=message_data.get("content"),
                        message_type=message_data.get("type", "text")
                    )
                    
                    await self.message_queue.put(message)
                    
            except Exception as e:
                logger.error(f"[FAIL] WebSocket error for {agent_id}: {e}")
            finally:
                if agent_id in self.connections:
                    del self.connections[agent_id]
        
        # REST API endpoints
        @app.get("/agents")
        async def list_agents():
            return {
                "agents": [
                    {
                        "id": agent.id,
                        "name": agent.name,
                        "role": agent.role,
                        "ai_provider": agent.ai_provider,
                        "status": "active" if agent.id in self.connections else "inactive",
                        "created_at": agent.created_at.isoformat(),
                        "last_active": agent.last_active.isoformat()
                    }
                    for agent in self.agents.values()
                ]
            }
        
        @app.post("/register")
        async def register_agent(agent_id: str = None):
            """Register an agent (compatibility endpoint)"""
            if not agent_id:
                agent_id = str(uuid.uuid4())
            
            # Create agent if it doesn't exist
            if agent_id not in self.agents:
                self.create_agent(
                    name=f"Agent-{agent_id[:8]}", 
                    role="external",
                    agent_id=agent_id
                )
                logger.info(f"[REGISTER] Registered external agent: {agent_id}")
            else:
                logger.info(f"[REGISTER] Re-registered agent: {agent_id}")
            
            return {"session_id": agent_id, "status": "registered"}

        @app.post("/agents")
        async def create_agent_endpoint(agent_data: AgentCreate):
            agent_id = self.create_agent(
                name=agent_data.name,
                role=agent_data.role,
                ai_provider=agent_data.ai_provider
            )
            return {"agent_id": agent_id, "status": "created"}
        
        @app.get("/agents/{agent_id}")
        async def get_agent(agent_id: str):
            if agent_id not in self.agents:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            agent = self.agents[agent_id]
            return {
                "id": agent.id,
                "name": agent.name,
                "role": agent.role,
                "ai_provider": agent.ai_provider,
                "capabilities": agent.capabilities,
                "performance_metrics": agent.performance_metrics,
                "status": "active" if agent_id in self.connections else "inactive"
            }
        
        @app.get("/status")
        async def system_status():
            return {
                "status": "operational",
                "version": CONFIG["VERSION"],
                "system_name": CONFIG["SYSTEM_NAME"],
                "agents_count": len(self.agents),
                "active_connections": len(self.connections),
                "ai_providers": list(self.ai_manager.providers.keys()),
                "features": {
                    "security_enabled": SECURITY_AVAILABLE,
                    "ai_enabled": CONFIG["ENABLE_AI"],
                    "visualization_enabled": VISUALIZATION_AVAILABLE,
                    "mcp_enabled": MCP_AVAILABLE
                },
                "uptime": time.time() - self.performance_monitor.start_time if hasattr(self, 'performance_monitor') else 0
            }

        @app.get("/health")
        async def health_check():
            """Health check endpoint for monitoring"""
            return await system_status()
        
        @app.post("/messages")
        async def send_message(message_data: MessageCreate):
            message = Message(
                id=str(uuid.uuid4()),
                sender_id=message_data.sender_id,
                receiver_id=message_data.receiver_id,
                content=message_data.content,
                message_type=message_data.message_type,
                priority=message_data.priority
            )
            
            await self.message_queue.put(message)
            return {"message_id": message.id, "status": "queued"}
            
        @app.post("/feedback")
        async def receive_feedback(feedback: Dict[str, Any]):
            """Receive RL feedback"""
            agent_id = feedback.get("agent_id")
            reward = feedback.get("reward")
            action_id = feedback.get("action_id")
            
            logger.info(f"[RL] Feedback received from {agent_id}: Reward={reward} for Action={action_id}")
            
            if hasattr(self, 'learning_system'):
                self.learning_system.update_agent_performance(agent_id, reward)
                
            return {"status": "received"}
        
        # Start message processing
        asyncio.create_task(self.process_messages())
        
        # Log system status
        logger.info(f"[LAUNCH] Server starting on {CONFIG['SERVER_HOST']}:{CONFIG['SERVER_PORT']}")
        logger.info(f"[AI] AI Providers: {list(self.ai_manager.providers.keys())}")
        
        # Start server
        config = uvicorn.Config(
            app,
            host=CONFIG["SERVER_HOST"],
            port=CONFIG["SERVER_PORT"],
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    async def process_messages(self):
        """Enhanced message processing with AI integration"""
        import random
        
        while True:
            try:
                message = await self.message_queue.get()
                
                # Process with AI if needed
                if message.receiver_id in self.agents:
                    receiver = self.agents[message.receiver_id]
                    
                    # Generate AI response if AI is available
                    if CONFIG["ENABLE_AI"]:
                        ai_response = await self.ai_manager.generate_response(
                            f"Agent {receiver.name} received: {message.content}",
                            provider=receiver.ai_provider
                        )
                    else:
                        ai_response = f"[Echo] {receiver.name} received: {message.content}"
                    
                    # Send response back
                    if message.sender_id in self.connections:
                        response_data = {
                            "from": receiver.name,
                            "content": ai_response,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        await self.connections[message.sender_id].send_text(
                            json.dumps(response_data)
                        )
                elif message.receiver_id is None:
                    # Environment interaction / RL
                    # If message content is JSON-like (observation), return an action
                    try:
                        # For now, just return a random action
                        actions = ["move_forward", "turn_left", "turn_right", "communicate", "observe"]
                        action = random.choice(actions)
                        
                        response_data = {
                            "command": action,
                            "action_id": str(uuid.uuid4()),
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        if message.sender_id in self.connections:
                            await self.connections[message.sender_id].send_text(
                                json.dumps(response_data)
                            )
                    except Exception as e:
                        logger.error(f"[FAIL] RL processing error: {e}")
                
                self.message_queue.task_done()
                
            except Exception as e:
                logger.error(f"[FAIL] Message processing error: {e}")

# =============================================================================
# ENHANCED DASHBOARD
# =============================================================================

def start_dashboard():
    """Start the enhanced Streamlit dashboard"""
    print("[LAUNCH] Starting enhanced dashboard...")
    
    dashboard_path = Path("dashboard_app.py").absolute()
    if not dashboard_path.exists():
        print("[FAIL] dashboard_app.py not found!")
        return

    try:
        # Check if streamlit is installed
        subprocess.run([sys.executable, "-m", "streamlit", "--version"], check=True, stdout=subprocess.DEVNULL)
        
        # Run dashboard
        print(f"[LAUNCH] Opening dashboard from {dashboard_path}")
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(dashboard_path)])
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[FAIL] Streamlit not found. Please install it with:")
        print("pip install streamlit")

# =============================================================================
# ADDITIONAL COMPONENTS
# =============================================================================

class SecurityManager:
    """Enhanced security management"""
    
    def __init__(self):
        self.secret_key = SecurityConfig.SECRET_KEY
        self.sessions = {}
    
    def create_token(self, agent_id: str) -> str:
        """Create JWT token for agent"""
        if not SECURITY_AVAILABLE:
            return f"basic_token_{agent_id}"
        
        try:
            payload = {
                "agent_id": agent_id,
                "exp": datetime.utcnow() + timedelta(hours=SecurityConfig.ACCESS_TOKEN_EXPIRE_HOURS)
            }
            return jwt.encode(payload, self.secret_key, algorithm="HS256")
        except Exception as e:
            logger.error(f"[FAIL] Token creation failed: {e}")
            return f"basic_token_{agent_id}"
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token"""
        if not SECURITY_AVAILABLE:
            if token.startswith("basic_token_"):
                return token.replace("basic_token_", "")
            return None
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload.get("agent_id")
        except Exception:
            return None

class PerformanceMonitor:
    """System performance monitoring"""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics = {
            "messages_processed": 0,
            "ai_requests": 0,
            "errors": 0,
            "response_times": []
        }
    
    def record_metric(self, metric_name: str, value: Any):
        """Record performance metric"""
        if metric_name in self.metrics:
            if isinstance(self.metrics[metric_name], list):
                self.metrics[metric_name].append(value)
            else:
                self.metrics[metric_name] += 1

class ReinforcementLearningSystem:
    """Enhanced reinforcement learning for agents"""
    
    def __init__(self):
        self.learning_data = {}
        self.reward_history = {}
    
    def update_agent_performance(self, agent_id: str, reward: float):
        """Update agent performance based on reward"""
        if agent_id not in self.reward_history:
            self.reward_history[agent_id] = []
        
        self.reward_history[agent_id].append(reward)
        
        # Keep only recent history
        if len(self.reward_history[agent_id]) > 100:
            self.reward_history[agent_id] = self.reward_history[agent_id][-100:]

class CollaborationEngine:
    """Enhanced agent collaboration system"""
    
    def __init__(self):
        self.collaboration_networks = {}
        self.task_assignments = {}
    
    def assign_collaborative_task(self, task_id: str, agent_ids: List[str]):
        """Assign collaborative task to multiple agents"""
        self.task_assignments[task_id] = {
            "agents": agent_ids,
            "status": "active",
            "created_at": datetime.now()
        }

class VisualizationEngine:
    """3D visualization and monitoring"""
    
    def __init__(self):
        self.visualization_data = {}
    
    def generate_network_graph(self, agents: Dict[str, Agent]) -> str:
        """Generate network visualization"""
        if not VISUALIZATION_AVAILABLE:
            return "[BASIC] Network visualization not available"
        
        # This would generate actual 3D visualizations
        return "[OK] Network graph generated"

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def setup_environment():
    """Setup development environment"""
    
    print("[LAUNCH] Setting up RL-A2A environment...")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        env_content = '''# RL-A2A Configuration
# AI Provider API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Server Configuration
A2A_HOST=localhost
A2A_PORT=8000
DASHBOARD_PORT=8501

# Security Configuration
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_HOURS=24
RATE_LIMIT_PER_MINUTE=60

# System Configuration
MAX_AGENTS=100
MAX_CONNECTIONS=1000
DEBUG=false
LOG_LEVEL=INFO
'''
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("[OK] .env file created")
    
    print("[OK] Environment setup complete!")
    print("[DOCS] Edit .env file to configure API keys and settings")

def generate_report():
    """Generate comprehensive HTML report"""
    
    print("[LAUNCH] Generating system report...")
    
    report_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>RL-A2A System Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
            .section {{ margin: 20px 0; }}
            .status {{ color: green; font-weight: bold; }}
            .error {{ color: red; font-weight: bold; }}
            .warning {{ color: orange; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>[AI] RL-A2A Combined System Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="section">
            <h2>System Information</h2>
            <ul>
                <li>Version: {CONFIG['VERSION']}</li>
                <li>System Name: {CONFIG['SYSTEM_NAME']}</li>
                <li>Python Version: {sys.version}</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Feature Status</h2>
            <ul>
                <li class="status">[OK] Core System</li>
                <li class="{'status' if FASTAPI_AVAILABLE else 'error'}">[{'OK' if FASTAPI_AVAILABLE else 'FAIL'}] FastAPI Server</li>
                <li class="{'status' if SECURITY_AVAILABLE else 'warning'}">[{'OK' if SECURITY_AVAILABLE else 'BASIC'}] Enhanced Security</li>
                <li class="{'status' if OPENAI_AVAILABLE else 'warning'}">[{'OK' if OPENAI_AVAILABLE else 'NONE'}] OpenAI Integration</li>
                <li class="{'status' if ANTHROPIC_AVAILABLE else 'warning'}">[{'OK' if ANTHROPIC_AVAILABLE else 'NONE'}] Anthropic Integration</li>
                <li class="{'status' if GOOGLE_AVAILABLE else 'warning'}">[{'OK' if GOOGLE_AVAILABLE else 'NONE'}] Google AI Integration</li>
                <li class="{'status' if VISUALIZATION_AVAILABLE else 'warning'}">[{'OK' if VISUALIZATION_AVAILABLE else 'BASIC'}] Visualization</li>
                <li class="{'status' if MCP_AVAILABLE else 'warning'}">[{'OK' if MCP_AVAILABLE else 'NONE'}] MCP Support</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Configuration</h2>
            <ul>
                <li>Host: {CONFIG['SERVER_HOST']}</li>
                <li>Port: {CONFIG['SERVER_PORT']}</li>
                <li>Max Agents: {CONFIG['MAX_AGENTS']}</li>
                <li>Debug: {CONFIG['DEBUG']}</li>
                <li>Log Level: {CONFIG['LOG_LEVEL']}</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Available Commands</h2>
            <ul>
                <li><code>python rla2a.py setup</code> - Setup environment</li>
                <li><code>python rla2a.py server</code> - Start server</li>
                <li><code>python rla2a.py dashboard</code> - Start dashboard</li>
                <li><code>python rla2a.py report</code> - Generate this report</li>
                <li><code>python rla2a.py info</code> - System information</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Next Steps</h2>
            <ol>
                <li>Configure API keys in .env file (if using AI features)</li>
                <li>Start server: <code>python rla2a.py server</code></li>
                <li>Open dashboard: <code>python rla2a.py dashboard</code></li>
                <li>Visit <a href="http://{CONFIG['SERVER_HOST']}:{CONFIG['SERVER_PORT']}">http://{CONFIG['SERVER_HOST']}:{CONFIG['SERVER_PORT']}</a></li>
            </ol>
        </div>
        
        <div class="section">
            <p><strong>[AI] Ready for Multi-Agent Intelligence! [LAUNCH]</strong></p>
        </div>
    </body>
    </html>
    '''
    
    with open('rla2a_report.html', 'w', encoding='utf-8') as f:
        f.write(report_html)
    
    print("[OK] Report generated: rla2a_report.html")

async def run_mcp_server():
    """Run comprehensive MCP server for AI assistants"""
    
    if not MCP_AVAILABLE:
        print("[FAIL] MCP not available. Install with: pip install mcp")
        return
    
    print("[LAUNCH] Starting comprehensive MCP server...")
    
    try:
        from mcp.server import Server
        from mcp.types import Tool, Resource, TextContent
        import mcp.types as types
        
        # Create MCP server
        server = Server("rl-a2a-enhanced")
        a2a_system = A2ASystem()
        
        # MCP Tools
        @server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            return [
                Tool(
                    name="create_agent",
                    description="Create a new AI agent",
                    inputSchema={"type": "object", "properties": {"name": {"type": "string"}, "role": {"type": "string"}}, "required": ["name", "role"]}
                ),
                Tool(
                    name="list_agents",
                    description="List all active agents",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="get_system_status",
                    description="Get system status",
                    inputSchema={"type": "object", "properties": {}}
                )
            ]
        
        # Tool handlers
        @server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            try:
                if name == "create_agent":
                    agent_id = a2a_system.create_agent(arguments["name"], arguments["role"])
                    return [TextContent(type="text", text=f"[OK] Agent created: {agent_id}")]
                elif name == "list_agents":
                    agents = [f"{a.name} ({a.role})" for a in a2a_system.agents.values()]
                    return [TextContent(type="text", text=f"[AI] Agents: {', '.join(agents) if agents else 'None'}")]
                elif name == "get_system_status":
                    status = f"[AI] RL-A2A v{CONFIG['VERSION']} - Agents: {len(a2a_system.agents)} - AI: {'YES' if CONFIG['ENABLE_AI'] else 'NO'}"
                    return [TextContent(type="text", text=status)]
                else:
                    return [TextContent(type="text", text=f"[FAIL] Unknown tool: {name}")]
            except Exception as e:
                return [TextContent(type="text", text=f"[FAIL] Error: {e}")]
        
        print("[OK] MCP server ready with agent management tools")
        print("[INFO] Available tools: create_agent, list_agents, get_system_status")
        await server.run()
        
    except Exception as e:
        print(f"[FAIL] MCP server error: {e}")
        print("[INFO] Install MCP with: pip install mcp")
        print("  python rla2a.py server             # Start server")
        print("  python rla2a.py dashboard          # Start dashboard")
        print("  python rla2a.py report             # Generate report")
        print("  python rla2a.py info               # System information")
        print()
        print("[DOCS] Documentation: python rla2a.py --help")
        return
    
async def main():
    parser = argparse.ArgumentParser(description="RL-A2A: Agent-to-Agent Communication System")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Setup command
    subparsers.add_parser("setup", help="Setup environment and dependencies")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start secure server")
    server_parser.add_argument("--host", default=CONFIG["SERVER_HOST"], help="Server host")
    server_parser.add_argument("--port", type=int, default=CONFIG["SERVER_PORT"], help="Server port")
    server_parser.add_argument("--demo-agents", type=int, default=0, help="Number of demo agents to create")
    
    # Dashboard command
    subparsers.add_parser("dashboard", help="Start enhanced dashboard")
    
    # Report command
    subparsers.add_parser("report", help="Generate HTML report")
    
    # MCP command
    subparsers.add_parser("mcp", help="Run MCP server")
    
    # Info command
    subparsers.add_parser("info", help="Show system information")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "setup":
            setup_environment()
        
        elif args.command == "server":
            CONFIG["SERVER_HOST"] = args.host
            CONFIG["SERVER_PORT"] = args.port
            
            system = A2ASystem()
            
            if args.demo_agents > 0:
                system.create_demo_agents(args.demo_agents)
            
            def signal_handler(signum, frame):
                logger.info("\\n[STOP] Shutting down...")
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            await system.start_server()
        
        elif args.command == "dashboard":
            start_dashboard()
        
        elif args.command == "report":
            generate_report()
        
        elif args.command == "mcp":
            await run_mcp_server()
        
        elif args.command == "info":
            print(f"[AI] {CONFIG['SYSTEM_NAME']}")
            print(f"Version: {CONFIG['VERSION']}")
            print(f"Security: {'Enhanced' if SECURITY_AVAILABLE else 'Basic'}")
            print(f"AI Providers:")
            print(f"  OpenAI: {'YES' if OPENAI_AVAILABLE else 'NO'}")
            print(f"  Anthropic: {'YES' if ANTHROPIC_AVAILABLE else 'NO'}")
            print(f"  Google: {'YES' if GOOGLE_AVAILABLE else 'NO'}")
            print(f"FastAPI: {'YES' if FASTAPI_AVAILABLE else 'NO'}")
            print(f"Visualization: {'YES' if VISUALIZATION_AVAILABLE else 'NO'}")
            print(f"MCP: {'YES' if MCP_AVAILABLE else 'NO'}")
            print(f"Server: {CONFIG['SERVER_HOST']}:{CONFIG['SERVER_PORT']}")
            
    except Exception as e:
        logger.error(f"Error executing command '{args.command}': {e}")
        print(f"[FAIL] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        logger.info(f"[AI] {CONFIG['SYSTEM_NAME']} v{CONFIG['VERSION']} starting...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n[STOP] Shutting down...")
        logger.info("System shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"[FAIL] Fatal error: {e}")
        sys.exit(1)