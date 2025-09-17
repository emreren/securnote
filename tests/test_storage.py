"""
Storage system tests.
"""

import pytest

from securnote.storage import NoteStorage


@pytest.mark.unit
class TestNoteStorage:
    """Test note storage functionality."""

    @pytest.fixture
    def storage(self, temp_dir):
        """Provide NoteStorage instance."""
        return NoteStorage(temp_dir)

    def test_add_note(self, storage):
        """Test adding a note."""
        note_id = storage.add_note(
            username="testuser",
            title_encrypted="encrypted_title",
            content_encrypted="encrypted_content",
            title_nonce="title_nonce123",
            content_nonce="content_nonce456",
        )

        assert note_id is not None
        assert len(note_id) > 0

    def test_get_notes(self, storage):
        """Test retrieving notes for a user."""
        # Initially no notes
        notes = storage.get_notes("testuser")
        assert len(notes) == 0

        # Add a note
        note_id = storage.add_note(
            username="testuser",
            title_encrypted="encrypted_title",
            content_encrypted="encrypted_content",
            title_nonce="title_nonce123",
            content_nonce="content_nonce456",
        )

        # Should have one note now
        notes = storage.get_notes("testuser")
        assert len(notes) == 1
        assert notes[0]["id"] == note_id

    def test_get_note_by_id(self, storage):
        """Test retrieving specific note by ID."""
        # Add a note
        note_id = storage.add_note(
            username="testuser",
            title_encrypted="encrypted_title",
            content_encrypted="encrypted_content",
            title_nonce="title_nonce123",
            content_nonce="content_nonce456",
        )

        # Retrieve note
        note = storage.get_note_by_id("testuser", note_id)
        assert note is not None
        assert note["title_encrypted"] == "encrypted_title"
        assert note["content_encrypted"] == "encrypted_content"

    def test_delete_note(self, storage):
        """Test deleting a note."""
        # Add a note
        note_id = storage.add_note(
            username="testuser",
            title_encrypted="encrypted_title",
            content_encrypted="encrypted_content",
            title_nonce="title_nonce123",
            content_nonce="content_nonce456",
        )

        # Delete note
        result = storage.delete_note("testuser", note_id)
        assert result is True

        # Note should no longer exist
        notes = storage.get_notes("testuser")
        assert len(notes) == 0

    def test_delete_nonexistent_note(self, storage):
        """Test deleting non-existent note."""
        result = storage.delete_note("testuser", "nonexistent_id")
        assert result is False
