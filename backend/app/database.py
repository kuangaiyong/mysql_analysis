"""
数据库连接管理模块
使用 SQLAlchemy ORM 管理数据库连接和Session
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from typing import Generator
from app.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy 基类"""

    pass


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.debug,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Generator[Session, None, None]:
    """
    依赖注入函数 - 获取数据库Session

    使用方法:
        @app.get("/api/items")
        async def get_items(db: Session = Depends(get_session)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 类型别名（用于类型提示）
from typing import Annotated
from fastapi import Depends

SessionDep = Annotated[Session, Depends(get_session)]


def init_db():
    """
    初始化数据库 - 创建所有表
    注意：生产环境应该使用Alembic迁移
    """
    Base.metadata.create_all(bind=engine)
