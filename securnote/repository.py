"""
Repository layer for data persistence.
"""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from .exceptions import FileCorruptedError, StorageError, UserNotFoundError
from .models import (
    AuthData,
    Certificate,
    Challenge,
    Note,
    RevocationEntry,
    User,
    ZKData,
)


class BaseRepository(ABC):
    """Base repository interface."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def _safe_file_read(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Safely read JSON file with error handling."""
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise FileCorruptedError(f"Failed to read {file_path}: {e}")

    def _safe_file_write(self, file_path: str, data: Dict[str, Any]) -> None:
        """Safely write JSON file with error handling."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Atomic write: write to temp file first, then rename
            temp_path = file_path + ".tmp"
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            os.rename(temp_path, file_path)
        except (IOError, OSError) as e:
            raise StorageError(f"Failed to write {file_path}: {e}")


class UserRepository(BaseRepository):
    """Repository for user data management."""

    def save_user(self, user: User) -> bool:
        """Save complete user data to unified storage."""
        user_file = os.path.join(self.data_dir, f"{user.username}.user")

        if os.path.exists(user_file):
            return False  # User already exists

        user_data = {
            "username": user.username,
            "auth_data": {
                "auth_salt": user.auth_data.auth_salt.hex(),
                "note_salt": user.auth_data.note_salt.hex(),
                "password_hash": user.auth_data.password_hash,
            },
            "zk_data": {
                "salt": user.zk_data.salt.hex(),
                "password_hash": user.zk_data.password_hash,
            },
            "certificate": {
                "cert_id": user.certificate.cert_id,
                "username": user.certificate.username,
                "public_key": user.certificate.public_key,
                "signature": user.certificate.signature,
                "issued_by": user.certificate.issued_by,
                "issued_at": user.certificate.issued_at,
            },
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "is_active": user.is_active,
        }

        self._safe_file_write(user_file, user_data)
        return True

    def get_user(self, username: str) -> Optional[User]:
        """Retrieve user by username."""
        user_file = os.path.join(self.data_dir, f"{username}.user")
        data = self._safe_file_read(user_file)

        if not data:
            return None

        try:
            auth_data = AuthData(
                auth_salt=bytes.fromhex(data["auth_data"]["auth_salt"]),
                note_salt=bytes.fromhex(data["auth_data"]["note_salt"]),
                password_hash=data["auth_data"]["password_hash"],
            )

            zk_data = ZKData(
                salt=bytes.fromhex(data["zk_data"]["salt"]),
                password_hash=data["zk_data"]["password_hash"],
            )

            certificate = Certificate(
                cert_id=data["certificate"]["cert_id"],
                username=data["certificate"]["username"],
                public_key=data["certificate"]["public_key"],
                signature=data["certificate"]["signature"],
                issued_by=data["certificate"]["issued_by"],
                issued_at=data["certificate"]["issued_at"],
            )

            return User(
                username=data["username"],
                auth_data=auth_data,
                zk_data=zk_data,
                certificate=certificate,
                created_at=(
                    datetime.fromisoformat(data["created_at"])
                    if data.get("created_at")
                    else None
                ),
                is_active=data.get("is_active", True),
            )
        except (KeyError, ValueError) as e:
            raise FileCorruptedError(f"Invalid user data format: {e}")

    def user_exists(self, username: str) -> bool:
        """Check if user exists."""
        user_file = os.path.join(self.data_dir, f"{username}.user")
        return os.path.exists(user_file)

    def update_user(self, user: User) -> None:
        """Update existing user data."""
        if not self.user_exists(user.username):
            raise UserNotFoundError(f"User {user.username} not found")

        user_file = os.path.join(self.data_dir, f"{user.username}.user")
        # Remove and recreate - simpler than merge
        os.remove(user_file)
        self.save_user(user)


class ChallengeRepository(BaseRepository):
    """Repository for ZK challenge management."""

    def save_challenge(self, challenge: Challenge) -> None:
        """Save challenge data."""
        challenge_file = os.path.join(
            self.data_dir, f"challenge_{challenge.challenge_id}.json"
        )

        challenge_data = {
            "challenge_id": challenge.challenge_id,
            "username": challenge.username,
            "challenge_data": challenge.challenge_data,
            "created_at": challenge.created_at.isoformat(),
            "used": challenge.used,
            "expires_at": (
                challenge.expires_at.isoformat() if challenge.expires_at else None
            ),
        }

        self._safe_file_write(challenge_file, challenge_data)

    def get_challenge(self, challenge_id: str) -> Optional[Challenge]:
        """Retrieve challenge by ID."""
        challenge_file = os.path.join(self.data_dir, f"challenge_{challenge_id}.json")
        data = self._safe_file_read(challenge_file)

        if not data:
            return None

        return Challenge(
            challenge_id=data["challenge_id"],
            username=data["username"],
            challenge_data=data["challenge_data"],
            created_at=datetime.fromisoformat(data["created_at"]),
            used=data.get("used", False),
            expires_at=(
                datetime.fromisoformat(data["expires_at"])
                if data.get("expires_at")
                else None
            ),
        )

    def mark_challenge_used(self, challenge_id: str) -> None:
        """Mark challenge as used."""
        challenge = self.get_challenge(challenge_id)
        if challenge:
            challenge.used = True
            self.save_challenge(challenge)

    def cleanup_expired_challenges(self, max_age_seconds: int = 300) -> int:
        """Clean up expired challenges. Returns count of cleaned challenges."""
        cleaned_count = 0
        current_time = datetime.now()

        for filename in os.listdir(self.data_dir):
            if filename.startswith("challenge_") and filename.endswith(".json"):
                file_path = os.path.join(self.data_dir, filename)
                try:
                    file_age = current_time.timestamp() - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        cleaned_count += 1
                except OSError:
                    continue

        return cleaned_count


class RevocationRepository(BaseRepository):
    """Repository for certificate revocation management."""

    def __init__(self, data_dir: str = "data"):
        super().__init__(data_dir)
        self.crl_file = os.path.join(data_dir, "certificate_revocation_list.json")

    def add_revocation(self, revocation: RevocationEntry) -> None:
        """Add certificate to revocation list."""
        crl_data = self._load_crl()

        # Check if already revoked
        for entry in crl_data["revoked_certificates"]:
            if entry["cert_id"] == revocation.cert_id:
                return  # Already revoked

        crl_data["revoked_certificates"].append(
            {
                "cert_id": revocation.cert_id,
                "revoked_at": revocation.revoked_at.isoformat(),
                "reason": revocation.reason,
            }
        )

        self._save_crl(crl_data)

    def is_revoked(self, cert_id: str) -> bool:
        """Check if certificate is revoked."""
        crl_data = self._load_crl()
        return any(
            entry["cert_id"] == cert_id for entry in crl_data["revoked_certificates"]
        )

    def get_revoked_certificates(self) -> List[RevocationEntry]:
        """Get all revoked certificates."""
        crl_data = self._load_crl()

        return [
            RevocationEntry(
                cert_id=entry["cert_id"],
                revoked_at=datetime.fromisoformat(entry["revoked_at"]),
                reason=entry["reason"],
            )
            for entry in crl_data["revoked_certificates"]
        ]

    def _load_crl(self) -> Dict[str, Any]:
        """Load certificate revocation list."""
        data = self._safe_file_read(self.crl_file)
        return data or {"revoked_certificates": []}

    def _save_crl(self, crl_data: Dict[str, Any]) -> None:
        """Save certificate revocation list."""
        self._safe_file_write(self.crl_file, crl_data)


class NoteRepository(BaseRepository):
    """Repository for note storage."""

    def __init__(self, data_dir: str = "data"):
        super().__init__(data_dir)
        self.notes_dir = os.path.join(data_dir, "notes")
        os.makedirs(self.notes_dir, exist_ok=True)

    def save_note(self, note: Note) -> str:
        """Save note and return note ID."""
        user_file = os.path.join(self.notes_dir, f"{note.username}.json")
        notes_data = self._safe_file_read(user_file) or {"notes": []}

        note_data = {
            "id": note.note_id,
            "title_encrypted": note.title_encrypted,
            "content_encrypted": note.content_encrypted,
            "title_nonce": note.title_nonce,
            "content_nonce": note.content_nonce,
            "timestamp": note.created_at.isoformat(),
        }

        notes_data["notes"].append(note_data)
        self._safe_file_write(user_file, notes_data)
        return note.note_id

    def get_user_notes(self, username: str) -> List[Note]:
        """Get all notes for a user."""
        user_file = os.path.join(self.notes_dir, f"{username}.json")
        data = self._safe_file_read(user_file)

        if not data:
            return []

        notes = []
        for note_data in data.get("notes", []):
            notes.append(
                Note(
                    note_id=note_data["id"],
                    username=username,
                    title_encrypted=note_data["title_encrypted"],
                    content_encrypted=note_data["content_encrypted"],
                    title_nonce=note_data["title_nonce"],
                    content_nonce=note_data["content_nonce"],
                    created_at=datetime.fromisoformat(note_data["timestamp"]),
                )
            )

        return notes

    def get_note_by_id(self, username: str, note_id: str) -> Optional[Note]:
        """Get specific note by ID."""
        notes = self.get_user_notes(username)
        for note in notes:
            if note.note_id == note_id:
                return note
        return None

    def delete_note(self, username: str, note_id: str) -> bool:
        """Delete note by ID."""
        user_file = os.path.join(self.notes_dir, f"{username}.json")
        data = self._safe_file_read(user_file)

        if not data:
            return False

        notes = data.get("notes", [])
        original_count = len(notes)
        data["notes"] = [note for note in notes if note["id"] != note_id]

        if len(data["notes"]) < original_count:
            self._safe_file_write(user_file, data)
            return True

        return False
