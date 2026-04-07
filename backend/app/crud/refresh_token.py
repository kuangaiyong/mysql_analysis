from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models.refresh_token import RefreshToken


def create_refresh_token(
    db: Session, token: str, user_id: int, expires_at: datetime
) -> RefreshToken:
    """
    创建 Refresh Token

    Args:
        db: 数据库会话
        token: Refresh Token 字符串
        user_id: 用户ID
        expires_at: 过期时间

    Returns:
        创建的 RefreshToken 对象
    """
    db_token = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def get_refresh_token(db: Session, token: str) -> Optional[RefreshToken]:
    """
    根据 Token 获取 Refresh Token

    Args:
        db: 数据库会话
        token: Refresh Token 字符串

    Returns:
        找到则返回 RefreshToken 对象，否则返回 None
    """
    return db.query(RefreshToken).filter(RefreshToken.token == token).first()


def verify_refresh_token(db: Session, token: str) -> Optional[RefreshToken]:
    """
    验证 Refresh Token 是否有效

    Args:
        db: 数据库会话
        token: Refresh Token 字符串

    Returns:
        Token 有效则返回 RefreshToken 对象，否则返回 None
    """
    db_token = get_refresh_token(db, token)
    if not db_token:
        return None
    if db_token.is_revoked:
        return None
    if db_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        return None
    return db_token


def revoke_refresh_token(db: Session, token_id: int) -> Optional[RefreshToken]:
    """
    撤销 Refresh Token

    Args:
        db: 数据库会话
        token_id: Refresh Token ID

    Returns:
        成功则返回撤销后的 RefreshToken 对象，不存在则返回 None
    """
    db_token = db.query(RefreshToken).filter(RefreshToken.id == token_id).first()
    if db_token:
        db_token.is_revoked = True
        db.commit()
        db.refresh(db_token)
    return db_token


def revoke_token_by_string(db: Session, token: str) -> bool:
    """
    通过 Token 字符串撤销

    Args:
        db: 数据库会话
        token: Refresh Token 字符串

    Returns:
        成功撤销返回 True，token 不存在返回 False
    """
    db_token = get_refresh_token(db, token)
    if db_token:
        revoke_refresh_token(db, db_token.id)
        return True
    return False
