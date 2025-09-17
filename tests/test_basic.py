"""
Basic tests for SecurNote functionality.
"""

import os
import shutil
import tempfile

from securnote.auth import UserAuth
from securnote.crypto import NoteCrypto
from securnote.storage import NoteStorage


def test_user_creation():
    """Test user creation and login."""
    with tempfile.TemporaryDirectory() as temp_dir:
        auth = UserAuth(temp_dir)

        # Create user
        assert auth.create_user("testuser", "password123") == True

        # User exists
        assert auth.user_exists("testuser") == True

        # Can't create same user twice
        assert auth.create_user("testuser", "password123") == False


def test_user_login():
    """Test user authentication."""
    with tempfile.TemporaryDirectory() as temp_dir:
        auth = UserAuth(temp_dir)

        # Create user
        auth.create_user("testuser", "password123")

        # Valid login
        note_key = auth.login("testuser", "password123")
        assert note_key is not None
        assert len(note_key) == 32  # 256-bit key

        # Invalid login
        assert auth.login("testuser", "wrongpassword") is None
        assert auth.login("nonexistent", "password123") is None


def test_note_encryption():
    """Test note encryption and decryption."""
    with tempfile.TemporaryDirectory() as temp_dir:
        auth = UserAuth(temp_dir)
        auth.create_user("testuser", "password123")
        note_key = auth.login("testuser", "password123")

        crypto = NoteCrypto(note_key)

        # Encrypt text
        original_text = "This is a secret note!"
        encrypted, nonce = crypto.encrypt(original_text)

        # Check encrypted data is different
        assert encrypted != original_text
        assert len(nonce) > 0

        # Decrypt text
        decrypted = crypto.decrypt(encrypted, nonce)
        assert decrypted == original_text


def test_note_storage():
    """Test note storage functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = NoteStorage(temp_dir)

        # Add note
        note_id = storage.add_note(
            "testuser", "encrypted_title", "encrypted_content", "nonce123", "nonce456"
        )
        assert note_id is not None

        # Get notes
        notes = storage.get_notes("testuser")
        assert len(notes) == 1
        assert notes[0]["id"] == note_id

        # Get specific note
        note = storage.get_note_by_id("testuser", note_id)
        assert note is not None
        assert note["title_encrypted"] == "encrypted_title"

        # Delete note
        assert storage.delete_note("testuser", note_id) == True
        assert len(storage.get_notes("testuser")) == 0


if __name__ == "__main__":
    print("Running basic tests...")
    test_user_creation()
    print("✓ User creation test passed")

    test_user_login()
    print("✓ User login test passed")

    test_note_encryption()
    print("✓ Note encryption test passed")

    test_note_storage()
    print("✓ Note storage test passed")

    print("All tests passed!")
