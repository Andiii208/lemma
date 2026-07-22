"""工具基类 — 所有工具继承此类"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ToolResult(BaseModel):
    """工具执行结果"""

    success: bool
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = {}

    @classmethod
    def ok(cls, output: Any, **metadata) -> ToolResult:
        return cls(success=True, output=output, metadata=metadata)

    @classmethod
    def fail(cls, error: str, **metadata) -> ToolResult:
        return cls(success=False, error=error, metadata=metadata)

    def to_display(self) -> str:
        """用于前端显示的格式化输出"""
        if self.success:
            return str(self.output) if self.output else "✅ 执行成功"
        return f"❌ 错误: {self.error}"


class Tool(ABC):
    """工具基类"""

    name: str = ""
    description: str = ""
    category: str = "general"

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        ...

    def to_openai_tool(self) -> dict:
        """转换为 OpenAI function calling 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self._get_parameters_schema(),
            },
        }

    @abstractmethod
    def _get_parameters_schema(self) -> dict:
        """获取参数 Schema"""
        ...
