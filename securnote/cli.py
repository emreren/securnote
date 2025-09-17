"""
Simple CLI interface for SecurNote.
"""

import getpass

from .auth import UserAuth
from .crypto import NoteCrypto
from .storage import NoteStorage


class SecurNoteCLI:
    def __init__(self):
        self.auth = UserAuth()
        self.storage = NoteStorage()
        self.current_user = None
        self.note_key = None
        self.crypto = None

    def register(self):
        """Register new user."""
        print("=== Register ===")
        username = input("Username: ").strip()

        if self.auth.user_exists(username):
            print("User already exists!")
            return

        password = getpass.getpass("Password: ")

        if self.auth.create_user(username, password):
            print(f"User '{username}' created successfully!")
        else:
            print("Failed to create user!")

    def login(self):
        """Login user."""
        print("=== Login ===")
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")

        note_key = self.auth.login(username, password)
        if note_key:
            self.current_user = username
            self.note_key = note_key
            self.crypto = NoteCrypto(note_key)
            print(f"Welcome {username}!")
        else:
            print("Invalid credentials!")

    def logout(self):
        """Logout current user."""
        if self.current_user:
            print(f"Goodbye {self.current_user}!")
            self.current_user = None
            self.note_key = None
            self.crypto = None
        else:
            print("Not logged in!")

    def add_note(self):
        """Add new note."""
        if not self.current_user:
            print("Please login first!")
            return

        print("=== Add Note ===")
        title = input("Title: ").strip()
        print("Content (press Enter twice to finish):")

        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        content = "\n".join(lines)

        # Encrypt title and content
        title_enc, title_nonce = self.crypto.encrypt(title)
        content_enc, content_nonce = self.crypto.encrypt(content)

        # Store with separate nonces
        note_id = self.storage.add_note(
            self.current_user, title_enc, content_enc, title_nonce, content_nonce
        )

        print(f"Note saved with ID: {note_id}")

    def list_notes(self):
        """List all notes."""
        if not self.current_user:
            print("Please login first!")
            return

        notes = self.storage.get_notes(self.current_user)
        if not notes:
            print("No notes found!")
            return

        print("=== Your Notes ===")
        for note in notes:
            # Decrypt title for display
            try:
                title = self.crypto.decrypt(
                    note["title_encrypted"], note["title_nonce"]
                )
                print(f"ID: {note['id'][:8]}... | {title} | {note['timestamp'][:19]}")
            except:
                print(
                    f"ID: {note['id'][:8]}... | [Encrypted] | {note['timestamp'][:19]}"
                )

    def view_note(self):
        """View specific note."""
        if not self.current_user:
            print("Please login first!")
            return

        note_id = input("Note ID: ").strip()
        note = self.storage.get_note_by_id(self.current_user, note_id)

        if not note:
            print("Note not found!")
            return

        try:
            title = self.crypto.decrypt(note["title_encrypted"], note["title_nonce"])
            content = self.crypto.decrypt(
                note["content_encrypted"], note["content_nonce"]
            )

            print(f"\n=== {title} ===")
            print(f"Created: {note['timestamp'][:19]}")
            print(f"\n{content}\n")
        except Exception as e:
            print(f"Failed to decrypt note: {e}")

    def delete_note(self):
        """Delete note."""
        if not self.current_user:
            print("Please login first!")
            return

        note_id = input("Note ID to delete: ").strip()

        if self.storage.delete_note(self.current_user, note_id):
            print("Note deleted!")
        else:
            print("Note not found!")

    def show_menu(self):
        """Show main menu."""
        if self.current_user:
            print(f"\n=== SecurNote - Logged in as {self.current_user} ===")
            print("1. Add Note")
            print("2. List Notes")
            print("3. View Note")
            print("4. Delete Note")
            print("5. Logout")
            print("6. Exit")
        else:
            print("\n=== SecurNote ===")
            print("1. Register")
            print("2. Login")
            print("3. Exit")

    def run(self):
        """Main CLI loop."""
        print("Welcome to SecurNote!")

        while True:
            self.show_menu()
            choice = input("\nChoice: ").strip()

            if not self.current_user:
                if choice == "1":
                    self.register()
                elif choice == "2":
                    self.login()
                elif choice == "3":
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice!")
            else:
                if choice == "1":
                    self.add_note()
                elif choice == "2":
                    self.list_notes()
                elif choice == "3":
                    self.view_note()
                elif choice == "4":
                    self.delete_note()
                elif choice == "5":
                    self.logout()
                elif choice == "6":
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice!")
