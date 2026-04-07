"""
测试 Refresh Token CRUD 操作
"""

import pytest
from datetime import datetime, timedelta
from app.crud.refresh_token import (
    create_refresh_token,
    get_refresh_token,
    revoke_refresh_token,
    revoke_token_by_string,
    verify_refresh_token,
)
from app.models.user import User
from app.models.refresh_token import RefreshToken


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    from app.crud.user import create_user
    from app.schemas.user import UserCreate

    user = create_user(
        db_session, UserCreate(username="testuser", password="password123")
    )

    yield user

    db_session.delete(user)
    db_session.commit()


def test_create_refresh_token(db_session, test_user):
    """测试创建 Refresh Token"""
    token_str = "test_refresh_token_123"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    refresh_token = create_refresh_token(
        db_session, token_str, test_user.id, expires_at
    )

    assert refresh_token is not None
    assert refresh_token.token == token_str
    assert refresh_token.user_id == test_user.id
    assert refresh_token.is_revoked is False


def test_get_refresh_token(db_session, test_user):
    """测试获取 Refresh Token"""
    token_str = "test_refresh_token_456"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    created = create_refresh_token(db_session, token_str, test_user.id, expires_at)

    found = get_refresh_token(db_session, token_str)

    assert found is not None
    assert found.id == created.id
    assert found.token == token_str


def test_verify_valid_refresh_token(db_session, test_user):
    """测试验证有效的 Refresh Token"""
    token_str = "test_valid_token"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    create_refresh_token(db_session, token_str, test_user.id, expires_at)

    token_obj = verify_refresh_token(db_session, token_str)

    assert token_obj is not None
    assert token_obj.token == token_str
    assert token_obj.is_revoked is False


def test_verify_expired_refresh_token(db_session, test_user):
    """测试验证过期的 Refresh Token"""
    token_str = "test_expired_token"
    expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    create_refresh_token(db_session, token_str, test_user.id, expires_at)

    token_obj = verify_refresh_token(db_session, token_str)

    assert token_obj is None


def test_verify_revoked_refresh_token(db_session, test_user):
    """测试验证已撤销的 Refresh Token"""
    token_str = "test_revoked_token"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    refresh_token = create_refresh_token(
        db_session, token_str, test_user.id, expires_at
    )
    revoke_refresh_token(db_session, refresh_token.id)

    token_obj = verify_refresh_token(db_session, token_str)

    assert token_obj is None


def test_revoke_refresh_token(db_session, test_user):
    """测试撤销 Refresh Token"""
    token_str = "test_revoke_token"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    refresh_token = create_refresh_token(
        db_session, token_str, test_user.id, expires_at
    )

    revoked = revoke_refresh_token(db_session, refresh_token.id)

    assert revoked is not None
    assert revoked.is_revoked is True


def test_revoke_refresh_token_not_found(db_session):
    """测试撤销不存在的 Refresh Token"""
    revoked = revoke_refresh_token(db_session, 99999)
    assert revoked is None


def test_revoke_token_by_string(db_session, test_user):
    """测试通过 Token 字符串撤销"""
    token_str = "test_revoke_by_string"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    create_refresh_token(db_session, token_str, test_user.id, expires_at)

    revoked = revoke_token_by_string(db_session, token_str)

    assert revoked is True

    token_obj = get_refresh_token(db_session, token_str)
    assert token_obj is not None
    assert token_obj.is_revoked is True


def test_revoke_token_by_string_not_found(db_session):
    """测试通过不存在的 Token 字符串撤销"""
    revoked = revoke_token_by_string(db_session, "nonexistent_token")
    assert revoked is False


def test_create_refresh_token_with_created_at(db_session, test_user):
    """测试创建 Refresh Token 时设置 created_at"""
    before_create = datetime.now(timezone.utc)
    token_str = "test_created_at_token"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    refresh_token = create_refresh_token(
        db_session, token_str, test_user.id, expires_at
    )

    assert refresh_token.created_at is not None
    assert refresh_token.created_at >= before_create
    assert refresh_token.created_at <= datetime.now(timezone.utc)
