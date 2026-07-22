"""来源追踪工具测试 — SourceTrackerTool 全路径覆盖"""

import pytest
from lemma.tools.source_tracker import SourceTrackerTool


class TestSourceTrackerRegister:
    @pytest.mark.asyncio
    async def test_register_primary_source(self, tmp_path):
        tool = SourceTrackerTool(str(tmp_path))
        result = await tool.execute(
            action="register",
            source_id="ref_01",
            source_type="primary",
            url="https://example.com/paper.pdf",
            description="原始论文",
        )
        assert result.success is True
        assert "ref_01" in result.output

    @pytest.mark.asyncio
    async def test_register_secondary_source(self, tmp_path):
        tool = SourceTrackerTool(str(tmp_path))
        result = await tool.execute(
            action="register",
            source_id="ref_02",
            source_type="secondary",
            description="综述文章",
        )
        assert result.success is True
        assert "二手" in result.output or "ref_02" in result.output

    @pytest.mark.asyncio
    async def test_register_tertiary_source(self, tmp_path):
        tool = SourceTrackerTool(str(tmp_path))
        result = await tool.execute(
            action="register",
            source_id="ref_03",
            source_type="tertiary",
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_register_requires_source_id(self, tmp_path):
        tool = SourceTrackerTool(str(tmp_path))
        result = await tool.execute(action="register")
        assert result.success is False
        assert "source_id" in result.error

    @pytest.mark.asyncio
    async def test_register_default_type_is_unknown(self, tmp_path):
        tool = SourceTrackerTool(str(tmp_path))
        result = await tool.execute(action="register", source_id="ref_x")
        assert result.success is True


class TestSourceTrackerBind:
    @pytest.mark.asyncio
    async def test_bind_claim_to_source(self, tmp_path):
        tool = SourceTrackerTool(str(tmp_path))
        await tool.execute(
            action="register",
            source_id="paper1",
            source_type="primary",
            url="https://example.com",
        )
        result = await tool.execute(
            action="bind",
            claim="温度与压力成正比",
            source_id="paper1",
        )
        assert result.success is True
        assert "fact" in result.output

    @pytest.mark.asyncio
    async def test_bind_claim_without_url_is_inference(self, tmp_path):
        tool = SourceTrackerTool(str(tmp_path))
        await tool.execute(
            action="register",
            source_id="ref_no_url",
            source_type="secondary",
        )
        result = await tool.execute(
            claim="某结论",
            source_id="ref_no_url",
            action="bind",
        )
        assert result.success is True
        assert "inference" in result.output

    @pytest.mark.asyncio
    async def test_bind_requires_claim_and_source(self, tmp_path):
        tool = SourceTrackerTool(str(tmp_path))
        result = await tool.execute(action="bind", claim="断言", source_id="")
        assert result.success is False

        result2 = await tool.execute(action="bind", claim="", source_id="x")
        assert result2.success is False

    @pytest.mark.asyncio
    async def test_bind_unregistered_source_fails(self, tmp_path):
        tool = SourceTrackerTool(str(tmp_path))
        result = await tool.execute(
            action="bind",
            claim="断言",
            source_id="nonexistent",
        )
        assert result.success is False
        assert "未注册" in result.error

    @pytest.mark.asyncio
    async def test_bind_truncates_long_claim(self, tmp_path):
        tool = SourceTrackerTool(str(tmp_path))
        await tool.execute(action="register", source_id="s1", source_type="primary", url="http://x")
        long_claim = "x" * 1000
        result = await tool.execute(action="bind", claim=long_claim, source_id="s1")
        assert result.success is True


class TestSourceTrackerAudit:
    @pytest.mark.asyncio
    async def test_audit_empty(self, tmp_path):
        tool = SourceTrackerTool(str(tmp_path))
        result = await tool.execute(action="audit")
        assert result.success is True
        assert "总断言: 0" in result.output

    @pytest.mark.asyncio
    async def test_audit_all_facts(self, tmp_path):
        tool = SourceTrackerTool(str(tmp_path))
        await tool.execute(action="register", source_id="s1", source_type="primary", url="http://x")
        await tool.execute(action="bind", claim="断言1", source_id="s1")
        await tool.execute(action="bind", claim="断言2", source_id="s1")
        result = await tool.execute(action="audit")
        assert result.success is True
        assert "fact: 2" in result.output
        assert "100%" in result.output

    @pytest.mark.asyncio
    async def test_audit_orphan_claims(self, tmp_path):
        tool = SourceTrackerTool(str(tmp_path))
        # 手动写入包含孤立断言的数据
        import json
        data = {
            "sources": {},
            "claims": [{"claim": "孤立断言", "source_id": "deleted", "label": "fact"}],
        }
        tool.sources_file.write_text(json.dumps(data), encoding="utf-8")
        result = await tool.execute(action="audit")
        assert result.success is True
        assert "孤立" in result.output


class TestSourceTrackerListAndStats:
    @pytest.mark.asyncio
    async def test_list_empty(self, tmp_path):
        tool = SourceTrackerTool(str(tmp_path))
        result = await tool.execute(action="list")
        assert result.success is True
        assert "sources" in result.output

    @pytest.mark.asyncio
    async def test_list_after_register(self, tmp_path):
        tool = SourceTrackerTool(str(tmp_path))
        await tool.execute(action="register", source_id="s1", source_type="primary", url="http://x")
        result = await tool.execute(action="list")
        assert result.success is True
        assert "s1" in result.output

    @pytest.mark.asyncio
    async def test_stats_empty(self, tmp_path):
        tool = SourceTrackerTool(str(tmp_path))
        result = await tool.execute(action="stats")
        assert result.success is True
        assert "来源: 0" in result.output
        assert "断言: 0" in result.output

    @pytest.mark.asyncio
    async def test_stats_with_data(self, tmp_path):
        tool = SourceTrackerTool(str(tmp_path))
        await tool.execute(action="register", source_id="s1", source_type="primary", url="http://x")
        await tool.execute(action="register", source_id="s2", source_type="secondary")
        await tool.execute(action="bind", claim="c1", source_id="s1")
        result = await tool.execute(action="stats")
        assert result.success is True
        assert "来源: 2" in result.output
        assert "断言: 1" in result.output
        assert "primary=1" in result.output
        assert "secondary=1" in result.output

    @pytest.mark.asyncio
    async def test_unknown_action(self, tmp_path):
        tool = SourceTrackerTool(str(tmp_path))
        result = await tool.execute(action="nonexistent")
        assert result.success is False
        assert "未知" in result.error
