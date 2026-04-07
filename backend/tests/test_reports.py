"""
性能报告测试
测试报告的创建、查询、更新和删除相关API端点
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime


def test_list_reports_empty(client: TestClient):
    """测试获取报告列表 - 空列表"""
    response = client.get("/api/v1/reports/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_list_reports_with_data(client: TestClient, test_report):
    """测试获取报告列表 - 有数据"""
    response = client.get("/api/v1/reports/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_create_report(client: TestClient, test_connection):
    """测试创建报告"""
    report_data = {
        "connection_id": test_connection.id,
        "report_type": "daily",
        "report_name": "测试日报",
        "description": "测试性能报告",
        "start_time": datetime(2024, 1, 1, 0, 0, 0).isoformat(),
        "end_time": datetime(2024, 1, 2, 0, 0, 0).isoformat(),
        "status": "completed",
    }

    response = client.post("/api/v1/reports/", json=report_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["report_name"] == "测试日报"


def test_create_report_invalid_data(client: TestClient, test_connection):
    """测试创建报告 - 无效数据"""
    report_data = {
        "connection_id": test_connection.id,
        "report_name": "",  # 无效：空名称
        "report_type": "daily",
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
    }

    response = client.post("/api/v1/reports/", json=report_data)
    assert response.status_code == 422


def test_create_report_missing_required_field(client: TestClient, test_connection):
    """测试创建报告 - 缺少必填字段"""
    report_data = {
        "connection_id": test_connection.id,
        "report_name": "测试报告",
        # 缺少 report_type, start_time, end_time
    }

    response = client.post("/api/v1/reports/", json=report_data)
    assert response.status_code == 422


def test_get_report(client: TestClient, test_report):
    """测试获取单个报告"""
    response = client.get(f"/api/v1/reports/{test_report.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_report.id
    assert data["report_name"] == test_report.report_name


def test_get_report_not_found(client: TestClient):
    """测试获取不存在的报告"""
    response = client.get("/api/v1/reports/99999")
    assert response.status_code == 404
    assert "不存在" in response.json()["detail"]


def test_update_report(client: TestClient, test_report):
    """测试更新报告"""
    update_data = {
        "report_name": "更新后的报告",
        "description": "更新的描述",
        "status": "completed",
    }

    response = client.put(f"/api/v1/reports/{test_report.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["report_name"] == "更新后的报告"
    assert data["description"] == "更新的描述"


def test_update_report_partial(client: TestClient, test_report):
    """测试部分更新报告"""
    update_data = {"description": "新描述"}

    response = client.put(f"/api/v1/reports/{test_report.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "新描述"
    assert data["report_name"] == test_report.report_name  # 保持不变


def test_update_report_not_found(client: TestClient):
    """测试更新不存在的报告"""
    update_data = {"report_name": "新名称"}
    response = client.put("/api/v1/reports/99999", json=update_data)
    assert response.status_code == 404


def test_delete_report(client: TestClient, test_report):
    """测试删除报告"""
    response = client.delete(f"/api/v1/reports/{test_report.id}")
    assert response.status_code == 204

    # 验证已删除
    get_response = client.get(f"/api/v1/reports/{test_report.id}")
    assert get_response.status_code == 404


def test_delete_report_not_found(client: TestClient):
    """测试删除不存在的报告"""
    response = client.delete("/api/v1/reports/99999")
    assert response.status_code == 404


def test_list_reports_with_filters(client: TestClient, test_connection, test_report):
    """测试获取报告列表 - 带筛选条件"""
    # 按连接筛选
    response = client.get(f"/api/v1/reports/?connection_id={test_connection.id}")
    assert response.status_code == 200
    data = response.json()
    assert all(report["connection_id"] == test_connection.id for report in data)

    # 按状态筛选
    response = client.get(f"/api/v1/reports/?status=completed")
    assert response.status_code == 200

    # 按类型筛选
    response = client.get(f"/api/v1/reports/?report_type=daily")
    assert response.status_code == 200


def test_list_reports_pagination(client: TestClient, test_connection):
    """测试获取报告列表 - 分页"""
    # 创建多个报告
    for i in range(5):
        report_data = {
            "connection_id": test_connection.id,
            "report_type": "daily",
            "report_name": f"测试报告{i}",
            "description": f"测试{i}",
            "start_time": datetime(2024, 1, 1, 0, 0, 0).isoformat(),
            "end_time": datetime(2024, 1, 2, 0, 0, 0).isoformat(),
            "status": "completed",
        }
        client.post("/api/v1/reports/", json=report_data)

    response = client.get("/api/v1/reports/?skip=0&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_get_reports_by_date_range(client: TestClient, test_connection, test_report):
    """测试获取指定时间范围内的报告"""
    start_date = datetime(2024, 1, 1, 0, 0, 0)
    end_date = datetime(2024, 1, 31, 23, 59, 59)

    response = client.get(
        f"/api/v1/reports/range/{test_connection.id}?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_reports_by_date_range_connection_not_found(client: TestClient):
    """测试获取时间范围报告 - 连接不存在返回空列表"""
    start_date = datetime(2024, 1, 1, 0, 0, 0)
    end_date = datetime(2024, 1, 31, 23, 59, 59)

    response = client.get(
        f"/api/v1/reports/range/99999?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
    )
    # API不验证connection是否存在，直接返回该connection的报告列表
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_update_report_status(client: TestClient, test_report):
    """测试更新报告状态"""
    response = client.patch(
        f"/api/v1/reports/{test_report.id}/status?report_status=completed"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"


def test_update_report_status_with_file_info(client: TestClient, test_report):
    """测试更新报告状态 - 包含文件信息"""
    response = client.patch(
        f"/api/v1/reports/{test_report.id}/status?report_status=completed&file_path=/path/to/report.pdf&file_size=102400"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["file_path"] == "/path/to/report.pdf"
    assert data["file_size"] == 102400


def test_update_report_status_not_found(client: TestClient):
    """测试更新不存在的报告状态"""
    response = client.patch("/api/v1/reports/99999/status?report_status=completed")
    assert response.status_code == 404


@pytest.mark.parametrize("report_type", ["daily", "weekly", "monthly", "custom"])
def test_create_reports_various_types(client: TestClient, test_connection, report_type):
    """测试创建不同类型的报告"""
    report_data = {
        "connection_id": test_connection.id,
        "report_type": report_type,
        "report_name": f"测试{report_type}报告",
        "description": "测试报告",
        "start_time": datetime(2024, 1, 1, 0, 0, 0).isoformat(),
        "end_time": datetime(2024, 1, 2, 0, 0, 0).isoformat(),
        "status": "pending",
    }

    response = client.post("/api/v1/reports/", json=report_data)
    assert response.status_code == 201
    data = response.json()
    assert data["report_type"] == report_type


@pytest.mark.parametrize("status", ["pending", "generating", "completed", "failed"])
def test_create_reports_various_statuses(client: TestClient, test_connection, status):
    """测试创建不同状态的报告"""
    report_data = {
        "connection_id": test_connection.id,
        "report_type": "daily",
        "report_name": "测试报告",
        "description": "测试报告",
        "start_time": datetime(2024, 1, 1, 0, 0, 0).isoformat(),
        "end_time": datetime(2024, 1, 2, 0, 0, 0).isoformat(),
        "status": status,
    }

    response = client.post("/api/v1/reports/", json=report_data)
    assert response.status_code == 201


@pytest.mark.parametrize("skip,limit", [(0, 10), (5, 20), (10, 5)])
def test_list_reports_pagination_variations(
    client: TestClient, test_connection, skip, limit
):
    """测试报告列表的各种分页参数"""
    response = client.get(f"/api/v1/reports/?skip={skip}&limit={limit}")
    assert response.status_code == 200


def test_list_reports_with_multiple_filters(client: TestClient, test_connection):
    """测试报告列表 - 多个筛选条件组合"""
    response = client.get(
        f"/api/v1/reports/?connection_id={test_connection.id}&status=completed&report_type=daily"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
