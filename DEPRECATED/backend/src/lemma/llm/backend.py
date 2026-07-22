"""LLM 后端抽象层 — 统一 OpenAI-compatible API 接口"""

from __future__ import annotations

import asyncio
import logging
import os
import random
from dataclasses import dataclass
from functools import wraps
from typing import Any

import openai
from openai import APIStatusError, AsyncOpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LLMConfig(BaseModel):
    """LLM 配置"""

    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    timeout: float = 120.0


@dataclass
class LLMResponse:
    """LLM 响应"""

    content: str
    model: str
    usage: dict[str, int]
    finish_reason: str
    tool_calls: list[dict] | None = None
    raw: Any = None


def _with_retry(max_retries: int = 3, base_delay: float = 1.0):
    """指数退避重试装饰器，针对 transient 错误"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except (
                    openai.RateLimitError,
                    openai.APIConnectionError,
                    openai.APITimeoutError,
                ) as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2**attempt) + random.uniform(0, 0.5)
                        await asyncio.sleep(delay)
                except APIStatusError as e:
                    if e.status_code in (500, 502, 503) and attempt < max_retries:
                        last_exception = e
                        delay = base_delay * (2**attempt) + random.uniform(0, 0.5)
                        await asyncio.sleep(delay)
                    else:
                        raise
            raise last_exception

        return wrapper

    return decorator


class LLMBackend:
    """OpenAI-compatible LLM 后端"""

    def __init__(self, config: LLMConfig, cost_tracker=None):
        self.config = config
        self.cost_tracker = cost_tracker
        resolved_key = (
            os.path.expandvars(config.api_key)
            if config.api_key.startswith("${")
            else config.api_key
        )
        if resolved_key.startswith("$"):
            resolved_key = os.environ.get(resolved_key.strip("${}"), "")
        self.client = AsyncOpenAI(
            api_key=resolved_key or "dummy",
            base_url=config.base_url,
            timeout=config.timeout,
        )
        self._call_count = 0
        self._total_tokens = 0

    @property
    def model(self) -> str:
        return self.config.model

    # 各模型上下文窗口限制
    MODEL_CONTEXT_LIMITS: dict[str, int] = {
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
        "gpt-4-turbo": 128000,
        "gpt-3.5-turbo": 16385,
        "deepseek-chat": 65536,
        "deepseek-reasoner": 65536,
    }

    def _estimate_tokens(self, messages: list[dict]) -> int:
        """粗略估算 token 数（中文约 1.5 字/token，英文约 4 字/token）"""
        total_chars = sum(len(m.get("content", "")) for m in messages)
        return int(total_chars * 1.2)  # 保守估计

    @_with_retry(max_retries=3, base_delay=1.0)
    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        """生成响应（带重试）"""
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        # Token 预检：如果估算 token 超过模型限制的 90%，记录警告
        estimated = self._estimate_tokens(messages)
        model_limit = self.MODEL_CONTEXT_LIMITS.get(self.config.model, 128000)
        if estimated > model_limit * 0.9:
            import logging
            logging.getLogger(__name__).warning(
                f"Estimated {estimated} tokens exceeds 90%% of {self.config.model} limit ({model_limit})"
            )

        try:
            response = await self.client.chat.completions.create(**kwargs)
        except Exception as e:
            error_msg = str(e)
            if self.config.api_key and self.config.api_key in error_msg:
                error_msg = error_msg.replace(self.config.api_key, "***")
            logger.error(f"LLM generate error: {error_msg}")
            return LLMResponse(
                content=f"[LLM Error] {error_msg}",
                model=self.config.model,
                usage={"prompt_tokens": 0, "completion_tokens": 0},
                finish_reason="error",
            )

        self._call_count += 1

        if not response.choices:
            return LLMResponse(
                content="[LLM Error] API 返回空响应 (no choices)",
                model=self.config.model,
                usage={"prompt_tokens": 0, "completion_tokens": 0},
                finish_reason="empty",
            )

        choice = response.choices[0]
        usage = response.usage

        tool_calls = None
        if choice.message.tool_calls:
            tool_calls = []
            for tc in choice.message.tool_calls:
                tool_calls.append(
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                )

        tokens = {
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
        }
        self._total_tokens += tokens["prompt_tokens"] + tokens["completion_tokens"]

        # 成本追踪
        if self.cost_tracker and usage:
            self.cost_tracker.record(
                model=self.config.model,
                input_tokens=tokens["prompt_tokens"],
                output_tokens=tokens["completion_tokens"],
            )

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            usage=tokens,
            finish_reason=choice.finish_reason or "stop",
            tool_calls=tool_calls,
            raw=response,
        )

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
    ):
        """流式生成响应，支持工具调用检测"""
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            stream = await self.client.chat.completions.create(**kwargs)
            tool_calls_buffer: list[dict] = []
            current_tool_call: dict | None = None
            total_prompt_tokens = 0
            total_completion_tokens = 0

            async for chunk in stream:
                # 捕获 usage 信息（最后一个 chunk）
                if chunk.usage:
                    total_prompt_tokens = chunk.usage.prompt_tokens or 0
                    total_completion_tokens = chunk.usage.completion_tokens or 0

                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                # 处理文本内容
                if delta.content:
                    yield delta.content

                # 处理工具调用
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        if tc_delta.index is not None:
                            while len(tool_calls_buffer) <= tc_delta.index:
                                tool_calls_buffer.append({"id": "", "name": "", "arguments": ""})
                            current_tool_call = tool_calls_buffer[tc_delta.index]

                        if current_tool_call:
                            if tc_delta.id:
                                current_tool_call["id"] = tc_delta.id
                            if tc_delta.function:
                                if tc_delta.function.name:
                                    current_tool_call["name"] = tc_delta.function.name
                                if tc_delta.function.arguments:
                                    current_tool_call["arguments"] += tc_delta.function.arguments

            # 成本追踪
            if self.cost_tracker and (total_prompt_tokens or total_completion_tokens):
                self.cost_tracker.record(
                    model=self.config.model,
                    input_tokens=total_prompt_tokens,
                    output_tokens=total_completion_tokens,
                )

            # 如果有工具调用，yield 完整的工具调用信息
            if tool_calls_buffer:
                yield {"type": "tool_calls", "calls": tool_calls_buffer}

        except Exception as e:
            yield {"type": "error", "message": str(e)}

    @property
    def stats(self) -> dict:
        return {
            "call_count": self._call_count,
            "total_tokens": self._total_tokens,
            "model": self.config.model,
        }
