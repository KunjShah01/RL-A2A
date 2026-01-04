"""
Key Manager - Cryptographic key management for DID/VC
"""

import secrets
import base64
from typing import Optional, Tuple
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)


class KeyManager:
    """
    Key Manager for generating and managing cryptographic keys
    
    Supports RSA and Ed25519 key pairs for DID/VC operations
    """
    
    @staticmethod
    def generate_ed25519_keypair() -> Tuple[bytes, bytes]:
        """
        Generate Ed25519 key pair
        
        Returns:
            Tuple of (private_key_bytes, public_key_bytes)
        """
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_key_bytes, public_key_bytes
    
    @staticmethod
    def generate_rsa_keypair(key_size: int = 2048) -> Tuple[bytes, bytes]:
        """
        Generate RSA key pair
        
        Args:
            key_size: Key size in bits (default 2048)
            
        Returns:
            Tuple of (private_key_bytes, public_key_bytes)
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_key_bytes, public_key_bytes
    
    @staticmethod
    def key_to_pem(key_bytes: bytes) -> str:
        """
        Convert key bytes to PEM string
        
        Args:
            key_bytes: Key bytes
            
        Returns:
            PEM string
        """
        return key_bytes.decode('utf-8')
    
    @staticmethod
    def key_to_base64(key_bytes: bytes) -> str:
        """
        Convert key bytes to base64 string
        
        Args:
            key_bytes: Key bytes
            
        Returns:
            Base64 string
        """
        return base64.b64encode(key_bytes).decode('utf-8')
    
    @staticmethod
    def base64_to_key(base64_str: str) -> bytes:
        """
        Convert base64 string to key bytes
        
        Args:
            base64_str: Base64 string
            
        Returns:
            Key bytes
        """
        return base64.b64decode(base64_str)
    
    @staticmethod
    def load_private_key(pem_string: str) -> ed25519.Ed25519PrivateKey:
        """
        Load private key from PEM string
        
        Args:
            pem_string: PEM string
            
        Returns:
            Private key object
        """
        return serialization.load_pem_private_key(
            pem_string.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
    
    @staticmethod
    def load_public_key(pem_string: str) -> ed25519.Ed25519PublicKey:
        """
        Load public key from PEM string
        
        Args:
            pem_string: PEM string
            
        Returns:
            Public key object
        """
        return serialization.load_pem_public_key(
            pem_string.encode('utf-8'),
            backend=default_backend()
        )
    
    @staticmethod
    def sign_message(message: bytes, private_key_pem: str) -> bytes:
        """
        Sign a message with a private key
        
        Args:
            message: Message bytes to sign
            private_key_pem: Private key PEM string
            
        Returns:
            Signature bytes
        """
        private_key = KeyManager.load_private_key(private_key_pem)
        if isinstance(private_key, ed25519.Ed25519PrivateKey):
            return private_key.sign(message)
        else:
            raise ValueError("Unsupported key type for signing")
    
    @staticmethod
    def verify_signature(message: bytes, signature: bytes, public_key_pem: str) -> bool:
        """
        Verify a message signature
        
        Args:
            message: Original message bytes
            signature: Signature bytes
            public_key_pem: Public key PEM string
            
        Returns:
            True if signature is valid
        """
        try:
            public_key = KeyManager.load_public_key(public_key_pem)
            if isinstance(public_key, ed25519.Ed25519PublicKey):
                public_key.verify(signature, message)
                return True
            else:
                return False
        except Exception as e:
            logger.debug(f"Signature verification failed: {e}")
            return False

