import pytest
from unittest.mock import patch, MagicMock
from jose import JWTError


class TestValidateUrlScheme:
    def test_valid_http(self):
        from app.core.security import _validate_url_scheme
        _validate_url_scheme("http://example.com")

    def test_valid_https(self):
        from app.core.security import _validate_url_scheme
        _validate_url_scheme("https://example.com")

    def test_invalid_scheme(self):
        from app.core.security import _validate_url_scheme
        with pytest.raises(ValueError, match="URL scheme"):
            _validate_url_scheme("ftp://example.com")

    def test_empty_scheme(self):
        from app.core.security import _validate_url_scheme
        with pytest.raises(ValueError, match="URL scheme"):
            _validate_url_scheme("example.com")

    def test_javascript_scheme_rejected(self):
        from app.core.security import _validate_url_scheme
        with pytest.raises(ValueError, match="URL scheme"):
            _validate_url_scheme("javascript:alert(1)")


class TestGetJwks:
    def teardown_method(self):
        import app.core.security as sec
        sec._jwks = []
        sec._jwks_fetched_at = 0.0

    @patch("app.core.security.urlopen")
    def test_fetch_jwks_success(self, mock_urlopen):
        from app.core.security import _get_jwks

        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"keys": [{"kid": "test-kid"}]}'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        keys = _get_jwks()
        assert len(keys) == 1
        assert keys[0]["kid"] == "test-kid"

    @patch("app.core.security.urlopen")
    def test_fetch_jwks_returns_cached(self, mock_urlopen):
        from app.core.security import _get_jwks

        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"keys": [{"kid": "cached-kid"}]}'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        _get_jwks()
        mock_urlopen.reset_mock()
        keys = _get_jwks()
        assert keys[0]["kid"] == "cached-kid"
        mock_urlopen.assert_not_called()

    @patch("app.core.security.urlopen", side_effect=Exception("Network error"))
    def test_fetch_jwks_failure_raises_when_cache_empty(self, mock_urlopen):
        from app.core.security import _get_jwks
        with pytest.raises(Exception, match="Network error"):
            _get_jwks()

    @patch("app.core.security.urlopen", side_effect=Exception("Network error"))
    def test_fetch_jwks_failure_returns_cache_when_populated(self, mock_urlopen):
        from app.core.security import _get_jwks

        import app.core.security as sec
        sec._jwks = [{"kid": "old-cached"}]
        sec._jwks_fetched_at = 1.0

        keys = _get_jwks()
        assert keys[0]["kid"] == "old-cached"

    @patch("app.core.security._validate_url_scheme", side_effect=ValueError("Bad URL"))
    def test_fetch_jwks_validate_url_failure(self, mock_validate):
        from app.core.security import _get_jwks
        import app.core.security as sec
        sec._jwks = []
        sec._jwks_fetched_at = 0.0

        with pytest.raises(ValueError, match="Bad URL"):
            _get_jwks()


class TestVerifySupabaseJwt:
    def _valid_jwk(self):
        return {
            "kty": "RSA",
            "kid": "test-kid",
            "alg": "RS256",
            "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMsst64eVv5B2MaxhOkaZETlKHhqqFh6iV1hK7lXz0EJS72Z3UzjVh3CV0l4Qk2UjB6jPqMXu0nJeUVjD0kRmBgF0u4y7Z3rBxNn47fLMq1CJjqRpiq3qVzGvyGxjJKwp2fuKQq4a_GuX0b4oFJpMqE9k8FPWHqE0IqB1n5qF3L8nuKm7DhXo8r1dDZwplJNRKWWjmHf0gdMIxEAcWQKCkI5CRaPBYGqzQ",
            "e": "AQAB",
        }

    @patch("app.core.security.jwt.get_unverified_header")
    @patch("app.core.security.jwt.decode")
    @patch("app.core.security.jwk.construct")
    @patch("app.core.security._get_jwks")
    def test_verify_success(self, mock_get_jwks, mock_jwk_construct, mock_decode, mock_get_header):
        from app.core.security import verify_supabase_jwt

        mock_get_header.return_value = {"kid": "test-kid", "alg": "RS256"}
        mock_get_jwks.return_value = [self._valid_jwk()]
        mock_jwk_construct.return_value = MagicMock()
        mock_decode.return_value = {"sub": "user-123", "aud": ""}

        result = verify_supabase_jwt("valid.token.here")
        assert result["sub"] == "user-123"

    @patch("app.core.security.jwt.get_unverified_header")
    def test_verify_missing_kid(self, mock_get_header):
        from app.core.security import verify_supabase_jwt
        from fastapi import HTTPException

        mock_get_header.return_value = {"alg": "RS256"}

        with pytest.raises(HTTPException) as exc:
            verify_supabase_jwt("token.no.kid")
        assert exc.value.status_code == 401

    @patch("app.core.security.jwt.get_unverified_header")
    @patch("app.core.security._get_jwks")
    def test_verify_no_matching_key(self, mock_get_jwks, mock_get_header):
        from app.core.security import verify_supabase_jwt
        from fastapi import HTTPException

        mock_get_header.return_value = {"kid": "unknown-kid"}
        mock_get_jwks.return_value = [{"kid": "different-kid"}]

        with pytest.raises(HTTPException) as exc:
            verify_supabase_jwt("token.no.match")
        assert exc.value.status_code == 401

    @patch("app.core.security.jwt.get_unverified_header")
    def test_verify_malformed_token(self, mock_get_header):
        from app.core.security import verify_supabase_jwt
        from fastapi import HTTPException

        mock_get_header.side_effect = JWTError("Malformed token")

        with pytest.raises(HTTPException) as exc:
            verify_supabase_jwt("bad.token")
        assert exc.value.status_code == 401

    @patch("app.core.security.jwt.get_unverified_header")
    @patch("app.core.security._get_jwks", side_effect=Exception("JWKS failure"))
    def test_verify_jwks_fetch_failure(self, mock_get_jwks, mock_get_header):
        from app.core.security import verify_supabase_jwt
        from fastapi import HTTPException

        mock_get_header.return_value = {"kid": "test-kid"}

        with pytest.raises(HTTPException) as exc:
            verify_supabase_jwt("token.jwks.fail")
        assert exc.value.status_code == 401


class TestVerifySupabaseJwtHttpExceptionPropagation:
    """Covers line 68: except HTTPException: raise — verifies HTTPException
    from jwt.get_unverified_header propagates without being caught by the
    generic except Exception handler."""

    @patch("app.core.security.jwt.get_unverified_header")
    def test_http_exception_raised_by_get_unverified_header_propagates(
        self, mock_get_header
    ):
        from app.core.security import verify_supabase_jwt
        from fastapi import HTTPException

        mock_get_header.side_effect = HTTPException(status_code=401)

        with pytest.raises(HTTPException) as exc:
            verify_supabase_jwt("some.token")

        assert exc.value.status_code == 401
