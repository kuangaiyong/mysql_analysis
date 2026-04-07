"""
用户CRUD操作
"""

from sqlalchemy.orm import Session
from typing import Optional
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.auth import get_password_hash, verify_password


def get_user(db: Session, user_id: int) -> Optional[User]:
    """根据ID获取用户"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """根据用户名获取用户"""
    return db.query(User).filter(User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """获取用户列表"""
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    """创建新用户"""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        password_hash=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    验证用户凭据

    Args:
        db: 数据库会话
        username: 用户名
        password: 明文密码

    Returns:
        验证成功返回User对象，失败返回None
    """
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def update_user_active_status(
    db: Session, user_id: int, is_active: bool
) -> Optional[User]:
    """更新用户激活状态"""
    user = get_user(db, user_id)
    if user:
        user.is_active = is_active
        db.commit()
        db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    """删除用户"""
    user = get_user(db, user_id)
    if user:
        db.delete(user)
        db.commit()
        return True
    return False
