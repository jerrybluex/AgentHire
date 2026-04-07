"""
Real tests for encryption/decryption functionality (C1 fix validation).

Tests that data encrypted with a key can be decrypted with the same key,
and that changing the key makes decryption fail with a clear error.
"""

import pytest
import os
from cryptography.fernet import Fernet

from app.core.security import encrypt_value, decrypt_value, get_encryption_manager


@pytest.mark.unit
class TestEncryptionRoundTrip:
    """Test encryption and decryption round-trip."""

    def test_encrypt_decrypt_roundtrip(self):
        ""Test that data encrypted can be decrypted back."""
        # Set a test key
        original_key = "test-key-for-encryption-32-chars-long!!"
        os.environ["SECURITY_SECRET_KEY"] = original_key

        # Clear any cached encryption manager
        get_encryption_manager()._key_cache.clear()

        # Test data
        original_data = "sensitive-contact-info@example.com"

        # Encrypt
        encrypted = encrypt_value(original_data)
        assert encrypted != original_data
        assert isinstance(encrypted, str)

        # Decrypt
        decrypted = decrypt_value(encrypted)
        assert decrypted == original_data

    def test_encrypt_produces_different_output_for_same_input(self):
        ""Test that encrypting same data twice produces different output (Fernet property)."""
        os.environ["SECURITY_SECRET_KEY"] = "test-key-for-encryption-32-chars-long!!"
        get_encryption_manager()._key_cache.clear()

        data = "test-data"
        encrypted1 = encrypt_value(data)
        encrypted2 = encrypt_value(data)

        # Should be different due to random IV
        assert encrypted1 != encrypted2

        # But both should decrypt to same value
        assert decrypt_value(encrypted1) == data
        assert decrypt_value(encrypted2) == data

    def test_decrypt_with_wrong_key_fails(self):
        ""Test that decrypting with wrong key raises InvalidToken."""
        # Set initial key
        os.environ["SECURITY_SECRET_KEY"] = "correct-key-for-encryption-32-chars!!"
        get_encryption_manager()._key_cache.clear()

        # Encrypt with correct key
        data = "important-data"
        encrypted = encrypt_value(data)

        # Change to wrong key
        os.environ["SECURITY_SECRET_KEY"] = "wrong-key-that-wont-match-32-chars"
        get_encryption_manager()._key_cache.clear()

        # Should fail to decrypt
        from cryptography.fernet import InvalidToken
        with pytest.raises(InvalidToken):
            decrypt_value(encrypted)

    def test_empty_string_encryption(self):
        ""Test that empty strings are handled correctly."""
        os.environ["SECURITY_SECRET_KEY"] = "test-key-for-encryption-32-chars-long!!"
        get_encryption_manager()._key_cache.clear()

        assert encrypt_value("") == ""
        assert decrypt_value("") == ""

    def test_unicode_encryption(self):
        ""Test that unicode characters are handled correctly."""
        os.environ["SECURITY_SECRET_KEY"] = "test-key-for-encryption-32-chars-long!!"
        get_encryption_manager()._key_cache.clear()

        data = "中文测试-email@例子.com"
        encrypted = encrypt_value(data)
        decrypted = decrypt_value(encrypted)

        assert decrypted == data


@pytest.mark.unit
class TestKeyGeneration:
    """Test key generation and validation."""

    def test_fernet_key_generation(self):
        ""Test generating a valid Fernet key."""
        key = Fernet.generate_key()
        assert isinstance(key, bytes)
        assert len(key) == 44  # Base64 encoded 32-byte key

        # Should be able to create Fernet instance
        fernet = Fernet(key)
        assert fernet is not None

    def test_key_derivation_is_deterministic(self):
        ""Test that same secret + purpose produces same key."""
        os.environ["SECURITY_SECRET_KEY"] = "deterministic-test-key-32-chars!"
        get_encryption_manager()._key_cache.clear()

        manager = get_encryption_manager()

        # Get key for same purpose twice
        key1 = manager._derive_key("contact")
        key2 = manager._derive_key("contact")

        assert key1 == key2

        # Different purpose should produce different key
        key3 = manager._derive_key("api_key")
        assert key3 != key1
