"""
用户相关 Pydantic Schema
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class UserBase(BaseModel):
    """用户基础模型"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")


class UserCreate(UserBase):
    """创建用户请求模型"""

    password: str = Field(..., min_length=6, max_length=100, description="密码")


class UserLogin(BaseModel):
    """登录请求模型"""

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserResponse(UserBase):
    """用户响应模型"""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token响应模型"""

    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class TokenData(BaseModel):
    """Token数据模型"""

    username: Optional[str] = None


class TokenResponse(BaseModel):
    """Token响应模型"""

    access_token: str = Field(..., description="访问令牌")
    refresh_token: Optional[str] = Field(default=None, description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class RefreshTokenRequest(BaseModel):
    """刷新Token请求模型"""

    refresh_token: str = Field(..., description="刷新令牌")


class RefreshTokenResponse(BaseModel):
    """刷新Token响应模型"""

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class LogoutRequest(BaseModel):
    """登出请求模型"""

    refresh_token: str = Field(..., description="刷新令牌")
