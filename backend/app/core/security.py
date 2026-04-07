"""
Security utilities for sensitive data encryption.
Uses Fernet symmetric encryption for contact information and other sensitive fields.
"""

import base64
import json
from typing import Any, Optional, Union

from cryptography.fernet import Fernet, InvalidToken
from pydantic import Field

from app.config import get_settings


class EncryptionKeyManager:
    """
    Manages encryption keys for Fernet symmetric encryption.
    Supports key rotation and derivation.
    """

    def __init__(self, secret_key: Optional[str] = None):
        settings = get_settings()
        self._secret_key = secret_key or settings.security.secret_key
        self._fernet: Optional[Fernet] = None
        self._key_cache: dict = {}

    def _derive_key(self, purpose: str = "default") -> bytes:
        """
        Derive an encryption key for a specific purpose.

        Args:
            purpose: Purpose identifier (e.g., "contact", "email")

        Returns:
            Derived key as bytes
        """
        if purpose in self._key_cache:
            return self._key_cache[purpose]

        # Use HKDF-like key derivation
        import hashlib

        combined = f"{self._secret_key}:{purpose}".encode()
        derived = hashlib.sha256(combined).digest()
        key = base64.urlsafe_b64encode(derived)
        self._key_cache[purpose] = key
        return key

    def get_fernet(self, purpose: str = "default") -> Fernet:
        """Get Fernet instance for encryption/decryption."""
        key = self._derive_key(purpose)
        return Fernet(key)

    def rotate_key(self, secret_key: str):
        """Rotate to a new secret key."""
        self._secret_key = secret_key
        self._fernet = None
        self._key_cache.clear()


# Global encryption manager
_encryption_manager: Optional[EncryptionKeyManager] = None


def get_encryption_manager() -> EncryptionKeyManager:
    """Get encryption manager singleton."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionKeyManager()
    return _encryption_manager


def encrypt_value(value: str, purpose: str = "default") -> str:
    """
    Encrypt a string value using Fernet symmetric encryption.

    Args:
        value: Plain text value to encrypt
        purpose: Encryption purpose for key derivation

    Returns:
        Base64-encoded encrypted string
    """
    if not value:
        return value

    manager = get_encryption_manager()
    fernet = manager.get_fernet(purpose)
    encrypted = fernet.encrypt(value.encode())
    return encrypted.decode()


def decrypt_value(encrypted_value: str, purpose: str = "default") -> str:
    """
    Decrypt an encrypted value.

    Args:
        encrypted_value: Base64-encoded encrypted string
        purpose: Encryption purpose for key derivation

    Returns:
        Decrypted plain text string

    Raises:
        InvalidToken: If decryption fails (wrong key or corrupted data)
    """
    if not encrypted_value:
        return encrypted_value

    manager = get_encryption_manager()
    fernet = manager.get_fernet(purpose)
    try:
        decrypted = fernet.decrypt(encrypted_value.encode())
        return decrypted.decode()
    except InvalidToken as e:
        # Log detailed error for debugging, but raise clear error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(
            f"Decryption failed for purpose='{purpose}'. "
            f"This usually means the SECURITY_SECRET_KEY has changed since the data was encrypted. "
            f"Check that your .env file contains the correct key."
        )
        raise InvalidToken(
            f"Unable to decrypt data: encryption key mismatch. "
            f"The SECURITY_SECRET_KEY may have changed since this data was encrypted. "
            f"Original error: {e}"
        ) from e


def encrypt_dict(data: dict, fields: list[str], purpose: str = "default") -> dict:
    """
    Encrypt specified fields in a dictionary.

    Args:
        data: Dictionary containing data to encrypt
        fields: List of field names to encrypt
        purpose: Encryption purpose for key derivation

    Returns:
        Dictionary with specified fields encrypted
    """
    result = data.copy()
    for field in fields:
        if field in result and result[field]:
            result[field] = encrypt_value(str(result[field]), purpose)
    return result


def decrypt_dict(data: dict, fields: list[str], purpose: str = "default") -> dict:
    """
    Decrypt specified fields in a dictionary.

    Args:
        data: Dictionary containing encrypted data
        fields: List of field names to decrypt
        purpose: Encryption purpose for key derivation

    Returns:
        Dictionary with specified fields decrypted
    """
    result = data.copy()
    for field in fields:
        if field in result and result[field]:
            try:
                result[field] = decrypt_value(result[field], purpose)
            except InvalidToken:
                # Field might not be encrypted (legacy data)
                pass
    return result


def encrypt_contact_info(contact: dict) -> dict:
    """
    Encrypt sensitive fields in contact information.

    Encrypts:
        - email
        - phone
        - mobile
        - wechat
        - qq

    Args:
        contact: Contact information dictionary

    Returns:
        Dictionary with sensitive fields encrypted
    """
    sensitive_fields = ["email", "phone", "mobile", "wechat", "qq"]
    return encrypt_dict(contact, sensitive_fields, purpose="contact")


def decrypt_contact_info(encrypted_contact: dict) -> dict:
    """
    Decrypt sensitive fields in contact information.

    Args:
        encrypted_contact: Contact info with encrypted fields

    Returns:
        Dictionary with sensitive fields decrypted
    """
    sensitive_fields = ["email", "phone", "mobile", "wechat", "qq"]
    return decrypt_dict(encrypted_contact, sensitive_fields, purpose="contact")


class SensitiveField:
    """
    Pydantic Field type for automatically encrypting sensitive data.
    Usage:
        class Agent(Base):
            email: SensitiveField = SensitiveField()
    """

    def __init__(
        self,
        purpose: str = "default",
        encrypted: bool = True,
        **kwargs,
    ):
        self.purpose = purpose
        self.encrypted = encrypted
        self.field_kwargs = kwargs

    def __repr__(self):
        return f"SensitiveField(purpose={self.purpose}, encrypted={self.encrypted})"


def mask_sensitive_value(value: str, visible_chars: int = 4) -> str:
    """
    Mask a sensitive value showing only last N characters.

    Args:
        value: Value to mask
        visible_chars: Number of characters to show at end

    Returns:
        Masked string like "****1234"
    """
    if not value or len(value) <= visible_chars:
        return "*" * len(value) if value else ""

    masked_length = len(value) - visible_chars
    return "*" * masked_length + value[-visible_chars:]


def mask_email(email: str) -> str:
    """Mask an email address."""
    if not email or "@" not in email:
        return mask_sensitive_value(email, 4)

    local, domain = email.rsplit("@", 1)
    masked_local = mask_sensitive_value(local, 3)
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask a phone number."""
    if not phone:
        return ""
    return mask_sensitive_value(phone, 4)


def generate_encrypted_field_hash(value: str) -> str:
    """
    Generate a hash of a sensitive field for lookup purposes.
    Uses HMAC-SHA256 with salt for secure, consistent lookups.

    Args:
        value: Value to hash

    Returns:
        Hex-encoded hash
    """
    import hashlib
    import hmac
    import os
    salt = os.environ.get("HASH_SALT", "")
    return hmac.new(salt.encode(), value.encode(), hashlib.sha256).hexdigest()


# Encryption service for use in services
class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    def __init__(self):
        self.manager = get_encryption_manager()

    def encrypt_contact(self, contact: dict) -> dict:
        """Encrypt contact information."""
        return encrypt_contact_info(contact)

    def decrypt_contact(self, encrypted_contact: dict) -> dict:
        """Decrypt contact information."""
        return decrypt_contact_info(encrypted_contact)

    def encrypt_field(self, value: str, purpose: str = "default") -> str:
        """Encrypt a single field."""
        return encrypt_value(value, purpose)

    def decrypt_field(self, encrypted_value: str, purpose: str = "default") -> str:
        """Decrypt a single field."""
        return decrypt_value(encrypted_value, purpose)


# Singleton instance
encryption_service = EncryptionService()
