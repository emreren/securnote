"""
Application facade layer - maintains backward compatibility with existing API.
"""

from typing import List, Optional, Tuple

from .logging_config import get_logger
from .exceptions import (
    AccessDeniedError,
    CertificateRevokedError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from .models import SecurityConfig
from .repository import (
    ChallengeRepository,
    NoteRepository,
    RevocationRepository,
    UserRepository,
)
from .services import AuthService, CertificateService, NoteService, ZKProofService


class SecurNoteApplication:
    """
    Application facade that maintains backward compatibility with existing UserAuth API.
    Clean architecture implementation with proper separation of concerns.
    """

    def __init__(self, data_dir: str = "data"):
        """Initialize application with all dependencies."""
        # Logger
        self.logger = get_logger(__name__)

        # Configuration
        self.config = SecurityConfig()

        # Repositories
        self.user_repo = UserRepository(data_dir)
        self.challenge_repo = ChallengeRepository(data_dir)
        self.revocation_repo = RevocationRepository(data_dir)
        self.note_repo = NoteRepository(data_dir)

        # Services
        self.auth_service = AuthService(self.user_repo, self.config)
        self.zk_service = ZKProofService(
            self.user_repo, self.challenge_repo, self.config
        )
        self.cert_service = CertificateService(
            self.user_repo, self.revocation_repo, self.config
        )
        self.note_service = NoteService(
            self.note_repo, self.auth_service, self.cert_service
        )

    # === Backward Compatible API ===

    def create_user(self, username: str, password: str) -> bool:
        """Create new user with all authentication systems. (Backward compatible)"""
        try:
            user = self.auth_service.create_user(username, password)

            # Save user first (without certificate)
            success = self.user_repo.save_user(user)
            if not success:
                self.logger.warning(f"Failed to save user {username} to repository")
                return False

            # Then issue certificate and update user
            user_with_cert = self.cert_service.issue_certificate_for_user(user)

            return True

        except UserAlreadyExistsError as e:
            self.logger.warning(f"User {username} already exists: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error creating user {username}: {e}")
            return False

    def login(self, username: str, password: str) -> Optional[bytes]:
        """Traditional login. (Backward compatible)"""
        try:
            return self.auth_service.authenticate_user(username, password)
        except (UserNotFoundError, InvalidCredentialsError):
            return None

    def zk_login(self, username: str, password: str) -> Optional[bytes]:
        """Zero-knowledge login. (Backward compatible)"""
        try:
            # ZK authentication
            if not self.zk_service.authenticate_zk(username, password):
                return None

            # If ZK succeeds, return note key from traditional system
            return self.auth_service.authenticate_user(username, password)
        except (UserNotFoundError, InvalidCredentialsError):
            return None

    def user_exists(self, username: str) -> bool:
        """Check if user exists. (Backward compatible)"""
        return self.user_repo.user_exists(username)

    def get_user_certificate(self, username: str) -> Optional[dict]:
        """Get user certificate. (Backward compatible)"""
        try:
            user = self.auth_service.get_user(username)
            cert = user.certificate

            if not cert.cert_id:  # Empty certificate
                return None

            return {
                "cert_id": cert.cert_id,
                "username": cert.username,
                "public_key": cert.public_key,
                "signature": cert.signature,
                "issued_by": cert.issued_by,
                "issued_at": cert.issued_at,
            }
        except UserNotFoundError:
            return None

    def validate_user_access(self, username: str) -> bool:
        """Validate user has valid certificate. (Backward compatible)"""
        try:
            return self.cert_service.verify_certificate(username)
        except Exception:
            return False

    def revoke_user_certificate(
        self, username: str, reason: str = "unspecified"
    ) -> bool:
        """Revoke user certificate. (Backward compatible)"""
        return self.cert_service.revoke_certificate(username, reason)

    # === Enhanced API ===

    def get_user_info(self, username: str) -> dict:
        """Get comprehensive user information."""
        try:
            user = self.auth_service.get_user(username)
            cert_valid = self.cert_service.verify_certificate(username)

            return {
                "username": user.username,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "is_active": user.is_active,
                "certificate_valid": cert_valid,
                "certificate_id": (
                    user.certificate.cert_id if user.certificate.cert_id else None
                ),
            }
        except UserNotFoundError:
            return {}

    def authenticate_with_validation(
        self, username: str, password: str
    ) -> Tuple[Optional[bytes], bool]:
        """
        Enhanced authentication with certificate validation.
        Returns: (note_key, access_granted)
        """
        try:
            # Traditional authentication
            note_key = self.auth_service.authenticate_user(username, password)

            # Certificate validation
            access_granted = self.cert_service.verify_certificate(username)

            return note_key, access_granted
        except (UserNotFoundError, InvalidCredentialsError):
            return None, False

    def create_note_secure(
        self, username: str, title: str, content: str, note_key: bytes
    ) -> str:
        """Create note with comprehensive security validation."""
        return self.note_service.create_note(username, title, content, note_key)

    def get_user_notes_secure(self, username: str) -> List[Tuple[str, str, str]]:
        """Get user notes with security validation."""
        return self.note_service.get_user_notes(username)

    def get_note_by_id_secure(
        self, username: str, note_id: str, note_key: bytes
    ) -> Optional[Tuple[str, str]]:
        """Get note by ID with security validation."""
        return self.note_service.get_note_by_id(username, note_id, note_key)

    def delete_note_secure(self, username: str, note_id: str) -> bool:
        """Delete note with security validation."""
        return self.note_service.delete_note(username, note_id)

    def get_revoked_certificates(self) -> List[dict]:
        """Get all revoked certificates."""
        revoked_list = self.cert_service.get_revoked_certificates()
        return [
            {
                "cert_id": rev.cert_id,
                "revoked_at": rev.revoked_at.isoformat(),
                "reason": rev.reason,
            }
            for rev in revoked_list
        ]

    def cleanup_expired_challenges(self) -> int:
        """Clean up expired challenges."""
        return self.challenge_repo.cleanup_expired_challenges(
            self.config.challenge_expiry_seconds
        )

    # === Properties ===

    @property
    def ca(self):
        """Access to Certificate Authority (for backward compatibility)."""
        return self.cert_service.ca


# Global application instance for backward compatibility
_app_instance = None


def get_application(data_dir: str = "data") -> SecurNoteApplication:
    """Get singleton application instance."""
    global _app_instance
    if _app_instance is None:
        _app_instance = SecurNoteApplication(data_dir)
    return _app_instance


# Backward compatible UserAuth class
class UserAuth:
    """
    Legacy UserAuth interface for backward compatibility.
    Delegates to clean architecture implementation.
    """

    def __init__(self, data_dir: str = "data"):
        self.app = get_application(data_dir)

    def create_user(self, username: str, password: str) -> bool:
        return self.app.create_user(username, password)

    def login(self, username: str, password: str) -> Optional[bytes]:
        return self.app.login(username, password)

    def zk_login(self, username: str, password: str) -> Optional[bytes]:
        return self.app.zk_login(username, password)

    def user_exists(self, username: str) -> bool:
        return self.app.user_exists(username)

    def get_user_certificate(self, username: str) -> Optional[dict]:
        return self.app.get_user_certificate(username)

    def validate_user_access(self, username: str) -> bool:
        return self.app.validate_user_access(username)

    def revoke_user_certificate(
        self, username: str, reason: str = "unspecified"
    ) -> bool:
        return self.app.revoke_user_certificate(username, reason)

    # Expose CA for backward compatibility
    @property
    def ca(self):
        return self.app.ca
