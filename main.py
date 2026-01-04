"""
RL-A2A v2.0 - Main Entry Point
Rebuilt architecture with all new features
"""

import asyncio
import logging
import sys
from pathlib import Path

from src.utils.config import Config, get_config
from src.utils.logger import setup_logging
from src.api.app import create_app

# Setup logging
logger = setup_logging()


async def main():
    """Main application entry point"""
    logger.info(f"Starting {Config.SYSTEM_NAME} v{Config.VERSION}")
    
    # Create FastAPI application
    app = create_app()
    
    # Import uvicorn
    try:
        import uvicorn
    except ImportError:
        logger.error("uvicorn not installed. Install with: pip install uvicorn")
        sys.exit(1)
    
    # Start server
    config = uvicorn.Config(
        app,
        host=Config.SERVER_HOST,
        port=Config.SERVER_PORT,
        log_level=Config.LOG_LEVEL.lower()
    )
    server = uvicorn.Server(config)
    
    logger.info(f"Server starting on {Config.SERVER_HOST}:{Config.SERVER_PORT}")
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)



