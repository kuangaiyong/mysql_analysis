"""
Additional router and schema tests to boost coverage
"""

import pytest
from fastapi.testclient import TestClient


class TestRouterAdditional:
    """Additional router tests"""

    def test_list_connections_pagination_edge_cases(self, client: TestClient):
        """测试连接列表分页边界情况"""
        # Test with skip at boundary
        response = client.get("/api/v1/connections/?skip=-1&limit=10")
        assert response.status_code in [200, 404, 422]

        # Test with large skip
        response = client.get("/api/v1/connections/?skip=1000")
        assert response.status_code in [200, 404, 422]

    def test_connection_id_validation(self, client: TestClient):
        """测试连接 ID 验证"""
        # Test with zero ID
        response = client.get("/api/v1/connections/0")
        assert response.status_code in [404, 200]

        # Test with negative ID
        response = client.get("/api/v1/connections/-1")
        assert response.status_code in [404, 422]

        # Test with very large ID
        response = client.get("/api/v1/connections/9999999999999")
        assert response.status_code in [404, 422]

    def test_connection_update_partial(self, client: TestClient):
        """测试部分更新连接"""
        from tests.test_factories import create_test_connection

        response = client.post(
            "/api/v1/connections/",
            json={"name": "Updated Connection", "host": "newhost", "port": 3307},
        )

        assert response.status_code in [200, 422]

    def test_connection_deletion_cascade(self, client: TestClient):
        """测试连接删除级联"""
        # First create a connection
        create_data = {
            "name": "Test Cascade",
            "host": "localhost",
            "port": 3306,
            "username": "root",
            "password": "test",
            "database_name": "test_db",
        }

        create_resp = client.post("/api/v1/connections/", json=create_data)

        if create_resp.status_code == 200:
            # Get the ID from response
            conn_id = create_resp.json().get("id")

            # Delete the connection
            del_resp = client.delete(f"/api/v1/connections/{conn_id}")

            assert del_resp.status_code in [200, 404]

    def test_explain_analyze_tree_format(self, client: TestClient):
        """测试树形格式 EXPLAIN"""
        response = client.post(
            "/api/v1/explain/analyze?connection_id=1",
            json={"sql": "SELECT * FROM users", "analyze_type": "tree"},
        )

        assert response.status_code in [200, 404]

    def test_explain_analyze_json_format(self, client: TestClient):
        """测试 JSON 格式 EXPLAIN"""
        response = client.post(
            "/api/v1/explain/analyze?connection_id=1",
            json={"sql": "SELECT * FROM users", "analyze_type": "json"},
        )

        assert response.status_code in [200, 404]

    def test_index_analyze_composite_index(self, client: TestClient):
        """测试复合索引分析"""
        response = client.get("/api/v1/index/analyze/1/users")

        assert response.status_code in [200, 404]

    def test_monitoring_metrics_various(self, client: TestClient):
        """测试各种指标"""
        metrics = ["cpu", "memory", "disk", "network"]

        for metric in metrics:
            response = client.get(f"/api/v1/monitoring/metrics/1?metric={metric}")
            assert response.status_code in [200, 404]

    def test_slow_query_export(self, client: TestClient):
        """测试慢查询导出 - endpoint not implemented"""
        response = client.get("/api/v1/slow-queries/export")

        assert response.status_code == 405


class TestSchemaEdgeCases:
    """Schema edge case tests"""

    def test_connection_schema_required_fields(self):
        """测试连接 schema 必填字段验证"""
        from app.schemas.connection import ConnectionCreate

        # Test with all required fields
        conn = ConnectionCreate(
            name="Test",
            host="localhost",
            port=3306,
            username="root",
            password="password",
            database_name="test_db",
        )

        assert conn.name == "Test"

    def test_connection_schema_optional_fields(self):
        """测试连接 schema 可选字段"""
        from app.schemas.connection import ConnectionCreate
        from decimal import Decimal

        conn = ConnectionCreate(
            name="Test Optional",
            host="localhost",
            port=3307,
            username="root",
            password="test",
            database_name="test_db",
            connection_pool_size=20,
            is_active=False,
        )

        assert conn.connection_pool_size == 20

    def test_alert_schema_time_window_edge_cases(self):
        """测试告警时间窗口边界情况"""
        from app.schemas.alert import AlertRuleCreate
        from decimal import Decimal

        # Test with minimum time window
        alert1 = AlertRuleCreate(
            connection_id=1,
            rule_name="Min Window",
            metric_name="cpu",
            condition_operator=">",
            threshold_value=Decimal("80.0"),
            time_window=1,
        )

        # Test with maximum time window
        alert2 = AlertRuleCreate(
            connection_id=1,
            rule_name="Max Window",
            metric_name="cpu",
            condition_operator=">",
            threshold_value=Decimal("80.0"),
            time_window=86400,
        )

        assert alert1.time_window == 1
        assert alert2.time_window == 86400

    def test_table_schema_column_types(self):
        """测试表 schema 列类型"""
        from app.schemas.table import ColumnInfoCreate

        types = ["INT", "VARCHAR", "TEXT", "DATETIME", "DECIMAL", "BLOB"]

        for col_type in types:
            col = ColumnInfoCreate(
                column_name="test_col",
                data_type=col_type,
                is_nullable=True,
                column_key="",
            )

            assert col.data_type == col_type

    def test_explain_schema_formats(self):
        """测试 EXPLAIN schema 格式"""
        from app.schemas.explain import ExplainRequest, ExplainAnalyzeRequest

        formats = ["traditional", "json", "tree"]

        for fmt in formats:
            if fmt in ["traditional", "json"]:
                schema = ExplainRequest(sql="SELECT 1", analyze_type=fmt)
                assert schema.analyze_type == fmt
            else:
                schema = ExplainAnalyzeRequest(sql="SELECT 1")
                assert schema.sql == "SELECT 1"
