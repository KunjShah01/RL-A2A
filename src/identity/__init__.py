"""
Identity module - DID/VC support for decentralized identity
"""

from .did_resolver import DIDResolver
from .vc_issuer import VCIssuer, VCVerifier
from .key_manager import KeyManager
from .auth_middleware import DIDAuthMiddleware

__all__ = [
    "DIDResolver",
    "VCIssuer",
    "VCVerifier",
    "KeyManager",
    "DIDAuthMiddleware",
]



