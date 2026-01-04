"""
Input Validator Middleware
"""

import logging
from typing import Any, Dict, Optional
import bleach


class InputValidator:
    """Input validator for sanitization and validation"""
    
    def __init__(self):
        """Initialize input validator"""
        self._logger = logging.getLogger(__name__)
    
    def sanitize_string(self, value: str, max_length: int = 10000) -> str:
        """
        Sanitize string input
        
        Args:
            value: String value
            max_length: Maximum length
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            value = str(value)
        
        # Truncate if too long
        if len(value) > max_length:
            value = value[:max_length]
        
        # Sanitize HTML
        try:
            value = bleach.clean(value, tags=[], strip=True)
        except Exception:
            # Fallback if bleach not available
            pass
        
        return value
    
    def validate_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Validate message data
        
        Args:
            message_data: Message data dictionary
            
        Returns:
            True if valid
        """
        required_fields = ["sender_id", "receiver_id", "content"]
        
        for field in required_fields:
            if field not in message_data:
                self._logger.warning(f"Missing required field: {field}")
                return False
        
        # Sanitize content
        if isinstance(message_data["content"], str):
            message_data["content"] = self.sanitize_string(message_data["content"])
        
        return True

