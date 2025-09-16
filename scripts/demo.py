"""
Demo script to showcase SecurNote functionality.
"""
from securnote.auth import UserAuth
from securnote.crypto import NoteCrypto
from securnote.storage import NoteStorage

def demo():
    print("=== SecurNote Demo ===\n")
    
    # Initialize components
    auth = UserAuth()
    storage = NoteStorage()
    
    # Create user
    print("1. Creating user 'demo' with password 'test123'...")
    if auth.create_user("demo", "test123"):
        print("✓ User created successfully!")
    else:
        print("User already exists!")
    
    # Login
    print("\n2. Logging in...")
    note_key = auth.login("demo", "test123")
    if note_key:
        print("✓ Login successful!")
        crypto = NoteCrypto(note_key)
    else:
        print("✗ Login failed!")
        return
    
    # Add encrypted note
    print("\n3. Adding encrypted note...")
    title = "My Secret Note"
    content = "This is a secret message that will be encrypted!"
    
    title_enc, title_nonce = crypto.encrypt(title)
    content_enc, content_nonce = crypto.encrypt(content)
    
    note_id = storage.add_note("demo", title_enc, content_enc, title_nonce, content_nonce)
    print(f"✓ Note added with ID: {note_id}")
    
    # List notes
    print("\n4. Listing encrypted notes from storage...")
    notes = storage.get_notes("demo")
    for note in notes:
        print(f"Raw encrypted title: {note['title_encrypted'][:50]}...")
        print(f"Raw encrypted content: {note['content_encrypted'][:50]}...")
    
    # Decrypt and show
    print("\n5. Decrypting and displaying note...")
    note = notes[0]
    decrypted_title = crypto.decrypt(note['title_encrypted'], note['title_nonce'])
    decrypted_content = crypto.decrypt(note['content_encrypted'], note['content_nonce'])
    
    print(f"Decrypted title: {decrypted_title}")
    print(f"Decrypted content: {decrypted_content}")
    
    # Show file structure
    print("\n6. File structure created:")
    import os
    for root, dirs, files in os.walk("data"):
        level = root.replace("data", "").count(os.sep)
        indent = " " * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = " " * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

if __name__ == "__main__":
    demo()