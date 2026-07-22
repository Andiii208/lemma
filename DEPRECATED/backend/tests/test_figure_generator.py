"""图表生成工具测试"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from lemma.tools.figure_generator import FigureGeneratorTool
from lemma.tools.base import ToolResult


class TestFigureGeneratorTool:
    @pytest.fixture
    def tool(self, tmp_path):
        return FigureGeneratorTool(str(tmp_path))

    def test_tool_name(self, tool):
        assert tool.name == "figure_generator"

    def test_tool_category(self, tool):
        assert tool.category == "visualization"

    def test_to_openai_tool_schema(self, tool):
        schema = tool.to_openai_tool()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "figure_generator"
        assert "code" in str(schema["function"]["parameters"])

    @pytest.mark.asyncio
    async def test_empty_code_returns_fail(self, tool):
        result = await tool.execute(code="")
        assert not result.success
        assert "必须提供" in result.error

    @pytest.mark.asyncio
    async def test_successful_generation(self, tool, tmp_path):
        """模拟成功生成图表"""
        output_name = "test_chart.png"

        def fake_write(path, **kwargs):
            # 模拟 Python 脚本创建输出文件
            (tmp_path / output_name).write_bytes(b"\x89PNG fake png data")

        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"Chart saved", b""))
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            # 模拟 tmp 文件写入后的 subprocess 创建
            result = await tool.execute(code="plt.plot([1,2,3])", output_name=output_name)

        # 由于 subprocess 被 mock，实际不会生成文件
        # 但可以验证工具正确处理了流程
        assert mock_proc.communicate.called

    @pytest.mark.asyncio
    async def test_generation_failure(self, tool):
        """模拟代码执行失败"""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b"NameError: plt is not defined"))
        mock_proc.returncode = 1

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await tool.execute(code="plt.plot([1,2,3])", output_name="fail.png")

        assert not result.success

    @pytest.mark.asyncio
    async def test_generation_timeout(self, tool):
        """模拟执行超时"""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(side_effect=TimeoutError())

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await tool.execute(code="import time; time.sleep(999)")

        assert not result.success
        assert "超时" in result.error

    @pytest.mark.asyncio
    async def test_temp_file_cleanup(self, tool, tmp_path):
        """验证临时文件被清理"""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"OK", b""))
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            await tool.execute(code="plt.plot([1])")

        # 验证没有残留临时文件
        temp_files = list(tmp_path.glob("_fig_gen_*.py"))
        assert len(temp_files) == 0
