#!/usr/bin/env python3

import json
import base64
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.exceptions import InvalidSignature


class ProvSigner:
    """
    Digital signature implementation for PROV logs using Ed25519
    Provides tamper-evident integrity protection for audit records
    """

    def __init__(
        self,
        private_key_path: Optional[str] = None,
        public_key_path: Optional[str] = None,
    ):
        self.private_key_path = private_key_path
        self.public_key_path = public_key_path
        self._private_key = None
        self._public_key = None

    def generate_keypair(
        self, private_key_path: str, public_key_path: str
    ) -> Tuple[str, str]:
        """
        Generate Ed25519 keypair and save to files

        Args:
            private_key_path: Path to save private key (PEM format)
            public_key_path: Path to save public key (PEM format)

        Returns:
            Tuple of (private_key_pem, public_key_pem) as strings
        """
        # Generate Ed25519 private key
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Serialize to PEM format
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        # Save to files
        Path(private_key_path).parent.mkdir(parents=True, exist_ok=True)
        Path(public_key_path).parent.mkdir(parents=True, exist_ok=True)

        with open(private_key_path, "wb") as f:
            f.write(private_pem)

        with open(public_key_path, "wb") as f:
            f.write(public_pem)

        # Set restrictive permissions on private key
        Path(private_key_path).chmod(0o600)

        return private_pem.decode("utf-8"), public_pem.decode("utf-8")

    def _load_private_key(self) -> Ed25519PrivateKey:
        """Load private key from file"""
        if self._private_key is None:
            if not self.private_key_path:
                raise ValueError("Private key path not specified")

            with open(self.private_key_path, "rb") as f:
                private_pem = f.read()

            self._private_key = serialization.load_pem_private_key(
                private_pem, password=None
            )

        return self._private_key

    def _load_public_key(self) -> Ed25519PublicKey:
        """Load public key from file"""
        if self._public_key is None:
            if not self.public_key_path:
                raise ValueError("Public key path not specified")

            with open(self.public_key_path, "rb") as f:
                public_pem = f.read()

            self._public_key = serialization.load_pem_public_key(public_pem)

        return self._public_key

    def _canonical_json(self, data: Dict[str, Any]) -> str:
        """
        Create canonical JSON representation for consistent signing
        Uses sorted keys and no extra whitespace
        """
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    def _hash_content(self, content: str) -> bytes:
        """Create SHA-256 hash of content for signing"""
        return hashlib.sha256(content.encode("utf-8")).digest()

    def sign_prov_record(self, prov_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign a PROV record and return signed version with signature metadata

        Args:
            prov_record: W3C PROV JSON-LD record to sign

        Returns:
            Signed PROV record with signature metadata
        """
        private_key = self._load_private_key()

        # Create canonical representation
        canonical_json = self._canonical_json(prov_record)
        content_hash = self._hash_content(canonical_json)

        # Sign the hash
        signature = private_key.sign(content_hash)

        # Create signature metadata
        timestamp = datetime.now(timezone.utc).isoformat()
        signature_b64 = base64.b64encode(signature).decode("utf-8")
        content_hash_b64 = base64.b64encode(content_hash).decode("utf-8")

        # Add signature metadata to the PROV record
        signed_record = prov_record.copy()
        signed_record["vpm:signature"] = {
            "algorithm": "Ed25519",
            "hash_algorithm": "SHA-256",
            "signature": signature_b64,
            "content_hash": content_hash_b64,
            "signed_at": timestamp,
            "signer": "vpm-mini-audit-system",
        }

        return signed_record

    def verify_prov_record(self, signed_record: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verify the signature of a signed PROV record

        Args:
            signed_record: Signed PROV record with signature metadata

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            public_key = self._load_public_key()

            # Extract signature metadata
            if "vpm:signature" not in signed_record:
                return False, "No signature found in record"

            sig_meta = signed_record["vmp:signature"]
            signature_b64 = sig_meta["signature"]
            content_hash_b64 = sig_meta["content_hash"]

            # Reconstruct record without signature for verification
            record_copy = signed_record.copy()
            del record_copy["vpm:signature"]

            # Create canonical representation and hash
            canonical_json = self._canonical_json(record_copy)
            computed_hash = self._hash_content(canonical_json)

            # Verify content hash matches
            stored_hash = base64.b64decode(content_hash_b64)
            if computed_hash != stored_hash:
                return (
                    False,
                    "Content hash mismatch - record may have been tampered with",
                )

            # Verify signature
            signature = base64.b64decode(signature_b64)
            public_key.verify(signature, computed_hash)

            return True, "Signature valid - record integrity verified"

        except InvalidSignature:
            return False, "Invalid signature - record may have been tampered with"
        except Exception as e:
            return False, f"Verification failed: {str(e)}"

    def batch_sign_records(self, prov_records: list) -> list:
        """
        Sign multiple PROV records in batch

        Args:
            prov_records: List of PROV records to sign

        Returns:
            List of signed PROV records
        """
        return [self.sign_prov_record(record) for record in prov_records]

    def export_public_key_info(self) -> Dict[str, str]:
        """
        Export public key information for verification purposes

        Returns:
            Dictionary with public key metadata
        """
        public_key = self._load_public_key()

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        # Create fingerprint
        key_hash = hashlib.sha256(public_pem).hexdigest()

        return {
            "algorithm": "Ed25519",
            "public_key_pem": public_pem.decode("utf-8"),
            "fingerprint": key_hash,
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }


if __name__ == "__main__":
    # Example usage
    import tempfile
    import os

    # Create temporary keypair for demonstration
    with tempfile.TemporaryDirectory() as tmpdir:
        private_key_path = os.path.join(tmpdir, "signing_key.pem")
        public_key_path = os.path.join(tmpdir, "signing_key.pub")

        signer = ProvSigner()

        # Generate keypair
        print("Generating Ed25519 keypair...")
        private_pem, public_pem = signer.generate_keypair(
            private_key_path, public_key_path
        )

        # Initialize with keypair
        signer = ProvSigner(private_key_path, public_key_path)

        # Example PROV record
        prov_record = {
            "@context": "https://vpm-mini.local/prov/context",
            "@id": "prov:example-123",
            "entity": {"entity:pod-123": {"type": "Entity", "label": "Test Pod"}},
            "activity": {
                "activity:review-456": {"type": "Activity", "label": "Admission Review"}
            },
            "agent": {
                "agent:spiffe:gatekeeper": {"type": "Agent", "label": "Gatekeeper"}
            },
        }

        # Sign the record
        print("\nSigning PROV record...")
        signed_record = signer.sign_prov_record(prov_record)

        # Verify the signature
        print("Verifying signature...")
        is_valid, message = signer.verify_prov_record(signed_record)
        print(f"Verification result: {is_valid} - {message}")

        # Export public key info
        print("\nPublic key information:")
        key_info = signer.export_public_key_info()
        print(f"Algorithm: {key_info['algorithm']}")
        print(f"Fingerprint: {key_info['fingerprint']}")
