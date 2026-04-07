"""
测试 Auth 核心服务
"""

import pytest
from datetime import datetime, timedelta, timezone
from app.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    generate_refresh_token_str,
    create_refresh_token_for_user,
)
from app.config import settings


@pytest.mark.auth
def test_password_hash_and_verify():
    """测试密码哈希和验证"""
    password = "test_password_123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


@pytest.mark.auth
def test_create_access_token():
    """测试创建 Access Token"""
    data = {"sub": "testuser"}
    token = create_access_token(data)

    assert token is not None
    assert isinstance(token, str)

    # 解码验证
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "testuser"
    assert "exp" in payload


@pytest.mark.auth
def test_decode_invalid_token():
    """测试解码无效 Token"""
    payload = decode_access_token("invalid_token")
    assert payload is None


@pytest.mark.auth
def test_generate_refresh_token_str():
    """测试生成 Refresh Token 字符串"""
    token = generate_refresh_token_str()

    assert token is not None
    assert isinstance(token, str)
    assert len(token) == 64
    # 不应该包含敏感信息
    assert "password" not in token.lower()


@pytest.mark.auth
def test_refresh_token_uniqueness():
    """测试生成的 Refresh Token 是唯一的"""
    tokens = set()
    for _ in range(100):
        token = generate_refresh_token_str()
        tokens.add(token)

    assert len(tokens) == 100, "所有生成的 token 应该是唯一的"


@pytest.mark.auth
def test_create_refresh_token_for_user():
    """测试为用户创建 Refresh Token"""
    token, expires_at = create_refresh_token_for_user(user_id=1)

    assert len(token) == 64
    expected_expires = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    assert abs((expires_at - expected_expires).total_seconds()) < 1
    assert isinstance(expires_at, datetime)
    assert expires_at.tzinfo == timezone.utc


@pytest.mark.auth
def test_create_refresh_token_for_user_invalid_id():
    """测试无效 user_id 抛出异常"""
    with pytest.raises(ValueError, match="user_id must be positive"):
        create_refresh_token_for_user(user_id=0)

    with pytest.raises(ValueError, match="user_id must be positive"):
        create_refresh_token_for_user(user_id=-1)
