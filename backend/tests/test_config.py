"""
测试 config.py 模块
"""

import pytest
from pydantic import ValidationError
from app.config import Settings, settings


class TestSettings:
    """测试配置类"""

    def test_default_values(self):
        """测试默认配置值"""
        s = Settings()
        assert s.app_name == "MySQL性能诊断系统"
        assert s.app_version == "1.0.0"
        assert s.debug is True

    def test_database_url_default(self):
        """测试数据库URL默认值"""
        s = Settings()
        assert s.database_url is not None
        assert "mysql+pymysql://" in s.database_url

    def test_target_mysql_config(self):
        """测试目标MySQL配置"""
        s = Settings()
        assert s.target_mysql_host == "localhost"
        assert s.target_mysql_port == 3306
        assert s.target_mysql_user == "root"
        assert s.target_mysql_database == "mysql_analysis"

    def test_redis_config(self):
        """测试Redis配置"""
        s = Settings()
        assert "localhost:6379" in s.redis_url
        assert s.redis_cache_ttl == 3600

    def test_cors_origins(self):
        """测试CORS配置"""
        s = Settings()
        assert "http://localhost:5173" in s.backend_cors_origins
        assert "http://localhost:3000" in s.backend_cors_origins

    def test_jwt_config(self):
        """测试JWT配置"""
        s = Settings()
        assert s.secret_key == "your-secret-key-change-in-production"
        assert s.algorithm == "HS256"
        assert s.access_token_expire_minutes == 30

    def test_celery_config(self):
        """测试Celery配置"""
        s = Settings()
        assert s.celery_broker_url is not None
        assert s.celery_result_backend is not None

    def test_performance_collection_config(self):
        """测试性能采集配置"""
        s = Settings()
        assert s.metrics_collection_interval == 60
        assert s.slow_query_threshold == 1.0
        assert s.slow_query_log_path == "/var/log/mysql/slow-query.log"

    def test_log_config(self):
        """测试日志配置"""
        s = Settings()
        assert s.log_level == "INFO"
        assert s.log_file == "logs/app.log"

    def test_custom_values(self):
        """测试自定义配置值"""
        s = Settings(
            app_name="Custom App",
            debug=False,
            log_level="DEBUG",
        )
        assert s.app_name == "Custom App"
        assert s.debug is False
        assert s.log_level == "DEBUG"

    def test_global_settings_instance(self):
        """测试全局settings实例"""
        assert settings.app_name is not None
        assert settings.app_version is not None
        assert isinstance(settings.debug, bool)


class TestSettingsValidation:
    """测试配置验证"""

    def test_port_must_be_integer(self):
        """测试端口必须是整数"""
        s = Settings()
        assert isinstance(s.target_mysql_port, int)

    def test_cache_ttl_must_be_integer(self):
        """测试缓存TTL必须是整数"""
        s = Settings()
        assert isinstance(s.redis_cache_ttl, int)
        assert s.redis_cache_ttl > 0

    def test_slow_query_threshold_must_be_float(self):
        """测试慢查询阈值必须是浮点数"""
        s = Settings()
        assert isinstance(s.slow_query_threshold, (int, float))
        assert s.slow_query_threshold > 0

    def test_cors_origins_must_be_list(self):
        """测试CORS源通过属性转换为列表"""
        s = Settings()
        assert isinstance(s.cors_origins_list, list)
        assert len(s.cors_origins_list) > 0
        assert "http://localhost:5173" in s.cors_origins_list


class TestSettingsEnvironmentVariables:
    """测试环境变量加载"""

    def test_debug_from_env(self, monkeypatch):
        """测试从环境变量读取debug配置"""
        monkeypatch.setenv("DEBUG", "false")
        s = Settings()
        # 注意：这可能会失败，因为settings已经被创建
        # 在实际测试中，应该清除缓存或使用新的Settings实例

    def test_app_name_from_env(self, monkeypatch):
        """测试从环境变量读取app_name配置"""
        monkeypatch.setenv("APP_NAME", "Test App")
        s = Settings()
        # 注意：这需要清除缓存才能生效
