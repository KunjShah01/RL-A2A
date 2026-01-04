"""
Configuration management
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    """
    Configuration manager
    """
    
    # System
    VERSION = "2.0.0"
    SYSTEM_NAME = "RL-A2A v2.0"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # Server
    SERVER_HOST = os.getenv("A2A_HOST", "localhost")
    SERVER_PORT = int(os.getenv("A2A_PORT", "8000"))
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8501"))
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    MAX_MESSAGE_SIZE = int(os.getenv("MAX_MESSAGE_SIZE", "1048576"))  # 1MB
    
    # AI Providers
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    DEFAULT_AI_PROVIDER = os.getenv("DEFAULT_AI_PROVIDER", "openai")
    
    # System Limits
    MAX_AGENTS = int(os.getenv("MAX_AGENTS", "1000"))
    MAX_CONNECTIONS = int(os.getenv("MAX_CONNECTIONS", "10000"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "rla2a.log")
    
    # FRL
    FRL_ENABLED = os.getenv("FRL_ENABLED", "false").lower() == "true"
    FRL_AGGREGATION_SERVER = os.getenv("FRL_AGGREGATION_SERVER")
    FRL_AGGREGATION_INTERVAL = int(os.getenv("FRL_AGGREGATION_INTERVAL", "3600"))  # seconds
    
    # HITL
    HITL_ENABLED = os.getenv("HITL_ENABLED", "true").lower() == "true"
    HITL_TIMEOUT_SECONDS = int(os.getenv("HITL_TIMEOUT_SECONDS", "3600"))
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "version": cls.VERSION,
            "system_name": cls.SYSTEM_NAME,
            "debug": cls.DEBUG,
            "server_host": cls.SERVER_HOST,
            "server_port": cls.SERVER_PORT,
            "max_agents": cls.MAX_AGENTS,
            "max_connections": cls.MAX_CONNECTIONS,
        }
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get config value"""
        return getattr(cls, key.upper(), default)


_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

