"""工具注册表 — 管理所有可用工具"""

from __future__ import annotations

from .base import Tool, ToolResult


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        """获取工具"""
        return self._tools.get(name)

    async def execute(self, name: str, **kwargs) -> ToolResult:
        """执行工具"""
        tool = self._tools.get(name)
        if not tool:
            return ToolResult.fail(f"Tool not found: {name}")
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            return ToolResult.fail(f"Tool execution error: {e}")

    def to_openai_tools(self) -> list[dict]:
        """转换为 OpenAI tools 格式"""
        return [tool.to_openai_tool() for tool in self._tools.values()]

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())

    @property
    def tool_descriptions(self) -> dict[str, str]:
        return {name: tool.description for name, tool in self._tools.items()}
