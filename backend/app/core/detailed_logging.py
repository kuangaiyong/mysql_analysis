"""
增强的日志配置
提供详细的错误堆栈跟踪和调试信息
"""

import logging
import sys
import traceback
from datetime import datetime
from typing import Any, Dict
import json


class DetailedFormatter(logging.Formatter):
    """详细的日志格式化器，包含完整上下文信息"""
    
    def format(self, record: logging.LogRecord) -> str:
        # 基础格式
        base_format = super().format(record)
        
        # 如果是错误日志，添加额外信息
        if record.levelno >= logging.ERROR:
            # 添加时间戳
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            # 添加文件和行号
            location = f"{record.filename}:{record.lineno}"
            
            # 添加函数名
            function = record.funcName
            
            # 构建详细信息
            details = [
                f"\n{'='*80}",
                f"[ERROR DETAILS] {timestamp}",
                f"Location: {location}",
                f"Function: {function}",
                f"Message: {record.getMessage()}",
            ]
            
            # 如果有异常信息，添加堆栈
            if record.exc_info:
                details.append("\n[EXCEPTION INFO]")
                exc_type, exc_value, exc_traceback = record.exc_info
                details.append(f"Exception Type: {exc_type.__name__}")
                details.append(f"Exception Value: {exc_value}")
                details.append("\n[STACK TRACE]")
                stack_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
                details.extend(stack_lines)
            
            # 如果有额外属性（如 request_id）
            if hasattr(record, 'request_id'):
                details.append(f"\nRequest ID: {record.request_id}")
            
            if hasattr(record, 'user_id'):
                details.append(f"User ID: {record.user_id}")
            
            details.append(f"{'='*80}\n")
            
            return base_format + "\n" + "\n".join(details)
        
        return base_format


def setup_detailed_logging(log_level: str = "INFO"):
    """
    设置详细的日志配置
    
    Args:
        log_level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    """
    # 创建格式化器
    formatter = DetailedFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 移除所有现有处理器
    root_logger.handlers = []
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 添加文件处理器
    file_handler = logging.FileHandler("logs/app_detailed.log")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    return root_logger


def log_error_with_context(
    logger: logging.Logger,
    message: str,
    error: Exception,
    context: Dict[str, Any] = None
):
    """
    记录带有详细上下文的错误
    
    Args:
        logger: 日志记录器
        message: 错误消息
        error: 异常对象
        context: 额外上下文信息
    """
    # 构建错误信息
    error_info = {
        "message": message,
        "error_type": type(error).__name__,
        "error_value": str(error),
        "timestamp": datetime.now().isoformat(),
    }
    
    # 添加上下文
    if context:
        error_info["context"] = context
    
    # 添加堆栈信息
    error_info["stack_trace"] = traceback.format_exc()
    
    # 记录错误
    logger.error(
        f"{message}: {error}",
        exc_info=True,
        extra={"error_details": error_info}
    )
    
    # 同时打印到控制台（方便调试）
    print(f"\n{'='*80}")
    print(f"[ERROR] {message}")
    print(f"Type: {error_info['error_type']}")
    print(f"Value: {error_info['error_value']}")
    if context:
        print(f"Context: {json.dumps(context, indent=2, ensure_ascii=False)}")
    print(f"Stack Trace:\n{error_info['stack_trace']}")
    print(f"{'='*80}\n")
