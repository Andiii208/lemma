"""工具自创 — Agent 动态生成并注册新工具

Agent 在发现现有工具不足时，可以自己编写工具代码。
生成的代码必须通过 SecurityChecker 才能注册。
"""
# mypy: disable-error-code="override"

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, TYPE_CHECKING
from .base import Tool

if TYPE_CHECKING:
    from .registry import ToolRegistry

from .base import Tool, ToolResult
from .sandbox import SecurityChecker

logger = logging.getLogger("ultramath.tool_forge")


class ToolForgeTool(Tool):
    """元工具 — 让 Agent 创建新工具"""

    name = "tool_forge"
    description = "创建新的 Python 工具。提供工具名称、描述和代码，系统会自动注册。"
    category = "meta"

    def __init__(self, registry: "ToolRegistry", work_dir: str = "."):
        self.registry = registry
        self.work_dir = Path(work_dir)

    async def execute(
        self, tool_name: str = "", description: str = "", code: str = "", **kwargs
    ) -> ToolResult:
        """创建并注册新工具"""
        if not tool_name:
            return ToolResult.fail("必须提供 tool_name")
        if not code:
            return ToolResult.fail("必须提供工具代码")

        # 安全检查
        checker = SecurityChecker()
        errors = checker.check(code)
        if errors:
            return ToolResult.fail(f"代码安全检查未通过: {'; '.join(errors)}")

        # 检查工具名冲突
        if tool_name in self.registry.tool_names:
            return ToolResult.fail(f"工具名已存在: {tool_name}")

        # 创建工具类
        try:
            tool = self._create_tool_from_code(tool_name, description, code)
            if tool:
                self.registry.register(tool)
                logger.info(f"Agent 创建了新工具: {tool_name}")
                return ToolResult.ok(
                    output=f"工具 '{tool_name}' 创建成功并已注册。\n描述: {description}"
                )
            return ToolResult.fail("无法从代码创建工具")
        except Exception as e:
            return ToolResult.fail(f"工具创建失败: {e}")

    def _create_tool_from_code(
        self, name: str, description: str, code: str
    ) -> Tool | None:
        """从代码字符串创建 Tool 实例"""
        # 构建动态工具类
        exec_globals: dict[str, Any] = {"__builtins__": {}}
        exec_locals: dict[str, Any] = {}

        try:
            exec(code, exec_globals, exec_locals)
        except Exception as e:
            logger.error(f"工具代码执行失败: {e}")
            return None

        # 查找 execute 函数
        execute_fn = exec_locals.get("execute")
        if not callable(execute_fn):
            return None

        # 创建动态工具
        schema = exec_locals.get("parameters_schema", {
            "type": "object",
            "properties": {},
        })

        return DynamicTool(
            name=name,
            description=description,
            execute_fn=execute_fn,
            schema=schema,
        )

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "新工具的名称",
                },
                "description": {
                    "type": "string",
                    "description": "工具的功能描述",
                },
                "code": {
                    "type": "string",
                    "description": "Python 代码，必须包含 async def execute(**kwargs) 函数",
                },
            },
            "required": ["tool_name", "code"],
        }


class DynamicTool(Tool):
    """动态创建的工具"""

    def __init__(
        self,
        name: str,
        description: str,
        execute_fn: Callable,
        schema: dict,
        category: str = "dynamic",
    ):
        self._name = name
        self._description = description
        self._execute_fn = execute_fn
        self._schema = schema
        self._category = category

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def category(self) -> str:
        return self._category

    async def execute(self, **kwargs) -> ToolResult:
        try:
            result = await self._execute_fn(**kwargs)
            if isinstance(result, ToolResult):
                return result
            return ToolResult.ok(output=str(result))
        except Exception as e:
            return ToolResult.fail(str(e))

    def _get_parameters_schema(self) -> dict:
        return self._schema
