"""
LLM 适配器模块

支持多种 LLM 提供商的统一接口
"""

import asyncio
import json
import logging
import time
import httpx
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List, Optional
from decimal import Decimal
from app.services.ai.llm_logger import LLMLogger
from app.services.ai.utils import DecimalEncoder

logger = logging.getLogger(__name__)

# 重试配置
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0  # 秒
RETRY_MAX_DELAY = 30.0  # 秒
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def extract_json_from_markdown(text: str) -> Any:
    """
    从 markdown 代码块中提取 JSON

    支持 ```json ... ``` 或 ``` ... ``` 格式
    如果不是 markdown 格式，则尝试直接解析为 JSON

    Args:
        text: 可能包含 JSON 的文本

    Returns:
        解析后的 Python 对象

    Raises:
        json.JSONDecodeError: 当无法解析为 JSON 时
    """
    text = text.strip()

    # 尝试提取 ```json ... ``` 代码块
    if "```json" in text:
        json_str = text.split("```json")[1].split("```")[0].strip()
        return json.loads(json_str)

    # 尝试提取 ``` ... ``` 代码块（不带语言标记）
    elif "```" in text:
        json_str = text.split("```")[1].split("```")[0].strip()
        return json.loads(json_str)

    # 尝试直接解析
    else:
        return json.loads(text)


class LLMAdapter(ABC):
    """LLM 适配器基类"""

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """
        发送对话请求

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            system_prompt: 系统提示
            temperature: 温度参数 (0-1)
            max_tokens: 最大 token 数

        Returns:
            模型回复文本
        """
        pass

    @abstractmethod
    async def analyze(
        self,
        prompt: str,
        data: Optional[Dict[str, Any]] = None,
        response_format: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        分析数据并返回结构化结果

        Args:
            prompt: 分析提示
            data: 附加数据
            response_format: 响应格式要求

        Returns:
            结构化分析结果
        """
        pass

    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return self.__class__.__name__.replace("Adapter", "").lower()

    async def chat_with_retry(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        max_retries: int = MAX_RETRIES,
    ) -> str:
        """
        带指数退避重试的 chat 调用

        对超时、429、5xx 错误自动重试
        """
        last_error: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                return await self.chat(
                    messages=messages,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as e:
                last_error = e
                err_str = str(e)
                is_retryable = (
                    isinstance(e, httpx.TimeoutException)
                    or "超时" in err_str
                    or "timeout" in err_str.lower()
                    or any(str(code) in err_str for code in RETRYABLE_STATUS_CODES)
                )
                if not is_retryable or attempt == max_retries - 1:
                    raise
                delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
                logger.warning(
                    f"{self.get_provider_name()} 请求失败 (第 {attempt + 1} 次)，"
                    f"{delay:.1f}s 后重试: {err_str[:100]}"
                )
                await asyncio.sleep(delay)
        raise last_error  # type: ignore

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """
        流式 chat — 逐 chunk 返回文本

        默认实现: 降级为非流式（一次性返回完整结果）
        子类可覆盖以实现真正的 SSE 流式输出
        """
        result = await self.chat(messages, system_prompt, temperature, max_tokens)
        yield result


class ZhipuAdapter(LLMAdapter):
    """
    智谱 AI GLM 适配器

    使用 Coding API 端点: https://open.bigmodel.cn/api/coding/paas/v4
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://open.bigmodel.cn/api/coding/paas/v4",
        model: str = "GLM-4",
        timeout: int = 300,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

        # API 端点
        self.chat_endpoint = f"{self.base_url}/chat/completions"

        # 初始化 LLM 日志记录器
        self.llm_logger = LLMLogger("zhipu")
        logger.info(
            f"ZhipuAdapter 初始化完成，API Key: {LLMLogger.mask_api_key(self.api_key)}"
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """发送对话请求"""
        start_time = time.time()

        # 构建消息列表
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        # 构建 prompt_preview
        prompt_preview_parts = []
        if system_prompt:
            prompt_preview_parts.append(f"[System]: {system_prompt[:200]}")
        for msg in full_messages[:3]:  # 最多3条消息
            prompt_preview_parts.append(f"[{msg['role']}]: {msg['content'][:100]}")
        prompt_preview = "\n".join(prompt_preview_parts)[:500]

        # 记录请求开始
        self.llm_logger.log_request(
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            message_count=len(full_messages),
            prompt_preview=prompt_preview,
        )

        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.chat_endpoint, headers=headers, json=payload
                )

                if response.status_code != 200:
                    error_text = response.text
                    duration = time.time() - start_time
                    self.llm_logger.log_error(
                        error=Exception(f"API 错误: {response.status_code}"),
                        duration=duration,
                        response_text=error_text,
                    )
                    raise Exception(
                        f"GLM API 请求失败: {response.status_code} - {error_text}"
                    )

                result = response.json()

                # 解析响应
                if "choices" in result and len(result["choices"]) > 0:
                    choice = result["choices"][0]
                    message = choice.get("message", {})
                    content = message.get("content") or ""
                    finish_reason = choice.get("finish_reason", "unknown")
                    duration = time.time() - start_time

                    # 推理模型回退：若 content 为空但有 reasoning_content，尝试从中提取
                    if not content and finish_reason == "length":
                        reasoning = message.get("reasoning_content", "")
                        if reasoning:
                            logger.warning(
                                f"GLM API content 为空（finish_reason=length），"
                                f"尝试从 reasoning_content 中提取结果"
                            )
                            content = reasoning

                    # 提取 token 使用量
                    usage = result.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)

                    # 记录响应成功
                    self.llm_logger.log_response(
                        duration=duration,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        response_len=len(content),
                        response_content=content,
                    )

                    if not content:
                        logger.error(
                            f"GLM API 返回空内容: finish_reason={finish_reason}, usage={usage}, raw_choice={choice}"
                        )
                        raise Exception(
                            f"GLM API 返回空内容（finish_reason={finish_reason}），请尝试减少输入数据量或检查模型配置"
                        )

                    return content
                else:
                    duration = time.time() - start_time
                    self.llm_logger.log_error(
                        error=Exception("响应格式异常"),
                        duration=duration,
                        response_text=str(result),
                    )
                    raise Exception("GLM API 响应格式异常")

        except httpx.TimeoutException as e:
            duration = time.time() - start_time
            self.llm_logger.log_error(error=e, duration=duration)
            raise Exception("GLM API 请求超时，请稍后重试")
        except Exception as e:
            duration = time.time() - start_time
            self.llm_logger.log_error(error=e, duration=duration)
            raise

    async def analyze(
        self,
        prompt: str,
        data: Optional[Dict[str, Any]] = None,
        response_format: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """分析数据并返回结构化结果"""

        # 构建分析提示
        analysis_prompt = prompt
        if data:
            analysis_prompt += f"\n\n## 数据\n```json\n{json.dumps(data, ensure_ascii=False, indent=2, cls=DecimalEncoder)}\n```"

        if response_format and response_format.get("type") == "json_object":
            analysis_prompt += "\n\n请以 JSON 格式返回结果。"

        messages = [{"role": "user", "content": analysis_prompt}]

        response = await self.chat(messages, temperature=0.2)

        # 尝试解析 JSON
        try:
            # 尝试提取 JSON 块
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            else:
                # 尝试直接解析
                return json.loads(response)
        except json.JSONDecodeError:
            # 返回原始文本
            return {"raw_response": response}

    def get_provider_name(self) -> str:
        return "zhipu"

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """智谱 GLM 真流式输出"""
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST", self.chat_endpoint, headers=headers, json=payload
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        raise Exception(f"GLM API 流式请求失败: {response.status_code} - {error_text.decode()}")

                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

            duration = time.time() - start_time
            self.llm_logger.log_response(
                duration=duration,
                prompt_tokens=0,
                completion_tokens=0,
                response_len=0,
                response_content="[streamed]",
            )
        except Exception as e:
            duration = time.time() - start_time
            self.llm_logger.log_error(error=e, duration=duration)
            raise


class OpenAIAdapter(LLMAdapter):
    """OpenAI 适配器"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
        timeout: int = 300,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

        self.logger = logging.getLogger(__name__)
        self.llm_logger = LLMLogger("openai")

        self.chat_endpoint = f"{self.base_url}/chat/completions"

        self.logger.info(
            f"OpenAIAdapter 初始化完成，API Key: {LLMLogger.mask_api_key(self.api_key)}"
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """发送对话请求"""

        start_time = time.time()

        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        # 构建 prompt_preview
        prompt_preview_parts = []
        if system_prompt:
            prompt_preview_parts.append(f"[System]: {system_prompt[:200]}")
        for msg in full_messages[:3]:  # 最多3条消息
            prompt_preview_parts.append(f"[{msg['role']}]: {msg['content'][:100]}")
        prompt_preview = "\n".join(prompt_preview_parts)[:500]

        # 记录请求开始
        self.llm_logger.log_request(
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            message_count=len(full_messages),
            prompt_preview=prompt_preview,
        )
        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.chat_endpoint, headers=headers, json=payload
                )

                if response.status_code != 200:
                    error_text = response.text
                    duration = time.time() - start_time
                    self.llm_logger.log_error(
                        error=Exception(f"API 错误: {response.status_code}"),
                        duration=duration,
                        response_text=error_text,
                    )
                    logger.error(
                        f"OpenAI API 错误: {response.status_code} - {error_text}"
                    )
                    raise Exception(f"OpenAI API 请求失败: {response.status_code}")
                result = response.json()

                if "choices" in result and len(result["choices"]) > 0:
                    choice = result["choices"][0]
                    message = choice.get("message", {})
                    content = message.get("content") or ""
                    finish_reason = choice.get("finish_reason", "unknown")
                    duration = time.time() - start_time

                    # 推理模型回退：若 content 为空但有 reasoning_content，尝试从中提取
                    if not content and finish_reason == "length":
                        reasoning = message.get("reasoning_content", "")
                        if reasoning:
                            logger.warning(
                                f"OpenAI API content 为空（finish_reason=length），"
                                f"尝试从 reasoning_content 中提取结果"
                            )
                            content = reasoning

                    # 提取 token 使用量
                    usage = result.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)

                    # 记录响应成功
                    self.llm_logger.log_response(
                        duration=duration,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        response_len=len(content),
                        response_content=content,
                    )
                    return content
                else:
                    duration = time.time() - start_time
                    self.llm_logger.log_error(
                        error=Exception("响应格式异常"),
                        duration=duration,
                        response_text=str(result),
                    )
                    raise Exception("OpenAI API 响应格式异常")
        except httpx.TimeoutException as e:
            duration = time.time() - start_time
            self.llm_logger.log_error(error=e, duration=duration)
            raise Exception("OpenAI API 请求超时")
        except Exception as e:
            duration = time.time() - start_time
            self.llm_logger.log_error(error=e, duration=duration)
            logger.error(f"OpenAI API 调用失败: {str(e)}")
            raise

    async def analyze(
        self,
        prompt: str,
        data: Optional[Dict[str, Any]] = None,
        response_format: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """分析数据并返回结构化结果"""

        analysis_prompt = prompt
        if data:
            analysis_prompt += f"\n\n## 数据\n```json\n{json.dumps(data, ensure_ascii=False, indent=2, cls=DecimalEncoder)}\n```"

        messages = [{"role": "user", "content": analysis_prompt}]

        payload_kwargs = {"temperature": 0.2}
        if response_format:
            payload_kwargs["response_format"] = response_format

        response = await self.chat(messages, **payload_kwargs)

        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            else:
                return json.loads(response)
        except json.JSONDecodeError:
            return {"raw_response": response}

    def get_provider_name(self) -> str:
        return "openai"

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """OpenAI 真流式输出"""
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST", self.chat_endpoint, headers=headers, json=payload
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        raise Exception(f"OpenAI API 流式请求失败: {response.status_code} - {error_text.decode()}")

                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"OpenAI 流式请求失败: {e}")
            raise


class ClaudeAdapter(LLMAdapter):
    """Claude 适配器"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.anthropic.com/v1",
        model: str = "claude-3-5-sonnet-20241022",
        timeout: int = 300,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

        self.messages_endpoint = f"{self.base_url}/messages"

        # 初始化日志记录器
        self.logger = logging.getLogger(__name__)
        self.llm_logger = LLMLogger("claude")
        self.logger.info(
            f"ClaudeAdapter 初始化完成，API Key: {LLMLogger.mask_api_key(self.api_key)}"
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """发送对话请求"""

        start_time = time.time()

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }

        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        # 构建 prompt_preview
        prompt_preview_parts = []
        if system_prompt:
            prompt_preview_parts.append(f"[System]: {system_prompt[:200]}")
        for msg in messages[:3]:  # 最多3条消息
            prompt_preview_parts.append(f"[{msg['role']}]: {msg['content'][:100]}")
        prompt_preview = "\n".join(prompt_preview_parts)[:500]

        # 记录请求开始
        self.llm_logger.log_request(
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            message_count=len(messages),
            prompt_preview=prompt_preview,
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.messages_endpoint, headers=headers, json=payload
                )

                if response.status_code != 200:
                    error_text = response.text
                    duration = time.time() - start_time

                    # 记录错误详情
                    self.llm_logger.log_error(
                        error=Exception(
                            f"Claude API 请求失败: {response.status_code} - {error_text}"
                        ),
                        duration=duration,
                        request_payload=payload,
                        response_text=error_text,
                    )

                    logger.error(
                        f"Claude API 错误: {response.status_code} - {error_text}"
                    )
                    raise Exception(f"Claude API 请求失败: {response.status_code}")

                result = response.json()

                if "content" in result and len(result["content"]) > 0:
                    content = result["content"][0].get("text", "")

                    # 提取 token 使用量
                    usage = result.get("usage", {})
                    prompt_tokens = usage.get("input_tokens", 0)
                    completion_tokens = usage.get("output_tokens", 0)

                    # 记录成功响应
                    duration = time.time() - start_time
                    self.llm_logger.log_response(
                        duration=duration,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        response_len=len(content),
                        response_content=content,
                    )

                    return content
                else:
                    duration = time.time() - start_time

                    # 记录响应格式错误
                    self.llm_logger.log_error(
                        error=Exception("Claude API 响应格式异常"),
                        duration=duration,
                        request_payload=payload,
                        response_text=str(result),
                    )

                    raise Exception("Claude API 响应格式异常")

        except httpx.TimeoutException as e:
            duration = time.time() - start_time

            # 记录超时错误
            self.llm_logger.log_error(
                error=e, duration=duration, request_payload=payload
            )

            raise Exception("Claude API 请求超时")
        except Exception as e:
            duration = time.time() - start_time

            # 记录其他错误
            self.llm_logger.log_error(
                error=e, duration=duration, request_payload=payload
            )

            logger.error(f"Claude API 调用失败: {str(e)}")
            raise

    async def analyze(
        self,
        prompt: str,
        data: Optional[Dict[str, Any]] = None,
        response_format: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """分析数据并返回结构化结果"""

        analysis_prompt = prompt
        if data:
            analysis_prompt += f"\n\n## 数据\n```json\n{json.dumps(data, ensure_ascii=False, indent=2, cls=DecimalEncoder)}\n```"

        analysis_prompt += "\n\n请以 JSON 格式返回结果。"

        messages = [{"role": "user", "content": analysis_prompt}]

        response = await self.chat(messages, temperature=0.2)

        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            else:
                return json.loads(response)
        except json.JSONDecodeError:
            return {"raw_response": response}

    def get_provider_name(self) -> str:
        return "claude"

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """Claude 真流式输出（使用 Messages API SSE 格式）"""
        payload: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST", self.messages_endpoint, headers=headers, json=payload
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        raise Exception(
                            f"Claude API 流式请求失败: {response.status_code} - {error_text.decode()}"
                        )

                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            event_type = chunk.get("type", "")
                            if event_type == "content_block_delta":
                                delta = chunk.get("delta", {})
                                text = delta.get("text", "")
                                if text:
                                    yield text
                        except json.JSONDecodeError:
                            continue

            duration = time.time() - start_time
            self.llm_logger.log_response(
                duration=duration,
                prompt_tokens=0,
                completion_tokens=0,
                response_len=0,
                response_content="[streamed]",
            )
        except Exception as e:
            duration = time.time() - start_time
            self.llm_logger.log_error(error=e, duration=duration)
            raise


class KimiAdapter(OpenAIAdapter):
    """
    Kimi AI 适配器

    使用 OpenAI 兼容 API 端点: https://api.kimi.com/coding/v1
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.kimi.com/coding/v1",
        model: str = "kimi-for-coding",
        timeout: int = 300,
    ):
        super().__init__(
            api_key=api_key, base_url=base_url, model=model, timeout=timeout
        )
        # 重新初始化日志记录器为 kimi
        self.llm_logger = LLMLogger("kimi")

    def get_provider_name(self) -> str:
        return "kimi"


def get_llm_adapter(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> LLMAdapter:
    """
    获取 LLM 适配器工厂函数

    Args:
        provider: 提供商名称 (kimi/zhipu/openai/claude)，默认读取配置 ai_provider
        api_key: API 密钥
        base_url: API 基础 URL
        model: 模型名称

    Returns:
        LLM 适配器实例
    """
    from app.config import settings

    provider = (provider or settings.ai_provider).lower()

    timeout = min(settings.ai_timeout, settings.ai_timeout_max)

    if provider == "zhipu":
        return ZhipuAdapter(
            api_key=api_key or settings.zhipu_api_key,
            base_url=base_url or settings.zhipu_api_base,
            model=model or settings.zhipu_model,
            timeout=timeout,
        )
    elif provider == "kimi":
        return KimiAdapter(
            api_key=api_key or settings.kimi_api_key,
            base_url=base_url or settings.kimi_api_base,
            model=model or settings.kimi_model,
            timeout=timeout,
        )
    elif provider == "openai":
        return OpenAIAdapter(
            api_key=api_key or settings.openai_api_key,
            base_url=base_url or settings.openai_base_url,
            model=model or settings.openai_model,
            timeout=timeout,
        )
    elif provider == "claude":
        return ClaudeAdapter(
            api_key=api_key or settings.anthropic_api_key,
            model=model or settings.claude_model,
            timeout=timeout,
        )
    else:
        raise ValueError(f"不支持的 LLM 提供商: {provider}")
