"""质量检查工具测试"""

import pytest
from lemma.tools.quality_checker import QualityCheckerTool


class TestQualityCheckerTool:
    @pytest.mark.asyncio
    async def test_syntax_check_valid(self, tmp_path):
        (tmp_path / "good.py").write_text("x = 1\nprint(x)\n", encoding="utf-8")
        tool = QualityCheckerTool(str(tmp_path))
        result = await tool.execute(check_type="syntax", target="good.py")
        assert result.success is True
        assert "语法正确" in result.output

    @pytest.mark.asyncio
    async def test_syntax_check_invalid(self, tmp_path):
        (tmp_path / "bad.py").write_text("def f(:\n", encoding="utf-8")
        tool = QualityCheckerTool(str(tmp_path))
        result = await tool.execute(check_type="syntax", target="bad.py")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_syntax_check_missing_file(self, tmp_path):
        tool = QualityCheckerTool(str(tmp_path))
        result = await tool.execute(check_type="syntax", target="nonexistent.py")
        assert result.success is False
        assert "不存在" in result.error

    @pytest.mark.asyncio
    async def test_unknown_check_type(self, tmp_path):
        tool = QualityCheckerTool(str(tmp_path))
        result = await tool.execute(check_type="unknown", target="test")
        assert result.success is False
        assert "未知" in result.error

    @pytest.mark.asyncio
    async def test_missing_target(self, tmp_path):
        tool = QualityCheckerTool(str(tmp_path))
        result = await tool.execute(check_type="syntax")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_ast_check(self, tmp_path):
        (tmp_path / "code.py").write_text("import os\nx = 1\n", encoding="utf-8")
        tool = QualityCheckerTool(str(tmp_path))
        result = await tool.execute(check_type="ast", target="code.py")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_figures_check_missing_dir(self, tmp_path):
        tool = QualityCheckerTool(str(tmp_path))
        result = await tool.execute(check_type="figures", target="nonexistent_dir")
        # 应该处理不存在的目录
        assert result is not None
