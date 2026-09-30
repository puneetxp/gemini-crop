"""
Encryption utilities for sensitive data at rest
Uses AES-256-GCM for field-level encryption
"""

import base64
import logging
import os
from typing import Optional

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings

logger = logging.getLogger(__name__)


class FieldEncryption:
    """
    Field-level encryption for sensitive database fields
    Uses AES-256-GCM for authenticated encryption
    """

    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize encryption with secret key

        Args:
            secret_key: Base secret key (uses settings.SECRET_KEY if not provided)
        """
        self.secret_key = secret_key or settings.SECRET_KEY

        # Derive a 256-bit key from the secret key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=b"cropsense-encryption-salt",  # Static salt for key derivation
            iterations=100000,
            backend=default_backend(),
        )
        self.key = kdf.derive(self.secret_key.encode())
        self.aesgcm = AESGCM(self.key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string value

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted value with nonce
        """
        if not plaintext:
            return plaintext

        try:
            # Generate a random 96-bit nonce (12 bytes)
            nonce = os.urandom(12)

            # Encrypt the plaintext
            ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode(), None)

            # Combine nonce + ciphertext and encode as base64
            encrypted_data = nonce + ciphertext
            return base64.b64encode(encrypted_data).decode("utf-8")

        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise ValueError("Failed to encrypt data")

    def decrypt(self, encrypted_value: str) -> str:
        """
        Decrypt an encrypted string value

        Args:
            encrypted_value: Base64-encoded encrypted value

        Returns:
            Decrypted plaintext string
        """
        if not encrypted_value:
            return encrypted_value

        try:
            # Decode from base64
            encrypted_data = base64.b64decode(encrypted_value.encode("utf-8"))

            # Extract nonce (first 12 bytes) and ciphertext
            nonce = encrypted_data[:12]
            ciphertext = encrypted_data[12:]

            # Decrypt
            plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode("utf-8")

        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise ValueError("Failed to decrypt data")

    def encrypt_if_not_encrypted(self, value: str) -> str:
        """
        Encrypt value only if it's not already encrypted
        Useful for migrations and updates

        Args:
            value: String value to encrypt

        Returns:
            Encrypted value
        """
        if not value:
            return value

        # Check if already encrypted (base64 encoded with proper length)
        try:
            decoded = base64.b64decode(value.encode("utf-8"))
            if len(decoded) > 12:  # Has nonce + ciphertext
                # Likely already encrypted, return as-is
                return value
        except Exception:
            pass

        # Not encrypted, encrypt it
        return self.encrypt(value)


# Global encryption instance
_encryption_instance: Optional[FieldEncryption] = None


def get_encryption() -> FieldEncryption:
    """Get or create global encryption instance"""
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = FieldEncryption()
    return _encryption_instance


def encrypt_field(value: str) -> str:
    """Convenience function to encrypt a field value"""
    return get_encryption().encrypt(value)


def decrypt_field(value: str) -> str:
    """Convenience function to decrypt a field value"""
    return get_encryption().decrypt(value)


# Sensitive field names that should be encrypted
SENSITIVE_FIELDS = {
    "password",
    "phone",
    "email",
    "contact_phone",
    "contact_email",
    "farmer_contact_phone",
    "farmer_contact_email",
    "buyer_contact_phone",
    "buyer_contact_email",
    "address",
    "bank_account",
    "payment_info",
}


def is_sensitive_field(field_name: str) -> bool:
    """
    Check if a field name indicates sensitive data

    Args:
        field_name: Name of the field

    Returns:
        True if field should be encrypted
    """
    field_lower = field_name.lower()

    # Check exact matches
    if field_lower in SENSITIVE_FIELDS:
        return True

    # Check partial matches
    sensitive_keywords = ["password", "phone", "email", "contact", "bank", "payment", "ssn", "tax"]
    return any(keyword in field_lower for keyword in sensitive_keywords)
