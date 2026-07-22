"""工具系统单元测试"""
import pytest
import os
from pathlib import Path

from lemma.tools.base import ToolResult
from lemma.tools.file_manager import FileManagerTool
from lemma.tools.code_executor import CodeExecutorTool
from lemma.tools.registry import ToolRegistry


class TestToolResult:
    def test_ok(self):
        result = ToolResult.ok(output="success", return_code=0)
        assert result.success is True
        assert result.output == "success"

    def test_fail(self):
        result = ToolResult.fail(error="something went wrong")
        assert result.success is False
        assert result.error == "something went wrong"

    def test_to_display_success(self):
        result = ToolResult.ok(output="42")
        assert "42" in result.to_display()

    def test_to_display_failure(self):
        result = ToolResult.fail(error="bad input")
        assert "❌" in result.to_display()
        assert "bad input" in result.to_display()


class TestToolRegistry:
    def test_register_and_get(self):
        registry = ToolRegistry()
        tool = FileManagerTool(work_dir="/tmp")
        registry.register(tool)
        assert registry.get("file_manager") is tool

    def test_get_unknown_returns_none(self):
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    @pytest.mark.asyncio
    async def test_execute_unknown_returns_fail(self):
        registry = ToolRegistry()
        result = await registry.execute("nonexistent")
        assert not result.success
        assert "not found" in result.error.lower()

    def test_tool_names(self):
        registry = ToolRegistry()
        registry.register(FileManagerTool(work_dir="/tmp"))
        assert "file_manager" in registry.tool_names

    def test_to_openai_tools(self):
        registry = ToolRegistry()
        registry.register(FileManagerTool(work_dir="/tmp"))
        tools = registry.to_openai_tools()
        assert len(tools) == 1
        assert tools[0]["type"] == "function"
        assert tools[0]["function"]["name"] == "file_manager"


class TestFileManager:
    @pytest.mark.asyncio
    async def test_write_and_read(self, tmp_path):
        tool = FileManagerTool(work_dir=str(tmp_path))
        result = await tool.execute(action="write", path="test.txt", content="hello world")
        assert result.success

        result = await tool.execute(action="read", path="test.txt")
        assert result.success
        assert "hello world" in str(result.output)

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self, tmp_path):
        tool = FileManagerTool(work_dir=str(tmp_path))
        result = await tool.execute(action="read", path="../../../etc/passwd")
        assert not result.success

    @pytest.mark.asyncio
    async def test_list_directory(self, tmp_path):
        tool = FileManagerTool(work_dir=str(tmp_path))
        await tool.execute(action="write", path="a.txt", content="a")
        await tool.execute(action="write", path="b.txt", content="b")
        result = await tool.execute(action="list", path=".")
        assert result.success
        assert "a.txt" in str(result.output)
        assert "b.txt" in str(result.output)


class TestCodeExecutor:
    @pytest.mark.asyncio
    async def test_simple_execution(self, tmp_path):
        tool = CodeExecutorTool(work_dir=str(tmp_path))
        result = await tool.execute(code="print(42)")
        assert result.success
        assert "42" in str(result.output)

    @pytest.mark.asyncio
    async def test_blocked_module(self, tmp_path):
        tool = CodeExecutorTool(work_dir=str(tmp_path))
        result = await tool.execute(code="import subprocess; subprocess.call(['ls'])")
        assert not result.success
        assert "安全检查" in str(result.error) or "Blocked" in str(result.error)

    @pytest.mark.asyncio
    async def test_blocked_os(self, tmp_path):
        tool = CodeExecutorTool(work_dir=str(tmp_path))
        result = await tool.execute(code="import os; os.system('echo pwned')")
        assert not result.success

    @pytest.mark.asyncio
    async def test_empty_code_fails(self, tmp_path):
        tool = CodeExecutorTool(work_dir=str(tmp_path))
        result = await tool.execute(code="")
        assert not result.success


class TestDataAnalyzerTool:
    @pytest.fixture
    def tool(self):
        from lemma.tools.data_analyzer import DataAnalyzerTool
        return DataAnalyzerTool()

    @pytest.mark.asyncio
    async def test_to_openai_tool(self, tool):
        schema = tool.to_openai_tool()
        assert schema["function"]["name"] == "data_analyzer"

    @pytest.mark.asyncio
    async def test_descriptive_stats(self, tool):
        result = await tool.execute(test_type="describe", data=[1.0, 2.0, 3.0, 4.0, 5.0])
        assert result.success is True

    @pytest.mark.asyncio
    async def test_invalid_test_type(self, tool):
        result = await tool.execute(test_type="unknown_test", data=[])
        assert result.success is False

    @pytest.mark.asyncio
    async def test_empty_data(self, tool):
        result = await tool.execute(test_type="describe", data=[])
        assert isinstance(result.success, bool)


class TestEquationSolverTool:
    @pytest.fixture
    def tool(self):
        from lemma.tools.equation_solver import EquationSolverTool
        return EquationSolverTool()

    @pytest.mark.asyncio
    async def test_to_openai_tool(self, tool):
        schema = tool.to_openai_tool()
        assert schema["function"]["name"] == "equation_solver"

    @pytest.mark.asyncio
    async def test_solve_linear(self, tool):
        result = await tool.execute(equations=["2*x + 3 = 7"], variables=["x"])
        assert result.success is True

    @pytest.mark.asyncio
    async def test_solve_system(self, tool):
        result = await tool.execute(equations=["x + y = 10", "x - y = 2"], variables=["x", "y"])
        assert result.success is True

    @pytest.mark.asyncio
    async def test_invalid_equation(self, tool):
        result = await tool.execute(equations=["invalid~~~eq"], variables=["x"])
        assert result.success is False
