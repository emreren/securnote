"""
Simple note encryption module with PKI support.
"""

import base64
import json
import os
import secrets
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class NoteCrypto:
    """Handles note encryption and decryption using AES-GCM."""

    def __init__(self, key: bytes) -> None:
        """Initialize with user's note key.

        Args:
            key: 256-bit encryption key for AES-GCM
        """
        self.key = key
        self.aes = AESGCM(key)

    def encrypt(self, text: str) -> Tuple[str, str]:
        """Encrypt text using AES-GCM.

        Args:
            text: Plain text to encrypt

        Returns:
            Tuple of (encrypted_data, nonce) as base64 strings
        """
        nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
        encrypted = self.aes.encrypt(nonce, text.encode(), None)

        # Return as base64 for JSON storage
        encrypted_b64 = base64.b64encode(encrypted).decode()
        nonce_b64 = base64.b64encode(nonce).decode()

        return encrypted_b64, nonce_b64

    def decrypt(self, encrypted_b64: str, nonce_b64: str) -> str:
        """Decrypt base64 encoded data.

        Args:
            encrypted_b64: Base64 encoded encrypted data
            nonce_b64: Base64 encoded nonce

        Returns:
            Original plain text
        """
        encrypted = base64.b64decode(encrypted_b64)
        nonce = base64.b64decode(nonce_b64)

        decrypted = self.aes.decrypt(nonce, encrypted, None)
        return decrypted.decode()


class CertificateAuthority:
    def __init__(self, ca_private_key=None, data_dir="data"):
        """Initialize CA with private key. Generate new one if not provided."""
        if ca_private_key is None:
            self.ca_private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
        else:
            self.ca_private_key = ca_private_key

        self.ca_public_key = self.ca_private_key.public_key()

        # Initialize CRL system
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.crl_file = os.path.join(data_dir, "revoked_certificates.json")
        self._init_crl()

    def export_ca_public_key(self):
        """Export CA public key as PEM format."""
        return self.ca_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def export_ca_private_key(self, password=None):
        """Export CA private key as PEM format."""
        encryption = (
            serialization.BestAvailableEncryption(password.encode())
            if password
            else serialization.NoEncryption()
        )
        return self.ca_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption,
        )

    def issue_certificate(self, username, user_public_key):
        """Issue certificate for user. Returns signed certificate."""
        # Generate unique certificate ID
        cert_id = secrets.token_hex(16)

        # Certificate message: username + public key
        cert_data = f"{username}:{user_public_key.decode()}".encode()

        # Sign the certificate with CA private key
        signature = self.ca_private_key.sign(
            cert_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )

        return {
            "cert_id": cert_id,
            "username": username,
            "public_key": user_public_key.decode(),
            "signature": base64.b64encode(signature).decode(),
            "issued_by": "SecurNote CA",
            "issued_at": datetime.now().isoformat(),
        }

    def verify_certificate(self, certificate):
        """Verify certificate signature and revocation status."""
        try:
            # First check if certificate is revoked
            if self.is_certificate_revoked(certificate.get("cert_id")):
                return False

            # Then verify signature
            cert_data = (
                f"{certificate['username']}:{certificate['public_key']}".encode()
            )
            signature = base64.b64decode(certificate["signature"])

            # Verify signature with CA public key
            self.ca_public_key.verify(
                signature,
                cert_data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except InvalidSignature:
            return False

    def _init_crl(self):
        """Initialize Certificate Revocation List file."""
        if not os.path.exists(self.crl_file):
            with open(self.crl_file, "w") as f:
                json.dump({"revoked_certificates": []}, f, indent=2)

    def revoke_certificate(self, cert_id, reason="unspecified"):
        """Revoke a certificate by adding it to CRL."""
        if not cert_id:
            return False

        # Load current CRL
        with open(self.crl_file, "r") as f:
            crl_data = json.load(f)

        # Check if already revoked
        for revoked_cert in crl_data["revoked_certificates"]:
            if revoked_cert["cert_id"] == cert_id:
                return False  # Already revoked

        # Add to revoked list
        revocation_entry = {
            "cert_id": cert_id,
            "revoked_at": datetime.now().isoformat(),
            "reason": reason,
        }

        crl_data["revoked_certificates"].append(revocation_entry)

        # Save updated CRL
        with open(self.crl_file, "w") as f:
            json.dump(crl_data, f, indent=2)

        return True

    def is_certificate_revoked(self, cert_id):
        """Check if certificate is revoked."""
        if not cert_id or not os.path.exists(self.crl_file):
            return False

        with open(self.crl_file, "r") as f:
            crl_data = json.load(f)

        # Check if cert_id is in revoked list
        for revoked_cert in crl_data["revoked_certificates"]:
            if revoked_cert["cert_id"] == cert_id:
                return True

        return False

    def get_revoked_certificates(self):
        """Get list of all revoked certificates."""
        if not os.path.exists(self.crl_file):
            return []

        with open(self.crl_file, "r") as f:
            crl_data = json.load(f)

        return crl_data["revoked_certificates"]

    @classmethod
    def from_private_key_pem(cls, pem_data, password=None):
        """Load CA from private key PEM data."""
        ca_private_key = serialization.load_pem_private_key(
            pem_data,
            password=password.encode() if password else None,
        )
        return cls(ca_private_key=ca_private_key)


class SecureUser:
    def __init__(self, username, private_key=None):
        """Initialize user with username and optional private key."""
        self.username = username
        if private_key is None:
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
        else:
            self.private_key = private_key

        self.public_key = self.private_key.public_key()
        self.certificate = None

    def export_public_key(self):
        """Export public key as PEM format."""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def request_certificate(self, ca):
        """Request certificate from CA."""
        user_public_key_pem = self.export_public_key()
        self.certificate = ca.issue_certificate(self.username, user_public_key_pem)
        return self.certificate

    def encrypt_message(self, message, recipient_certificate, ca):
        """Encrypt message for recipient using their certificate."""
        # First verify sender's (our) certificate is not revoked
        if self.certificate and not ca.verify_certificate(self.certificate):
            raise ValueError("Sender certificate is revoked or invalid")

        # Then verify recipient's certificate
        if not ca.verify_certificate(recipient_certificate):
            raise ValueError("Invalid or revoked recipient certificate")

        # Load recipient's public key
        recipient_public_key = serialization.load_pem_public_key(
            recipient_certificate["public_key"].encode()
        )

        # Encrypt message
        ciphertext = recipient_public_key.encrypt(
            message.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

        # Sign the message
        signature = self.private_key.sign(
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )

        return {
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "signature": base64.b64encode(signature).decode(),
            "sender_certificate": self.certificate,
        }

    def decrypt_message(self, encrypted_message, ca):
        """Decrypt and verify message."""
        # Verify sender's certificate
        sender_cert = encrypted_message["sender_certificate"]
        if not ca.verify_certificate(sender_cert):
            raise ValueError("Invalid sender certificate")

        # Decrypt message
        ciphertext = base64.b64decode(encrypted_message["ciphertext"])
        plaintext = self.private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

        # Verify signature
        sender_public_key = serialization.load_pem_public_key(
            sender_cert["public_key"].encode()
        )
        signature = base64.b64decode(encrypted_message["signature"])

        try:
            sender_public_key.verify(
                signature,
                plaintext,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return plaintext.decode(), True  # (message, signature_valid)
        except InvalidSignature:
            return plaintext.decode(), False  # Message decrypted but signature invalid
