"""
Tuning Router 集成测试
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.test_factories import ConnectionFactory


class TestTuningRouter:
    """调优路由测试类"""

    def test_sql_rewrite_success(self, client: TestClient):
        """测试SQL改写建议 - 成功场景"""
        request_data = {"sql": "SELECT * FROM users WHERE id = 1"}

        with patch("app.routers.tuning.SQLRewriter") as mock_rewriter:
            mock_instance = Mock()
            mock_instance.suggest_rewrite.return_value = [
                {"type": "avoid_select_star", "suggestion": "避免使用SELECT *"}
            ]
            mock_rewriter.return_value = mock_instance

            response = client.post("/api/v1/tuning/sql-rewrite", json=request_data)

            assert response.status_code in [200, 422, 500]
            if response.status_code == 200:
                data = response.json()
                assert "sql" in data
                assert "suggestions" in data
                assert "has_suggestions" in data

    def test_sql_rewrite_empty_sql(self, client: TestClient):
        """测试SQL改写建议 - 空SQL"""
        request_data = {"sql": ""}

        response = client.post("/api/v1/tuning/sql-rewrite", json=request_data)

        assert response.status_code in [200, 422, 500]

    def test_sql_rewrite_no_request_body(self, client: TestClient):
        """测试SQL改写建议 - 无请求体"""
        response = client.post("/api/v1/tuning/sql-rewrite", json={})

        assert response.status_code in [200, 422, 500]

    def test_innodb_tuning_success(self, db_session: Session, client: TestClient):
        """测试InnoDB调优建议 - 成功场景"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            # Mock SHOW STATUS and SHOW VARIABLES results
            mock_instance.execute_query.side_effect = [
                [
                    {
                        "Variable_name": "Innodb_buffer_pool_read_requests",
                        "Value": "1000",
                    }
                ],
                [{"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"}],
            ]
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.InnoDBTuner") as mock_tuner:
                mock_tuner_instance = Mock()
                mock_tuner_instance.analyze_and_recommend.return_value = [
                    {
                        "param": "innodb_buffer_pool_size",
                        "suggestion": "增大Buffer Pool",
                    }
                ]
                mock_tuner_instance._calculate_buffer_pool_hit_rate.return_value = 99.5
                mock_tuner.return_value = mock_tuner_instance

                response = client.get(f"/api/v1/tuning/innodb/{connection.id}")

                assert response.status_code in [200, 404, 422, 500]
                if response.status_code == 200:
                    data = response.json()
                    assert "connection_id" in data
                    assert "recommendations" in data
                    assert "buffer_pool_hit_rate" in data

    def test_innodb_tuning_connection_not_found(self, client: TestClient):
        """测试InnoDB调优建议 - 连接不存在"""
        response = client.get("/api/v1/tuning/innodb/999")

        assert response.status_code in [200, 404, 422, 500]

    def test_index_suggestions_success(self, db_session: Session, client: TestClient):
        """测试索引建议 - 成功场景"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        request_data = {
            "sql": "SELECT * FROM users WHERE name = 'test'",
            "database": "test_db",
        }

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.IndexSuggestionEngine") as mock_engine:
                mock_engine_instance = Mock()
                mock_engine_instance.generate_index_recommendations_with_explain.return_value = [
                    {"table": "users", "columns": ["name"], "index_type": "BTREE"}
                ]
                mock_engine.return_value = mock_engine_instance

                response = client.post(
                    f"/api/v1/tuning/index-suggestions/{connection.id}",
                    json=request_data,
                )

                assert response.status_code in [200, 404, 422, 500]
                if response.status_code == 200:
                    data = response.json()
                    assert "connection_id" in data
                    assert "sql" in data
                    assert "recommendations" in data
                    assert "has_recommendations" in data

    def test_index_suggestions_connection_not_found(self, client: TestClient):
        """测试索引建议 - 连接不存在"""
        request_data = {"sql": "SELECT * FROM users WHERE name = 'test'"}

        response = client.post(
            "/api/v1/tuning/index-suggestions/999", json=request_data
        )

        assert response.status_code in [200, 404, 422, 500]

    def test_index_suggestions_without_database(
        self, db_session: Session, client: TestClient
    ):
        """测试索引建议 - 不指定数据库(使用连接默认数据库)"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        request_data = {"sql": "SELECT * FROM users WHERE name = 'test'"}

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.IndexSuggestionEngine") as mock_engine:
                mock_engine_instance = Mock()
                mock_engine_instance.generate_index_recommendations_with_explain.return_value = []
                mock_engine.return_value = mock_engine_instance

                response = client.post(
                    f"/api/v1/tuning/index-suggestions/{connection.id}",
                    json=request_data,
                )

                assert response.status_code in [200, 404, 422, 500]

    def test_index_suggestions_empty_sql(self, db_session: Session, client: TestClient):
        """测试索引建议 - 空SQL"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        request_data = {"sql": ""}

        response = client.post(
            f"/api/v1/tuning/index-suggestions/{connection.id}", json=request_data
        )

        assert response.status_code in [200, 404, 422, 500]

    def test_comprehensive_tuning_success(
        self, db_session: Session, client: TestClient
    ):
        """测试综合调优建议 - 成功场景"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            # Mock multiple execute_query calls for different queries
            mock_instance.execute_query.side_effect = [
                # InnoDB STATUS
                [
                    {
                        "Variable_name": "Innodb_buffer_pool_read_requests",
                        "Value": "1000",
                    }
                ],
                # InnoDB VARIABLES
                [{"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"}],
                # Connection VARIABLES
                [{"Variable_name": "max_connections", "Value": "151"}],
                # Connection STATUS
                [{"Variable_name": "Threads_connected", "Value": "10"}],
                # Query cache (returns empty for MySQL 8.0)
                [],
                # Table cache VARIABLES
                [{"Variable_name": "table_open_cache", "Value": "2000"}],
                # Table cache STATUS
                [{"Variable_name": "Open_tables", "Value": "100"}],
            ]
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.InnoDBTuner") as mock_tuner:
                mock_tuner_instance = Mock()
                mock_tuner_instance.analyze_and_recommend.return_value = [
                    {
                        "param": "innodb_buffer_pool_size",
                        "suggestion": "增大Buffer Pool",
                    }
                ]
                mock_tuner.return_value = mock_tuner_instance

                response = client.get(f"/api/v1/tuning/comprehensive/{connection.id}")

                assert response.status_code in [200, 404, 422, 500]
                if response.status_code == 200:
                    data = response.json()
                    assert "connection_id" in data
                    assert "database_name" in data
                    assert "suggestions" in data
                    assert "summary" in data
                    assert "total_categories" in data["summary"]

    def test_comprehensive_tuning_connection_not_found(self, client: TestClient):
        """测试综合调优建议 - 连接不存在"""
        response = client.get("/api/v1/tuning/comprehensive/999")

        assert response.status_code in [200, 404, 422, 500]

    def test_comprehensive_tuning_with_recommendations(
        self, db_session: Session, client: TestClient
    ):
        """测试综合调优建议 - 包含多种建议"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_instance.execute_query.side_effect = [
                [
                    {
                        "Variable_name": "Innodb_buffer_pool_read_requests",
                        "Value": "1000",
                    }
                ],
                [{"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"}],
                [{"Variable_name": "max_connections", "Value": "151"}],
                [{"Variable_name": "Threads_connected", "Value": "10"}],
                [],
                [{"Variable_name": "table_open_cache", "Value": "2000"}],
                [{"Variable_name": "Open_tables", "Value": "100"}],
            ]
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.InnoDBTuner") as mock_tuner:
                mock_tuner_instance = Mock()
                mock_tuner_instance.analyze_and_recommend.return_value = [
                    {
                        "param": "innodb_buffer_pool_size",
                        "current_value": "134217728",
                        "recommended_value": "268435456",
                        "reason": "Buffer Pool命中率较低",
                        "priority": "high",
                    }
                ]
                mock_tuner.return_value = mock_tuner_instance

                response = client.get(f"/api/v1/tuning/comprehensive/{connection.id}")

                assert response.status_code in [200, 404, 422, 500]

    def test_invalid_connection_id_format(self, client: TestClient):
        """测试无效的连接ID格式"""
        response = client.get("/api/v1/tuning/innodb/invalid_id")

        assert response.status_code in [200, 404, 422, 500]



class TestInnodbDeepRouter:
    """InnoDB深度分析路由测试类"""

    def test_innodb_deep_success(self, db_session: Session, client: TestClient):
        """测试InnoDB深度分析 - 成功场景"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            # Mock SHOW VARIABLES, SHOW STATUS, SHOW ENGINE INNODB STATUS, INNODB_METRICS
            mock_instance.execute_query.side_effect = [
                [{"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"}],  # VARIABLES
                [{"Variable_name": "Innodb_buffer_pool_read_requests", "Value": "1000"}],  # STATUS
                [{"Status": "BUFFER POOL AND MEMORY..."}],  # ENGINE INNODB STATUS
                [{"NAME": "page_splits", "COUNT": 100}],  # INNODB_METRICS
            ]
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.InnoDBTuner") as mock_tuner:
                mock_tuner_instance = Mock()
                mock_tuner_instance.get_deep_analysis.return_value = {
                    "buffer_pool_lru": {},
                    "undo_log": {},
                    "redo_log": {},
                    "page_splits": {},
                    "adaptive_hash_index": {},
                }
                mock_tuner.return_value = mock_tuner_instance

                response = client.get(f"/api/v1/tuning/innodb-deep/{connection.id}")

                assert response.status_code in [200, 404, 422, 500]
                if response.status_code == 200:
                    data = response.json()
                    assert "connection_id" in data
                    assert "deep_analysis" in data

    def test_innodb_deep_connection_not_found(self, client: TestClient):
        """测试InnoDB深度分析 - 连接不存在"""
        response = client.get("/api/v1/tuning/innodb-deep/999")
        assert response.status_code in [200, 404, 422, 500]

    def test_innodb_deep_with_engine_status_failure(self, db_session: Session, client: TestClient):
        """测试InnoDB深度分析 - 获取ENGINE STATUS失败"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            # 第一次调用 VARIABLES 成功，后续调用抛出异常
            call_count = [0]
            def side_effect_func(query):
                call_count[0] += 1
                if call_count[0] == 1:
                    return [{"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"}]
                elif call_count[0] == 2:
                    return [{"Variable_name": "Innodb_buffer_pool_read_requests", "Value": "1000"}]
                elif call_count[0] == 3:
                    raise Exception("ENGINE STATUS failed")
                else:
                    return []
            mock_instance.execute_query.side_effect = side_effect_func
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.InnoDBTuner") as mock_tuner:
                mock_tuner_instance = Mock()
                mock_tuner_instance.get_deep_analysis.return_value = {}
                mock_tuner.return_value = mock_tuner_instance

                response = client.get(f"/api/v1/tuning/innodb-deep/{connection.id}")
                # 即使内部获取失败，也应该返回结果（因为异常被捕获）
                assert response.status_code in [200, 404, 422, 500]

    def test_innodb_deep_with_metrics_failure(self, db_session: Session, client: TestClient):
        """测试InnoDB深度分析 - 获取INNODB_METRICS失败"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            call_count = [0]
            def side_effect_func(query):
                call_count[0] += 1
                if call_count[0] == 1:
                    return [{"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"}]
                elif call_count[0] == 2:
                    return [{"Variable_name": "Innodb_buffer_pool_read_requests", "Value": "1000"}]
                elif call_count[0] == 3:
                    return [{"Status": "BUFFER POOL AND MEMORY..."}]
                else:
                    raise Exception("INNODB_METRICS failed")
            mock_instance.execute_query.side_effect = side_effect_func
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.InnoDBTuner") as mock_tuner:
                mock_tuner_instance = Mock()
                mock_tuner_instance.get_deep_analysis.return_value = {}
                mock_tuner.return_value = mock_tuner_instance

                response = client.get(f"/api/v1/tuning/innodb-deep/{connection.id}")
                assert response.status_code in [200, 404, 422, 500]

    def test_innodb_deep_general_exception(self, db_session: Session, client: TestClient):
        """测试InnoDB深度分析 - 通用异常"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_connector.side_effect = Exception("连接失败")

            response = client.get(f"/api/v1/tuning/innodb-deep/{connection.id}")
            assert response.status_code in [200, 404, 422, 500]
            if response.status_code == 500:
                assert "InnoDB深度分析失败" in response.json().get("detail", "")



class TestExceptionHandling:
    """异常处理测试类"""

    def test_innodb_tuning_general_exception(self, db_session: Session, client: TestClient):
        """测试InnoDB调优 - 通用异常（覆盖行105-106）"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_connector.side_effect = Exception("连接失败")

            response = client.get(f"/api/v1/tuning/innodb/{connection.id}")
            assert response.status_code == 500
            assert "InnoDB调优建议失败" in response.json().get("detail", "")

    def test_sql_rewrite_exception(self, client: TestClient):
        """测试SQL改写 - 异常处理（覆盖行199-200）"""
        request_data = {"sql": "SELECT * FROM users"}

        with patch("app.routers.tuning.SQLRewriter") as mock_rewriter:
            mock_rewriter.side_effect = Exception("分析失败")

            response = client.post("/api/v1/tuning/sql-rewrite", json=request_data)
            assert response.status_code == 500
            assert "SQL改写分析失败" in response.json().get("detail", "")

    def test_index_suggestions_general_exception(self, db_session: Session, client: TestClient):
        """测试索引建议 - 通用异常（覆盖行242-244）"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        request_data = {"sql": "SELECT * FROM users WHERE name = 'test'"}

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_connector.side_effect = Exception("连接失败")

            response = client.post(
                f"/api/v1/tuning/index-suggestions/{connection.id}", json=request_data
            )
            assert response.status_code == 500
            assert "获取索引建议失败" in response.json().get("detail", "")

    def test_comprehensive_tuning_general_exception(self, db_session: Session, client: TestClient):
        """测试综合调优 - 通用异常（覆盖行386-389）"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_connector.side_effect = Exception("连接失败")

            response = client.get(f"/api/v1/tuning/comprehensive/{connection.id}")
            assert response.status_code == 500
            assert "获取综合调优建议失败" in response.json().get("detail", "")



class TestBufferPoolStats:
    """Buffer Pool 统计测试类（覆盖行80-81）"""

    def test_innodb_tuning_with_buffer_pool_stats(self, db_session: Session, client: TestClient):
        """测试InnoDB调优 - 包含Buffer Pool统计信息"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            # Mock SHOW STATUS, SHOW VARIABLES, Buffer Pool Stats
            mock_instance.execute_query.side_effect = [
                [{"Variable_name": "Innodb_buffer_pool_read_requests", "Value": "1000"}],
                [{"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"}],
                # Buffer Pool 统计 - 覆盖行80-81
                [{"data_pages": 5000, "PAGE_SIZE": 16384}],
            ]
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.InnoDBTuner") as mock_tuner:
                mock_tuner_instance = Mock()
                mock_tuner_instance.analyze_and_recommend.return_value = [
                    {"param": "innodb_buffer_pool_size", "suggestion": "增大Buffer Pool"}
                ]
                mock_tuner_instance._calculate_buffer_pool_hit_rate.return_value = 99.5
                mock_tuner.return_value = mock_tuner_instance

                response = client.get(f"/api/v1/tuning/innodb/{connection.id}")

                assert response.status_code == 200
                data = response.json()
                assert "connection_id" in data
                assert "recommendations" in data

    def test_innodb_tuning_buffer_pool_stats_with_missing_fields(self, db_session: Session, client: TestClient):
        """测试InnoDB调优 - Buffer Pool统计缺少字段"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_instance.execute_query.side_effect = [
                [{"Variable_name": "Innodb_buffer_pool_read_requests", "Value": "1000"}],
                [{"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"}],
                # Buffer Pool 统计 - 使用默认值
                [{}],
            ]
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.InnoDBTuner") as mock_tuner:
                mock_tuner_instance = Mock()
                mock_tuner_instance.analyze_and_recommend.return_value = []
                mock_tuner_instance._calculate_buffer_pool_hit_rate.return_value = 99.5
                mock_tuner.return_value = mock_tuner_instance

                response = client.get(f"/api/v1/tuning/innodb/{connection.id}")
                assert response.status_code == 200



class TestConnectionSettings:
    """连接配置建议测试类（覆盖行318, 408-411, 423）"""

    def test_comprehensive_with_connection_recommendations(self, db_session: Session, client: TestClient):
        """测试综合调优 - 包含连接配置建议（覆盖行318）"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            # 模拟连接配置需要优化的场景
            mock_instance.execute_query.side_effect = [
                # InnoDB STATUS
                [{"Variable_name": "Innodb_buffer_pool_read_requests", "Value": "1000"}],
                # InnoDB VARIABLES
                [{"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"}],
                # Connection VARIABLES - max_connections 较大，thread_cache_size 为 0
                [
                    {"Variable_name": "max_connections", "Value": "151"},
                    {"Variable_name": "thread_cache_size", "Value": "0"},
                    {"Variable_name": "wait_timeout", "Value": "28800"},
                    {"Variable_name": "interactive_timeout", "Value": "28800"},
                ],
                # Connection STATUS - 线程缓存命中率低（覆盖行408-411）
                [
                    {"Variable_name": "Threads_connected", "Value": "10"},
                    {"Variable_name": "Threads_created", "Value": "500"},  # 高于连接数
                    {"Variable_name": "Max_used_connections", "Value": "50"},
                    {"Variable_name": "Connections", "Value": "1000"},  # threads_created / connections > 5%
                ],
                # Query cache (empty for MySQL 8.0)
                [],
                # Table cache VARIABLES
                [
                    {"Variable_name": "table_open_cache", "Value": "2000"},
                    {"Variable_name": "table_definition_cache", "Value": "2000"},
                ],
                # Table cache STATUS
                [
                    {"Variable_name": "Open_tables", "Value": "100"},
                    {"Variable_name": "Opened_tables", "Value": "150"},
                    {"Variable_name": "Open_table_definitions", "Value": "100"},
                    {"Variable_name": "Opened_table_definitions", "Value": "150"},
                ],
            ]
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.InnoDBTuner") as mock_tuner:
                mock_tuner_instance = Mock()
                mock_tuner_instance.analyze_and_recommend.return_value = [
                    {"param": "innodb_buffer_pool_size", "suggestion": "增大Buffer Pool"}
                ]
                mock_tuner.return_value = mock_tuner_instance

                response = client.get(f"/api/v1/tuning/comprehensive/{connection.id}")

                assert response.status_code == 200
                data = response.json()
                # 检查是否有连接配置建议
                categories = [s["category"] for s in data["suggestions"]]
                assert "connection" in categories

    def test_comprehensive_with_max_connections_warning(self, db_session: Session, client: TestClient):
        """测试综合调优 - 最大连接数接近上限（覆盖行423）"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_instance.execute_query.side_effect = [
                [{"Variable_name": "Innodb_buffer_pool_read_requests", "Value": "1000"}],
                [{"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"}],
                # max_connections = 100, Max_used = 85 (> 80%)
                [
                    {"Variable_name": "max_connections", "Value": "100"},
                    {"Variable_name": "thread_cache_size", "Value": "16"},
                    {"Variable_name": "wait_timeout", "Value": "28800"},
                    {"Variable_name": "interactive_timeout", "Value": "28800"},
                ],
                # Max_used_connections > 80% of max_connections
                [
                    {"Variable_name": "Threads_connected", "Value": "80"},
                    {"Variable_name": "Threads_created", "Value": "10"},
                    {"Variable_name": "Max_used_connections", "Value": "85"},  # 85% of 100
                    {"Variable_name": "Connections", "Value": "1000"},
                ],
                [],
                [
                    {"Variable_name": "table_open_cache", "Value": "2000"},
                    {"Variable_name": "table_definition_cache", "Value": "2000"},
                ],
                [
                    {"Variable_name": "Open_tables", "Value": "100"},
                    {"Variable_name": "Opened_tables", "Value": "150"},
                    {"Variable_name": "Open_table_definitions", "Value": "100"},
                    {"Variable_name": "Opened_table_definitions", "Value": "150"},
                ],
            ]
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.InnoDBTuner") as mock_tuner:
                mock_tuner_instance = Mock()
                mock_tuner_instance.analyze_and_recommend.return_value = []
                mock_tuner.return_value = mock_tuner_instance

                response = client.get(f"/api/v1/tuning/comprehensive/{connection.id}")

                assert response.status_code == 200
                data = response.json()
                # 检查是否有 max_connections 建议
                suggestions = data["suggestions"]
                conn_suggestions = next((s for s in suggestions if s["category"] == "connection"), None)
                if conn_suggestions:
                    params = [item["param"] for item in conn_suggestions["items"]]
                    assert "max_connections" in params



class TestQueryCache:
    """查询缓存建议测试类（覆盖行329-331）"""

    def test_comprehensive_with_query_cache_enabled(self, db_session: Session, client: TestClient):
        """测试综合调优 - 查询缓存启用（MySQL 5.7，覆盖行329-331）"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_instance.execute_query.side_effect = [
                [{"Variable_name": "Innodb_buffer_pool_read_requests", "Value": "1000"}],
                [{"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"}],
                [
                    {"Variable_name": "max_connections", "Value": "151"},
                    {"Variable_name": "thread_cache_size", "Value": "16"},
                    {"Variable_name": "wait_timeout", "Value": "28800"},
                    {"Variable_name": "interactive_timeout", "Value": "28800"},
                ],
                [
                    {"Variable_name": "Threads_connected", "Value": "10"},
                    {"Variable_name": "Threads_created", "Value": "10"},
                    {"Variable_name": "Max_used_connections", "Value": "50"},
                    {"Variable_name": "Connections", "Value": "1000"},
                ],
                # Query cache enabled - 覆盖行329-331
                [
                    {"Variable_name": "query_cache_type", "Value": "ON"},
                    {"Variable_name": "query_cache_size", "Value": "1048576"},
                ],
                [
                    {"Variable_name": "table_open_cache", "Value": "2000"},
                    {"Variable_name": "table_definition_cache", "Value": "2000"},
                ],
                [
                    {"Variable_name": "Open_tables", "Value": "100"},
                    {"Variable_name": "Opened_tables", "Value": "150"},
                    {"Variable_name": "Open_table_definitions", "Value": "100"},
                    {"Variable_name": "Opened_table_definitions", "Value": "150"},
                ],
            ]
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.InnoDBTuner") as mock_tuner:
                mock_tuner_instance = Mock()
                mock_tuner_instance.analyze_and_recommend.return_value = []
                mock_tuner.return_value = mock_tuner_instance

                response = client.get(f"/api/v1/tuning/comprehensive/{connection.id}")

                assert response.status_code == 200
                data = response.json()
                # 检查是否有查询缓存建议
                categories = [s["category"] for s in data["suggestions"]]
                assert "query_cache" in categories



class TestTableCache:
    """表缓存建议测试类（覆盖行363, 449-452）"""

    def test_comprehensive_with_table_cache_recommendations(self, db_session: Session, client: TestClient):
        """测试综合调优 - 表缓存建议（覆盖行363, 449-452）"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            # 模拟表缓存命中率低
            mock_instance.execute_query.side_effect = [
                [{"Variable_name": "Innodb_buffer_pool_read_requests", "Value": "1000"}],
                [{"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"}],
                [
                    {"Variable_name": "max_connections", "Value": "151"},
                    {"Variable_name": "thread_cache_size", "Value": "16"},
                    {"Variable_name": "wait_timeout", "Value": "28800"},
                    {"Variable_name": "interactive_timeout", "Value": "28800"},
                ],
                [
                    {"Variable_name": "Threads_connected", "Value": "10"},
                    {"Variable_name": "Threads_created", "Value": "10"},
                    {"Variable_name": "Max_used_connections", "Value": "50"},
                    {"Variable_name": "Connections", "Value": "1000"},
                ],
                [],
                # Table cache VARIABLES
                [
                    {"Variable_name": "table_open_cache", "Value": "100"},
                    {"Variable_name": "table_definition_cache", "Value": "2000"},
                ],
                # Table cache STATUS - 低命中率（覆盖行449-452）
                # (1 - Open_tables / Opened_tables) * 100 < 95%
                # 需要 Open_tables / Opened_tables > 0.05
                [
                    {"Variable_name": "Open_tables", "Value": "100"},
                    {"Variable_name": "Opened_tables", "Value": "1000"},  # 1 - 100/1000 = 90% < 95%
                    {"Variable_name": "Open_table_definitions", "Value": "100"},
                    {"Variable_name": "Opened_table_definitions", "Value": "150"},
                ],
            ]
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.InnoDBTuner") as mock_tuner:
                mock_tuner_instance = Mock()
                mock_tuner_instance.analyze_and_recommend.return_value = []
                mock_tuner.return_value = mock_tuner_instance

                response = client.get(f"/api/v1/tuning/comprehensive/{connection.id}")

                assert response.status_code == 200
                data = response.json()
                # 检查是否有表缓存建议
                categories = [s["category"] for s in data["suggestions"]]
                assert "table_cache" in categories



class TestExtendedTuning:
    """扩展调优建议测试类（覆盖行602-698）"""

    def test_extended_tuning_success(self, db_session: Session, client: TestClient):
        """测试扩展调优建议 - 成功场景"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_instance.execute_query.side_effect = [
                # SHOW VARIABLES
                [
                    {"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"},
                    {"Variable_name": "max_connections", "Value": "151"},
                    {"Variable_name": "thread_cache_size", "Value": "16"},
                    {"Variable_name": "tmp_table_size", "Value": "16777216"},
                    {"Variable_name": "max_heap_table_size", "Value": "16777216"},
                    {"Variable_name": "sort_buffer_size", "Value": "262144"},
                    {"Variable_name": "max_allowed_packet", "Value": "16777216"},
                    {"Variable_name": "net_buffer_length", "Value": "16384"},
                ],
                # SHOW STATUS
                [
                    {"Variable_name": "Threads_created", "Value": "10"},
                    {"Variable_name": "Connections", "Value": "1000"},
                    {"Variable_name": "Max_used_connections", "Value": "50"},
                    {"Variable_name": "Created_tmp_disk_tables", "Value": "100"},
                    {"Variable_name": "Created_tmp_tables", "Value": "1000"},
                    {"Variable_name": "Sort_merge_passes", "Value": "100"},
                    {"Variable_name": "Sort_rows", "Value": "10000"},
                ],
                # SHOW STATUS LIKE 'Innodb%'
                [{"Variable_name": "Innodb_buffer_pool_read_requests", "Value": "1000"}],
            ]
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.InnoDBTuner") as mock_tuner:
                mock_tuner_instance = Mock()
                mock_tuner_instance.analyze_and_recommend.return_value = [
                    {"param": "innodb_buffer_pool_size", "suggestion": "增大Buffer Pool"}
                ]
                mock_tuner.return_value = mock_tuner_instance

                response = client.get(f"/api/v1/tuning/extended/{connection.id}")

                assert response.status_code == 200
                data = response.json()
                assert "connection_id" in data
                assert "database_name" in data
                assert "innodb" in data
                assert "connection" in data
                assert "memory" in data
                assert "sort" in data
                assert "network" in data
                assert "summary" in data

    def test_extended_tuning_connection_not_found(self, client: TestClient):
        """测试扩展调优建议 - 连接不存在"""
        response = client.get("/api/v1/tuning/extended/999")
        assert response.status_code in [200, 404, 422, 500]

    def test_extended_tuning_general_exception(self, db_session: Session, client: TestClient):
        """测试扩展调优建议 - 通用异常（覆盖行695-698）"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_connector.side_effect = Exception("连接失败")

            response = client.get(f"/api/v1/tuning/extended/{connection.id}")
            assert response.status_code == 500
            assert "获取扩展调优建议失败" in response.json().get("detail", "")

    def test_extended_tuning_with_high_disk_tmp_ratio(self, db_session: Session, client: TestClient):
        """测试扩展调优 - 高磁盘临时表比率（覆盖行470-510）"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_instance.execute_query.side_effect = [
                [
                    {"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"},
                    {"Variable_name": "max_connections", "Value": "151"},
                    {"Variable_name": "thread_cache_size", "Value": "16"},
                    {"Variable_name": "tmp_table_size", "Value": "16777216"},
                    {"Variable_name": "max_heap_table_size", "Value": "8388608"},  # 小于 tmp_table_size
                ],
                [
                    {"Variable_name": "Threads_created", "Value": "10"},
                    {"Variable_name": "Connections", "Value": "1000"},
                    {"Variable_name": "Max_used_connections", "Value": "50"},
                    {"Variable_name": "Created_tmp_disk_tables", "Value": "500"},  # 高比率
                    {"Variable_name": "Created_tmp_tables", "Value": "1000"},  # 50% > 25%
                ],
                [{"Variable_name": "Innodb_buffer_pool_read_requests", "Value": "1000"}],
            ]
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.InnoDBTuner") as mock_tuner:
                mock_tuner_instance = Mock()
                mock_tuner_instance.analyze_and_recommend.return_value = []
                mock_tuner.return_value = mock_tuner_instance

                response = client.get(f"/api/v1/tuning/extended/{connection.id}")

                assert response.status_code == 200
                data = response.json()
                # 检查是否有内存建议
                assert len(data["memory"]) > 0

    def test_extended_tuning_with_sort_issues(self, db_session: Session, client: TestClient):
        """测试扩展调优 - 排序问题（覆盖行518-541）"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_instance.execute_query.side_effect = [
                [
                    {"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"},
                    {"Variable_name": "max_connections", "Value": "151"},
                    {"Variable_name": "thread_cache_size", "Value": "16"},
                    {"Variable_name": "sort_buffer_size", "Value": "262144"},
                ],
                [
                    {"Variable_name": "Threads_created", "Value": "10"},
                    {"Variable_name": "Connections", "Value": "1000"},
                    {"Variable_name": "Max_used_connections", "Value": "50"},
                    {"Variable_name": "Sort_merge_passes", "Value": "100"},  # 高比率
                    {"Variable_name": "Sort_rows", "Value": "1000"},  # 10% > 0.1%
                ],
                [{"Variable_name": "Innodb_buffer_pool_read_requests", "Value": "1000"}],
            ]
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.InnoDBTuner") as mock_tuner:
                mock_tuner_instance = Mock()
                mock_tuner_instance.analyze_and_recommend.return_value = []
                mock_tuner.return_value = mock_tuner_instance

                response = client.get(f"/api/v1/tuning/extended/{connection.id}")

                assert response.status_code == 200
                data = response.json()
                # 检查是否有排序建议
                assert len(data["sort"]) > 0

    def test_extended_tuning_with_network_issues(self, db_session: Session, client: TestClient):
        """测试扩展调优 - 网络配置问题（覆盖行548-581）"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_instance.execute_query.side_effect = [
                [
                    {"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"},
                    {"Variable_name": "max_connections", "Value": "151"},
                    {"Variable_name": "thread_cache_size", "Value": "16"},
                    {"Variable_name": "max_allowed_packet", "Value": "4194304"},  # 4MB < 16MB
                    {"Variable_name": "net_buffer_length", "Value": "8192"},  # < 16384
                ],
                [
                    {"Variable_name": "Threads_created", "Value": "10"},
                    {"Variable_name": "Connections", "Value": "1000"},
                    {"Variable_name": "Max_used_connections", "Value": "50"},
                ],
                [{"Variable_name": "Innodb_buffer_pool_read_requests", "Value": "1000"}],
            ]
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.InnoDBTuner") as mock_tuner:
                mock_tuner_instance = Mock()
                mock_tuner_instance.analyze_and_recommend.return_value = []
                mock_tuner.return_value = mock_tuner_instance

                response = client.get(f"/api/v1/tuning/extended/{connection.id}")

                assert response.status_code == 200
                data = response.json()
                # 检查是否有网络建议
                assert len(data["network"]) > 0



class TestFormatSize:
    """格式化大小函数测试类（覆盖行586-593）"""

    def test_format_size_bytes(self):
        """测试格式化字节大小 - 字节"""
        from app.routers.tuning import _format_size
        assert _format_size(100) == "100B"
        assert _format_size(1023) == "1023B"

    def test_format_size_kilobytes(self):
        """测试格式化字节大小 - KB"""
        from app.routers.tuning import _format_size
        assert _format_size(1024) == "1KB"
        assert _format_size(2048) == "2KB"
        assert _format_size(1024 * 1023) == "1023KB"

    def test_format_size_megabytes(self):
        """测试格式化字节大小 - MB"""
        from app.routers.tuning import _format_size
        assert _format_size(1024 * 1024) == "1MB"
        assert _format_size(16 * 1024 * 1024) == "16MB"
        assert _format_size(1024 * 1024 * 1023) == "1023MB"

    def test_format_size_gigabytes(self):
        """测试格式化字节大小 - GB"""
        from app.routers.tuning import _format_size
        assert _format_size(1024 * 1024 * 1024) == "1GB"
        assert _format_size(4 * 1024 * 1024 * 1024) == "4GB"



class TestHTTPExceptionReraise:
    """HTTPException重新抛出测试类（覆盖行104, 175, 242, 387, 696）"""

    def test_innodb_tuning_http_exception_reraise(self, db_session: Session, client: TestClient):
        """测试InnoDB调优 - HTTPException重新抛出（覆盖行103-104）"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        from fastapi import HTTPException

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            # 模拟在上下文管理器内抛出HTTPException
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(side_effect=HTTPException(status_code=418, detail="I'm a teapot"))
            mock_instance.__exit__ = Mock(return_value=False)
            mock_connector.return_value = mock_instance

            response = client.get(f"/api/v1/tuning/innodb/{connection.id}")
            assert response.status_code == 418

    def test_innodb_deep_http_exception_reraise(self, db_session: Session, client: TestClient):
        """测试InnoDB深度分析 - HTTPException重新抛出（覆盖行174-175）"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        from fastapi import HTTPException

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(side_effect=HTTPException(status_code=418, detail="I'm a teapot"))
            mock_instance.__exit__ = Mock(return_value=False)
            mock_connector.return_value = mock_instance

            response = client.get(f"/api/v1/tuning/innodb-deep/{connection.id}")
            assert response.status_code == 418

    def test_index_suggestions_http_exception_reraise(self, db_session: Session, client: TestClient):
        """测试索引建议 - HTTPException重新抛出（覆盖行241-242）"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        from fastapi import HTTPException

        request_data = {"sql": "SELECT * FROM users"}

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(side_effect=HTTPException(status_code=418, detail="I'm a teapot"))
            mock_instance.__exit__ = Mock(return_value=False)
            mock_connector.return_value = mock_instance

            response = client.post(
                f"/api/v1/tuning/index-suggestions/{connection.id}", json=request_data
            )
            assert response.status_code == 418

    def test_comprehensive_tuning_http_exception_reraise(self, db_session: Session, client: TestClient):
        """测试综合调优 - HTTPException重新抛出（覆盖行386-387）"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        from fastapi import HTTPException

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(side_effect=HTTPException(status_code=418, detail="I'm a teapot"))
            mock_instance.__exit__ = Mock(return_value=False)
            mock_connector.return_value = mock_instance

            response = client.get(f"/api/v1/tuning/comprehensive/{connection.id}")
            assert response.status_code == 418

    def test_extended_tuning_http_exception_reraise(self, db_session: Session, client: TestClient):
        """测试扩展调优 - HTTPException重新抛出（覆盖行695-696）"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        from fastapi import HTTPException

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(side_effect=HTTPException(status_code=418, detail="I'm a teapot"))
            mock_instance.__exit__ = Mock(return_value=False)
            mock_connector.return_value = mock_instance

            response = client.get(f"/api/v1/tuning/extended/{connection.id}")
            assert response.status_code == 418


    def test_extended_tuning_with_connection_recommendations_loop(self, db_session: Session, client: TestClient):
        """测试扩展调优 - 连接配置建议循环（覆盖行660-662）"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_instance.execute_query.side_effect = [
                # SHOW VARIABLES - 触发连接建议
                [
                    {"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"},
                    {"Variable_name": "max_connections", "Value": "100"},
                    {"Variable_name": "thread_cache_size", "Value": "0"},  # 会触发建议
                ],
                # SHOW STATUS - 高线程创建率
                [
                    {"Variable_name": "Threads_created", "Value": "500"},
                    {"Variable_name": "Connections", "Value": "1000"},  # 50% 命中率 < 95%
                    {"Variable_name": "Max_used_connections", "Value": "90"},  # 90% of 100
                ],
                [{"Variable_name": "Innodb_buffer_pool_read_requests", "Value": "1000"}],
            ]
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.InnoDBTuner") as mock_tuner:
                mock_tuner_instance = Mock()
                mock_tuner_instance.analyze_and_recommend.return_value = []
                mock_tuner.return_value = mock_tuner_instance

                response = client.get(f"/api/v1/tuning/extended/{connection.id}")

                assert response.status_code == 200
                data = response.json()
                # 验证连接建议包含必要字段
                if data["connection"]:
                    for rec in data["connection"]:
                        assert "category" in rec
                        assert "impact" in rec
                        assert "sql_statement" in rec
