"""
数据库与 Redis 连接管理模块
"""

from typing import Annotated, Generator, Optional

from fastapi import Depends
from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy 基类"""


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.debug,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_redis_client: Optional[Redis] = None


def get_session() -> Generator[Session, None, None]:
    """依赖注入函数 - 获取数据库 Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SessionDep = Annotated[Session, Depends(get_session)]


def _build_redis_client() -> Optional[Redis]:
    if not settings.redis_url:
        return None

    try:
        client = Redis.from_url(
            settings.redis_url,
            password=settings.redis_password or None,
            decode_responses=True,
        )
        client.ping()
        return client
    except Exception:
        return None


def get_redis() -> Optional[Redis]:
    """获取 Redis 客户端，不可用时返回 None"""
    global _redis_client
    if _redis_client is None:
        _redis_client = _build_redis_client()
    return _redis_client


def reset_redis_client() -> None:
    """测试或重载场景下重置 Redis 客户端"""
    global _redis_client
    _redis_client = None


def init_db() -> None:
    """初始化数据库 - 开发环境允许自动建表"""
    Base.metadata.create_all(bind=engine)
