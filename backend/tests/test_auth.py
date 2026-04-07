"""
认证模块测试
"""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)


@pytest.mark.auth
class TestPasswordHashing:
    """密码哈希测试"""

    def test_password_hash_creates_different_hashes(self):
        """测试相同密码生成不同哈希值（bcrypt加盐）"""
        password = "test_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        assert hash1 != password
        assert hash2 != password

    def test_verify_password_correct(self):
        """测试正确密码验证"""
        password = "test_password"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """测试错误密码验证"""
        password = "test_password"
        hashed = get_password_hash(password)

        assert verify_password("wrong_password", hashed) is False


@pytest.mark.auth
class TestJWTToken:
    """JWT令牌测试"""

    def test_create_access_token(self):
        """测试创建访问令牌"""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token_valid(self):
        """测试解码有效令牌"""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        payload = decode_access_token(token)

        assert payload is not None
        assert payload.get("sub") == "testuser"

    def test_decode_access_token_invalid(self):
        """测试解码无效令牌"""
        invalid_token = "invalid.token.here"

        payload = decode_access_token(invalid_token)

        assert payload is None


@pytest.mark.auth
class TestAuthEndpoints:
    """认证端点测试"""

    def test_register_user_success(self, client: TestClient):
        """测试成功注册用户"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "password": "password123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_register_user_duplicate_username(
        self, client: TestClient, db_session: Session
    ):
        """测试注册重复用户名"""
        # 先创建一个用户
        user = User(
            username="existinguser",
            password_hash=get_password_hash("password123"),
        )
        db_session.add(user)
        db_session.commit()

        # 尝试用相同用户名注册
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "existinguser",
                "password": "password456",
            },
        )

        assert response.status_code == 400
        assert "已被注册" in response.json()["detail"]

    def test_register_user_short_username(self, client: TestClient):
        """测试用户名太短"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "ab",  # 少于3个字符
                "password": "password123",
            },
        )

        assert response.status_code == 422

    def test_register_user_short_password(self, client: TestClient):
        """测试密码太短"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "password": "12345",  # 少于6个字符
            },
        )

        assert response.status_code == 422

    def test_login_success(self, client: TestClient, db_session: Session):
        """测试成功登录"""
        # 创建测试用户
        user = User(
            username="loginuser",
            password_hash=get_password_hash("password123"),
        )
        db_session.add(user)
        db_session.commit()

        # 登录
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "loginuser",
                "password": "password123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, db_session: Session):
        """测试错误密码登录"""
        user = User(
            username="loginuser",
            password_hash=get_password_hash("password123"),
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "loginuser",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """测试不存在的用户登录"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent",
                "password": "password123",
            },
        )

        assert response.status_code == 401

    def test_get_current_user_success(self, client: TestClient, db_session: Session):
        """测试获取当前用户信息"""
        # 创建测试用户
        user = User(
            username="meuser",
            password_hash=get_password_hash("password123"),
        )
        db_session.add(user)
        db_session.commit()

        # 登录获取token
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "meuser",
                "password": "password123",
            },
        )
        token = login_response.json()["access_token"]

        # 获取当前用户信息
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "meuser"
        assert data["is_active"] is True

    def test_get_current_user_no_token(self, client: TestClient):
        """测试无token获取用户信息"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """测试无效token获取用户信息"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code == 401


@pytest.mark.auth
class TestRefreshToken:
    """Refresh Token测试"""

    def test_login_without_remember_me(self, client: TestClient, db_session: Session):
        """测试登录（不记住我）"""
        user = User(
            username="auth_test_user",
            password_hash=get_password_hash("password123"),
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "auth_test_user",
                "password": "password123",
                "remember_me": "false",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" not in data
        assert data["token_type"] == "bearer"

    def test_login_with_remember_me(self, client: TestClient, db_session: Session):
        """测试登录（记住我）"""
        user = User(
            username="auth_test_user2",
            password_hash=get_password_hash("password123"),
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "auth_test_user2",
                "password": "password123",
                "remember_me": "true",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert len(data["refresh_token"]) > 20

    def test_login_wrong_password(self, client: TestClient, db_session: Session):
        """测试登录（密码错误）"""
        user = User(
            username="auth_test_user3",
            password_hash=get_password_hash("password123"),
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={"username": "auth_test_user3", "password": "wrong_password"},
        )

        assert response.status_code == 401

    def test_login_without_remember_me_param(
        self, client: TestClient, db_session: Session
    ):
        """测试登录（不提供remember_me参数）"""
        user = User(
            username="auth_test_user4",
            password_hash=get_password_hash("password123"),
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={"username": "auth_test_user4", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" not in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_success(
        self, client: TestClient, db_session: Session, test_user: User
    ):
        """测试刷新 Token 成功"""
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "auth_test_user",
                "password": "password123",
                "remember_me": "true",
            },
        )
        old_refresh_token = login_response.json()["refresh_token"]

        from app.crud.refresh_token import get_refresh_token

        old_token_obj = get_refresh_token(db_session, old_refresh_token)
        assert old_token_obj is not None

        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": old_refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["refresh_token"] != old_refresh_token

        db_session.refresh(old_token_obj)
        assert old_token_obj.is_revoked is True

    def test_refresh_token_invalid(self, client: TestClient):
        """测试刷新 Token（无效）"""
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == 401

    def test_refresh_token_expired(self, client: TestClient, db_session: Session):
        """测试刷新 Token（过期）"""
        from app.crud.refresh_token import create_refresh_token

        user = User(
            username="auth_test_user5",
            password_hash=get_password_hash("password123"),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        expired_token = "expired_test_token"
        expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        create_refresh_token(db_session, expired_token, int(user.id), expires_at)

        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": expired_token}
        )

        assert response.status_code == 401

    def test_refresh_token_revoked(self, client: TestClient, db_session: Session):
        """测试刷新已撤销的 Token"""
        from app.crud.refresh_token import create_refresh_token, revoke_refresh_token

        user = User(
            username="auth_test_user6",
            password_hash=get_password_hash("password123"),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        token = "revoked_test_token"
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        created = create_refresh_token(db_session, token, int(user.id), expires_at)

        revoke_refresh_token(db_session, int(created.id))

        response = client.post("/api/v1/auth/refresh", json={"refresh_token": token})

        assert response.status_code == 401
        assert "无效或过期" in response.json()["detail"]


@pytest.mark.auth
class TestLogout:
    """登出测试"""

    def test_logout_success(self, client: TestClient, db_session: Session):
        """测试登出成功"""
        user = User(
            username="logout_test_user",
            password_hash=get_password_hash("password123"),
        )
        db_session.add(user)
        db_session.commit()

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "logout_test_user",
                "password": "password123",
                "remember_me": "true",
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        response = client.post(
            "/api/v1/auth/logout", json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200

        refresh_response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

        assert refresh_response.status_code == 401

    def test_logout_invalid_token(self, client: TestClient):
        """测试登出（无效Token）"""
        response = client.post(
            "/api/v1/auth/logout", json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == 200


@pytest.mark.auth
class TestAuthEdgeCases:
    """认证边界测试"""

    def test_create_refresh_token_invalid_user_id(self, client: TestClient):
        """测试无效用户ID创建refresh token"""
        from app.core.auth import create_refresh_token_for_user

        try:
            create_refresh_token_for_user(user_id=0)
            assert False, "应该抛出异常"
        except ValueError as e:
            assert "user_id must be positive" in str(e)

    def test_get_users(self, client: TestClient, db_session: Session):
        """测试获取用户列表"""
        from app.crud.user import get_users, create_user
        from app.schemas.user import UserCreate

        user1 = create_user(
            db_session, UserCreate(username="user1", password="password123")
        )
        user2 = create_user(
            db_session, UserCreate(username="user2", password="password123")
        )

        users = get_users(db_session)
        assert len(users) >= 2
        usernames = [u.username for u in users]
        assert "user1" in usernames
        assert "user2" in usernames

    def test_delete_user(self, client: TestClient, db_session: Session):
        """测试删除用户"""
        from app.crud.user import create_user, delete_user, get_user
        from app.schemas.user import UserCreate

        user = create_user(
            db_session, UserCreate(username="delete_test_user", password="password123")
        )
        user_id = int(user.id)

        deleted = delete_user(db_session, user_id)
        assert deleted is True

        user = get_user(db_session, user_id)
        assert user is None

    def test_delete_nonexistent_user(self, client: TestClient, db_session: Session):
        """测试删除不存在的用户"""
        from app.crud.user import delete_user

        deleted = delete_user(db_session, 999999)
        assert deleted is False

    def test_update_user_active_status(self, client: TestClient, db_session: Session):
        """测试更新用户激活状态"""
        from app.crud.user import create_user, update_user_active_status, get_user
        from app.schemas.user import UserCreate

        user = create_user(
            db_session, UserCreate(username="status_test_user", password="password123")
        )
        assert user.is_active is True
        user_id = int(user.id)

        updated = update_user_active_status(db_session, user_id, False)
        assert updated is not None
        assert updated.is_active is False

        updated = update_user_active_status(db_session, user_id, True)
        assert updated is not None
        assert updated.is_active is True

    def test_update_nonexistent_user_status(
        self, client: TestClient, db_session: Session
    ):
        """测试更新不存在的用户状态"""
        from app.crud.user import update_user_active_status

        updated = update_user_active_status(db_session, 999999, False)
        assert updated is None
