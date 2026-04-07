"""
连接管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_session, Session as SessionType
from app.schemas.connection import (
    ConnectionCreate,
    ConnectionUpdate,
    ConnectionResponse,
    ConnectionTest,
)
from app.crud import connection as connection_crud
from app.services.mysql_connector import MySQLConnector

router = APIRouter()


@router.post(
    "/", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED
)
async def create_connection(
    connection: ConnectionCreate, db: SessionType = Depends(get_session)
):
    """创建新的数据库连接配置"""
    # 测试连接是否有效
    try:
        mysql_conn = MySQLConnector(
            host=connection.host,
            port=connection.port,
            user=connection.username,
            password=connection.password,
            database=connection.database_name,
        )
        mysql_conn.test_connection()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"数据库连接失败: {str(e)}"
        )

    # 创建连接记录
    return connection_crud.create_connection(db=db, connection=connection)


@router.get("/", response_model=List[ConnectionResponse])
async def list_connections(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    host: Optional[str] = None,
    database_name: Optional[str] = None,
    db: SessionType = Depends(get_session),
):
    """获取所有连接配置（支持搜索）"""
    return connection_crud.get_connections(
        db=db, skip=skip, limit=limit, name=name, host=host, database_name=database_name
    )


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(connection_id: int, db: SessionType = Depends(get_session)):
    """获取单个连接详情"""
    connection = connection_crud.get_connection(db=db, connection_id=connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="连接不存在")
    return connection


@router.put("/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: int,
    update_data: ConnectionUpdate,
    db: SessionType = Depends(get_session),
):
    """更新连接配置"""
    connection = connection_crud.update_connection(
        db=db, connection_id=connection_id, connection_update=update_data
    )
    if not connection:
        raise HTTPException(status_code=404, detail="连接不存在")
    return connection


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(connection_id: int, db: SessionType = Depends(get_session)):
    """删除连接配置"""
    success = connection_crud.delete_connection(db=db, connection_id=connection_id)
    if not success:
        raise HTTPException(status_code=404, detail="连接不存在")


@router.post("/test", status_code=status.HTTP_200_OK)
async def test_connection_endpoint(connection: ConnectionTest):
    """测试数据库连接"""
    try:
        mysql_conn = MySQLConnector(
            host=connection.host,
            port=connection.port,
            user=connection.username,
            password=connection.password,
            database=connection.database_name,
        )
        mysql_conn.test_connection()
        return {"status": "success", "message": "连接成功"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"连接失败: {str(e)}"
        )
