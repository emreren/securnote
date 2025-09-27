"""
Remote CLI interface for SecurNote
Allows command-line operations for SSH-based remote access
"""

import argparse
import sys
from typing import Optional

from .cli import SecurNoteCLI
from .auth import UserAuth
from .crypto import NoteCrypto
from .storage import NoteStorage


class RemoteCLI:
    """Command-line interface for remote SSH access."""

    def __init__(self):
        self.auth = UserAuth()
        self.storage = NoteStorage()

    def register_user(self, username: str, password: str) -> bool:
        """Register a new user."""
        if self.auth.user_exists(username):
            print(f"Error: User '{username}' already exists")
            return False

        success = self.auth.create_user(username, password)
        if success:
            print(f"✓ User '{username}' registered successfully")
            return True
        else:
            print(f"Error: Failed to register user '{username}'")
            return False

    def login_user(self, username: str, password: str) -> Optional[NoteCrypto]:
        """Login user and return crypto instance."""
        note_key = self.auth.login(username, password)
        if note_key:
            return NoteCrypto(note_key)
        return None

    def list_notes(self, username: str, password: str) -> None:
        """List all notes for user."""
        crypto = self.login_user(username, password)
        if not crypto:
            print("Error: Invalid credentials")
            return

        notes = self.storage.get_notes(username)
        if not notes:
            print("No notes found")
            return

        print("Your Notes:")
        print("-" * 50)
        for i, note in enumerate(notes, 1):
            try:
                title = crypto.decrypt(note["title_encrypted"], note["title_nonce"])
                created = note['timestamp'][:19]
                print(f"{i}. {title}")
                print(f"   ID: {note['id']}")
                print(f"   Created: {created}")
                print()
            except Exception:
                print(f"{i}. [Decryption Failed]")
                print(f"   ID: {note['id']}")
                print()

    def view_note(self, username: str, password: str, note_id: str) -> None:
        """View a specific note."""
        crypto = self.login_user(username, password)
        if not crypto:
            print("Error: Invalid credentials")
            return

        note = self.storage.get_note_by_id(username, note_id)
        if not note:
            print("Error: Note not found")
            return

        try:
            title = crypto.decrypt(note["title_encrypted"], note["title_nonce"])
            content = crypto.decrypt(note["content_encrypted"], note["content_nonce"])
            created = note['timestamp'][:19]

            print("=" * 60)
            print(f"Title: {title}")
            print(f"Created: {created}")
            print("=" * 60)
            print(content)
            print("=" * 60)
        except Exception as e:
            print(f"Error: Failed to decrypt note - {e}")

    def add_note(self, username: str, password: str, title: str, content: str) -> None:
        """Add a new note."""
        crypto = self.login_user(username, password)
        if not crypto:
            print("Error: Invalid credentials")
            return

        if not title.strip():
            print("Error: Title cannot be empty")
            return

        if not content.strip():
            print("Error: Content cannot be empty")
            return

        try:
            # Encrypt title and content
            title_enc, title_nonce = crypto.encrypt(title)
            content_enc, content_nonce = crypto.encrypt(content)

            # Store note
            note_id = self.storage.add_note(
                username, title_enc, content_enc, title_nonce, content_nonce
            )

            print(f"✓ Note '{title}' added successfully")
            print(f"Note ID: {note_id}")
        except Exception as e:
            print(f"Error: Failed to add note - {e}")

    def delete_note(self, username: str, password: str, note_id: str) -> None:
        """Delete a note."""
        crypto = self.login_user(username, password)
        if not crypto:
            print("Error: Invalid credentials")
            return

        # Check if note exists and get title for confirmation
        note = self.storage.get_note_by_id(username, note_id)
        if not note:
            print("Error: Note not found")
            return

        try:
            title = crypto.decrypt(note["title_encrypted"], note["title_nonce"])
            print(f"Note to delete: '{title}'")
        except Exception:
            print(f"Note to delete: [ID: {note_id}]")

        # Delete note
        if self.storage.delete_note(username, note_id):
            print("✓ Note deleted successfully")
        else:
            print("Error: Failed to delete note")

    def interactive_mode(self) -> None:
        """Start interactive CLI mode."""
        print("Starting SecurNote interactive mode...")
        cli = SecurNoteCLI()
        cli.run()


def main():
    """Main entry point for remote CLI."""
    parser = argparse.ArgumentParser(
        description="SecurNote - Secure note-taking with encryption",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (default)
  securnote

  # Register new user
  securnote register alice password123

  # List notes
  securnote list alice password123

  # View specific note
  securnote view alice password123 note-id-here

  # Add note (single line)
  securnote add alice password123 "Meeting Notes" "Remember to call John"

  # Add note (multiline via stdin)
  echo "Long note content here" | securnote add alice password123 "My Note" -

  # Delete note
  securnote delete alice password123 note-id-here

SSH Examples:
  # Connect to remote server
  ssh user@server securnote

  # Run remote commands
  ssh user@server securnote list alice password123
  ssh user@server 'securnote view alice password123 abc123'
        """
    )

    parser.add_argument(
        'command',
        nargs='?',
        choices=['register', 'list', 'view', 'add', 'delete'],
        help='Command to execute'
    )

    parser.add_argument(
        'username',
        nargs='?',
        help='Username for authentication'
    )

    parser.add_argument(
        'password',
        nargs='?',
        help='Password for authentication'
    )

    parser.add_argument(
        'arg1',
        nargs='?',
        help='First argument (note-id for view/delete, title for add)'
    )

    parser.add_argument(
        'arg2',
        nargs='?',
        help='Second argument (content for add command)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='SecurNote 1.0.0'
    )

    args = parser.parse_args()

    # If no command specified, start interactive mode
    if not args.command:
        cli = RemoteCLI()
        cli.interactive_mode()
        return

    # Validate required arguments
    if not args.username or not args.password:
        print("Error: Username and password required for all commands")
        parser.print_help()
        sys.exit(1)

    cli = RemoteCLI()

    try:
        if args.command == 'register':
            success = cli.register_user(args.username, args.password)
            sys.exit(0 if success else 1)

        elif args.command == 'list':
            cli.list_notes(args.username, args.password)

        elif args.command == 'view':
            if not args.arg1:
                print("Error: Note ID required for view command")
                sys.exit(1)
            cli.view_note(args.username, args.password, args.arg1)

        elif args.command == 'add':
            if not args.arg1:  # title
                print("Error: Title required for add command")
                sys.exit(1)

            content = args.arg2

            # If content is "-", read from stdin
            if content == "-":
                content = sys.stdin.read().strip()

            if not content:
                print("Error: Content required for add command")
                sys.exit(1)

            cli.add_note(args.username, args.password, args.arg1, content)

        elif args.command == 'delete':
            if not args.arg1:
                print("Error: Note ID required for delete command")
                sys.exit(1)
            cli.delete_note(args.username, args.password, args.arg1)

    except KeyboardInterrupt:
        print("\nOperation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()