"""
DID-based Authentication Middleware
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .did_resolver import DIDResolver
from .key_manager import KeyManager

logger = logging.getLogger(__name__)


class DIDAuthMiddleware:
    """
    DID-based Authentication Middleware
    
    Provides authentication using Decentralized Identifiers
    """
    
    def __init__(self, did_resolver: DIDResolver):
        """
        Initialize DID Auth Middleware
        
        Args:
            did_resolver: DID resolver instance
        """
        self.did_resolver = did_resolver
        self.key_manager = KeyManager()
        self.security = HTTPBearer(auto_error=False)
        self._logger = logging.getLogger(__name__)
    
    async def authenticate(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Authenticate request using DID
        
        Args:
            request: FastAPI request object
            
        Returns:
            Authentication context with DID and agent info, or None if not authenticated
        """
        # Try to get authorization header
        credentials: Optional[HTTPAuthorizationCredentials] = await self.security(request)
        
        if not credentials:
            # Check for DID in headers or query params
            did = request.headers.get("X-Agent-DID") or request.query_params.get("did")
            if did:
                return await self._authenticate_did(did, request)
            return None
        
        # Check for DID token format
        token = credentials.credentials
        if token.startswith("did:"):
            return await self._authenticate_did(token, request)
        
        # Otherwise, treat as JWT with DID claim (fallback)
        return await self._authenticate_jwt(token, request)
    
    async def _authenticate_did(self, did: str, request: Request) -> Optional[Dict[str, Any]]:
        """
        Authenticate using DID directly
        
        Args:
            did: Decentralized Identifier
            request: Request object
            
        Returns:
            Authentication context
        """
        # Resolve DID
        did_doc = self.did_resolver.resolve(did)
        if not did_doc:
            self._logger.warning(f"Could not resolve DID: {did}")
            return None
        
        # Check for signature in headers
        signature = request.headers.get("X-Signature")
        message = request.headers.get("X-Message")
        
        if signature and message:
            # Verify signature
            # In production, implement full signature verification
            pass
        
        return {
            "did": did,
            "did_document": did_doc,
            "authenticated": True,
        }
    
    async def _authenticate_jwt(self, token: str, request: Request) -> Optional[Dict[str, Any]]:
        """
        Authenticate using JWT (fallback for backward compatibility)
        
        Args:
            token: JWT token
            request: Request object
            
        Returns:
            Authentication context
        """
        # In production, decode JWT and extract DID claim
        # For now, return None to require DID-based auth
        return None
    
    def require_auth(self, request: Request) -> Dict[str, Any]:
        """
        Require authentication (raises exception if not authenticated)
        
        Args:
            request: Request object
            
        Returns:
            Authentication context
            
        Raises:
            HTTPException: If not authenticated
        """
        # This would be used as a dependency in FastAPI routes
        # For now, provide a simple implementation
        auth_context = None  # Would call authenticate(request)
        
        if not auth_context:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return auth_context


def get_auth_context(request: Request) -> Optional[Dict[str, Any]]:
    """
    Dependency function for FastAPI to get auth context
    
    Args:
        request: Request object
        
    Returns:
        Authentication context or None
    """
    # This would be injected with the middleware instance
    # For now, return None
    return None



