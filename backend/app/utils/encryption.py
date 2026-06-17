import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import settings


def get_master_key() -> bytes:
    # WARNING: If MASTER_ENCRYPTION_KEY is lost (not rotated), all
    # stored user API keys become permanently undecryptable. No
    # recovery path exists. Back up the key securely outside Render
    # env vars (e.g. a password manager) before any production deploy.
    hex_key = settings.MASTER_ENCRYPTION_KEY
    if len(hex_key) != 64:
        raise ValueError("MASTER_ENCRYPTION_KEY must be exactly 64 hex characters (32 bytes)")
    return bytes.fromhex(hex_key)


def encrypt_api_key(plaintext: str, master_key: bytes) -> tuple[str, str]:
    iv = os.urandom(12)
    aesgcm = AESGCM(master_key)
    ciphertext = aesgcm.encrypt(iv, plaintext.encode(), None)
    return base64.b64encode(ciphertext).decode(), base64.b64encode(iv).decode()


def decrypt_api_key(encrypted_b64: str, iv_b64: str, master_key: bytes) -> str:
    ciphertext = base64.b64decode(encrypted_b64)
    iv = base64.b64decode(iv_b64)
    aesgcm = AESGCM(master_key)
    return aesgcm.decrypt(iv, ciphertext, None).decode()
