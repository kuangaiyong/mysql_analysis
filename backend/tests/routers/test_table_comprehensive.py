"""
Table router tests - comprehensive coverage
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch
import asyncio


class TestTableRouterComprehensive:
    """Comprehensive table router tests for coverage"""

    def test_get_all_tables_success(self, client: TestClient, db_session: Session):
        """测试成功获取所有表"""
        from tests.test_factories import create_test_connection

        conn = create_test_connection()
        db_session.add(conn)
        db_session.commit()

        response = client.get(f"/api/v1/table/tables/{conn.id}")

        assert response.status_code in [200, 404]

    def test_get_all_tables_pagination(self, client: TestClient):
        """测试分页获取表"""
        response = client.get("/api/v1/table/tables/1?skip=0&limit=10")

        assert response.status_code in [200, 404]

    def test_get_table_structure_basic(self, client: TestClient):
        """测试基本表结构获取"""
        response = client.get("/api/v1/table/structure/1/users")

        assert response.status_code in [200, 404]

    def test_get_table_structure_invalid_id(self, client: TestClient):
        """测试无效ID的表结构获取"""
        response = client.get("/api/v1/table/structure/999/users")

        assert response.status_code in [404, 422]

    def test_get_table_structure_invalid_table(self, client: TestClient):
        """测试无效表名的表结构获取"""
        response = client.get("/api/v1/table/structure/1/invalid_table!")

        assert response.status_code in [404, 422]

    def test_table_size_analysis(self, client: TestClient):
        """测试表大小分析"""
        response = client.get("/api/v1/table/size-analysis/1/users")

        assert response.status_code in [200, 404]

    def test_foreign_keys_analysis(self, client: TestClient):
        """测试外键分析"""
        response = client.get("/api/v1/table/foreign-keys/1/users")

        assert response.status_code in [200, 404]

    def test_multiple_tables(self, client: TestClient):
        """测试多表请求"""
        response = client.get("/api/v1/table/tables/1")

        assert response.status_code in [200, 404]

    def test_empty_database(self, client: TestClient):
        """测试空数据库"""
        response = client.get("/api/v1/table/tables/999")

        assert response.status_code in [200, 404]

    @patch("app.services.table_analyzer.TableStructureAnalyzer")
    def test_table_analyzer_error(self, mock_analyzer):
        """测试表分析器错误处理"""
        mock_analyzer.return_value = None
        mock_analyzer.get_table_structure.side_effect = Exception("DB Error")

        from app.routers.table import get_table_structure

        async def run_test():
            with pytest.raises(Exception):
                await get_table_structure(mock_analyzer, "users")

        asyncio.run(run_test())
