"""RAG 管线集成测试 — 验证知识加载→检索→注入完整链路"""

import pytest
import tempfile
from pathlib import Path
from lemma.memory.long_term import LongTermMemory
from lemma.knowledge.loader import KnowledgeLoader


@pytest.fixture
def knowledge_dir():
    """创建临时知识目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        models = Path(tmpdir) / "models"
        models.mkdir()
        (models / "test_model.md").write_text(
            "# 线性规划模型\n\n"
            "线性规划是数学建模中最常用的优化方法之一。"
            "标准形式为：min c^T x, s.t. Ax = b, x >= 0。"
            "求解方法包括单纯形法和内点法。",
            encoding="utf-8",
        )
        yield tmpdir


@pytest.fixture
def long_term():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield LongTermMemory(persist_dir=tmpdir)


class TestRAGPipeline:
    def test_load_and_retrieve_matches(self, knowledge_dir, long_term):
        """load_all 和 _retrieve_knowledge 使用相同 collection 名称"""
        loader = KnowledgeLoader(knowledge_dir, long_term)
        stats = loader.load_all()
        assert stats["knowledge_models"] > 0, "知识加载失败"

        # query_knowledge 应该能查到
        results = loader.query_knowledge("线性规划", n_results=3)
        assert len(results) > 0, "查询返回空 — collection name 不匹配"
        assert any("线性规划" in r.get("content", "") for r in results), (
            "查询结果中不包含实际知识内容"
        )

    def test_retrieve_via_agent_method(self, knowledge_dir, long_term):
        """模拟 agent._retrieve_knowledge 的查询逻辑"""
        loader = KnowledgeLoader(knowledge_dir, long_term)
        loader.load_all()

        # 使用与 agent.py 相同的 collection 列表
        found = []
        for collection in ["knowledge_models", "knowledge_references", "knowledge_reviews"]:
            try:
                hits = long_term.query(collection, "线性规划", n_results=3)
                for hit in hits:
                    content = hit.get("content", "")
                    if content and len(content) > 30:
                        found.append(content[:800])
            except Exception:
                pass

        assert len(found) > 0, (
            "agent._retrieve_knowledge 使用的 collection 名称与 loader 不匹配"
        )

    def test_loader_query_knowledge(self, knowledge_dir, long_term):
        """loader.query_knowledge 能跨 collection 检索"""
        loader = KnowledgeLoader(knowledge_dir, long_term)
        loader.load_all()

        results = loader.query_knowledge("线性规划", n_results=5)
        assert len(results) > 0
        for r in results:
            assert "collection" in r
