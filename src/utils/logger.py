"""
Logging setup and utilities
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from .config import Config


def setup_logging(
    log_file: Optional[str] = None,
    log_level: Optional[str] = None,
    logger_name: str = "rla2a"
) -> logging.Logger:
    """
    Setup logging configuration
    
    Args:
        log_file: Optional log file path
        log_level: Optional log level
        logger_name: Logger name
        
    Returns:
        Configured logger
    """
    level = log_level or Config.LOG_LEVEL
    file_path = log_file or Config.LOG_FILE
    
    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler
    if file_path:
        log_path = Path(file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get logger by name
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

