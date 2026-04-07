"""
Refresh Token 模型
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class RefreshToken(Base):
    """Refresh Token 表"""

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    token = Column(
        String(255), unique=True, nullable=False, index=True, comment="Refresh Token"
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    is_revoked = Column(Boolean, default=False, comment="是否已撤销")

    user = relationship("User", back_populates="refresh_tokens")
