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
        self.editor_preference = None  # 'inline' or 'external'
        self.external_editor = None    # editor command

    def setup_editor_preference(self):
        """Setup editor preference on first run."""
        if self.editor_preference is not None:
            return  # Already set up

        print("\n=== Editor Setup ===")
        print("Choose your preferred note editing method:")
        print("1. Inline typing (type directly in terminal)")
        print("2. External editor (nano, vim, etc.)")

        while True:
            choice = input("Choose (1/2): ").strip()
            if choice == "1":
                self.editor_preference = "inline"
                print("✓ Editor preference set to: Inline typing")
                break
            elif choice == "2":
                self.editor_preference = "external"
                self._setup_external_editor()
                break
            else:
                print("Please choose 1 or 2")

    def _setup_external_editor(self):
        """Setup external editor selection."""
        import os
        import subprocess

        # Check available editors
        available_editors = []
        common_editors = ['nano', 'vim', 'vi', 'code', 'gedit']

        for editor in common_editors:
            try:
                subprocess.run(['which', editor], capture_output=True, check=True)
                available_editors.append(editor)
            except subprocess.CalledProcessError:
                pass

        if not available_editors:
            print("No common editors found. Using environment EDITOR or nano as fallback.")
            self.external_editor = os.environ.get('EDITOR', 'nano')
            print(f"✓ External editor set to: {self.external_editor}")
            return

        print(f"\nAvailable editors: {', '.join(available_editors)}")
        print("Or type custom editor command")

        while True:
            editor_choice = input(f"Choose editor [{available_editors[0]}]: ").strip()

            if not editor_choice:
                editor_choice = available_editors[0]

            # Test if the editor works
            try:
                subprocess.run(['which', editor_choice], capture_output=True, check=True)
                self.external_editor = editor_choice
                print(f"✓ External editor set to: {editor_choice}")
                break
            except subprocess.CalledProcessError:
                print(f"Editor '{editor_choice}' not found. Try another.")

    def change_editor_preference(self):
        """Allow user to change editor preference."""
        print(f"\nCurrent preference: {self.editor_preference}")
        if self.editor_preference == "external":
            print(f"Current external editor: {self.external_editor}")

        print("\n1. Switch to inline typing")
        print("2. Switch to external editor")
        print("3. Keep current setting")

        choice = input("Choose (1/2/3): ").strip()

        if choice == "1":
            self.editor_preference = "inline"
            print("✓ Switched to inline typing")
        elif choice == "2":
            self.editor_preference = "external"
            self._setup_external_editor()
        elif choice == "3":
            print("Keeping current setting")
        else:
            print("Invalid choice")

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

        # Setup editor preference if not set
        self.setup_editor_preference()

        print("=== Add Note ===")
        title = input("Title: ").strip()

        if self.editor_preference == "external":
            content = self._edit_with_external_editor()
            if content is None:
                print("Note creation cancelled.")
                return
        else:
            print("Content (press Enter twice to finish):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            content = "\n".join(lines)

        if not content.strip():
            print("Empty content, note not saved.")
            return

        # Encrypt title and content
        title_enc, title_nonce = self.crypto.encrypt(title)
        content_enc, content_nonce = self.crypto.encrypt(content)

        # Store with separate nonces
        note_id = self.storage.add_note(
            self.current_user, title_enc, content_enc, title_nonce, content_nonce
        )

        print(f"Note saved with ID: {note_id}")

    def _edit_with_external_editor(self):
        """Open external editor for note content."""
        import os
        import subprocess
        import tempfile

        # Use configured external editor
        editor = self.external_editor or os.environ.get('EDITOR', 'nano')

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write("# Enter your note content here\n# Lines starting with # will be removed\n\n")

        try:
            # Open editor
            print(f"Opening {editor}... (save and exit to continue)")
            result = subprocess.run([editor, tmp_path], check=True)

            # Read content back
            with open(tmp_path, 'r') as f:
                content = f.read()

            # Remove comment lines
            lines = []
            for line in content.split('\n'):
                if not line.strip().startswith('#'):
                    lines.append(line)

            return '\n'.join(lines).strip()

        except subprocess.CalledProcessError:
            print("Editor was cancelled or failed.")
            return None
        except FileNotFoundError:
            print(f"Editor '{editor}' not found. Install it or set EDITOR environment variable.")
            print("Available editors: nano, vim, vi")
            return None
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

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
        for i, note in enumerate(notes, 1):
            # Decrypt title for display
            try:
                title = self.crypto.decrypt(
                    note["title_encrypted"], note["title_nonce"]
                )
                print(f"{i}. {title}")
                print(f"   ID: {note['id']}")
                print(f"   Created: {note['timestamp'][:19]}")
                print()
            except:
                print(f"{i}. [Encrypted Title]")
                print(f"   ID: {note['id']}")
                print(f"   Created: {note['timestamp'][:19]}")
                print()

    def view_note(self):
        """View specific note."""
        if not self.current_user:
            print("Please login first!")
            return

        # Show notes list first
        notes = self.storage.get_notes(self.current_user)
        if not notes:
            print("No notes found!")
            return

        print("\n=== Your Notes ===")
        for i, note in enumerate(notes, 1):
            try:
                title = self.crypto.decrypt(note["title_encrypted"], note["title_nonce"])
                print(f"{i}. {title} (ID: {note['id']})")
            except:
                print(f"{i}. [Encrypted] (ID: {note['id']})")

        print("\nYou can copy-paste the full ID or just type the number (1, 2, etc.)")
        user_input = input("Note ID or number: ").strip()

        # Check if user entered a number or full ID
        note = None
        if user_input.isdigit():
            # User entered a number
            note_num = int(user_input)
            if 1 <= note_num <= len(notes):
                note = notes[note_num - 1]
            else:
                print("Invalid note number!")
                return
        else:
            # User entered full ID
            note = self.storage.get_note_by_id(self.current_user, user_input)

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

        # Show notes list first
        notes = self.storage.get_notes(self.current_user)
        if not notes:
            print("No notes found!")
            return

        print("\n=== Your Notes ===")
        for i, note in enumerate(notes, 1):
            try:
                title = self.crypto.decrypt(note["title_encrypted"], note["title_nonce"])
                print(f"{i}. {title} (ID: {note['id']})")
            except:
                print(f"{i}. [Encrypted] (ID: {note['id']})")

        print("\nYou can copy-paste the full ID or just type the number (1, 2, etc.)")
        user_input = input("Note ID or number to delete: ").strip()

        # Check if user entered a number or full ID
        note_to_delete = None
        if user_input.isdigit():
            # User entered a number
            note_num = int(user_input)
            if 1 <= note_num <= len(notes):
                note_to_delete = notes[note_num - 1]
            else:
                print("Invalid note number!")
                return
        else:
            # User entered full ID
            for note in notes:
                if note['id'] == user_input:
                    note_to_delete = note
                    break

        if not note_to_delete:
            print("Note not found!")
            return

        # Show note title for confirmation
        try:
            title = self.crypto.decrypt(note_to_delete["title_encrypted"], note_to_delete["title_nonce"])
            confirm = input(f"Are you sure you want to delete '{title}'? (y/N): ").strip().lower()
        except:
            confirm = input(f"Are you sure you want to delete this note? (y/N): ").strip().lower()

        if confirm == 'y':
            if self.storage.delete_note(self.current_user, note_to_delete['id']):
                print("Note deleted!")
            else:
                print("Error deleting note!")
        else:
            print("Delete cancelled.")

    def edit_note(self):
        """Edit existing note with external editor."""
        if not self.current_user:
            print("Please login first!")
            return

        # Show notes list first
        notes = self.storage.get_notes(self.current_user)
        if not notes:
            print("No notes found!")
            return

        print("\n=== Your Notes ===")
        for i, note in enumerate(notes, 1):
            try:
                title_dec = self.crypto.decrypt(note["title_encrypted"], note["title_nonce"])
                print(f"{i}. {title_dec} (ID: {note['id']})")
            except:
                print(f"{i}. [Encrypted] (ID: {note['id']})")

        print("\nYou can copy-paste the full ID or just type the number (1, 2, etc.)")
        user_input = input("Note ID or number to edit: ").strip()

        # Check if user entered a number or full ID
        note = None
        if user_input.isdigit():
            # User entered a number
            note_num = int(user_input)
            if 1 <= note_num <= len(notes):
                note = notes[note_num - 1]
            else:
                print("Invalid note number!")
                return
        else:
            # User entered full ID
            note = self.storage.get_note_by_id(self.current_user, user_input)

        if not note:
            print("Note not found!")
            return

        try:
            current_title = self.crypto.decrypt(note["title_encrypted"], note["title_nonce"])
            current_content = self.crypto.decrypt(note["content_encrypted"], note["content_nonce"])

            print(f"Editing: {current_title}")
            print("1. Edit title only")
            print("2. Edit content with external editor")
            print("3. Edit both")
            choice = input("Choose option (1/2/3): ").strip()

            new_title = current_title
            new_content = current_content

            if choice in ["1", "3"]:
                new_title = input(f"Title [{current_title}]: ").strip()
                if not new_title:
                    new_title = current_title

            if choice in ["2", "3"]:
                print("Opening editor with current content...")
                import tempfile
                import os

                # Create temp file with current content
                with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tmp_file:
                    tmp_file.write(current_content)
                    tmp_path = tmp_file.name

                editor = self.external_editor or os.environ.get('EDITOR', 'nano')
                import subprocess

                try:
                    subprocess.run([editor, tmp_path], check=True)
                    with open(tmp_path, 'r') as f:
                        new_content = f.read().strip()
                except subprocess.CalledProcessError:
                    print("Editor cancelled.")
                    return
                except FileNotFoundError:
                    print(f"Editor '{editor}' not found.")
                    return
                finally:
                    os.unlink(tmp_path)

            # Update note
            if new_title != current_title or new_content != current_content:
                # Delete old note
                self.storage.delete_note(self.current_user, note_id)

                # Create new encrypted note
                title_enc, title_nonce = self.crypto.encrypt(new_title)
                content_enc, content_nonce = self.crypto.encrypt(new_content)

                new_note_id = self.storage.add_note(
                    self.current_user, title_enc, content_enc, title_nonce, content_nonce
                )
                print(f"Note updated with new ID: {new_note_id}")
            else:
                print("No changes made.")

        except Exception as e:
            print(f"Error editing note: {e}")

    def show_menu(self):
        """Show main menu."""
        if self.current_user:
            print(f"\n=== SecurNote - Logged in as {self.current_user} ===")
            if self.editor_preference:
                pref_text = f"external ({self.external_editor})" if self.editor_preference == "external" else "inline"
                print(f"Editor: {pref_text}")
            print("1. Add Note")
            print("2. List Notes")
            print("3. View Note")
            print("4. Edit Note")
            print("5. Delete Note")
            print("6. Change Editor Preference")
            print("7. Logout")
            print("8. Exit")
        else:
            print("\n=== SecurNote ===")
            print("1. Register")
            print("2. Login")
            print("3. Exit")

    def run(self):
        """Main CLI loop."""
        print("Welcome to SecurNote!")
        print("Your secure note-taking application with encryption.")
        print("="*50)

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
                    self.edit_note()
                elif choice == "5":
                    self.delete_note()
                elif choice == "6":
                    self.change_editor_preference()
                elif choice == "7":
                    self.logout()
                elif choice == "8":
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice!")
