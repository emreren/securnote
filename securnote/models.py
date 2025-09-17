"""
Data models and domain entities for SecurNote.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class AuthData:
    """Traditional authentication data."""

    auth_salt: bytes
    note_salt: bytes
    password_hash: str


@dataclass
class ZKData:
    """Zero-knowledge proof authentication data."""

    salt: bytes
    password_hash: str


@dataclass
class Certificate:
    """PKI certificate data."""

    cert_id: str
    username: str
    public_key: str
    signature: str
    issued_by: str
    issued_at: str


@dataclass
class User:
    """Complete user entity."""

    username: str
    auth_data: AuthData
    zk_data: ZKData
    certificate: Certificate
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    is_active: bool = True


@dataclass
class Challenge:
    """ZK-proof challenge entity."""

    challenge_id: str
    username: str
    challenge_data: str
    created_at: datetime
    used: bool = False
    expires_at: Optional[datetime] = None


@dataclass
class RevocationEntry:
    """Certificate revocation entry."""

    cert_id: str
    revoked_at: datetime
    reason: str


@dataclass
class Note:
    """Encrypted note entity."""

    note_id: str
    username: str
    title_encrypted: str
    content_encrypted: str
    title_nonce: str
    content_nonce: str
    created_at: datetime
    updated_at: Optional[datetime] = None


@dataclass
class SecurityConfig:
    """Security configuration."""

    pbkdf2_iterations: int = 100000
    rsa_key_size: int = 2048
    challenge_expiry_seconds: int = 300
    auth_salt_size: int = 32
    note_salt_size: int = 32
    zk_salt_size: int = 16
    aes_nonce_size: int = 12
