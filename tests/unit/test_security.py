"""
Unit tests for Security/Encryption functionality.
Tests Fernet encryption/decryption and contact info protection.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestEncryptionBasic:
    """Tests for basic encryption operations."""

    @pytest.fixture(autouse=True)
    def setup_encryption(self):
        """Set up encryption with a known test key."""
        test_key = "test-secret-key-for-unit-tests-1234567890"
        with patch("app.core.security.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                security=MagicMock(secret_key=test_key)
            )
            yield test_key

    def test_encrypt_value_returns_different_value(self, setup_encryption):
        """Test that encryption produces different output than input."""
        from app.core.security import encrypt_value

        original = "sensitive@example.com"
        encrypted = encrypt_value(original)

        assert encrypted != original
        assert len(encrypted) > 0

    def test_decrypt_value_returns_original(self, setup_encryption):
        """Test that decryption returns original value."""
        from app.core.security import encrypt_value, decrypt_value

        original = "sensitive@example.com"
        encrypted = encrypt_value(original)
        decrypted = decrypt_value(encrypted)

        assert decrypted == original

    def test_encrypt_empty_string(self, setup_encryption):
        """Test that empty strings are returned as-is."""
        from app.core.security import encrypt_value

        result = encrypt_value("")
        assert result == ""

    def test_encrypt_none_value(self, setup_encryption):
        """Test that None values are returned as-is."""
        from app.core.security import encrypt_value

        result = encrypt_value(None)
        assert result is None

    def test_encrypt_value_with_purpose(self, setup_encryption):
        """Test encryption with different purposes produces different results."""
        from app.core.security import encrypt_value

        value = "test@example.com"
        encrypted1 = encrypt_value(value, purpose="contact")
        encrypted2 = encrypt_value(value, purpose="email")

        assert encrypted1 != encrypted2

    def test_decrypt_with_wrong_purpose_fails(self, setup_encryption):
        """Test that decryption with wrong purpose fails."""
        from app.core.security import encrypt_value, decrypt_value
        from cryptography.fernet import InvalidToken

        value = "test@example.com"
        encrypted = encrypt_value(value, purpose="contact")

        with pytest.raises(InvalidToken):
            decrypt_value(encrypted, purpose="wrong_purpose")


class TestEncryptionDict:
    """Tests for dictionary encryption operations."""

    @pytest.fixture(autouse=True)
    def setup_encryption(self):
        """Set up encryption with a known test key."""
        test_key = "test-secret-key-for-unit-tests-1234567890"
        with patch("app.core.security.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                security=MagicMock(secret_key=test_key)
            )
            yield test_key

    def test_encrypt_dict_only_specified_fields(self, setup_encryption):
        """Test that only specified fields are encrypted."""
        from app.core.security import encrypt_dict

        data = {"name": "John", "email": "john@example.com", "phone": "123456"}
        result = encrypt_dict(data, ["email", "phone"])

        assert result["name"] == "John"  # Not encrypted
        assert result["email"] != "john@example.com"
        assert result["phone"] != "123456"

    def test_decrypt_dict_only_specified_fields(self, setup_encryption):
        """Test that only specified fields are decrypted."""
        from app.core.security import encrypt_dict, decrypt_dict

        data = {"name": "John", "email": "john@example.com", "phone": "123456"}
        encrypted = encrypt_dict(data, ["email", "phone"])
        decrypted = decrypt_dict(encrypted, ["email", "phone"])

        assert decrypted["name"] == "John"  # Wasn't encrypted
        assert decrypted["email"] == "john@example.com"
        assert decrypted["phone"] == "123456"

    def test_encrypt_dict_preserves_missing_fields(self, setup_encryption):
        """Test that missing fields are handled correctly."""
        from app.core.security import encrypt_dict

        data = {"name": "John"}
        result = encrypt_dict(data, ["email"])

        assert result["name"] == "John"
        assert "email" not in result or result["email"] is None


class TestContactInfoEncryption:
    """Tests for contact information encryption."""

    @pytest.fixture(autouse=True)
    def setup_encryption(self):
        """Set up encryption with a known test key."""
        test_key = "test-secret-key-for-unit-tests-1234567890"
        with patch("app.core.security.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                security=MagicMock(secret_key=test_key)
            )
            yield test_key

    def test_encrypt_contact_info(self, setup_encryption):
        """Test encrypting full contact info."""
        from app.core.security import encrypt_contact_info

        contact = {
            "email": "test@example.com",
            "phone": "1234567890",
            "mobile": "0987654321",
            "wechat": "wechat_id",
            "qq": "123456",
            "name": "John",  # Not a sensitive field
        }

        encrypted = encrypt_contact_info(contact)

        assert encrypted["email"] != "test@example.com"
        assert encrypted["phone"] != "1234567890"
        assert encrypted["mobile"] != "0987654321"
        assert encrypted["wechat"] != "wechat_id"
        assert encrypted["qq"] != "123456"
        assert encrypted["name"] == "John"  # Not encrypted

    def test_decrypt_contact_info(self, setup_encryption):
        """Test decrypting full contact info."""
        from app.core.security import encrypt_contact_info, decrypt_contact_info

        contact = {
            "email": "test@example.com",
            "phone": "1234567890",
            "mobile": "0987654321",
        }

        encrypted = encrypt_contact_info(contact)
        decrypted = decrypt_contact_info(encrypted)

        assert decrypted["email"] == "test@example.com"
        assert decrypted["phone"] == "1234567890"
        assert decrypted["mobile"] == "0987654321"

    def test_roundtrip_contact_info(self, setup_encryption):
        """Test that contact info survives encryption roundtrip."""
        from app.core.security import encrypt_contact_info, decrypt_contact_info

        original = {
            "email": "contact@company.com",
            "phone": "+86-10-12345678",
            "wechat": "wechat123",
        }

        encrypted = encrypt_contact_info(original)
        decrypted = decrypt_contact_info(encrypted)

        assert decrypted == original


class TestMaskingFunctions:
    """Tests for sensitive data masking functions."""

    def test_mask_sensitive_value_shows_last_chars(self):
        """Test that masking shows last N characters."""
        from app.core.security import mask_sensitive_value

        result = mask_sensitive_value("1234567890", visible_chars=4)
        assert result == "******7890"

    def test_mask_sensitive_value_short_string(self):
        """Test masking short strings."""
        from app.core.security import mask_sensitive_value

        result = mask_sensitive_value("123", visible_chars=4)
        assert result == "***"

    def test_mask_email(self):
        """Test email masking."""
        from app.core.security import mask_email

        result = mask_email("john.doe@example.com")
        assert "***" in result
        assert "@example.com" in result
        assert "john" not in result

    def test_mask_email_invalid(self):
        """Test masking invalid email."""
        from app.core.security import mask_email

        result = mask_email("invalid-email")
        assert "****" in result or result == ""

    def test_mask_phone(self):
        """Test phone masking."""
        from app.core.security import mask_phone

        result = mask_phone("13812345678")
        assert result == "****5678"

    def test_mask_phone_empty(self):
        """Test masking empty phone."""
        from app.core.security import mask_phone

        result = mask_phone("")
        assert result == ""


class TestEncryptionService:
    """Tests for EncryptionService class."""

    @pytest.fixture(autouse=True)
    def setup_encryption(self):
        """Set up encryption with a known test key."""
        test_key = "test-secret-key-for-unit-tests-1234567890"
        with patch("app.core.security.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                security=MagicMock(secret_key=test_key)
            )
            yield test_key

    def test_encryption_service_singleton(self, setup_encryption):
        """Test that encryption_service is available."""
        from app.core.security import encryption_service

        assert encryption_service is not None

    def test_encrypt_contact_via_service(self, setup_encryption):
        """Test encrypting contact via service."""
        from app.core.security import encryption_service

        contact = {"email": "test@example.com", "name": "John"}
        encrypted = encryption_service.encrypt_contact(contact)

        assert encrypted["email"] != "test@example.com"
        assert encrypted["name"] == "John"

    def test_decrypt_contact_via_service(self, setup_encryption):
        """Test decrypting contact via service."""
        from app.core.security import encryption_service

        contact = {"email": "test@example.com"}
        encrypted = encryption_service.encrypt_contact(contact)
        decrypted = encryption_service.decrypt_contact(encrypted)

        assert decrypted["email"] == "test@example.com"

    def test_encrypt_field(self, setup_encryption):
        """Test encrypting single field."""
        from app.core.security import encryption_service

        encrypted = encryption_service.encrypt_field("secret", purpose="test")
        assert encrypted != "secret"

    def test_decrypt_field(self, setup_encryption):
        """Test decrypting single field."""
        from app.core.security import encryption_service

        encrypted = encryption_service.encrypt_field("secret", purpose="test")
        decrypted = encryption_service.decrypt_field(encrypted, purpose="test")
        assert decrypted == "secret"


class TestEncryptionKeyManager:
    """Tests for EncryptionKeyManager class."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        with patch("app.core.security.get_settings") as mock:
            mock.return_value = MagicMock(
                security=MagicMock(secret_key="test-key-12345")
            )
            yield mock

    def test_derive_key_same_purpose(self, mock_settings):
        """Test that same purpose generates same key."""
        from app.core.security import EncryptionKeyManager

        manager = EncryptionKeyManager()
        key1 = manager._derive_key("contact")
        key2 = manager._derive_key("contact")

        assert key1 == key2

    def test_derive_key_different_purposes(self, mock_settings):
        """Test that different purposes generate different keys."""
        from app.core.security import EncryptionKeyManager

        manager = EncryptionKeyManager()
        key1 = manager._derive_key("contact")
        key2 = manager._derive_key("email")

        assert key1 != key2

    def test_get_fernet(self, mock_settings):
        """Test getting Fernet instance."""
        from app.core.security import EncryptionKeyManager

        manager = EncryptionKeyManager()
        fernet = manager.get_fernet("test")

        assert fernet is not None

    def test_rotate_key_clears_cache(self, mock_settings):
        """Test that key rotation clears cached keys."""
        from app.core.security import EncryptionKeyManager

        manager = EncryptionKeyManager()
        key1 = manager._derive_key("contact")
        manager.rotate_key("new-key")
        key2 = manager._derive_key("contact")

        assert key1 != key2


class TestAgentSecretEncryption:
    """Tests for agent_secret encryption in agent registration and authentication.
    
    Critical security requirement: agent_secret must be stored encrypted,
    not as plaintext. This prevents database泄露 from exposing all secrets.
    """

    @pytest.fixture(autouse=True)
    def setup_encryption(self):
        """Set up encryption with a known test key."""
        test_key = "test-secret-key-for-unit-tests-1234567890"
        with patch("app.core.security.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                security=MagicMock(secret_key=test_key)
            )
            yield test_key

    def test_agent_secret_is_encrypted_not_plaintext(self, setup_encryption):
        """
        Test that agent_secret is stored encrypted, not as plaintext.
        This is a critical security requirement.
        """
        from app.core.security import encrypt_value
        import secrets

        # Simulate agent registration
        original_secret = f"as_{secrets.token_urlsafe(32)}"
        stored_value = encrypt_value(original_secret, purpose="agent_secret")

        # The stored value should NOT be the plaintext secret
        assert stored_value != original_secret

        # The stored value should be longer (Fernet adds overhead)
        assert len(stored_value) > len(original_secret)

    def test_agent_secret_can_be_decrypted(self, setup_encryption):
        """
        Test that encrypted agent_secret can be decrypted for HMAC verification.
        """
        from app.core.security import encrypt_value, decrypt_value
        import secrets

        original_secret = f"as_{secrets.token_urlsafe(32)}"
        encrypted = encrypt_value(original_secret, purpose="agent_secret")
        decrypted = decrypt_value(encrypted, purpose="agent_secret")

        assert decrypted == original_secret

    def test_encrypted_agent_secret_requires_correct_purpose(self, setup_encryption):
        """
        Test that encrypted agent_secret cannot be decrypted with wrong purpose.
        """
        from app.core.security import encrypt_value, decrypt_value
        from cryptography.fernet import InvalidToken
        import secrets

        original_secret = f"as_{secrets.token_urlsafe(32)}"
        encrypted = encrypt_value(original_secret, purpose="agent_secret")

        # Trying to decrypt with wrong purpose should fail
        with pytest.raises(InvalidToken):
            decrypt_value(encrypted, purpose="wrong_purpose")

    def test_hmac_verification_works_after_decryption(self, setup_encryption):
        """
        Test that HMAC verification works correctly with decrypted secret.
        """
        import hashlib
        import hmac
        from app.core.security import encrypt_value, decrypt_value
        import secrets

        # Agent registration
        agent_id = "agt_test123"
        original_secret = f"as_{secrets.token_urlsafe(32)}"
        stored_encrypted = encrypt_value(original_secret, purpose="agent_secret")

        # Authentication - decrypt and verify HMAC
        timestamp = 1704067200  # Fixed timestamp for testing
        message = f"{agent_id}{timestamp}"

        # User calculates signature with original secret
        user_signature = hmac.new(
            original_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        # Server decrypts and calculates expected signature
        decrypted_secret = decrypt_value(stored_encrypted, purpose="agent_secret")
        expected_signature = hmac.new(
            decrypted_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        # HMAC verification should succeed
        assert hmac.compare_digest(user_signature, expected_signature)

    def test_hmac_fails_with_wrong_secret(self, setup_encryption):
        """
        Test that HMAC verification fails with wrong secret.
        """
        import hashlib
        import hmac
        from app.core.security import encrypt_value, decrypt_value
        import secrets

        agent_id = "agt_test123"
        original_secret = f"as_{secrets.token_urlsafe(32)}"
        wrong_secret = f"as_{secrets.token_urlsafe(32)}"
        stored_encrypted = encrypt_value(original_secret, purpose="agent_secret")

        timestamp = 1704067200
        message = f"{agent_id}{timestamp}"

        # User signs with WRONG secret
        wrong_signature = hmac.new(
            wrong_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        # Server decrypts with correct secret
        decrypted_secret = decrypt_value(stored_encrypted, purpose="agent_secret")
        expected_signature = hmac.new(
            decrypted_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        # HMAC verification should fail
        assert not hmac.compare_digest(wrong_signature, expected_signature)
