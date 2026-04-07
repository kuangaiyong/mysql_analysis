"""
JWT认证模块
实现JWT token生成、验证和密码哈希
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import secrets
import string

from jose import jwt, JWTError
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_session

# OAuth2密码流
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码

    Returns:
        密码是否匹配
    """
    # bcrypt限制密码长度为72字节
    password_bytes = plain_password.encode("utf-8")[:72]
    # 确保hashed_password是bytes
    hashed_bytes = (
        hashed_password.encode("utf-8")
        if isinstance(hashed_password, str)
        else hashed_password
    )
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_password_hash(password: str) -> str:
    """
    生成密码哈希

    Args:
        password: 明文密码

    Returns:
        哈希后的密码字符串
    """
    # bcrypt限制密码长度为72字节
    password_bytes = password.encode("utf-8")[:72]
    # 生成salt并哈希密码
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌

    Args:
        data: 要编码的数据（通常是 {"sub": username}）
        expires_delta: 过期时间增量

    Returns:
        JWT令牌字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码JWT令牌

    Args:
        token: JWT令牌字符串

    Returns:
        解码后的payload，无效时返回None
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_session)
) -> Any:
    """
    获取当前认证用户

    Args:
        token: JWT令牌
        db: 数据库会话

    Returns:
        User对象

    Raises:
        HTTPException: 认证失败时抛出401错误
    """
    from app.crud import user as user_crud

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = user_crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Any = Depends(get_current_user),
) -> Any:
    """
    获取当前活跃用户

    Args:
        current_user: 当前用户

    Returns:
        活跃的User对象

    Raises:
        HTTPException: 用户未激活时抛出400错误
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户未激活")
    return current_user


def generate_refresh_token_str() -> str:
    """
    生成随机 Refresh Token 字符串

    Returns:
        64字符的随机字符串
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(64))


def create_refresh_token_for_user(user_id: int) -> tuple[str, datetime]:
    """
    为用户创建 Refresh Token

    Args:
        user_id: 用户ID

    Returns:
        (token_string, expires_at)

    Raises:
        ValueError: 如果 user_id 或 refresh_token_expire_days 无效
    """
    if user_id <= 0:
        raise ValueError("user_id must be positive")

    if settings.refresh_token_expire_days <= 0:
        raise ValueError("refresh_token_expire_days must be positive")

    token_str = generate_refresh_token_str()
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    return token_str, expires_at
