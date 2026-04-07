"""
日志配置模块
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from app.config import settings


def setup_logging():
    """配置应用日志"""

    # 日志文件路径（处理相对于backend目录的路径）
    log_file_path = Path(settings.log_file)

    # 确保日志目录存在
    log_file_path.parent.mkdir(exist_ok=True, parents=True)

    # 日志文件完整路径
    log_file = log_file_path.resolve()

    # 配置日志格式
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # 配置日志处理器
    handlers = [
        # 控制台处理器
        logging.StreamHandler(sys.stdout),
        # 文件处理器（带轮转）
        RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        ),
    ]

    # 配置根日志记录器
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=handlers,
        force=True,
    )

    # 设置SQLAlchemy日志级别
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

    # 设置uvicorn日志级别
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    # 获取根日志记录器
    logger = logging.getLogger(__name__)
    logger.info(f"日志系统初始化完成，日志级别: {settings.log_level}")
    logger.info(f"日志文件: {log_file.absolute()}")

    return logger


# 初始化日志
app_logger = setup_logging()
