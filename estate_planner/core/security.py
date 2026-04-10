"""
Security module — Fernet encryption with key stored in OS keychain.

The encryption key is generated once and stored in Windows Credential Manager
(or macOS Keychain / Linux SecretService) via the `keyring` library.
It never touches disk. All sensitive JSON files are encrypted at rest.
"""
import os
import keyring
from cryptography.fernet import Fernet

_SERVICE = "EstatePath"
_KEY_NAME = "data_encryption_key"


def _get_or_create_key() -> bytes:
    """Retrieve the Fernet key from OS keychain, creating it if absent."""
    stored = keyring.get_password(_SERVICE, _KEY_NAME)
    if stored is None:
        key = Fernet.generate_key().decode()
        keyring.set_password(_SERVICE, _KEY_NAME, key)
        return key.encode()
    return stored.encode()


def encrypt(plaintext: str) -> bytes:
    """Encrypt a UTF-8 string and return ciphertext bytes."""
    return Fernet(_get_or_create_key()).encrypt(plaintext.encode("utf-8"))


def decrypt(ciphertext: bytes) -> str:
    """Decrypt ciphertext bytes and return a UTF-8 string."""
    return Fernet(_get_or_create_key()).decrypt(ciphertext).decode("utf-8")


def key_available() -> bool:
    """Return True if the keychain is accessible (sanity check on startup)."""
    try:
        _get_or_create_key()
        return True
    except Exception:
        return False
