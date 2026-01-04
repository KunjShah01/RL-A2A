"""
DID Resolver - Decentralized Identifier resolution
"""

import logging
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class DIDResolver:
    """
    DID Resolver for resolving Decentralized Identifiers
    
    Supports did:web and did:key methods initially
    """
    
    # DID regex pattern
    DID_PATTERN = re.compile(r'^did:([a-z0-9]+):([a-zA-Z0-9._:%-]+)$')
    
    def __init__(self):
        """Initialize DID resolver"""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._logger = logging.getLogger(__name__)
    
    def parse_did(self, did: str) -> Optional[Dict[str, str]]:
        """
        Parse a DID into components
        
        Args:
            did: Decentralized Identifier string
            
        Returns:
            Dictionary with method and identifier, or None if invalid
        """
        match = self.DID_PATTERN.match(did)
        if not match:
            return None
        
        return {
            "did": did,
            "method": match.group(1),
            "identifier": match.group(2),
        }
    
    def resolve(self, did: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a DID to its document
        
        Args:
            did: Decentralized Identifier to resolve
            
        Returns:
            DID document or None if resolution fails
        """
        # Check cache
        if did in self._cache:
            return self._cache[did]
        
        # Parse DID
        parsed = self.parse_did(did)
        if not parsed:
            self._logger.warning(f"Invalid DID format: {did}")
            return None
        
        method = parsed["method"]
        identifier = parsed["identifier"]
        
        # Route to method-specific resolver
        if method == "key":
            doc = self._resolve_did_key(identifier)
        elif method == "web":
            doc = self._resolve_did_web(identifier)
        else:
            self._logger.warning(f"Unsupported DID method: {method}")
            return None
        
        # Cache result
        if doc:
            self._cache[did] = doc
        
        return doc
    
    def _resolve_did_key(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Resolve did:key identifier
        
        Args:
            identifier: DID key identifier
            
        Returns:
            DID document
        """
        # did:key resolution is deterministic
        # For now, return a basic document structure
        # In production, implement proper multibase/multicodec decoding
        return {
            "id": f"did:key:{identifier}",
            "verificationMethod": [{
                "id": f"did:key:{identifier}#keys-1",
                "type": "Ed25519VerificationKey2020",
                "controller": f"did:key:{identifier}",
                "publicKeyMultibase": identifier,
            }],
            "authentication": [f"did:key:{identifier}#keys-1"],
            "assertionMethod": [f"did:key:{identifier}#keys-1"],
        }
    
    def _resolve_did_web(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Resolve did:web identifier
        
        Args:
            identifier: DID web identifier (domain/path)
            
        Returns:
            DID document
        """
        # did:web resolution requires HTTP fetch
        # For now, return a basic structure
        # In production, implement HTTP resolution
        domain = identifier.split('/')[0]
        return {
            "id": f"did:web:{identifier}",
            "verificationMethod": [{
                "id": f"did:web:{identifier}#keys-1",
                "type": "Ed25519VerificationKey2020",
                "controller": f"did:web:{identifier}",
            }],
            "service": [{
                "id": f"did:web:{identifier}#service",
                "type": "LinkedDomains",
                "serviceEndpoint": f"https://{domain}",
            }],
        }
    
    def clear_cache(self) -> None:
        """Clear DID resolution cache"""
        self._cache.clear()
    
    def get_verification_method(self, did: str, method_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get verification method from DID document
        
        Args:
            did: Decentralized Identifier
            method_id: Optional specific verification method ID
            
        Returns:
            Verification method object
        """
        doc = self.resolve(did)
        if not doc:
            return None
        
        verification_methods = doc.get("verificationMethod", [])
        if not verification_methods:
            return None
        
        if method_id:
            # Find specific method
            for method in verification_methods:
                if method.get("id") == method_id:
                    return method
            return None
        else:
            # Return first method
            return verification_methods[0]



