"""API key encryption/decryption — base64 XOR with local salt."""

import base64
from hashlib import sha256

_SALT_CACHE: str | None = None


def _get_salt() -> str:
    global _SALT_CACHE
    if _SALT_CACHE is not None:
        return _SALT_CACHE
    from backend.config import load_config

    cfg = load_config()
    _SALT_CACHE = cfg.get("crypto_salt", "")
    return _SALT_CACHE


def _derive_key(salt: str) -> bytes:
    """Derive a 32-byte key from the salt via SHA-256."""
    return sha256(salt.encode("utf-8")).digest()


def encrypt_api_key(plaintext: str) -> str:
    """XOR plaintext with derived key, then base64-encode."""
    key = _derive_key(_get_salt())
    plain_bytes = plaintext.encode("utf-8")
    key_repeated = (key * (len(plain_bytes) // len(key) + 1))[: len(plain_bytes)]
    encrypted = bytes(a ^ b for a, b in zip(plain_bytes, key_repeated))
    return base64.b64encode(encrypted).decode("ascii")


def decrypt_api_key(encoded: str) -> str:
    """Base64-decode then XOR with derived key to recover plaintext."""
    key = _derive_key(_get_salt())
    encrypted = base64.b64decode(encoded)
    key_repeated = (key * (len(encrypted) // len(key) + 1))[: len(encrypted)]
    decrypted = bytes(a ^ b for a, b in zip(encrypted, key_repeated))
    return decrypted.decode("utf-8")


def mask_api_key(api_key: str | None) -> str | None:
    """Return masked key — show only last 4 characters."""
    if api_key is None or len(api_key) <= 4:
        return api_key
    return "..." + api_key[-4:]
