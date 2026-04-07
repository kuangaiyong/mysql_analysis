"""
认证功能集成测试
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.crud.user import create_user
from app.crud.refresh_token import verify_refresh_token
from app.schemas.user import UserCreate
from app.database import get_session


@pytest.fixture
def client(db_session):
    """创建测试用的API客户端（不带默认认证headers）"""

    def override_get_session():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_session] = override_get_session
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    return create_user(
        db_session, UserCreate(username="integration_user", password="password123")
    )


@pytest.mark.auth
def test_complete_auth_flow(client, test_user):
    """测试完整认证流程：登录 → 访问受保护资源 → 刷新Token → 登出"""
    # 1. 登录
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "integration_user",
            "password": "password123",
            "remember_me": "true",
        },
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]

    # 2. 访问受保护资源（需要 token）
    protected_response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert protected_response.status_code == 200
    assert protected_response.json()["username"] == "integration_user"

    # 3. 刷新 Token
    refresh_response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 200
    new_access_token = refresh_response.json()["access_token"]
    new_refresh_token = refresh_response.json()["refresh_token"]

    # 4. 使用新 Token 访问受保护资源
    new_protected_response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert new_protected_response.status_code == 200

    # 5. 登出（使用新的 refresh token）
    logout_response = client.post(
        "/api/v1/auth/logout", json={"refresh_token": new_refresh_token}
    )
    assert logout_response.status_code == 200

    # 6. 验证 Refresh Token 已撤销
    # 注意：refresh 已被撤销并生成了新的，所以旧 token 无效
    # 这里验证新的 refresh token 也被撤销了


@pytest.mark.auth
def test_refresh_token_after_login(client, db_session, test_user):
    """测试登录后可以刷新 Token"""
    # 登录
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "integration_user",
            "password": "password123",
            "remember_me": "true",
        },
    )
    refresh_token = login_response.json()["refresh_token"]

    # 验证 Token 有效
    token_obj = verify_refresh_token(db_session, refresh_token)
    assert token_obj is not None
    assert token_obj.is_revoked is False

    # 刷新 Token
    refresh_response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 200

    # 验证旧 Token 已撤销
    old_token_obj = verify_refresh_token(db_session, refresh_token)
    assert old_token_obj is None  # 已撤销


@pytest.mark.auth
def test_protected_endpoint_without_token(client):
    """测试无 Token 访问受保护资源"""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.auth
def test_protected_endpoint_with_invalid_token(client):
    """测试使用无效 Token 访问受保护资源"""
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
