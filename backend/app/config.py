"""
配置管理模块
使用 Pydantic Settings 管理应用配置
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, ValidationInfo
from typing import List
import os
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @field_validator("database_url", "secret_key", mode="before")
    @classmethod
    def validate_required_config(cls, v: str, info: ValidationInfo) -> str:
        """验证必须的配置项"""
        if not v or not v.strip():
            field_name = info.field_name
            # 尝试从环境变量获取
            env_value = os.environ.get(field_name.upper())
            if env_value:
                return env_value
            raise ValueError(
                f"配置项 '{field_name}' 未设置。请在 .env 文件中设置 {field_name.upper()} "
                f"或通过环境变量提供"
            )
        return v

    @field_validator("debug", mode="before")
    @classmethod
    def validate_debug_mode(cls, v: bool) -> bool:
        """验证 debug 模式"""
        if v and os.environ.get("ENVIRONMENT", "development").lower() == "production":
            logger.warning("生产环境中 debug 模式已启用，建议设置 debug=false")
        return v
    @property
    def cors_origins_list(self) -> List[str]:
        """将 CORS origins 字符串转换为列表"""
        if not self.backend_cors_origins:
            return []
        return [origin.strip() for origin in self.backend_cors_origins.split(",")]

    # ==================== 应用信息 ====================
    app_name: str = "MySQL性能诊断系统"
    app_version: str = "1.0.0"
    debug: bool = True

    # ==================== 数据库配置 ====================
    # 系统自己的数据库（存储配置、指标、分析结果等）
    database_url: str

    # ==================== 目标MySQL数据库配置（被监控的数据库）====================
    target_mysql_host: str = "localhost"
    target_mysql_port: int = 3306
    target_mysql_user: str = ""
    target_mysql_password: str = ""
    target_mysql_database: str = ""

    # ==================== Redis配置 ====================
    redis_url: str = ""
    redis_password: str = ""
    redis_cache_ttl: int = 3600

    # ==================== CORS配置 ====================
    backend_cors_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:3000"

    # ==================== JWT配置 ====================
    # ==================== 密码加密配置 ====================
    password_encryption_key: str = ""

    # ==================== JWT配置 ====================
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # ==================== Celery配置 ====================
    celery_broker_url: str = ""
    celery_result_backend: str = ""
    celery_task_always_eager: bool = False

    # ==================== 任务中心配置 ====================
    task_execution_mode: str = "auto"  # auto / celery / local
    task_queue_name: str = "analysis"
    task_stale_timeout_seconds: int = 300
    task_stream_poll_interval: float = 1.0
    task_heartbeat_interval_seconds: int = 15

    # ==================== 性能采集配置 ====================
    metrics_collection_interval: int = 60
    slow_query_threshold: float = 1.0
    slow_query_log_path: str = "/var/log/mysql/slow-query.log"

    # ==================== 日志配置 ====================
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    # ==================== 邮件配置 ====================
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@example.com"
    smtp_use_tls: bool = True

    # ==================== AI 配置 ====================
    # AI 服务总开关
    ai_enabled: bool = True
    ai_provider: str = "zhipu"  # zhipu / kimi / openai / claude

    # Kimi AI (默认使用 Coding API 端点)
    kimi_api_key: str = ""
    kimi_api_base: str = "https://api.kimi.com/coding/v1"
    kimi_model: str = "kimi-for-coding"

    # 智谱 AI GLM (可选)
    zhipu_api_key: str = ""
    zhipu_api_base: str = "https://open.bigmodel.cn/api/coding/paas/v4"
    zhipu_model: str = "GLM-5"

    # OpenAI (可选)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"

    # Claude (可选)
    anthropic_api_key: str = ""
    claude_model: str = "claude-3-5-sonnet-20241022"


    # AI 限流配置
    ai_rate_limit_requests: int = 100  # 每小时请求数限制
    ai_max_tokens: int = 16384  # 最大 token 数（GLM-5 coding 端点支持 16384）
    ai_timeout: int = 900  # 请求超时（秒），默认 15 分钟
    ai_timeout_max: int = 900  # 最大请求超时（秒），15 分钟
    ai_temperature: float = 0.3  # 默认温度
    
    # AI 缓存配置
    ai_cache_enabled: bool = True  # 是否启用缓存
    ai_cache_ttl: int = 1800  # 缓存过期时间（秒），默认 30 分钟
    ai_cache_max_size: int = 1000  # 内存缓存最大条目数
    ai_context_default_depth: str = "standard"  # 默认采集深度: quick/standard/deep


# 创建全局配置实例
settings = Settings()
