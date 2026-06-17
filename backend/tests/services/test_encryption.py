import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from app.utils.encryption import encrypt_api_key, decrypt_api_key, get_master_key


class TestEncryptionRoundTrip:
    def test_get_master_key_returns_32_bytes(self):
        key = get_master_key()
        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_get_master_key_invalid_length(self):
        import os as _os
        from app.core.config import settings
        orig = settings.MASTER_ENCRYPTION_KEY
        settings.MASTER_ENCRYPTION_KEY = "short"
        with pytest.raises(ValueError, match="exactly 64"):
            get_master_key()
        settings.MASTER_ENCRYPTION_KEY = orig

    def test_encrypt_decrypt_round_trip(self):
        master_key = get_master_key()
        original = "sk-proj-my-real-api-key-1234567890"
        encrypted, iv = encrypt_api_key(original, master_key)
        assert isinstance(encrypted, str)
        assert isinstance(iv, str)
        assert encrypted != original
        decrypted = decrypt_api_key(encrypted, iv, master_key)
        assert decrypted == original

    def test_wrong_key_fails(self):
        key_a = get_master_key()
        import os as _os
        key_b = _os.urandom(32)
        original = "sk-ant-my-claude-key"
        encrypted, iv = encrypt_api_key(original, key_a)
        with pytest.raises(Exception):
            decrypt_api_key(encrypted, iv, key_b)

    def test_different_iv_each_time(self):
        master_key = get_master_key()
        original = "same-key"
        enc1, iv1 = encrypt_api_key(original, master_key)
        enc2, iv2 = encrypt_api_key(original, master_key)
        assert iv1 != iv2
        assert enc1 != enc2