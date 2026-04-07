"""
测试 RefreshToken 模型
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.models.refresh_token import RefreshToken


@pytest.fixture(scope="function")
def test_user(db_session: Session):
    """创建测试用户fixture"""
    user = User(
        username="test_user",
        password_hash="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    yield user

    db_session.delete(user)
    db_session.commit()


@pytest.fixture(scope="function")
def test_refresh_token(db_session: Session, test_user: User):
    """创建测试RefreshToken fixture"""
    token = RefreshToken(
        token="test_token_123",
        user_id=test_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        is_revoked=False,
    )
    db_session.add(token)
    db_session.commit()
    db_session.refresh(token)
    return token


class TestRefreshTokenModel:
    """RefreshToken 模型测试"""

    def test_create_refresh_token(self, db_session: Session, test_user: User):
        """测试创建RefreshToken"""
        token = RefreshToken(
            token="test_token_123",
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)

        assert token.id is not None
        assert token.token == "test_token_123"
        assert token.user_id == test_user.id
        assert token.is_revoked is False

    def test_refresh_token_defaults(self, db_session: Session, test_user: User):
        """测试RefreshToken默认值"""
        token = RefreshToken(
            token="test_token_456",
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db_session.add(token)
        db_session.commit()

        assert token.is_revoked is False
        assert token.created_at is not None
        assert isinstance(token.created_at, datetime)

    def test_refresh_token_to_user_relationship(
        self, db_session: Session, test_user: User
    ):
        """测试RefreshToken与User的关系"""
        token = RefreshToken(
            token="test_token_789",
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)

        assert token.user_id == test_user.id
        assert token.user is not None
        assert token.user.username == "test_user"

    def test_user_has_refresh_tokens(self, db_session: Session, test_user: User):
        """测试User包含refresh_tokens关系"""
        token1 = RefreshToken(
            token="token_1",
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        token2 = RefreshToken(
            token="token_2",
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db_session.add_all([token1, token2])
        db_session.commit()
        db_session.refresh(test_user)

        assert len(test_user.refresh_tokens) == 2
        assert test_user.refresh_tokens[0].token == "token_1"
        assert test_user.refresh_tokens[1].token == "token_2"

    def test_cascade_delete_user_deletes_tokens(
        self, db_session: Session, test_user: User
    ):
        """测试删除用户级联删除RefreshTokens"""
        token1 = RefreshToken(
            token="token_cascade_1",
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        token2 = RefreshToken(
            token="token_cascade_2",
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db_session.add_all([token1, token2])
        db_session.commit()

        # 验证token存在
        tokens_before = (
            db_session.query(RefreshToken)
            .filter(RefreshToken.user_id == test_user.id)
            .all()
        )
        assert len(tokens_before) == 2

        # 删除用户
        db_session.delete(test_user)
        db_session.commit()

        # 验证tokens被级联删除
        tokens_after = (
            db_session.query(RefreshToken)
            .filter(RefreshToken.user_id == test_user.id)
            .all()
        )
        assert len(tokens_after) == 0

    def test_unique_token_constraint(self, db_session: Session, test_user: User):
        """测试token唯一约束"""
        token1 = RefreshToken(
            token="duplicate_token",
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db_session.add(token1)
        db_session.commit()

        token2 = RefreshToken(
            token="duplicate_token",
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db_session.add(token2)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

    def test_is_revoked_can_be_modified(self, db_session: Session, test_user: User):
        """测试is_revoked字段可以被修改"""
        token = RefreshToken(
            token="revoke_token",
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            is_revoked=False,
        )
        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)

        assert token.is_revoked is False

        # 修改is_revoked
        token.is_revoked = True
        db_session.commit()
        db_session.refresh(token)

        assert token.is_revoked is True

    def test_expired_token(self, db_session: Session, test_user: User):
        """测试过期token"""
        token = RefreshToken(
            token="expired_token",
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)

        assert token.expires_at < datetime.now(timezone.utc)
