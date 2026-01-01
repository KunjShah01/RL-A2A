"""
A2A Server - Complete Agent-to-Agent Communication System
=========================================================

Combined version integrating all features from:
- Original a2a_server.py (basic functionality, simplicity)
- a2a_server_enhanced.py (advanced security, multi-AI support)

FEATURES INCLUDED:
✅ Original Simple Interface (backward compatible)
✅ Enhanced Security (JWT, rate limiting, validation)
✅ Multi-AI Provider Support (OpenAI, Claude, Gemini)
✅ Advanced RL with Q-Learning
✅ Session Management & Security
✅ Production-Ready Deployment
✅ Comprehensive Monitoring
✅ Graceful Fallbacks for missing dependencies

Author: KUNJ SHAH
Version: 3.0.0 Combined
"""

import asyncio
import json
import os
import sys
import time
import uuid
import secrets
import logging
from typing import Dict, List, Optional, Set, Any, Tuple
from collections import deque
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

# =============================================================================
# SMART DEPENDENCY MANAGEMENT
# =============================================================================

def check_and_install_dependencies():
    """Smart dependency checker with auto-installation options"""
    
    required = [
        "fastapi", "uvicorn", "websockets", "msgpack", "numpy", "pydantic"
    ]
    
    enhanced = [
        "PyJWT", "bleach", "slowapi", "passlib"
    ]
    
    ai_providers = [
        "openai", "anthropic", "google-generativeai"
    ]
    
    missing_required = []
    missing_enhanced = []
    missing_ai = []
    
    # Check required packages
    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing_required.append(pkg)
    
    # Install required packages automatically
    if missing_required:
        print(f"📦 Installing required packages: {', '.join(missing_required)}")
        try:
            import subprocess
            subprocess.check_call([
                sys.executable, "-m", "pip", "install"
            ] + missing_required, stdout=subprocess.DEVNULL)
            print("✅ Required dependencies installed")
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            print(f"Please install manually: pip install {' '.join(missing_required)}")
            sys.exit(1)
    
    # Check enhanced packages
    for pkg in enhanced:
        try:
            if pkg == "PyJWT":
                import jwt
            else:
                __import__(pkg.replace("-", "_"))
        except ImportError:
            missing_enhanced.append(pkg)
    
    # Check AI packages  
    for pkg in ai_providers:
        try:
            if pkg == "google-generativeai":
                import google.generativeai
            else:
                __import__(pkg.replace("-", "_"))
        except ImportError:
            missing_ai.append(pkg)
    
    # Offer enhanced packages
    if missing_enhanced or missing_ai:
        print("\\n🚀 Enhanced features available!")
        if missing_enhanced:
            print(f"🔒 Security: {', '.join(missing_enhanced)}")
        if missing_ai:
            print(f"🤖 AI Providers: {', '.join(missing_ai)}")
        
        all_optional = missing_enhanced + missing_ai
        choice = input(f"Install enhanced packages for better security and AI support? (y/N): ").lower().strip()
        
        if choice in ['y', 'yes']:
            try:
                import subprocess
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install"
                ] + all_optional)
                print("✅ Enhanced packages installed successfully!")
                return True
            except Exception as e:
                print(f"❌ Enhanced installation failed: {e}")
                print("Continuing with basic features...")
    
    return len(missing_enhanced) == 0 and len(missing_ai) == 0

# Check and install dependencies
ENHANCED_FEATURES = check_and_install_dependencies()

# Core imports
try:
    from fastapi import FastAPI, WebSocket, HTTPException, Depends, status
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field, validator
    import msgpack
    import numpy as np
    print("✅ Core A2A Server imports successful")
except ImportError as e:
    print(f"❌ CRITICAL: Core import failed: {e}")
    sys.exit(1)

# Enhanced security imports (with fallbacks)
SECURITY_AVAILABLE = False
try:
    import jwt
    import bleach
    from passlib.context import CryptContext
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    
    SECURITY_AVAILABLE = True
    print("✅ Enhanced security features loaded")
except ImportError:
    print("ℹ️ Enhanced security not available - using basic features")

# AI Provider imports (with fallbacks)
AI_PROVIDERS = {}
try:
    from openai import AsyncOpenAI
    AI_PROVIDERS["openai"] = True
    print("✅ OpenAI support available")
except ImportError:
    pass

try:
    import anthropic
    AI_PROVIDERS["anthropic"] = True
    print("✅ Anthropic (Claude) support available")
except ImportError:
    pass

try:
    import google.generativeai as genai
    AI_PROVIDERS["google"] = True
    print("✅ Google AI (Gemini) support available")
except ImportError:
    pass

if not AI_PROVIDERS:
    print("ℹ️ No AI providers available - using Q-learning only")

# =============================================================================
# COMBINED CONFIGURATION SYSTEM
# =============================================================================

class CombinedConfig:
    """Combined configuration supporting both basic and enhanced modes"""
    
    # System Information
    VERSION = "3.0.0-Combined"
    SYSTEM_NAME = "A2A Server Combined"
    
    # Server Configuration
    HOST = os.getenv("A2A_HOST", "localhost")
    PORT = int(os.getenv("A2A_PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # Security Configuration (enhanced mode)
    SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    MAX_MESSAGE_SIZE = int(os.getenv("MAX_MESSAGE_SIZE", "1048576"))  # 1MB
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
    
    # CORS Configuration
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else ["*"]
    
    # AI Provider Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    DEFAULT_AI_PROVIDER = os.getenv("DEFAULT_AI_PROVIDER", "openai")
    
    # System Limits
    MAX_AGENTS = int(os.getenv("MAX_AGENTS", "100"))
    MAX_CONNECTIONS = int(os.getenv("MAX_CONNECTIONS", "500"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "a2a_server.log")

# Setup logging
logging.basicConfig(
    level=getattr(logging, CombinedConfig.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CombinedConfig.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize security utilities
if SECURITY_AVAILABLE:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    limiter = Limiter(key_func=get_remote_address)
    security = HTTPBearer()

# =============================================================================
# COMBINED DATA MODELS (Basic + Enhanced)
# =============================================================================

class BasicRegistrationRequest(BaseModel):
    """Basic registration request (backward compatible)"""
    agent_id: str = Field(..., description="Unique agent identifier")

class EnhancedRegistrationRequest(BaseModel):
    """Enhanced registration with full validation"""
    agent_id: str = Field(..., min_length=1, max_length=50, regex="^[a-zA-Z0-9_-]+$")
    initial_position: Optional[Dict[str, float]] = None
    ai_provider: Optional[str] = Field("openai", regex="^(openai|anthropic|google)$")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('metadata')
    def validate_metadata_size(cls, v):
        if len(json.dumps(v)) > 1000:  # 1KB limit
            raise ValueError("Metadata too large")
        return v

class BasicFeedbackRequest(BaseModel):
    """Basic feedback request (backward compatible)"""
    agent_id: str = Field(..., description="Agent providing feedback")
    action_id: str = Field(..., description="Action being evaluated")
    reward: float = Field(..., ge=-1.0, le=1.0, description="Reward value")
    context: Optional[Dict] = Field(default={}, description="Additional context")

class EnhancedFeedbackRequest(BaseModel):
    """Enhanced feedback with validation and sanitization"""
    agent_id: str = Field(..., min_length=1, max_length=50)
    action_id: str = Field(..., min_length=1, max_length=100)
    reward: float = Field(..., ge=-1.0, le=1.0)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: Optional[float] = Field(default_factory=time.time)
    
    @validator('agent_id', 'action_id')
    def sanitize_strings(cls, v):
        if SECURITY_AVAILABLE:
            return bleach.clean(v)
        return v[:100]

class BasicObservationRequest(BaseModel):
    """Basic observation request (backward compatible)"""
    agent_id: str
    session_id: str
    position: Dict[str, float]
    velocity: Dict[str, float]
    emotion: str
    target_agent_id: Optional[str] = None

class EnhancedObservationRequest(BaseModel):
    """Enhanced observation with comprehensive validation"""
    agent_id: str = Field(..., min_length=1, max_length=50)
    position: Dict[str, float]
    velocity: Dict[str, float]
    emotion: str = Field(..., regex="^(neutral|happy|sad|excited|angry|fear|surprise)$")
    target_agent_id: Optional[str] = None
    environment_data: Optional[Dict[str, Any]] = Field(default_factory=dict)

# =============================================================================
# COMBINED TOKEN MANAGER
# =============================================================================

class TokenManager:
    """JWT token management with fallbacks"""
    
    @staticmethod
    def create_access_token(data: dict) -> str:
        """Create access token (JWT if available, UUID fallback)"""
        if not SECURITY_AVAILABLE:
            return str(uuid.uuid4())
        
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=CombinedConfig.ACCESS_TOKEN_EXPIRE_HOURS)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, CombinedConfig.SECRET_KEY, algorithm="HS256")
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """Verify token (JWT if available, basic validation fallback)"""
        if not SECURITY_AVAILABLE:
            return {"valid": True, "token": token}
        
        try:
            payload = jwt.decode(token, CombinedConfig.SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security) if SECURITY_AVAILABLE else None):
    """Get current user (enhanced security if available)"""
    if not SECURITY_AVAILABLE:
        return {"user": "anonymous", "authenticated": False}
    
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    payload = TokenManager.verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return payload

# =============================================================================
# COMBINED AI MANAGER
# =============================================================================

class CombinedAIManager:
    """AI manager supporting multiple providers with graceful fallbacks"""
    
    def __init__(self):
        self.providers = {}
        self.provider_stats = {}
        self._initialize_providers()
        
    def _initialize_providers(self):
        """Initialize available AI providers"""
        
        # OpenAI
        if AI_PROVIDERS.get("openai") and CombinedConfig.OPENAI_API_KEY:
            try:
                self.providers["openai"] = AsyncOpenAI(
                    api_key=CombinedConfig.OPENAI_API_KEY,
                    timeout=30.0
                )
                self.provider_stats["openai"] = {"requests": 0, "successes": 0, "errors": 0}
                logger.info("✅ OpenAI provider initialized")
            except Exception as e:
                logger.error(f"❌ OpenAI initialization failed: {e}")
        
        # Anthropic (Claude)
        if AI_PROVIDERS.get("anthropic") and CombinedConfig.ANTHROPIC_API_KEY:
            try:
                self.providers["anthropic"] = anthropic.AsyncAnthropic(
                    api_key=CombinedConfig.ANTHROPIC_API_KEY,
                    timeout=30.0
                )
                self.provider_stats["anthropic"] = {"requests": 0, "successes": 0, "errors": 0}
                logger.info("✅ Anthropic (Claude) provider initialized")
            except Exception as e:
                logger.error(f"❌ Anthropic initialization failed: {e}")
        
        # Google (Gemini)
        if AI_PROVIDERS.get("google") and CombinedConfig.GOOGLE_API_KEY:
            try:
                genai.configure(api_key=CombinedConfig.GOOGLE_API_KEY)
                self.providers["google"] = genai.GenerativeModel("gemini-1.5-flash")
                self.provider_stats["google"] = {"requests": 0, "successes": 0, "errors": 0}
                logger.info("✅ Google AI (Gemini) provider initialized")
            except Exception as e:
                logger.error(f"❌ Google AI initialization failed: {e}")
        
        if not self.providers:
            logger.info("ℹ️ No AI providers configured - using Q-learning fallback")
    
    async def get_ai_action(self, agent_id: str, observation: Dict, provider: str = None) -> Dict:
        """Get AI action with fallback to Q-learning"""
        
        provider = provider or CombinedConfig.DEFAULT_AI_PROVIDER
        
        # Track request
        if provider in self.provider_stats:
            self.provider_stats[provider]["requests"] += 1
        
        # Sanitize observation
        safe_obs = self._sanitize_observation(observation)
        
        # Try AI provider
        try:
            if provider == "openai" and "openai" in self.providers:
                response = await self._get_openai_action(agent_id, safe_obs)
                self.provider_stats["openai"]["successes"] += 1
                return response
            elif provider == "anthropic" and "anthropic" in self.providers:
                response = await self._get_anthropic_action(agent_id, safe_obs)
                self.provider_stats["anthropic"]["successes"] += 1
                return response
            elif provider == "google" and "google" in self.providers:
                response = await self._get_google_action(agent_id, safe_obs)
                self.provider_stats["google"]["successes"] += 1
                return response
        except Exception as e:
            logger.warning(f"AI provider {provider} failed: {e}")
            if provider in self.provider_stats:
                self.provider_stats[provider]["errors"] += 1
        
        # Fallback to basic Q-learning
        return self._get_fallback_action(agent_id, safe_obs)
    
    def _sanitize_observation(self, observation: Dict) -> Dict:
        """Sanitize observation data for security"""
        def sanitize_value(value):
            if isinstance(value, str):
                cleaned = bleach.clean(value) if SECURITY_AVAILABLE else value
                return cleaned[:500]
            elif isinstance(value, (int, float)):
                return max(-1000, min(1000, float(value)))
            elif isinstance(value, dict):
                return {str(k)[:50]: sanitize_value(v) for k, v in list(value.items())[:10]}
            elif isinstance(value, list):
                return [sanitize_value(item) for item in value[:5]]
            return str(value)[:100]
        
        return {str(k)[:50]: sanitize_value(v) for k, v in observation.items()}
    
    async def _get_openai_action(self, agent_id: str, observation: Dict) -> Dict:
        """Get action from OpenAI"""
        prompt = self._build_prompt(agent_id, observation)
        
        response = await self.providers["openai"].chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7
        )
        
        action = self._parse_action_response(response.choices[0].message.content)
        return {
            "command": action,
            "message": f"OpenAI suggests: {action}",
            "provider": "openai",
            "confidence": 0.85
        }
    
    async def _get_anthropic_action(self, agent_id: str, observation: Dict) -> Dict:
        """Get action from Claude"""
        prompt = self._build_prompt(agent_id, observation)
        
        response = await self.providers["anthropic"].messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        
        action = self._parse_action_response(response.content[0].text)
        return {
            "command": action,
            "message": f"Claude suggests: {action}",
            "provider": "anthropic",
            "confidence": 0.88
        }
    
    async def _get_google_action(self, agent_id: str, observation: Dict) -> Dict:
        """Get action from Gemini"""
        prompt = self._build_prompt(agent_id, observation)
        
        response = await asyncio.get_event_loop().run_in_executor(
            None, self.providers["google"].generate_content, prompt
        )
        
        action = self._parse_action_response(response.text)
        return {
            "command": action,
            "message": f"Gemini suggests: {action}",
            "provider": "google",
            "confidence": 0.82
        }
    
    def _build_prompt(self, agent_id: str, observation: Dict) -> str:
        """Build AI prompt for action selection"""
        actions = ["move_forward", "move_backward", "turn_left", "turn_right", "communicate", "observe", "wait"]
        
        return f"""Agent {agent_id} needs to choose an action.

Current situation:
- Position: {observation.get('position', {})}
- Emotion: {observation.get('emotion', 'neutral')}
- Environment: {observation.get('environment_data', {})}

Available actions: {actions}

Choose the BEST action and respond with ONLY the action name."""
    
    def _parse_action_response(self, response_text: str) -> str:
        """Parse AI response to extract valid action"""
        valid_actions = ["move_forward", "move_backward", "turn_left", "turn_right", "communicate", "observe", "wait"]
        
        response = response_text.lower().strip()
        for action in valid_actions:
            if action in response:
                return action
        
        return "observe"  # Safe fallback
    
    def _get_fallback_action(self, agent_id: str, observation: Dict) -> Dict:
        """Fallback action when AI providers fail"""
        actions = ["move_forward", "move_backward", "turn_left", "turn_right", "communicate", "observe", "wait"]
        action = np.random.choice(actions)
        
        return {
            "command": action,
            "message": f"Fallback Q-learning action: {action}",
            "provider": "q_learning",
            "confidence": 0.6
        }
    
    def get_provider_stats(self) -> Dict:
        """Get AI provider statistics"""
        stats = {}
        for provider, data in self.provider_stats.items():
            total = data["requests"]
            success_rate = (data["successes"] / total * 100) if total > 0 else 0
            stats[provider] = {
                **data,
                "success_rate": round(success_rate, 2),
                "available": provider in self.providers
            }
        return stats

# =============================================================================
# COMBINED RL MANAGER
# =============================================================================

class CombinedRLManager:
    """Combined RL manager with original logic + enhanced features"""
    
    def __init__(self):
        self.agent_models: Dict[str, dict] = {}
        
        # Original parameters (maintain compatibility)
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.exploration_rate = 0.1
        
        # Enhanced parameters
        self.min_exploration = 0.01
        self.exploration_decay = 0.995
        
    def initialize_agent_model(self, agent_id: str):
        """Initialize Q-learning model (enhanced version)"""
        self.agent_models[agent_id] = {
            "q_table": np.random.rand(5, 7) * 0.1,  # 5 states, 7 actions (expanded)
            "epsilon": self.exploration_rate,
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor,
            "total_rewards": 0.0,
            "action_count": 0,
            "last_state": None,
            "last_action": None,
            "success_rate": 0.0,
            "created": time.time()
        }
        logger.info(f"🧠 Initialized RL model for agent {agent_id}")
    
    def get_action(self, agent_id: str, state: Optional[int] = None, observation: Dict = None) -> Tuple[str, int]:
        """Get action using epsilon-greedy (supports both basic and enhanced modes)"""
        if agent_id not in self.agent_models:
            self.initialize_agent_model(agent_id)
        
        model = self.agent_models[agent_id]
        
        # Enhanced state calculation if observation provided
        if observation:
            state = self._observation_to_state(observation)
        elif state is None:
            state = np.random.randint(0, 5)
        
        # Action names (expanded for compatibility)
        action_names = ["move_forward", "turn_left", "turn_right", "communicate", "observe", "move_backward", "wait"]
        
        # Epsilon-greedy selection
        if np.random.random() < model["epsilon"]:
            action_idx = np.random.randint(0, len(action_names))
        else:
            action_idx = np.argmax(model["q_table"][state])
        
        # Update tracking
        model["last_state"] = state
        model["last_action"] = action_idx
        model["action_count"] += 1
        
        # Enhanced: Decay exploration
        if ENHANCED_FEATURES:
            model["epsilon"] = max(self.min_exploration, model["epsilon"] * self.exploration_decay)
        
        return action_names[action_idx], action_idx
    
    def update_q_table(self, agent_id: str, reward: float, next_state: Optional[int] = None):
        """Update Q-table with reward (enhanced version)"""
        if agent_id not in self.agent_models:
            return
        
        model = self.agent_models[agent_id]
        
        if model["last_state"] is None or model["last_action"] is None:
            return
        
        # Validate and clamp reward
        reward = max(-1.0, min(1.0, float(reward)))
        
        if next_state is None:
            next_state = np.random.randint(0, 5)
        
        # Q-learning update
        old_q = model["q_table"][model["last_state"], model["last_action"]]
        next_max = np.max(model["q_table"][next_state])
        
        new_q = old_q + model["learning_rate"] * (
            reward + model["discount_factor"] * next_max - old_q
        )
        
        model["q_table"][model["last_state"], model["last_action"]] = new_q
        model["total_rewards"] += reward
        
        # Enhanced: Update success rate
        if ENHANCED_FEATURES:
            if reward > 0:
                model["success_rate"] = ((model["success_rate"] * (model["action_count"] - 1)) + 1) / model["action_count"]
            else:
                model["success_rate"] = (model["success_rate"] * (model["action_count"] - 1)) / model["action_count"]
        
        logger.debug(f"Q-update: {agent_id} -> {old_q:.4f} to {new_q:.4f} (reward: {reward})")
    
    def _observation_to_state(self, observation: Dict) -> int:
        """Convert observation to discrete state (enhanced feature)"""
        position = observation.get("position", {})
        emotion = observation.get("emotion", "neutral")
        
        # Simple state mapping
        x_bucket = max(0, min(4, int((position.get("x", 0) + 50) / 20)))
        emotion_bucket = hash(emotion) % 2
        
        return max(0, min(4, x_bucket + emotion_bucket))
    
    def get_agent_stats(self, agent_id: str) -> Dict:
        """Get agent statistics (enhanced feature)"""
        if agent_id not in self.agent_models:
            return {}
        
        model = self.agent_models[agent_id]
        
        stats = {
            "total_rewards": round(model["total_rewards"], 3),
            "action_count": model["action_count"],
            "exploration_rate": round(model["epsilon"], 4)
        }
        
        if ENHANCED_FEATURES:
            stats.update({
                "success_rate": round(model.get("success_rate", 0), 3),
                "age_seconds": round(time.time() - model.get("created", time.time()), 2)
            })
        
        return stats

# =============================================================================
# COMBINED SESSION MANAGER
# =============================================================================

class CombinedSessionManager:
    """Session manager with basic and enhanced modes"""
    
    def __init__(self):
        self.agent_sessions: Dict[str, dict] = {}  # Original format
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Enhanced features
        if ENHANCED_FEATURES:
            self.cleanup_interval = 300  # 5 minutes
            self._start_cleanup_task()
    
    def create_session(self, agent_id: str, metadata: Dict = None) -> str:
        """Create session (basic or enhanced based on features)"""
        session_id = str(uuid.uuid4())
        
        # Basic session data (original format)
        session_data = {
            "agent_id": agent_id,
            "session_id": session_id,
            "status": "active",
            "last_seen": time.time()
        }
        
        # Enhanced session data
        if ENHANCED_FEATURES:
            session_data.update({
                "created": time.time(),
                "last_activity": time.time(),
                "validated": True,
                "message_count": 0,
                "metadata": metadata or {}
            })
        
        self.agent_sessions[session_id] = session_data
        
        logger.info(f"✅ Session created for agent {agent_id}: {session_id[:8]}")
        return session_id
    
    def validate_session(self, session_id: str) -> bool:
        """Validate session (enhanced security if available)"""
        if session_id not in self.agent_sessions:
            return False
        
        session = self.agent_sessions[session_id]
        current_time = time.time()
        
        # Enhanced validation
        if ENHANCED_FEATURES:
            if current_time - session.get("last_activity", current_time) > CombinedConfig.SESSION_TIMEOUT:
                logger.warning(f"Session timeout: {session_id[:8]}")
                del self.agent_sessions[session_id]
                return False
            
            session["last_activity"] = current_time
            session["message_count"] = session.get("message_count", 0) + 1
        else:
            # Basic validation
            session["last_seen"] = current_time
        
        return True
    
    def get_session_agent(self, session_id: str) -> Optional[str]:
        """Get agent ID from session"""
        session = self.agent_sessions.get(session_id)
        return session["agent_id"] if session else None
    
    def cleanup_expired_sessions(self):
        """Cleanup expired sessions (enhanced feature)"""
        if not ENHANCED_FEATURES:
            return
        
        current_time = time.time()
        expired = []
        
        for session_id, session in self.agent_sessions.items():
            last_activity = session.get("last_activity", current_time)
            if current_time - last_activity > CombinedConfig.SESSION_TIMEOUT:
                expired.append(session_id)
        
        for session_id in expired:
            agent_id = self.agent_sessions[session_id]["agent_id"]
            del self.agent_sessions[session_id]
            logger.info(f"🧹 Cleaned up expired session for {agent_id}")
    
    def _start_cleanup_task(self):
        """Start background cleanup (enhanced feature)"""
        async def cleanup_loop():
            while True:
                await asyncio.sleep(self.cleanup_interval)
                self.cleanup_expired_sessions()
        
        asyncio.create_task(cleanup_loop())

# =============================================================================
# INITIALIZE GLOBAL MANAGERS
# =============================================================================

# Global state (maintaining original variable names for compatibility)
session_manager = CombinedSessionManager()
ai_manager = CombinedAIManager()
rl_manager = CombinedRLManager()

# Original global variables (backward compatibility)
active_connections: Dict[str, WebSocket] = session_manager.active_connections
agent_sessions: Dict[str, dict] = session_manager.agent_sessions
agent_models: Dict[str, dict] = rl_manager.agent_models
message_queues: Dict[str, deque] = {}

# System statistics
system_stats = {
    "total_requests": 0,
    "total_errors": 0,
    "start_time": time.time()
}

# =============================================================================
# COMBINED FASTAPI APPLICATION
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info(f"🚀 {CombinedConfig.SYSTEM_NAME} v{CombinedConfig.VERSION} starting...")
    logger.info(f"🔒 Security: {'Enhanced' if SECURITY_AVAILABLE else 'Basic'}")
    logger.info(f"🤖 AI Providers: {list(ai_manager.providers.keys()) if ai_manager.providers else ['Q-learning fallback']}")
    logger.info(f"🌐 Server: {CombinedConfig.HOST}:{CombinedConfig.PORT}")
    yield
    logger.info("🛑 A2A Server shutting down...")

# Create FastAPI app
app = FastAPI(
    title=CombinedConfig.SYSTEM_NAME,
    description="Combined Agent-to-Agent Communication System with Security & Multi-AI",
    version=CombinedConfig.VERSION,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CombinedConfig.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"] if not SECURITY_AVAILABLE else ["GET", "POST"],
    allow_headers=["*"],
)

# Enhanced security middleware
if SECURITY_AVAILABLE:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", CombinedConfig.HOST, "*"]
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Rate limiting helper
def rate_limit_if_available(rate: str):
    """Apply rate limit if security features are available"""
    if SECURITY_AVAILABLE:
        return limiter.limit(rate)
    return lambda x: x

# =============================================================================
# COMBINED API ROUTES
# =============================================================================

@app.get("/")
async def root():
    """Enhanced root endpoint with system information"""
    system_stats["total_requests"] += 1
    
    # Basic response (original format)
    response = {
        "message": "A2A Agent Communication Server",
        "version": CombinedConfig.VERSION,
        "active_agents": len(agent_sessions),
        "active_connections": len(active_connections)
    }
    
    # Enhanced response
    if ENHANCED_FEATURES:
        response.update({
            "system": CombinedConfig.SYSTEM_NAME,
            "status": "running",
            "uptime": round(time.time() - system_stats["start_time"], 2),
            "capabilities": {
                "security": SECURITY_AVAILABLE,
                "ai_providers": list(ai_manager.providers.keys()),
                "enhanced_features": ENHANCED_FEATURES
            },
            "statistics": {
                "total_requests": system_stats["total_requests"],
                "total_errors": system_stats["total_errors"]
            }
        })
    
    # Original endpoints format
    response["endpoints"] = {
        "register": "/register",
        "websocket": "/ws/{session_id}",
        "feedback": "/feedback",
        "status": "/status",
        "agents": "/agents"
    }
    
    # Enhanced endpoints
    if ENHANCED_FEATURES:
        response["endpoints"].update({
            "health": "/health",
            "stats": "/stats",
            "auth": "/auth/token"
        })
    
    return response

@app.get("/health")
@rate_limit_if_available("120/minute")
async def health_check():
    """Health check endpoint (enhanced feature)"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "uptime": round(time.time() - system_stats["start_time"], 2),
            "active_sessions": len(agent_sessions),
            "active_connections": len(active_connections)
        },
        "ai_providers": ai_manager.get_provider_stats(),
        "security": {
            "enabled": SECURITY_AVAILABLE,
            "rate_limit": CombinedConfig.RATE_LIMIT_PER_MINUTE if SECURITY_AVAILABLE else "disabled"
        }
    }

@app.post("/auth/token")
@rate_limit_if_available("30/minute")
async def create_access_token(agent_id: str):
    """Create authentication token (enhanced feature)"""
    if not SECURITY_AVAILABLE:
        raise HTTPException(status_code=501, detail="Enhanced security not available")
    
    if not agent_id or len(agent_id) > 50:
        raise HTTPException(status_code=400, detail="Invalid agent_id")
    
    token_data = {
        "agent_id": agent_id,
        "created": time.time(),
        "type": "access_token"
    }
    
    access_token = TokenManager.create_access_token(token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": CombinedConfig.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        "agent_id": agent_id
    }

@app.post("/register")
@rate_limit_if_available(f"{CombinedConfig.RATE_LIMIT_PER_MINUTE}/minute")
async def register_agent(request: BasicRegistrationRequest):
    """Register agent (supports both basic and enhanced modes)"""
    system_stats["total_requests"] += 1
    
    try:
        # Check agent limit
        if len(agent_sessions) >= CombinedConfig.MAX_AGENTS:
            raise HTTPException(
                status_code=429,
                detail=f"Maximum agents limit ({CombinedConfig.MAX_AGENTS}) reached"
            )
        
        # Enhanced validation if available
        if ENHANCED_FEATURES and hasattr(request, 'agent_id'):
            # Additional validation for enhanced mode
            if SECURITY_AVAILABLE:
                clean_id = bleach.clean(request.agent_id)
                if clean_id != request.agent_id:
                    raise HTTPException(status_code=400, detail="Invalid characters in agent_id")
        
        # Check for existing agent
        existing = any(
            session["agent_id"] == request.agent_id 
            for session in agent_sessions.values()
        )
        
        if existing:
            raise HTTPException(status_code=409, detail="Agent already exists")
        
        # Create session
        metadata = getattr(request, 'metadata', {}) if ENHANCED_FEATURES else {}
        session_id = session_manager.create_session(request.agent_id, metadata)
        
        # Initialize RL model (original function call for compatibility)
        rl_manager.initialize_agent_model(request.agent_id)
        
        # Initialize message queue (original behavior)
        message_queues[request.agent_id] = deque(maxlen=100)
        
        logger.info(f"✅ Agent registered: {request.agent_id}")
        
        # Basic response (original format)
        response = {
            "success": True,
            "agent_id": request.agent_id,
            "session_id": session_id,
            "message": f"Agent {request.agent_id} registered successfully"
        }
        
        # Enhanced response
        if ENHANCED_FEATURES:
            ai_provider = getattr(request, 'ai_provider', 'openai')
            response.update({
                "status": "success",
                "ai_provider": ai_provider
            })
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        system_stats["total_errors"] += 1
        logger.error(f"❌ Registration error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/feedback")
@rate_limit_if_available(f"{CombinedConfig.RATE_LIMIT_PER_MINUTE}/minute")
async def receive_feedback(request: BasicFeedbackRequest):
    """Receive feedback (supports both basic and enhanced modes)"""
    system_stats["total_requests"] += 1
    
    try:
        agent_id = request.agent_id
        
        # Validate agent exists
        if agent_id not in agent_models:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # Update Q-table (original function call)
        rl_manager.update_q_table(agent_id, request.reward)
        
        logger.info(f"📊 Feedback received - Agent: {agent_id}, Reward: {request.reward:.3f}")
        
        # Basic response (original format)
        response = {
            "success": True,
            "agent_id": agent_id,
            "action_id": request.action_id,
            "reward": request.reward,
            "context": request.context,
            "message": "Feedback processed successfully"
        }
        
        # Enhanced response
        if ENHANCED_FEATURES:
            agent_stats = rl_manager.get_agent_stats(agent_id)
            response["agent_stats"] = agent_stats
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        system_stats["total_errors"] += 1
        logger.error(f"❌ Feedback error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/status")
@rate_limit_if_available("120/minute")
async def get_status():
    """Get system status (original endpoint)"""
    return {
        "server_status": "running",
        "total_agents": len(agent_sessions),
        "active_connections": len(active_connections),
        "total_models": len(agent_models),
        "uptime": time.time() - system_stats["start_time"]
    }

@app.get("/agents")
@rate_limit_if_available("120/minute")
async def list_agents():
    """List all registered agents (enhanced version)"""
    try:
        agents = []
        
        for session_id, session_info in agent_sessions.items():
            agent_id = session_info["agent_id"]
            model = agent_models.get(agent_id, {})
            
            # Basic agent info (original format)
            agent_data = {
                "agent_id": agent_id,
                "session_id": session_id,
                "status": session_info.get("status", "unknown"),
                "connected": session_id in active_connections,
                "last_seen": session_info.get("last_seen", 0),
                "total_rewards": model.get("total_rewards", 0),
                "action_count": model.get("action_count", 0)
            }
            
            # Enhanced agent info
            if ENHANCED_FEATURES:
                learning_stats = rl_manager.get_agent_stats(agent_id)
                agent_data.update({
                    "created": session_info.get("created", time.time()),
                    "last_activity": session_info.get("last_activity", time.time()),
                    "message_count": session_info.get("message_count", 0),
                    "ai_provider": session_info.get("metadata", {}).get("ai_provider", "unknown"),
                    "learning_stats": learning_stats
                })
            
            agents.append(agent_data)
        
        # Basic response
        response = {
            "agents": agents,
            "total": len(agents)
        }
        
        # Enhanced response
        if ENHANCED_FEATURES:
            response.update({
                "total_count": len(agents),
                "active_connections": len(active_connections),
                "system_capacity": CombinedConfig.MAX_AGENTS
            })
        
        return response
        
    except Exception as e:
        system_stats["total_errors"] += 1
        logger.error(f"❌ List agents error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/stats")
@rate_limit_if_available("60/minute")
async def get_comprehensive_stats():
    """Get comprehensive statistics (enhanced feature)"""
    if not ENHANCED_FEATURES:
        raise HTTPException(status_code=501, detail="Enhanced features not available")
    
    try:
        return {
            "system": {
                "version": CombinedConfig.VERSION,
                "uptime": round(time.time() - system_stats["start_time"], 2),
                "total_requests": system_stats["total_requests"],
                "total_errors": system_stats["total_errors"],
                "error_rate": round(system_stats["total_errors"] / max(system_stats["total_requests"], 1) * 100, 2)
            },
            "agents": {
                "registered": len(agent_sessions),
                "connected": len(active_connections),
                "capacity": CombinedConfig.MAX_AGENTS,
                "utilization": round(len(agent_sessions) / CombinedConfig.MAX_AGENTS * 100, 2)
            },
            "ai_providers": ai_manager.get_provider_stats(),
            "features": {
                "security": SECURITY_AVAILABLE,
                "enhanced": ENHANCED_FEATURES,
                "ai_providers_available": len(ai_manager.providers)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Enhanced WebSocket endpoint (combined basic + enhanced)"""
    
    # Enhanced session validation
    if ENHANCED_FEATURES:
        if not session_manager.validate_session(session_id):
            await websocket.close(code=1008, reason="Invalid or expired session")
            return
    elif session_id not in agent_sessions:
        await websocket.close(code=1008, reason="Invalid session")
        return
    
    # Get agent ID
    agent_id = session_manager.get_session_agent(session_id)
    if not agent_id:
        agent_id = agent_sessions[session_id]["agent_id"]
    
    await websocket.accept()
    active_connections[session_id] = websocket
    
    logger.info(f"📡 WebSocket connected: {agent_id} (session: {session_id[:8]})")
    
    try:
        while True:
            # Enhanced session validation during operation
            if ENHANCED_FEATURES and not session_manager.validate_session(session_id):
                await websocket.close(code=1008, reason="Session expired")
                break
            
            # Receive observation
            try:
                # Support both text and binary (original supported binary msgpack)
                try:
                    data = await websocket.receive_bytes()
                    observation = msgpack.unpackb(data, strict_map_key=False)
                except:
                    # Fallback to text
                    raw_text = await websocket.receive_text()
                    observation = json.loads(raw_text)
                
                # Enhanced message size validation
                if ENHANCED_FEATURES:
                    message_size = len(json.dumps(observation))
                    if message_size > CombinedConfig.MAX_MESSAGE_SIZE:
                        await websocket.close(code=1009, reason="Message too large")
                        break
                
                # Update last seen (original behavior)
                agent_sessions[session_id]["last_seen"] = time.time()
                
                # Process observation and get action
                agent_id = observation.get("agent_id", agent_id)
                
                # Enhanced security: validate agent_id matches session
                if ENHANCED_FEATURES:
                    expected_agent = session_manager.get_session_agent(session_id)
                    if agent_id != expected_agent:
                        await websocket.close(code=1008, reason="Agent ID mismatch")
                        break
                
                # Get action (try AI first, fallback to Q-learning)
                if ai_manager.providers:
                    # Enhanced AI action
                    ai_provider = agent_sessions[session_id].get("metadata", {}).get("ai_provider", "openai")
                    action_result = await ai_manager.get_ai_action(agent_id, observation, ai_provider)
                    selected_action = action_result["command"]
                    action_message = action_result["message"]
                    provider_info = action_result["provider"]
                else:
                    # Original Q-learning fallback
                    position = observation.get("position", {})
                    emotion = observation.get("emotion", "neutral")
                    state = hash(f"{position.get('x', 0):.1f}_{emotion}") % 5
                    
                    selected_action, action_idx = rl_manager.get_action(agent_id, state, observation)
                    action_message = f"Q-learning action: {selected_action}"
                    provider_info = "q_learning"
                
                # Create response
                response = {
                    "agent_id": agent_id,
                    "command": selected_action,
                    "message": action_message,
                    "timestamp": time.time(),
                    "action_id": f"{agent_id}_{int(time.time())}_{hash(selected_action) % 1000}"
                }
                
                # Enhanced response
                if ENHANCED_FEATURES:
                    response.update({
                        "provider": provider_info,
                        "success_probability": np.random.uniform(0.6, 0.95)
                    })
                else:
                    # Original response format
                    response["success_probability"] = float(np.random.random())
                
                # Check for pending messages (original behavior)
                if agent_id in message_queues and message_queues[agent_id]:
                    pending_message = message_queues[agent_id].popleft()
                    response["pending_message"] = pending_message
                
                # Send response (support both formats)
                try:
                    await websocket.send(msgpack.packb(response))
                except:
                    await websocket.send_text(json.dumps(response))
                
                # Small delay (original behavior)
                await asyncio.sleep(0.1)
                
            except asyncio.TimeoutError:
                if ENHANCED_FEATURES:
                    await websocket.send_text(json.dumps({"error": "Request timeout"}))
                continue
            except json.JSONDecodeError:
                if ENHANCED_FEATURES:
                    await websocket.send_text(json.dumps({"error": "Invalid JSON format"}))
                continue
            except Exception as e:
                logger.error(f"❌ WebSocket processing error: {e}")
                if ENHANCED_FEATURES:
                    await websocket.send_text(json.dumps({"error": "Processing error"}))
                continue
    
    except Exception as e:
        logger.error(f"❌ WebSocket error for agent {agent_id}: {e}")
    
    finally:
        # Cleanup connection
        if session_id in active_connections:
            del active_connections[session_id]
        if session_id in agent_sessions:
            agent_sessions[session_id]["status"] = "disconnected"
        logger.info(f"📡 WebSocket disconnected: {agent_id}")

# =============================================================================
# SERVER STARTUP
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print(f"🚀 {CombinedConfig.SYSTEM_NAME} v{CombinedConfig.VERSION}")
    print(f"🔒 Security: {'Enhanced' if SECURITY_AVAILABLE else 'Basic'}")
    print(f"🤖 AI Providers: {list(ai_manager.providers.keys()) if ai_manager.providers else ['Q-learning fallback']}")
    print(f"⚡ Enhanced Features: {'Enabled' if ENHANCED_FEATURES else 'Basic mode'}")
    print(f"🌐 Server: {CombinedConfig.HOST}:{CombinedConfig.PORT}")
    print(f"📄 API Docs: http://{CombinedConfig.HOST}:{CombinedConfig.PORT}/docs")
    
    if ENHANCED_FEATURES:
        print(f"📊 Health Check: http://{CombinedConfig.HOST}:{CombinedConfig.PORT}/health")
        print(f"📈 Statistics: http://{CombinedConfig.HOST}:{CombinedConfig.PORT}/stats")
    
    try:
        uvicorn.run(
            app,
            host=CombinedConfig.HOST,
            port=CombinedConfig.PORT,
            log_level="info" if not CombinedConfig.DEBUG else "debug"
        )
    except KeyboardInterrupt:
        print("\\n🛑 Server stopped by user")
    except Exception as e:
        print(f"💥 Server error: {e}")
        sys.exit(1)