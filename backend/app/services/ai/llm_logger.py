"""
LLM 专用日志模块
提供 LLM API 调用的结构化日志记录
"""

import logging
import os
from typing import Optional


class LLMLogger:
    """LLM API 调用日志记录器"""

    def __init__(self, provider: str):
        """
        初始化 LLM 日志记录器

        Args:
            provider: LLM 提供商名称（如 zhipu, openai, anthropic）
        """
        self.provider = provider
        self.logger = logging.getLogger(f"llm.{provider}")

        # 从环境变量读取日志级别，默认 INFO
        log_level = os.getenv("LLM_LOG_LEVEL", "INFO").upper()
        self.logger.setLevel(getattr(logging, log_level))

        # 如果没有处理器，添加一个
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        # 禁止日志传播到根 logger，避免重复输出
        self.logger.propagate = False

    def log_request(
        self,
        model: str,
        temperature: float,
        max_tokens: int,
        message_count: int,
        prompt_preview: Optional[str] = None,
    ) -> None:
        """
        记录 LLM 请求开始

        Args:
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            message_count: 消息数量
            prompt_preview: 提示词预览（可选）
        """
        # INFO 级别：摘要信息
        prompt_summary = ""
        if prompt_preview:
            prompt_summary = prompt_preview[:100]
            if len(prompt_preview) > 100:
                prompt_summary += "..."

        self.logger.info(
            f"[LLM Request] provider={self.provider} model={model} "
            f"temperature={temperature} messages={message_count}"
            + (f" prompt_preview={prompt_summary}" if prompt_summary else "")
        )

        # DEBUG 级别：完整内容
        if self.logger.isEnabledFor(logging.DEBUG) and prompt_preview:
            self.logger.debug(
                f"[LLM Request Details] provider={self.provider} model={model}\n"
                f"temperature={temperature} max_tokens={max_tokens}\n"
                f"messages={message_count}\n"
                f"prompt_preview:\n{prompt_preview}"
            )

    def log_response(
        self,
        duration: float,
        prompt_tokens: int,
        completion_tokens: int,
        response_len: int,
        response_content: Optional[str] = None,
    ) -> None:
        """
        记录 LLM 响应成功

        Args:
            duration: 请求耗时（秒）
            prompt_tokens: 提示词 token 数
            completion_tokens: 完成 token 数
            response_len: 响应文本长度
            response_content: 响应内容（可选）
        """
        total_tokens = prompt_tokens + completion_tokens

        # INFO 级别：摘要信息
        response_summary = ""
        if response_content:
            response_summary = response_content[:200]
            if len(response_content) > 200:
                response_summary += "..."

        self.logger.info(
            f"[LLM Response] provider={self.provider} "
            f"duration={duration:.2f}s "
            f"tokens={prompt_tokens}+{completion_tokens}={total_tokens} "
            f"response_len={response_len}"
            + (f" response_preview={response_summary}" if response_summary else "")
        )

        # DEBUG 级别：完整响应内容
        if self.logger.isEnabledFor(logging.DEBUG) and response_content:
            self.logger.debug(
                f"[LLM Response Details] provider={self.provider}\n"
                f"duration={duration:.2f}s\n"
                f"response_content:\n{response_content}"
            )

    def log_error(
        self,
        error: Exception,
        duration: float,
        request_payload: Optional[dict] = None,
        response_text: Optional[str] = None,
    ) -> None:
        """
        记录 LLM 错误详情

        Args:
            error: 异常对象
            duration: 请求耗时（秒）
            request_payload: 请求载荷（可选）
            response_text: 响应文本（可选）
        """
        error_type = type(error).__name__
        error_message = str(error)

        # INFO 级别：错误摘要
        self.logger.error(
            f"[LLM Error] provider={self.provider} "
            f"error_type={error_type} "
            f"duration={duration:.2f}s "
            f"error_message={error_message}"
        )

        # DEBUG 级别：完整请求/响应内容
        if self.logger.isEnabledFor(logging.DEBUG):
            debug_info = [f"[LLM Error Details] provider={self.provider}"]
            debug_info.append(f"error_type={error_type}")
            debug_info.append(f"error_message={error_message}")
            debug_info.append(f"duration={duration:.2f}s")

            if request_payload:
                debug_info.append(f"request_payload={request_payload}")

            if response_text:
                debug_info.append(f"response_text={response_text}")

            self.logger.debug("\n".join(debug_info))

    @staticmethod
    def mask_api_key(api_key: str) -> str:
        """
        脱敏 API Key，只显示前4位和后4位

        Args:
            api_key: API 密钥

        Returns:
            脱敏后的 API 密钥
        """
        if not api_key:
            return "***"

        if len(api_key) <= 8:
            # 太短的 key，只显示首尾各2位
            return f"{api_key[:2]}...{api_key[-2:]}" if len(api_key) >= 4 else "***"

        # 显示前4位和后4位
        return f"{api_key[:4]}...{api_key[-4:]}"
