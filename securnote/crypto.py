"""
Simple note encryption module.
"""
import base64
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class NoteCrypto:
    def __init__(self, key):
        """Initialize with user's note key."""
        self.key = key
        self.aes = AESGCM(key)
    
    def encrypt(self, text):
        """Encrypt text. Returns (encrypted_data, nonce) as base64 strings."""
        nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
        encrypted = self.aes.encrypt(nonce, text.encode(), None)
        
        # Return as base64 for JSON storage
        encrypted_b64 = base64.b64encode(encrypted).decode()
        nonce_b64 = base64.b64encode(nonce).decode()
        
        return encrypted_b64, nonce_b64
    
    def decrypt(self, encrypted_b64, nonce_b64):
        """Decrypt base64 encoded data. Returns original text."""
        encrypted = base64.b64decode(encrypted_b64)
        nonce = base64.b64decode(nonce_b64)
        
        decrypted = self.aes.decrypt(nonce, encrypted, None)
        return decrypted.decode()