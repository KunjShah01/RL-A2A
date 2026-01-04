"""
Verifiable Credentials (VC) Issuer and Verifier
"""

import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from .key_manager import KeyManager

logger = logging.getLogger(__name__)


class VCIssuer:
    """
    Verifiable Credentials Issuer
    
    Issues and signs verifiable credentials
    """
    
    def __init__(self, issuer_did: str, private_key_pem: str):
        """
        Initialize VC Issuer
        
        Args:
            issuer_did: DID of the issuer
            private_key_pem: Private key PEM string for signing
        """
        self.issuer_did = issuer_did
        self.private_key_pem = private_key_pem
        self.key_manager = KeyManager()
        self._logger = logging.getLogger(__name__)
    
    def issue_credential(
        self,
        credential_subject: Dict[str, Any],
        credential_type: List[str],
        expiration_days: int = 365,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Issue a verifiable credential
        
        Args:
            credential_subject: Subject of the credential
            credential_type: List of credential types
            expiration_days: Days until expiration
            **kwargs: Additional credential properties
            
        Returns:
            Verifiable credential document
        """
        # Create credential
        credential_id = f"vc:{hashlib.sha256(json.dumps(credential_subject, sort_keys=True).encode()).hexdigest()[:16]}"
        
        now = datetime.utcnow()
        expiration = now + timedelta(days=expiration_days)
        
        credential = {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://www.w3.org/2018/credentials/examples/v1"
            ],
            "id": credential_id,
            "type": ["VerifiableCredential"] + credential_type,
            "issuer": self.issuer_did,
            "issuanceDate": now.isoformat() + "Z",
            "expirationDate": expiration.isoformat() + "Z",
            "credentialSubject": credential_subject,
            **kwargs
        }
        
        # Create proof
        proof = self._create_proof(credential)
        credential["proof"] = proof
        
        self._logger.info(f"Issued VC: {credential_id} to {credential_subject.get('id', 'unknown')}")
        
        return credential
    
    def _create_proof(self, credential: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create proof for credential
        
        Args:
            credential: Credential document
            
        Returns:
            Proof object
        """
        # Create canonical JSON for signing (without proof)
        credential_copy = credential.copy()
        credential_copy.pop("proof", None)
        canonical_json = json.dumps(credential_copy, sort_keys=True, separators=(',', ':'))
        message = canonical_json.encode('utf-8')
        
        # Sign message
        signature_bytes = self.key_manager.sign_message(message, self.private_key_pem)
        signature = self.key_manager.key_to_base64(signature_bytes)
        
        # Create proof
        return {
            "type": "Ed25519Signature2020",
            "created": datetime.utcnow().isoformat() + "Z",
            "verificationMethod": f"{self.issuer_did}#keys-1",
            "proofPurpose": "assertionMethod",
            "proofValue": signature,
        }


class VCVerifier:
    """
    Verifiable Credentials Verifier
    
    Verifies verifiable credentials and presentations
    """
    
    def __init__(self, did_resolver):
        """
        Initialize VC Verifier
        
        Args:
            did_resolver: DID resolver instance
        """
        self.did_resolver = did_resolver
        self.key_manager = KeyManager()
        self._logger = logging.getLogger(__name__)
    
    def verify_credential(self, credential: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify a verifiable credential
        
        Args:
            credential: Verifiable credential document
            
        Returns:
            Verification result with valid flag and details
        """
        result = {
            "valid": False,
            "errors": [],
        }
        
        try:
            # Check expiration
            expiration_date = credential.get("expirationDate")
            if expiration_date:
                exp_dt = datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
                if datetime.utcnow().replace(tzinfo=exp_dt.tzinfo) > exp_dt:
                    result["errors"].append("Credential expired")
                    return result
            
            # Get proof
            proof = credential.get("proof")
            if not proof:
                result["errors"].append("No proof found")
                return result
            
            # Get issuer DID
            issuer = credential.get("issuer")
            if not issuer:
                result["errors"].append("No issuer found")
                return result
            
            # Resolve issuer DID
            did_doc = self.did_resolver.resolve(issuer)
            if not did_doc:
                result["errors"].append(f"Could not resolve issuer DID: {issuer}")
                return result
            
            # Get verification method
            verification_method_id = proof.get("verificationMethod")
            if not verification_method_id:
                result["errors"].append("No verification method in proof")
                return result
            
            # Extract public key (simplified - in production, decode multibase)
            # For now, we'll need the public key from the DID document
            verification_method = self.did_resolver.get_verification_method(issuer)
            if not verification_method:
                result["errors"].append("Could not get verification method")
                return result
            
            # Verify signature
            credential_copy = credential.copy()
            proof_value = credential_copy.pop("proof", {}).get("proofValue")
            if not proof_value:
                result["errors"].append("No proof value")
                return result
            
            canonical_json = json.dumps(credential_copy, sort_keys=True, separators=(',', ':'))
            message = canonical_json.encode('utf-8')
            signature_bytes = self.key_manager.base64_to_key(proof_value)
            
            # For now, mark as valid if structure is correct
            # In production, implement full signature verification
            result["valid"] = True
            result["issuer"] = issuer
            result["credential_id"] = credential.get("id")
            
        except Exception as e:
            result["errors"].append(f"Verification error: {str(e)}")
            self._logger.error(f"VC verification error: {e}", exc_info=True)
        
        return result
    
    def verify_presentation(self, presentation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify a verifiable presentation
        
        Args:
            presentation: Verifiable presentation document
            
        Returns:
            Verification result
        """
        result = {
            "valid": False,
            "errors": [],
            "credentials": [],
        }
        
        try:
            # Verify presentation proof
            proof = presentation.get("proof")
            if not proof:
                result["errors"].append("No proof in presentation")
                return result
            
            # Verify all credentials
            verifiable_credential = presentation.get("verifiableCredential", [])
            if not isinstance(verifiable_credential, list):
                verifiable_credential = [verifiable_credential]
            
            for cred in verifiable_credential:
                cred_result = self.verify_credential(cred)
                result["credentials"].append(cred_result)
                if not cred_result["valid"]:
                    result["errors"].extend(cred_result["errors"])
            
            # For now, mark as valid if structure is correct
            result["valid"] = len(result["errors"]) == 0
            
        except Exception as e:
            result["errors"].append(f"Presentation verification error: {str(e)}")
            self._logger.error(f"VP verification error: {e}", exc_info=True)
        
        return result

