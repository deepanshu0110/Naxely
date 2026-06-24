import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from fastapi import HTTPException
from app.api import deps


def _user(tier: str, encrypted_api_key: str | None = None, api_key_iv: str | None = None):
    u = type('FakeUser', (), {})()
    u.tier = tier
    u.encrypted_api_key = encrypted_api_key
    u.api_key_iv = api_key_iv
    return u


class TestRequireProOrAbove:
    def test_pro_user_allowed(self):
        user = _user('pro')
        result = deps._check_tier(user, {'pro', 'agency'}, 'pro')
        assert result is user

    def test_agency_user_allowed(self):
        user = _user('agency')
        result = deps._check_tier(user, {'pro', 'agency'}, 'pro')
        assert result is user

    def test_free_user_blocked(self):
        user = _user('free')
        with pytest.raises(HTTPException) as exc:
            deps._check_tier(user, {'pro', 'agency'}, 'pro')
        assert exc.value.status_code == 403
        assert exc.value.detail['code'] == 'UPGRADE_REQUIRED'
        assert exc.value.detail['current_tier'] == 'free'
        assert exc.value.detail['required_tier'] == 'pro'

    def test_none_tier_defaults_to_free(self):
        user = _user(None)
        with pytest.raises(HTTPException) as exc:
            deps._check_tier(user, {'pro', 'agency'}, 'pro')
        assert exc.value.status_code == 403


class TestRequireAgency:
    def test_agency_user_allowed(self):
        user = _user('agency')
        result = deps._check_tier(user, {'agency'}, 'agency')
        assert result is user

    def test_pro_user_blocked(self):
        user = _user('pro')
        with pytest.raises(HTTPException) as exc:
            deps._check_tier(user, {'agency'}, 'agency')
        assert exc.value.status_code == 403
        assert exc.value.detail['code'] == 'UPGRADE_REQUIRED'
        assert exc.value.detail['current_tier'] == 'pro'
        assert exc.value.detail['required_tier'] == 'agency'

    def test_free_user_blocked(self):
        user = _user('free')
        with pytest.raises(HTTPException) as exc:
            deps._check_tier(user, {'agency'}, 'agency')
        assert exc.value.status_code == 403


class TestRequireByok:
    def test_free_user_without_key_allowed(self):
        user = _user('free')
        result = deps.require_byok(current_user=user)
        assert result is user

    def test_free_user_with_key_blocked(self):
        user = _user('free', encrypted_api_key='sekret', api_key_iv='iv')
        with pytest.raises(HTTPException) as exc:
            deps.require_byok(current_user=user)
        assert exc.value.status_code == 403
        assert exc.value.detail['code'] == 'UPGRADE_REQUIRED'

    def test_pro_user_with_key_allowed(self):
        user = _user('pro', encrypted_api_key='sekret', api_key_iv='iv')
        result = deps.require_byok(current_user=user)
        assert result is user
