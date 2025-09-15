"""
Simple user authentication module.
"""
import hashlib
import secrets
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


class UserAuth:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def create_user(self, username, password):
        """Create new user. Returns True if success."""
        user_file = os.path.join(self.data_dir, f"{username}.auth")
        
        if os.path.exists(user_file):
            return False
        
        # Generate salts
        auth_salt = secrets.token_bytes(32)
        note_salt = secrets.token_bytes(32)
        
        # Hash password for auth
        auth_hash = hashlib.sha256(auth_salt + password.encode()).hexdigest()
        
        # Save to file
        with open(user_file, 'wb') as f:
            f.write(auth_salt + note_salt + b':' + auth_hash.encode())
        
        return True
    
    def login(self, username, password):
        """Login user. Returns note_key if success, None if fail."""
        user_file = os.path.join(self.data_dir, f"{username}.auth")
        
        if not os.path.exists(user_file):
            return None
        
        # Read file
        with open(user_file, 'rb') as f:
            data = f.read()
        
        # Parse data
        auth_salt = data[:32]
        note_salt = data[32:64] 
        stored_hash = data[65:].decode()  # Skip ':'
        
        # Check password
        password_hash = hashlib.sha256(auth_salt + password.encode()).hexdigest()
        if password_hash != stored_hash:
            return None
        
        # Generate note key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=note_salt,
            iterations=100000
        )
        note_key = kdf.derive(password.encode())
        return note_key
    
    def user_exists(self, username):
        """Check if user exists."""
        user_file = os.path.join(self.data_dir, f"{username}.auth")
        return os.path.exists(user_file)