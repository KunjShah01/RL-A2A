"""
Rate Limiter Middleware
"""

import time
import logging
from typing import Dict, Optional
from collections import defaultdict, deque


class RateLimiter:
    """Rate limiter using token bucket algorithm"""
    
    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize rate limiter
        
        Args:
            requests_per_minute: Maximum requests per minute
        """
        self.requests_per_minute = requests_per_minute
        self.tokens_per_second = requests_per_minute / 60.0
        self.buckets: Dict[str, deque] = defaultdict(lambda: deque())
        self._logger = logging.getLogger(__name__)
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed
        
        Args:
            identifier: Request identifier (e.g., agent_id, IP address)
            
        Returns:
            True if allowed
        """
        now = time.time()
        bucket = self.buckets[identifier]
        
        # Remove old entries (older than 1 minute)
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        
        # Check if under limit
        if len(bucket) < self.requests_per_minute:
            bucket.append(now)
            return True
        
        self._logger.debug(f"Rate limit exceeded for {identifier}")
        return False

