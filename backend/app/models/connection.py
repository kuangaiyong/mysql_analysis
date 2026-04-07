"""
MySQL连接配置表
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime
from sqlalchemy.orm import Session
from app.database import Base

class Connection(Base):
    """MySQL连接配置表"""

    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(100), nullable=False, comment="连接名称")
    host = Column(String(255), nullable=False, comment="主机地址")
    port = Column(Integer, default=3306, comment="端口")
    username = Column(String(100), nullable=False, comment="用户名")
    password_encrypted = Column(Text, comment="加密密码")
    database_name = Column(String(100), comment="数据库名")
    connection_pool_size = Column(Integer, default=10, comment="连接池大小")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

