"""
认证路由
提供登录、注册和Token验证端点
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_session
from app.schemas.user import (
    UserCreate,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutRequest,
)
from app.crud import user as user_crud
from app.crud.refresh_token import (
    create_refresh_token,
    verify_refresh_token,
    revoke_refresh_token,
    revoke_token_by_string,
)
from app.core.auth import (
    create_access_token,
    get_current_active_user,
    create_refresh_token_for_user,
)
from app.config import settings
from app.models.user import User

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="创建新用户账号。用户名必须唯一，密码将被加密存储。",
    responses={
        201: {"description": "用户创建成功"},
        400: {"description": "用户名已被注册"},
    },
)
async def register(user: UserCreate, db: Session = Depends(get_session)):
    """
    注册新用户

    - **username**: 用户名，必须唯一
    - **password**: 密码，将被加密存储
    """
    # 检查用户名是否已存在
    db_user = user_crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已被注册"
        )

    # 创建用户
    return user_crud.create_user(db=db, user=user)


@router.post(
    "/login",
    response_model=TokenResponse,
    response_model_exclude_unset=True,
    summary="用户登录",
    description="使用OAuth2密码流进行用户认证，返回JWT令牌。如果remember_me=true，将同时返回refresh_token（7天过期）。",
    responses={
        200: {"description": "登录成功"},
        401: {"description": "用户名或密码错误"},
    },
)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_session),
):
    """
    用户登录

    使用OAuth2密码流，返回JWT令牌和Refresh Token

    - **username**: 用户名
    - **password**: 密码
    - **remember_me**: 可选，设为'true'时返回refresh_token（7天过期）

    返回:
    - access_token: JWT访问令牌（30分钟过期）
    - token_type: 固定为'bearer'
    - refresh_token: 可选，刷新令牌（仅当remember_me=true时返回）
    """
    user = user_crud.authenticate_user(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    form = await request.form()
    remember_me = form.get("remember_me")

    response_data = {"access_token": access_token, "token_type": "bearer"}

    if remember_me == "true":
        refresh_token_str, expires_at = create_refresh_token_for_user(int(user.id))
        create_refresh_token(db, refresh_token_str, int(user.id), expires_at)
        response_data["refresh_token"] = refresh_token_str

    return TokenResponse(**response_data)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="获取当前用户信息",
    description="获取当前已认证用户的详细信息。需要Bearer Token认证。",
    responses={
        200: {"description": "用户信息"},
        401: {"description": "未认证或Token无效"},
    },
)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    获取当前用户信息（验证Token有效性）

    需要在请求头中携带有效的Bearer Token。
    用于验证Token有效性和获取用户信息。
    """
    return current_user


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="刷新访问令牌",
    description="使用Refresh Token获取新的Access Token和Refresh Token。旧的Refresh Token将被撤销。",
    responses={
        200: {"description": "令牌刷新成功"},
        401: {"description": "无效或过期的刷新令牌"},
    },
)
async def refresh_token(
    request: RefreshTokenRequest, db: Session = Depends(get_session)
):
    """
    刷新 Access Token

    使用 Refresh Token 获取新的 Access Token 和 Refresh Token

    - **refresh_token**: 有效的刷新令牌

    返回:
    - access_token: 新的JWT访问令牌
    - refresh_token: 新的刷新令牌（旧的将被撤销）
    - token_type: 固定为'bearer'
    """
    refresh_token_obj = verify_refresh_token(db, request.refresh_token)
    if not refresh_token_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的刷新令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = user_crud.get_user(db, refresh_token_obj.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    revoke_refresh_token(db, refresh_token_obj.id)

    new_refresh_token_str, new_expires_at = create_refresh_token_for_user(user.id)
    create_refresh_token(db, new_refresh_token_str, user.id, new_expires_at)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token_str,
        "token_type": "bearer",
    }


@router.post(
    "/logout",
    summary="用户登出",
    description="撤销Refresh Token，用户需要重新登录获取新的令牌。",
    responses={
        200: {"description": "登出成功"},
        401: {"description": "未认证"},
    },
)
async def logout(request: LogoutRequest, db: Session = Depends(get_session)):
    """
    用户登出

    撤销 Refresh Token，使刷新令牌失效

    - **refresh_token**: 要撤销的刷新令牌
    """
    revoke_token_by_string(db, request.refresh_token)

    return {"message": "登出成功"}
