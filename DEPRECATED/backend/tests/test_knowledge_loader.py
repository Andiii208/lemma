"""KnowledgeLoader 测试"""
import pytest
from pathlib import Path

from lemma.knowledge.loader import KnowledgeLoader
from lemma.memory.long_term import LongTermMemory


@pytest.fixture
def long_term_memory(tmp_path):
    """创建临时 LongTermMemory 实例"""
    return LongTermMemory(persist_dir=str(tmp_path / "chromadb"))


@pytest.fixture
def loader(tmp_path, long_term_memory):
    """创建 KnowledgeLoader 实例"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return KnowledgeLoader(str(data_dir), long_term_memory)


class TestKnowledgeLoader:
    def test_loader_initialization(self, tmp_path, long_term_memory):
        """KnowledgeLoader 应能正确初始化"""
        loader = KnowledgeLoader(str(tmp_path), long_term_memory)
        assert loader.data_dir == tmp_path
        assert loader.long_term is long_term_memory

    def test_load_all_empty_directory(self, loader):
        """空目录应返回 0 统计"""
        stats = loader.load_all()
        assert isinstance(stats, dict)
        assert all(v == 0 for v in stats.values())

    def test_load_all_with_markdown_files(self, tmp_path, long_term_memory):
        """有 .md 文件的目录应正确加载"""
        data_dir = tmp_path / "data"
        models_dir = data_dir / "models"
        models_dir.mkdir(parents=True)
        (models_dir / "test.md").write_text(
            "# 测试模型\n线性规划是优化方法。", encoding="utf-8"
        )
        loader = KnowledgeLoader(str(data_dir), long_term_memory)
        stats = loader.load_all()
        assert stats.get("knowledge_models", 0) >= 1

    def test_query_knowledge_returns_list(self, loader):
        """查询应返回列表"""
        results = loader.query_knowledge("测试查询")
        assert isinstance(results, list)

    def test_query_knowledge_with_data(self, tmp_path, long_term_memory):
        """有数据时查询应返回结果"""
        data_dir = tmp_path / "data"
        models_dir = data_dir / "models"
        models_dir.mkdir(parents=True)
        (models_dir / "optimization.md").write_text(
            "# 优化方法\n线性规划用于资源分配。", encoding="utf-8"
        )
        loader = KnowledgeLoader(str(data_dir), long_term_memory)
        loader.load_all()
        results = loader.query_knowledge("线性规划", n_results=3)
        assert len(results) > 0

    def test_get_model_library_empty(self, loader):
        """空目录应返回空字典"""
        lib = loader.get_model_library()
        assert lib == {}

    def test_get_model_library_with_files(self, tmp_path, long_term_memory):
        """有 .md 文件时应返回内容字典"""
        data_dir = tmp_path / "data"
        models_dir = data_dir / "models"
        models_dir.mkdir(parents=True)
        (models_dir / "linear.md").write_text(
            "# 线性规划\n目标函数和约束条件。", encoding="utf-8"
        )
        loader = KnowledgeLoader(str(data_dir), long_term_memory)
        lib = loader.get_model_library()
        assert "linear" in lib
        assert "线性规划" in lib["linear"]

    def test_query_results_contain_collection(self, tmp_path, long_term_memory):
        """查询结果应包含 collection 字段"""
        data_dir = tmp_path / "data"
        models_dir = data_dir / "models"
        models_dir.mkdir(parents=True)
        (models_dir / "test.md").write_text(
            "# 测试\n知识库测试内容。", encoding="utf-8"
        )
        loader = KnowledgeLoader(str(data_dir), long_term_memory)
        loader.load_all()
        results = loader.query_knowledge("知识库", n_results=1)
        if results:
            assert "collection" in results[0]
