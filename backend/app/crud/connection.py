"""
连接 CRUD 操作
"""

from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional
from app.models.connection import Connection
from app.schemas.connection import ConnectionCreate, ConnectionUpdate


def get_connection(db: Session, connection_id: int) -> Optional[Connection]:
    """获取单个连接"""
    return db.execute(
        select(Connection).where(Connection.id == connection_id)
    ).scalar_one_or_none()


def get_connections(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    host: Optional[str] = None,
    database_name: Optional[str] = None,
) -> List[Connection]:
    """获取所有连接（支持搜索）"""
    query = select(Connection)

    if name:
        query = query.where(Connection.name.ilike(f"%{name}%"))
    if host:
        query = query.where(Connection.host.ilike(f"%{host}%"))
    if database_name:
        query = query.where(Connection.database_name.ilike(f"%{database_name}%"))

    return list(db.execute(query.offset(skip).limit(limit)).scalars().all())


def create_connection(db: Session, connection: ConnectionCreate) -> Connection:
    """创建连接"""
    connection_data = connection.model_dump()
    password = connection_data.pop("password", None)
    if password:
        connection_data["password_encrypted"] = password
    db_connection = Connection(**connection_data)
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    return db_connection


def update_connection(
    db: Session, connection_id: int, connection_update: ConnectionUpdate
) -> Optional[Connection]:
    """更新连接"""
    db_connection = get_connection(db, connection_id)
    if not db_connection:
        return None

    update_data = connection_update.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        if field == "password":
            setattr(db_connection, "password_encrypted", value)
        else:
            setattr(db_connection, field, value)

    db.commit()
    db.refresh(db_connection)
    return db_connection


def delete_connection(db: Session, connection_id: int) -> bool:
    """删除连接及其所有关联数据

    Args:
        db: 数据库会话
        connection_id: 连接ID

    Returns:
        True如果删除成功，False otherwise
    """
    from app.services.cascade_delete_service import cascade_delete_connection

    return cascade_delete_connection(db, connection_id)


def get_active_connections(db: Session) -> List[Connection]:
    """获取所有活跃的连接

    Args:
        db: 数据库会话

    Returns:
        活跃连接列表
    """
    query = select(Connection).where(Connection.is_active == True)
    return list(db.execute(query).scalars().all())
