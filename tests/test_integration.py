"""
Integration tests for complete workflows.
"""

import pytest

from securnote.crypto import NoteCrypto


@pytest.mark.integration
class TestIntegration:
    """Test complete user workflows."""

    def test_full_note_workflow(self, app, test_user_data, test_note_data):
        """Test complete note creation, encryption, and retrieval workflow."""
        # Create user
        assert app.create_user(test_user_data["username"], test_user_data["password"])

        # Login to get encryption key
        note_key = app.login(test_user_data["username"], test_user_data["password"])
        assert note_key is not None

        # Create crypto instance
        crypto = NoteCrypto(note_key)

        # Encrypt note data
        title_encrypted, title_nonce = crypto.encrypt(test_note_data["title"])
        content_encrypted, content_nonce = crypto.encrypt(test_note_data["content"])

        # Store note using storage layer
        from securnote.storage import NoteStorage

        storage = NoteStorage(app.user_repo.data_dir)
        note_id = storage.add_note(
            username=test_user_data["username"],
            title_encrypted=title_encrypted,
            content_encrypted=content_encrypted,
            title_nonce=title_nonce,
            content_nonce=content_nonce,
        )

        # Retrieve and decrypt note
        stored_note = storage.get_note_by_id(test_user_data["username"], note_id)
        assert stored_note is not None

        decrypted_title = crypto.decrypt(
            stored_note["title_encrypted"], stored_note["title_nonce"]
        )
        decrypted_content = crypto.decrypt(
            stored_note["content_encrypted"], stored_note["content_nonce"]
        )

        # Verify decrypted data matches original
        assert decrypted_title == test_note_data["title"]
        assert decrypted_content == test_note_data["content"]

    def test_multiple_users_isolation(self, app):
        """Test that users cannot access each other's data."""
        # Create two users
        assert app.create_user("user1", "password1")
        assert app.create_user("user2", "password2")

        # Login as user1 and create note
        user1_key = app.login("user1", "password1")
        crypto1 = NoteCrypto(user1_key)

        from securnote.storage import NoteStorage

        storage = NoteStorage(app.user_repo.data_dir)

        title_enc, title_nonce = crypto1.encrypt("User1 Secret")
        content_enc, content_nonce = crypto1.encrypt("This is user1's private note")

        note_id = storage.add_note(
            username="user1",
            title_encrypted=title_enc,
            content_encrypted=content_enc,
            title_nonce=title_nonce,
            content_nonce=content_nonce,
        )

        # User2 should not see user1's notes
        user2_notes = storage.get_notes("user2")
        assert len(user2_notes) == 0

        # User2 should not access user1's note by ID
        user2_note = storage.get_note_by_id("user2", note_id)
        assert user2_note is None
