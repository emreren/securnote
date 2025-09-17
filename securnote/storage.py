"""
Simple JSON file storage for notes.
"""

import json
import os
import uuid
from datetime import datetime


class NoteStorage:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.notes_dir = os.path.join(data_dir, "notes")
        os.makedirs(self.notes_dir, exist_ok=True)

    def _get_user_file(self, username):
        """Get user's notes file path."""
        return os.path.join(self.notes_dir, f"{username}.json")

    def _load_notes(self, username):
        """Load user's notes from file."""
        user_file = self._get_user_file(username)
        if not os.path.exists(user_file):
            return []

        with open(user_file, "r") as f:
            data = json.load(f)
            return data.get("notes", [])

    def _save_notes(self, username, notes):
        """Save user's notes to file."""
        user_file = self._get_user_file(username)
        data = {"notes": notes}

        with open(user_file, "w") as f:
            json.dump(data, f, indent=2)

    def add_note(
        self, username, title_encrypted, content_encrypted, title_nonce, content_nonce
    ):
        """Add new encrypted note."""
        notes = self._load_notes(username)

        note = {
            "id": str(uuid.uuid4()),
            "title_encrypted": title_encrypted,
            "content_encrypted": content_encrypted,
            "title_nonce": title_nonce,
            "content_nonce": content_nonce,
            "timestamp": datetime.now().isoformat(),
        }

        notes.append(note)
        self._save_notes(username, notes)
        return note["id"]

    def get_notes(self, username):
        """Get all user's notes."""
        return self._load_notes(username)

    def get_note_by_id(self, username, note_id):
        """Get specific note by ID."""
        notes = self._load_notes(username)
        for note in notes:
            if note["id"] == note_id:
                return note
        return None

    def delete_note(self, username, note_id):
        """Delete note by ID. Returns True if deleted."""
        notes = self._load_notes(username)
        for i, note in enumerate(notes):
            if note["id"] == note_id:
                notes.pop(i)
                self._save_notes(username, notes)
                return True
        return False
