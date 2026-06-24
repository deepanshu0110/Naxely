from __future__ import annotations
import hashlib
import secrets
import logging

logger = logging.getLogger(__name__)

KEY_PREFIX = "nax_"
KEY_LENGTH = 36


def generate_api_key() -> tuple[str, str, str, str]:
    raw_key = KEY_PREFIX + secrets.token_hex(16)
    key_prefix = raw_key[:8]
    key_suffix = raw_key[-4:]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, key_prefix, key_suffix, key_hash


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    computed = hashlib.sha256(raw_key.encode()).hexdigest()
    return secrets.compare_digest(computed, stored_hash)


def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()
