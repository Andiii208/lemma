"""证据地图工具测试"""

import pytest
from lemma.tools.evidence_map import EvidenceMapTool


class TestEvidenceMapTool:
    @pytest.mark.asyncio
    async def test_stats_empty(self, tmp_path):
        tool = EvidenceMapTool(str(tmp_path))
        result = await tool.execute(action="stats")
        assert result.success is True
        assert "0 节点" in result.output

    @pytest.mark.asyncio
    async def test_add_node(self, tmp_path):
        tool = EvidenceMapTool(str(tmp_path))
        result = await tool.execute(
            action="add_node",
            node_id="n1",
            question="核心问题是什么？",
            answer="排队论",
            confidence="high",
            sources=["src1", "src2"],
        )
        assert result.success is True
        assert "n1" in result.output

    @pytest.mark.asyncio
    async def test_add_node_requires_id(self, tmp_path):
        tool = EvidenceMapTool(str(tmp_path))
        result = await tool.execute(action="add_node")
        assert result.success is False
        assert "node_id" in result.error

    @pytest.mark.asyncio
    async def test_add_child_node(self, tmp_path):
        tool = EvidenceMapTool(str(tmp_path))
        await tool.execute(action="add_node", node_id="root", question="根问题")
        result = await tool.execute(
            action="add_node",
            node_id="child1",
            parent_id="root",
            question="子问题",
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_get_tree(self, tmp_path):
        tool = EvidenceMapTool(str(tmp_path))
        await tool.execute(action="add_node", node_id="n1", question="Q1")
        result = await tool.execute(action="get_tree", node_id="n1")
        assert result.success is True
        assert "Q1" in result.output

    @pytest.mark.asyncio
    async def test_get_tree_root(self, tmp_path):
        tool = EvidenceMapTool(str(tmp_path))
        await tool.execute(action="add_node", node_id="n1", question="Q1")
        result = await tool.execute(action="get_tree")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_audit_pass(self, tmp_path):
        tool = EvidenceMapTool(str(tmp_path))
        await tool.execute(
            action="add_node",
            node_id="n1",
            confidence="high",
            sources=["s1", "s2"],
        )
        result = await tool.execute(action="audit")
        assert result.success is True
        assert "通过" in result.output

    @pytest.mark.asyncio
    async def test_audit_fail(self, tmp_path):
        tool = EvidenceMapTool(str(tmp_path))
        await tool.execute(
            action="add_node",
            node_id="n1",
            confidence="high",
            sources=["s1"],  # 只有 1 个来源，High 需要 >= 2
        )
        result = await tool.execute(action="audit")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_unknown_action(self, tmp_path):
        tool = EvidenceMapTool(str(tmp_path))
        result = await tool.execute(action="unknown")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_stats_after_add(self, tmp_path):
        tool = EvidenceMapTool(str(tmp_path))
        await tool.execute(action="add_node", node_id="n1", confidence="high", sources=["s1", "s2"], is_atomic=True)
        result = await tool.execute(action="stats")
        assert "1 节点" in result.output
        assert "1 原子问题" in result.output
