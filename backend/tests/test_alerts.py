"""
告警管理测试
测试告警规则和告警历史相关API端点
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime


def test_list_alert_rules_empty(client: TestClient):
    """测试获取告警规则列表 - 空列表"""
    response = client.get("/api/v1/alerts/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_alert_rules_with_data(client: TestClient, test_alert_rule):
    """测试获取告警规则列表 - 有数据"""
    response = client.get("/api/v1/alerts/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_create_alert_rule(client: TestClient, test_connection):
    """测试创建告警规则"""
    rule_data = {
        "connection_id": test_connection.id,
        "rule_name": "CPU使用率告警",
        "metric_name": "cpu_usage",
        "condition_operator": ">",
        "threshold_value": 90.0,
        "time_window": 60,
        "severity": "critical",
        "notification_channels": {"system": True, "email": False},
    }

    response = client.post("/api/v1/alerts/", json=rule_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["rule_name"] == "CPU使用率告警"


def test_create_alert_rule_invalid_name(client: TestClient, test_connection):
    """测试创建告警规则 - 无效名称"""
    rule_data = {
        "connection_id": test_connection.id,
        "rule_name": "",  # 无效：空名称
        "metric_name": "cpu_usage",
        "condition_operator": ">",
        "threshold_value": 90.0,
        "severity": "critical",
        "notification_channels": {"system": True},
    }

    response = client.post("/api/v1/alerts/", json=rule_data)
    assert response.status_code == 422


def test_create_alert_rule_missing_required_field(client: TestClient, test_connection):
    """测试创建告警规则 - 缺少必填字段"""
    rule_data = {
        "connection_id": test_connection.id,
        "rule_name": "测试告警",
        "metric_name": "cpu_usage",
        # 缺少 condition_operator, threshold_value, severity
    }

    response = client.post("/api/v1/alerts/", json=rule_data)
    assert response.status_code == 422


def test_get_alert_rule(client: TestClient, test_alert_rule):
    """测试获取单个告警规则"""
    response = client.get(f"/api/v1/alerts/{test_alert_rule.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_alert_rule.id
    assert data["rule_name"] == test_alert_rule.rule_name


def test_get_alert_rule_not_found(client: TestClient):
    """测试获取不存在的告警规则"""
    response = client.get("/api/v1/alerts/99999")
    assert response.status_code == 404
    assert "不存在" in response.json()["detail"]


def test_update_alert_rule(client: TestClient, test_alert_rule):
    """测试更新告警规则"""
    update_data = {
        "rule_name": "更新后的规则",
        "threshold_value": 95.0,
        "severity": "warning",
    }

    response = client.put(f"/api/v1/alerts/{test_alert_rule.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["rule_name"] == "更新后的规则"
    assert data["threshold_value"] == 95.0
    assert data["severity"] == "warning"


def test_update_alert_rule_partial(client: TestClient, test_alert_rule):
    """测试部分更新告警规则"""
    update_data = {"threshold_value": 80.0}

    response = client.put(f"/api/v1/alerts/{test_alert_rule.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["threshold_value"] == 80.0
    assert data["rule_name"] == test_alert_rule.rule_name  # 保持不变


def test_update_alert_rule_not_found(client: TestClient):
    """测试更新不存在的告警规则"""
    update_data = {"rule_name": "新名称"}
    response = client.put("/api/v1/alerts/99999", json=update_data)
    assert response.status_code == 404


def test_delete_alert_rule(client: TestClient, test_alert_rule):
    """测试删除告警规则"""
    response = client.delete(f"/api/v1/alerts/{test_alert_rule.id}")
    assert response.status_code == 204  # 删除成功返回204 No Content

    # 验证已删除
    get_response = client.get(f"/api/v1/alerts/{test_alert_rule.id}")
    assert get_response.status_code == 404


def test_delete_alert_rule_not_found(client: TestClient):
    """测试删除不存在的告警规则"""
    response = client.delete("/api/v1/alerts/99999")
    assert response.status_code == 404


def test_list_alert_rules_with_filters(
    client: TestClient, test_connection, test_alert_rule
):
    """测试获取告警规则列表 - 带筛选条件"""
    # 筛选特定连接
    response = client.get(f"/api/v1/alerts/?connection_id={test_connection.id}")
    assert response.status_code == 200
    data = response.json()
    assert all(rule["connection_id"] == test_connection.id for rule in data)

    # 筛选启用状态
    response = client.get(f"/api/v1/alerts/?is_enabled=true")
    assert response.status_code == 200


def test_list_alert_rules_pagination(client: TestClient, test_connection):
    """测试获取告警规则列表 - 分页"""
    # 创建多个规则
    for i in range(5):
        rule_data = {
            "connection_id": test_connection.id,
            "rule_name": f"测试规则{i}",
            "metric_name": "cpu_usage",
            "condition_operator": ">",
            "threshold_value": 80 + i * 2,
            "severity": "warning",
            "notification_channels": {"system": True},
        }
        client.post("/api/v1/alerts/", json=rule_data)

    response = client.get("/api/v1/alerts/?skip=0&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_list_alert_history_empty(client: TestClient):
    """测试获取告警历史列表 - 空列表"""
    response = client.get("/api/v1/alerts/history/list")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_alert_history_with_connection_filter(client: TestClient, test_connection):
    """测试获取告警历史 - 按连接筛选"""
    response = client.get(
        f"/api/v1/alerts/history/list?connection_id={test_connection.id}"
    )
    assert response.status_code == 200


def test_resolve_alert(
    client: TestClient, db_session, test_connection, test_alert_rule
):
    """测试解决告警"""
    from app.models.alert import AlertHistory

    # 创建告警历史（需要显式设置id，因为SQLite不支持BigInteger的autoincrement）
    alert_history = AlertHistory(
        id=1,
        alert_rule_id=test_alert_rule.id,
        connection_id=test_connection.id,
        alert_time=datetime.now(),
        metric_value=95.0,
        message="CPU使用率超过阈值",
        status="active",
    )
    db_session.add(alert_history)
    db_session.commit()
    db_session.refresh(alert_history)

    # 解决告警
    response = client.post(f"/api/v1/alerts/history/{alert_history.id}/resolve")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "resolved"
    assert data["resolved_at"] is not None


def test_resolve_alert_not_found(client: TestClient):
    """测试解决不存在的告警"""
    response = client.post("/api/v1/alerts/history/99999/resolve")
    assert response.status_code == 404


def test_list_active_alerts(
    client: TestClient, db_session, test_connection, test_alert_rule
):
    """测试获取活跃告警"""
    from app.models.alert import AlertHistory

    # 创建活跃告警（需要显式设置id）
    alert_history = AlertHistory(
        id=2,
        alert_rule_id=test_alert_rule.id,
        connection_id=test_connection.id,
        alert_time=datetime.now(),
        metric_value=95.0,
        message="CPU使用率超过阈值",
        status="active",
    )
    db_session.add(alert_history)
    db_session.commit()

    response = client.get(
        f"/api/v1/alerts/active/list?connection_id={test_connection.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_alert_statistics(client: TestClient, test_connection):
    """测试获取告警统计"""
    response = client.get(f"/api/v1/alerts/statistics/{test_connection.id}?days=7")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


def test_get_alert_statistics_connection_not_found(client: TestClient):
    """测试获取告警统计 - 连接不存在"""
    response = client.get("/api/v1/alerts/statistics/99999")
    assert response.status_code == 404


@pytest.mark.parametrize("severity", ["critical", "warning", "info"])
def test_create_alert_rules_various_severities(
    client: TestClient, test_connection, severity
):
    """测试创建不同严重级别的告警规则"""
    rule_data = {
        "connection_id": test_connection.id,
        "rule_name": f"测试{severity}告警",
        "metric_name": "cpu_usage",
        "condition_operator": ">",
        "threshold_value": 90.0,
        "severity": severity,
        "notification_channels": {"system": True},
    }

    response = client.post("/api/v1/alerts/", json=rule_data)
    assert response.status_code == 201


@pytest.mark.parametrize("condition_operator", [">", "<", "=", ">=", "<="])
def test_create_alert_rules_various_operators(
    client: TestClient, test_connection, condition_operator
):
    """测试创建不同操作符的告警规则"""
    rule_data = {
        "connection_id": test_connection.id,
        "rule_name": "测试告警",
        "metric_name": "cpu_usage",
        "condition_operator": condition_operator,
        "threshold_value": 90.0,
        "severity": "warning",
        "notification_channels": {"system": True},
    }

    response = client.post("/api/v1/alerts/", json=rule_data)
    assert response.status_code == 201
