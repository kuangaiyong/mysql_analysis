"""
连接管理测试
测试所有连接相关的API端点
"""

import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.connection import Connection


def test_create_connection_success(client: TestClient, mock_mysql_connector):
    """测试创建连接成功"""
    response = client.post(
        "/api/v1/connections/",
        json={
            "name": "测试连接",
            "host": "localhost",
            "port": 3306,
            "username": "root",
            "password": "test_password",
            "database_name": "test_db",
            "connection_pool_size": 10,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "测试连接"
    assert data["host"] == "localhost"
    assert data["port"] == 3306


def test_create_connection_invalid_data(client: TestClient):
    """测试创建连接 - 无效数据"""
    response = client.post(
        "/api/v1/connections/",
        json={
            "name": "",  # 无效：空名称
            "host": "localhost",
            "port": 3306,
            "username": "root",
            "password": "test_password",
        },
    )
    assert response.status_code in [422, 400]  # Unprocessable Entity


def test_create_connection_missing_required_field(client: TestClient):
    """测试创建连接 - 缺少必填字段"""
    response = client.post(
        "/api/v1/connections/",
        json={
            "name": "测试连接",
            "host": "localhost",
            "port": 3306,
            # 缺少 username 和 password
        },
    )
    assert response.status_code in [422, 400]


def test_create_connection_invalid_port(client: TestClient):
    """测试创建连接 - 无效端口"""
    response = client.post(
        "/api/v1/connections/",
        json={
            "name": "测试连接",
            "host": "localhost",
            "port": 99999,  # 超出范围
            "username": "root",
            "password": "test_password",
        },
    )
    assert response.status_code in [422, 400]


def test_list_connections_empty(client: TestClient):
    """测试获取连接列表 - 空列表"""
    response = client.get("/api/v1/connections/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_list_connections_with_data(client: TestClient, db_session: Session):
    """测试获取连接列表 - 有数据"""
    # 创建测试连接
    connection = Connection(
        name="连接1",
        host="localhost",
        port=3306,
        username="root",
        password_encrypted="encrypted",
        database_name="test_db",
        connection_pool_size=10,
        is_active=True,
    )
    db_session.add(connection)
    db_session.commit()

    response = client.get("/api/v1/connections/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == "连接1"


def test_list_connections_pagination(client: TestClient, db_session: Session):
    """测试获取连接列表 - 分页"""
    # 创建多个连接
    for i in range(5):
        connection = Connection(
            name=f"连接{i}",
            host="localhost",
            port=3306,
            username="root",
            password_encrypted="encrypted",
            database_name="test_db",
            connection_pool_size=10,
            is_active=True,
        )
        db_session.add(connection)
    db_session.commit()

    response = client.get("/api/v1/connections/?skip=0&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_list_connections_pagination_skip(client: TestClient, db_session: Session):
    """测试获取连接列表 - 跳过前2个"""
    # 创建多个连接
    for i in range(5):
        connection = Connection(
            name=f"连接{i}",
            host="localhost",
            port=3306,
            username="root",
            password_encrypted="encrypted",
            database_name="test_db",
            connection_pool_size=10,
            is_active=True,
        )
        db_session.add(connection)
    db_session.commit()

    response = client.get("/api/v1/connections/?skip=2&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3  # 5 - 2 = 3


def test_get_connection_success(
    client: TestClient, db_session: Session, mock_mysql_connector
):
    """测试获取单个连接"""
    # 先创建一个连接
    create_data = {
        "name": "测试连接",
        "host": "localhost",
        "port": 3306,
        "username": "root",
        "password": "test_password",
    }
    create_response = client.post("/api/v1/connections/", json=create_data)
    connection_id = create_response.json()["id"]

    # 获取连接
    response = client.get(f"/api/v1/connections/{connection_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == connection_id
    assert data["name"] == "测试连接"


def test_get_connection_not_found(client: TestClient):
    """测试获取不存在的连接"""
    response = client.get("/api/v1/connections/99999")
    assert response.status_code == 404
    assert "不存在" in response.json()["detail"]


def test_update_connection(
    client: TestClient, db_session: Session, mock_mysql_connector
):
    """测试更新连接"""
    # 先创建连接
    create_data = {
        "name": "原始连接",
        "host": "localhost",
        "port": 3306,
        "username": "root",
        "password": "test_password",
    }
    create_response = client.post("/api/v1/connections/", json=create_data)
    connection_id = create_response.json()["id"]

    # 更新连接
    update_data = {"name": "更新后的连接", "connection_pool_size": 20}
    response = client.put(f"/api/v1/connections/{connection_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "更新后的连接"
    assert data["connection_pool_size"] == 20


def test_update_connection_partial(
    client: TestClient, db_session: Session, mock_mysql_connector
):
    """测试部分更新连接"""
    # 先创建连接
    create_data = {
        "name": "原始连接",
        "host": "localhost",
        "port": 3306,
        "username": "root",
        "password": "test_password",
        "database_name": "test_db",
    }
    create_response = client.post("/api/v1/connections/", json=create_data)
    connection_id = create_response.json()["id"]

    # 只更新名称
    update_data = {"name": "新名称"}
    response = client.put(f"/api/v1/connections/{connection_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "新名称"
    assert data["host"] == "localhost"  # 保持不变


def test_update_connection_not_found(client: TestClient):
    """测试更新不存在的连接"""
    update_data = {"name": "新名称"}
    response = client.put("/api/v1/connections/99999", json=update_data)
    assert response.status_code == 404


def test_delete_connection(
    client: TestClient, db_session: Session, mock_mysql_connector
):
    """测试删除连接"""
    # 先创建连接
    create_data = {
        "name": "待删除连接",
        "host": "localhost",
        "port": 3306,
        "username": "root",
        "password": "test_password",
    }
    create_response = client.post("/api/v1/connections/", json=create_data)
    connection_id = create_response.json()["id"]

    # 删除连接
    response = client.delete(f"/api/v1/connections/{connection_id}")
    assert response.status_code == 204

    # 验证已删除
    get_response = client.get(f"/api/v1/connections/{connection_id}")
    assert get_response.status_code == 404


def test_delete_connection_not_found(client: TestClient):
    """测试删除不存在的连接"""
    response = client.delete("/api/v1/connections/99999")
    assert response.status_code == 404


def test_test_connection_success(client: TestClient, mock_mysql_connector):
    """测试连接 - 成功"""
    response = client.post(
        "/api/v1/connections/test",
        json={
            "host": "localhost",
            "port": 3306,
            "username": "root",
            "password": "test_password",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "连接成功" in data["message"]


def test_test_connection_failure(client: TestClient, mock_mysql_connector):
    """测试连接 - 失败"""
    # Mock connection test to raise exception
    mock_mysql_connector.test_connection.side_effect = Exception("连接失败")

    response = client.post(
        "/api/v1/connections/test",
        json={
            "host": "localhost",
            "port": 9999,
            "username": "root",
            "password": "wrong_password",
        },
    )

    assert response.status_code == 400
    assert "连接失败" in response.json()["detail"]


def test_connection_with_all_fields(client: TestClient, mock_mysql_connector):
    """测试创建包含所有字段的连接"""
    connection_data = {
        "name": "完整连接",
        "host": "192.168.1.100",
        "port": 3307,
        "username": "admin",
        "password": "secure_password",
        "database_name": "production_db",
        "connection_pool_size": 20,
    }

    response = client.post("/api/v1/connections/", json=connection_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "完整连接"
    assert data["host"] == "192.168.1.100"
    assert data["port"] == 3307
    assert data["database_name"] == "production_db"
    assert data["connection_pool_size"] == 20
    assert data["is_active"] == True


def test_connection_is_active_default(client: TestClient, mock_mysql_connector):
    """测试创建连接时is_active默认为True"""
    connection_data = {
        "name": "默认激活连接",
        "host": "localhost",
        "port": 3306,
        "username": "root",
        "password": "test",
    }

    response = client.post("/api/v1/connections/", json=connection_data)
    assert response.status_code == 201
    data = response.json()
    assert data["is_active"] == True


@pytest.mark.parametrize("invalid_port", [0, -1, 65536, 100000])
def test_create_connection_invalid_ports(client: TestClient, invalid_port):
    """测试创建连接 - 各种无效端口"""
    response = client.post(
        "/api/v1/connections/",
        json={
            "name": "测试连接",
            "host": "localhost",
            "port": invalid_port,
            "username": "root",
            "password": "test",
        },
    )
    assert response.status_code in [422, 400]


@pytest.mark.parametrize("invalid_name", ["", "   ", "a" * 101])
def test_create_connection_invalid_names(client: TestClient, invalid_name, mock_mysql_connector):
    """测试创建连接 - 各种无效名称"""
    response = client.post(
        "/api/v1/connections/",
        json={
            "name": invalid_name,
            "host": "localhost",
            "port": 3306,
            "username": "root",
            "password": "test",
        },
    )
    assert response.status_code in [422, 400]
