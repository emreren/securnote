"""
Service layer for business logic.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .crypto import CertificateAuthority, NoteCrypto, SecureUser
from .exceptions import (
    CertificateRevokedError,
    ChallengeAlreadyUsedError,
    ChallengeExpiredError,
    InvalidCredentialsError,
    InvalidProofError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from .models import (
    AuthData,
    Certificate,
    Challenge,
    Note,
    RevocationEntry,
    SecurityConfig,
    User,
    ZKData,
)
from .repository import (
    ChallengeRepository,
    NoteRepository,
    RevocationRepository,
    UserRepository,
)


class AuthService:
    """Authentication business logic."""

    def __init__(self, user_repo: UserRepository, config: SecurityConfig):
        self.user_repo = user_repo
        self.config = config

    def create_user(self, username: str, password: str) -> User:
        """Create new user with all authentication data."""
        if self.user_repo.user_exists(username):
            raise UserAlreadyExistsError(f"User {username} already exists")

        # Generate traditional auth data
        auth_salt = secrets.token_bytes(self.config.auth_salt_size)
        note_salt = secrets.token_bytes(self.config.note_salt_size)
        auth_hash = hashlib.sha256(auth_salt + password.encode()).hexdigest()

        auth_data = AuthData(
            auth_salt=auth_salt, note_salt=note_salt, password_hash=auth_hash
        )

        # Generate ZK auth data
        zk_salt = secrets.token_bytes(self.config.zk_salt_size)
        zk_hash = hashlib.sha256(zk_salt + password.encode()).hexdigest()

        zk_data = ZKData(salt=zk_salt, password_hash=zk_hash)

        # Create placeholder certificate (will be filled by CertificateService)
        certificate = Certificate(
            cert_id="",
            username=username,
            public_key="",
            signature="",
            issued_by="",
            issued_at="",
        )

        user = User(
            username=username,
            auth_data=auth_data,
            zk_data=zk_data,
            certificate=certificate,
        )

        return user

    def authenticate_user(self, username: str, password: str) -> Optional[bytes]:
        """Traditional authentication. Returns note key if successful."""
        user = self.user_repo.get_user(username)
        if not user:
            raise UserNotFoundError(f"User {username} not found")

        # Verify password
        password_hash = hashlib.sha256(
            user.auth_data.auth_salt + password.encode()
        ).hexdigest()
        if password_hash != user.auth_data.password_hash:
            raise InvalidCredentialsError("Invalid password")

        # Generate note key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=user.auth_data.note_salt,
            iterations=self.config.pbkdf2_iterations,
        )
        note_key = kdf.derive(password.encode())
        return note_key

    def get_user(self, username: str) -> User:
        """Get user by username."""
        user = self.user_repo.get_user(username)
        if not user:
            raise UserNotFoundError(f"User {username} not found")
        return user


class ZKProofService:
    """Zero-knowledge proof business logic."""

    def __init__(
        self,
        user_repo: UserRepository,
        challenge_repo: ChallengeRepository,
        config: SecurityConfig,
    ):
        self.user_repo = user_repo
        self.challenge_repo = challenge_repo
        self.config = config

    def create_challenge(self, username: str) -> str:
        """Create ZK challenge for user."""
        user = self.user_repo.get_user(username)
        if not user:
            raise UserNotFoundError(f"User {username} not found")

        challenge_id = secrets.token_hex(16)
        challenge_data = secrets.token_hex(16)

        challenge = Challenge(
            challenge_id=challenge_id,
            username=username,
            challenge_data=challenge_data,
            created_at=datetime.now(),
            expires_at=datetime.now()
            + timedelta(seconds=self.config.challenge_expiry_seconds),
        )

        self.challenge_repo.save_challenge(challenge)
        return challenge_data

    def create_proof(self, username: str, password: str, challenge_data: str) -> str:
        """Create ZK proof for given challenge."""
        user = self.user_repo.get_user(username)
        if not user:
            raise UserNotFoundError(f"User {username} not found")

        # Recreate password hash
        password_hash = hashlib.sha256(
            user.zk_data.salt + password.encode()
        ).hexdigest()

        # Verify password is correct
        if password_hash != user.zk_data.password_hash:
            raise InvalidCredentialsError("Invalid password for ZK proof")

        # Generate proof: hash(password_hash + challenge)
        proof = hashlib.sha256((password_hash + challenge_data).encode()).hexdigest()
        return proof

    def verify_proof(self, username: str, challenge_data: str, proof: str) -> bool:
        """Verify ZK proof."""
        import os

        # Find challenge by data (simplified - in production would use better lookup)
        # For now, iterate through recent challenges
        for filename in os.listdir(self.challenge_repo.data_dir):
            if filename.startswith("challenge_") and filename.endswith(".json"):
                challenge_id = filename[10:-5]  # Extract ID from filename
                challenge = self.challenge_repo.get_challenge(challenge_id)

                if (
                    challenge
                    and challenge.username == username
                    and challenge.challenge_data == challenge_data
                ):
                    # Check if already used
                    if challenge.used:
                        raise ChallengeAlreadyUsedError("Challenge already used")

                    # Check if expired
                    if challenge.expires_at and datetime.now() > challenge.expires_at:
                        raise ChallengeExpiredError("Challenge expired")

                    # Get user and verify proof
                    user = self.user_repo.get_user(username)
                    if not user:
                        return False

                    expected_proof = hashlib.sha256(
                        (user.zk_data.password_hash + challenge_data).encode()
                    ).hexdigest()

                    if proof == expected_proof:
                        # Mark challenge as used
                        self.challenge_repo.mark_challenge_used(challenge_id)
                        return True

        return False

    def authenticate_zk(self, username: str, password: str) -> bool:
        """Complete ZK authentication flow."""
        challenge_data = self.create_challenge(username)
        proof = self.create_proof(username, password, challenge_data)
        return self.verify_proof(username, challenge_data, proof)


class CertificateService:
    """PKI certificate business logic."""

    def __init__(
        self,
        user_repo: UserRepository,
        revocation_repo: RevocationRepository,
        config: SecurityConfig,
    ):
        self.user_repo = user_repo
        self.revocation_repo = revocation_repo
        self.config = config
        self.ca = CertificateAuthority(data_dir=user_repo.data_dir)

    def issue_certificate_for_user(self, user: User) -> User:
        """Issue PKI certificate for user and update user entity."""
        # Create SecureUser instance
        secure_user = SecureUser(user.username)

        # Request certificate from CA
        cert_data = secure_user.request_certificate(self.ca)

        # Update user's certificate
        user.certificate = Certificate(
            cert_id=cert_data["cert_id"],
            username=cert_data["username"],
            public_key=cert_data["public_key"],
            signature=cert_data["signature"],
            issued_by=cert_data["issued_by"],
            issued_at=cert_data["issued_at"],
        )

        # Save updated user
        self.user_repo.update_user(user)
        return user

    def verify_certificate(self, username: str) -> bool:
        """Verify user's certificate is valid and not revoked."""
        user = self.user_repo.get_user(username)
        if not user or not user.certificate.cert_id:
            return False

        # Check if revoked
        if self.revocation_repo.is_revoked(user.certificate.cert_id):
            return False

        # Verify with CA
        cert_dict = {
            "cert_id": user.certificate.cert_id,
            "username": user.certificate.username,
            "public_key": user.certificate.public_key,
            "signature": user.certificate.signature,
            "issued_by": user.certificate.issued_by,
            "issued_at": user.certificate.issued_at,
        }

        return self.ca.verify_certificate(cert_dict)

    def revoke_certificate(self, username: str, reason: str = "unspecified") -> bool:
        """Revoke user's certificate."""
        user = self.user_repo.get_user(username)
        if not user or not user.certificate.cert_id:
            return False

        revocation = RevocationEntry(
            cert_id=user.certificate.cert_id, revoked_at=datetime.now(), reason=reason
        )

        self.revocation_repo.add_revocation(revocation)
        return True

    def get_revoked_certificates(self) -> List[RevocationEntry]:
        """Get all revoked certificates."""
        return self.revocation_repo.get_revoked_certificates()


class NoteService:
    """Note management business logic."""

    def __init__(
        self,
        note_repo: NoteRepository,
        auth_service: AuthService,
        cert_service: CertificateService,
    ):
        self.note_repo = note_repo
        self.auth_service = auth_service
        self.cert_service = cert_service

    def create_note(
        self, username: str, title: str, content: str, note_key: bytes
    ) -> str:
        """Create encrypted note with access validation."""
        # Validate user has valid certificate
        if not self.cert_service.verify_certificate(username):
            raise CertificateRevokedError(
                f"Certificate for {username} is revoked or invalid"
            )

        # Encrypt note
        crypto = NoteCrypto(note_key)
        title_encrypted, title_nonce = crypto.encrypt(title)
        content_encrypted, content_nonce = crypto.encrypt(content)

        # Create note entity
        note = Note(
            note_id=secrets.token_hex(16),
            username=username,
            title_encrypted=title_encrypted,
            content_encrypted=content_encrypted,
            title_nonce=title_nonce,
            content_nonce=content_nonce,
            created_at=datetime.now(),
        )

        return self.note_repo.save_note(note)

    def get_user_notes(self, username: str) -> List[Tuple[str, str, str]]:
        """Get decrypted notes for user with access validation."""
        # Validate access
        if not self.cert_service.verify_certificate(username):
            raise CertificateRevokedError(
                f"Certificate for {username} is revoked or invalid"
            )

        # Get note key
        user = self.auth_service.get_user(username)
        # Note: In real implementation, we'd need password to derive key
        # This is a simplified version

        notes = self.note_repo.get_user_notes(username)
        return [
            (note.note_id, note.title_encrypted, note.created_at.isoformat())
            for note in notes
        ]

    def get_note_by_id(
        self, username: str, note_id: str, note_key: bytes
    ) -> Optional[Tuple[str, str]]:
        """Get and decrypt specific note."""
        # Validate access
        if not self.cert_service.verify_certificate(username):
            raise CertificateRevokedError(
                f"Certificate for {username} is revoked or invalid"
            )

        note = self.note_repo.get_note_by_id(username, note_id)
        if not note:
            return None

        # Decrypt
        crypto = NoteCrypto(note_key)
        title = crypto.decrypt(note.title_encrypted, note.title_nonce)
        content = crypto.decrypt(note.content_encrypted, note.content_nonce)

        return title, content

    def delete_note(self, username: str, note_id: str) -> bool:
        """Delete note with access validation."""
        # Validate access
        if not self.cert_service.verify_certificate(username):
            raise CertificateRevokedError(
                f"Certificate for {username} is revoked or invalid"
            )

        return self.note_repo.delete_note(username, note_id)
