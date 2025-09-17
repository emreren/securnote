"""
Custom exceptions for SecurNote application.
"""


class SecurNoteError(Exception):
    """Base exception for SecurNote application."""

    pass


class AuthenticationError(SecurNoteError):
    """Authentication related errors."""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password."""

    pass


class UserAlreadyExistsError(AuthenticationError):
    """User already exists in the system."""

    pass


class UserNotFoundError(AuthenticationError):
    """User does not exist in the system."""

    pass


class CertificateError(SecurNoteError):
    """Certificate related errors."""

    pass


class CertificateRevokedError(CertificateError):
    """Certificate has been revoked."""

    pass


class InvalidCertificateError(CertificateError):
    """Certificate is invalid or corrupted."""

    pass


class CertificateNotFoundError(CertificateError):
    """Certificate not found."""

    pass


class ZKProofError(SecurNoteError):
    """Zero-knowledge proof related errors."""

    pass


class InvalidProofError(ZKProofError):
    """ZK proof validation failed."""

    pass


class ChallengeExpiredError(ZKProofError):
    """Challenge has expired."""

    pass


class ChallengeAlreadyUsedError(ZKProofError):
    """Challenge has already been used."""

    pass


class StorageError(SecurNoteError):
    """Data storage related errors."""

    pass


class FileCorruptedError(StorageError):
    """Data file is corrupted or unreadable."""

    pass


class AccessDeniedError(SecurNoteError):
    """Access denied due to security policy."""

    pass
