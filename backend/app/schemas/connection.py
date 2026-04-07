"""
连接配置 Pydantic Schema
"""

from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import Optional


class ConnectionBase(BaseModel):
    """连接基础模型"""

    name: str = Field(..., min_length=1, max_length=100, description="连接名称")
    host: str = Field(..., description="主机地址")
    port: int = Field(default=3306, ge=1, le=65535, description="端口")
    username: str = Field(..., min_length=1, max_length=100, description="用户名")
    password: str = Field(..., min_length=1, description="密码")
    database_name: Optional[str] = Field(None, max_length=100, description="数据库名")
    connection_pool_size: int = Field(
        default=10, ge=1, le=100, description="连接池大小"
    )
    is_active: bool = Field(default=True, description="是否启用")

    @validator("name")
    def validate_name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("连接名称不能为空或仅包含空白字符")
        return v.strip()


class ConnectionCreate(ConnectionBase):
    """创建连接请求模型"""

    pass


class ConnectionTest(BaseModel):
    """测试连接请求模型"""

    host: str = Field(..., description="主机地址")
    port: int = Field(default=3306, ge=1, le=65535, description="端口")
    username: str = Field(..., min_length=1, max_length=100, description="用户名")
    password: str = Field(..., min_length=1, description="密码")
    database_name: Optional[str] = Field(None, max_length=100, description="数据库名")


class ConnectionUpdate(BaseModel):
    """更新连接请求模型"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    host: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=1)
    database_name: Optional[str] = Field(None, max_length=100)
    connection_pool_size: Optional[int] = Field(None, ge=1, le=100)


class ConnectionResponse(BaseModel):
    """连接响应模型"""

    id: int
    name: str
    host: str
    port: int
    username: str
    database_name: Optional[str]
    connection_pool_size: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
