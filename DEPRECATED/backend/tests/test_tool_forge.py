"""工具自创测试"""

import pytest
from lemma.tools.tool_forge import ToolForgeTool, DynamicTool
from lemma.tools.registry import ToolRegistry
from lemma.tools.base import ToolResult


class TestToolForge:
    @pytest.mark.asyncio
    async def test_create_valid_tool(self):
        registry = ToolRegistry()
        forge = ToolForgeTool(registry, "/tmp")

        code = """
async def execute(greeting="hello", **kwargs):
    return f"Tool says: {greeting}"
"""
        result = await forge.execute(
            tool_name="my_greeting",
            description="A greeting tool",
            code=code,
        )
        assert result.success is True
        assert "my_greeting" in registry.tool_names

    @pytest.mark.asyncio
    async def test_create_blocked_code(self):
        registry = ToolRegistry()
        forge = ToolForgeTool(registry, "/tmp")

        code = """
import os
async def execute(**kwargs):
    os.system("rm -rf /")
"""
        result = await forge.execute(tool_name="evil", code=code)
        assert result.success is False
        assert "安全检查" in result.error

    @pytest.mark.asyncio
    async def test_create_duplicate_name(self):
        registry = ToolRegistry()
        forge = ToolForgeTool(registry, "/tmp")

        # 先注册一个
        registry.register(DynamicTool(
            name="existing",
            description="exists",
            execute_fn=lambda **kw: "ok",
            schema={},
        ))

        result = await forge.execute(
            tool_name="existing",
            code="async def execute(**kwargs): return 'duplicate'",
        )
        assert result.success is False
        assert "已存在" in result.error

    @pytest.mark.asyncio
    async def test_create_missing_name(self):
        registry = ToolRegistry()
        forge = ToolForgeTool(registry, "/tmp")
        result = await forge.execute(code="async def execute(**kwargs): return 1")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_create_missing_code(self):
        registry = ToolRegistry()
        forge = ToolForgeTool(registry, "/tmp")
        result = await forge.execute(tool_name="test")
        assert result.success is False


class TestDynamicTool:
    @pytest.mark.asyncio
    async def test_execute(self):
        async def my_fn(x=1, **kwargs):
            return x * 2

        tool = DynamicTool(name="double", description="Doubles", execute_fn=my_fn, schema={})
        result = await tool.execute(x=5)
        assert result.success is True
        assert "10" in result.output

    def test_properties(self):
        tool = DynamicTool(name="t", description="desc", execute_fn=lambda **k: None, schema={})
        assert tool.name == "t"
        assert tool.description == "desc"
