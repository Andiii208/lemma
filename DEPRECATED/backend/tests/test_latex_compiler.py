"""LaTeX 编译器工具测试"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio

from lemma.tools.latex_compiler import LatexCompilerTool
from lemma.tools.base import ToolResult


class TestLatexCompilerTool:
    @pytest.fixture
    def tool(self, tmp_path):
        return LatexCompilerTool(str(tmp_path))

    @pytest.fixture
    def sample_tex(self, tmp_path):
        tex = tmp_path / "test.tex"
        tex.write_text(r"""
\documentclass{article}
\begin{document}
Hello World
\end{document}
""")
        return "test.tex"

    def test_tool_name(self, tool):
        assert tool.name == "latex_compiler"

    def test_tool_category(self, tool):
        assert tool.category == "document"

    def test_to_openai_tool_schema(self, tool):
        schema = tool.to_openai_tool()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "latex_compiler"
        assert "tex_file" in str(schema["function"]["parameters"])

    @pytest.mark.asyncio
    async def test_empty_tex_file_returns_fail(self, tool):
        result = await tool.execute(tex_file="")
        assert not result.success
        assert "必须提供" in result.error

    @pytest.mark.asyncio
    async def test_missing_file_returns_fail(self, tool):
        result = await tool.execute(tex_file="nonexistent.tex")
        assert not result.success
        assert "不存在" in result.error

    @pytest.mark.asyncio
    async def test_compile_success(self, tool, sample_tex, tmp_path):
        """模拟成功编译：xelatex 返回 0 且 PDF 存在"""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake pdf")

        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"Output written on test.pdf", b""))
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await tool.execute(tex_file=sample_tex, passes=1)

        assert result.success
        assert "编译成功" in str(result.output)

    @pytest.mark.asyncio
    async def test_compile_failure(self, tool, sample_tex):
        """模拟编译失败：xelatex 返回非零"""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"! Undefined control sequence.", b""))
        mock_proc.returncode = 1

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await tool.execute(tex_file=sample_tex, passes=1)

        assert not result.success
        assert "编译失败" in result.error

    @pytest.mark.asyncio
    async def test_compile_timeout(self, tool, sample_tex):
        """模拟编译超时"""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(side_effect=TimeoutError())

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await tool.execute(tex_file=sample_tex, passes=1)

        assert not result.success
        assert "超时" in result.error

    @pytest.mark.asyncio
    async def test_multiple_passes(self, tool, sample_tex, tmp_path):
        """测试多遍编译"""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake pdf")

        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"OK", b""))
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await tool.execute(tex_file=sample_tex, passes=3)

        assert result.success
        # 确认调用了 3 次
        assert mock_proc.communicate.await_count == 3
