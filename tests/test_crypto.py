"""
Cryptography tests.
"""

import pytest

from securnote.crypto import NoteCrypto


@pytest.mark.unit
class TestNoteCrypto:
    """Test note encryption/decryption."""

    @pytest.fixture
    def crypto(self):
        """Provide NoteCrypto instance with test key."""
        test_key = b"0" * 32  # 256-bit test key
        return NoteCrypto(test_key)

    def test_encryption_decryption(self, crypto):
        """Test basic encryption and decryption."""
        original_text = "This is a secret message!"

        # Encrypt
        encrypted, nonce = crypto.encrypt(original_text)

        # Verify encrypted data is different
        assert encrypted != original_text
        assert len(nonce) > 0

        # Decrypt
        decrypted = crypto.decrypt(encrypted, nonce)
        assert decrypted == original_text

    def test_different_nonces(self, crypto):
        """Test that each encryption uses different nonce."""
        text = "Same message"

        encrypted1, nonce1 = crypto.encrypt(text)
        encrypted2, nonce2 = crypto.encrypt(text)

        # Different nonces should produce different ciphertext
        assert nonce1 != nonce2
        assert encrypted1 != encrypted2

        # But both should decrypt to same message
        assert crypto.decrypt(encrypted1, nonce1) == text
        assert crypto.decrypt(encrypted2, nonce2) == text

    def test_invalid_decryption(self, crypto):
        """Test decryption with invalid data."""
        with pytest.raises(Exception):
            crypto.decrypt("invalid_data", "invalid_nonce")
