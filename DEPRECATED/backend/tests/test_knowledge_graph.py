"""知识图谱与案例库测试"""

import pytest
from lemma.knowledge.graph import KnowledgeGraph, Entity, Relation
from lemma.knowledge.case_library import CaseLibrary, Case


class TestKnowledgeGraph:
    def test_add_entity(self):
        kg = KnowledgeGraph()
        kg.add_entity(Entity(entity_id="e1", name="排队论", entity_type="concept"))
        assert len(kg.entities) == 1

    def test_add_relation(self):
        kg = KnowledgeGraph()
        kg.add_entity(Entity(entity_id="e1", name="排队论", entity_type="concept"))
        kg.add_entity(Entity(entity_id="e2", name="优化", entity_type="concept"))
        kg.add_relation(Relation(source_id="e1", target_id="e2", relation_type="uses"))
        assert len(kg.relations) == 1

    def test_find_entity(self):
        kg = KnowledgeGraph()
        kg.add_entity(Entity(entity_id="e1", name="排队论模型", entity_type="method"))
        found = kg.find_entity("排队论")
        assert found is not None
        assert found.entity_id == "e1"

    def test_get_related(self):
        kg = KnowledgeGraph()
        kg.add_entity(Entity(entity_id="e1", name="A", entity_type="concept"))
        kg.add_entity(Entity(entity_id="e2", name="B", entity_type="concept"))
        kg.add_relation(Relation(source_id="e1", target_id="e2", relation_type="uses"))

        related = kg.get_related("e1")
        assert len(related) == 1
        assert related[0][0].name == "B"

    def test_query(self):
        kg = KnowledgeGraph()
        kg.add_entity(Entity(entity_id="e1", name="线性规划", entity_type="method"))
        kg.add_entity(Entity(entity_id="e2", name="整数规划", entity_type="method"))
        results = kg.query("规划")
        assert len(results) == 2

    def test_load_from_markdown(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text(
            "# 排队论\n\n## 模型分类\n\n- **M/M/1 模型**: 单服务台\n- **M/M/c 模型**: 多服务台",
            encoding="utf-8",
        )
        kg = KnowledgeGraph()
        count = kg.load_from_markdown(str(md_file))
        assert count >= 3  # 排队论 + 模型分类 + M/M/1 + M/M/c

    def test_save_and_load(self, tmp_path):
        kg = KnowledgeGraph()
        kg.add_entity(Entity(entity_id="e1", name="test", entity_type="concept"))
        path = str(tmp_path / "graph.json")
        kg.save(path)

        kg2 = KnowledgeGraph(persist_path=path)
        assert len(kg2.entities) == 1
        assert kg2.entities["e1"].name == "test"

    def test_stats(self):
        kg = KnowledgeGraph()
        kg.add_entity(Entity(entity_id="e1", name="A", entity_type="concept"))
        kg.add_entity(Entity(entity_id="e2", name="B", entity_type="method"))
        stats = kg.stats
        assert stats["entities"] == 2
        assert "concept" in stats["types"]


class TestCaseLibrary:
    def test_add_and_search(self, tmp_path):
        lib = CaseLibrary(str(tmp_path / "cases"))
        lib.add_case(Case(
            case_id="c1",
            domain_id="math",
            phase_id="writing",
            quality_score=0.9,
            tags=["优化"],
        ))

        results = lib.search(domain_id="math")
        assert len(results) == 1
        assert results[0].quality_score == 0.9

    def test_search_filter(self, tmp_path):
        lib = CaseLibrary(str(tmp_path / "cases"))
        lib.add_case(Case(case_id="c1", domain_id="math", quality_score=0.9))
        lib.add_case(Case(case_id="c2", domain_id="paper", quality_score=0.5))

        assert len(lib.search(domain_id="math")) == 1
        assert len(lib.search(min_score=0.8)) == 1

    def test_count(self, tmp_path):
        lib = CaseLibrary(str(tmp_path / "cases"))
        assert lib.count == 0
        lib.add_case(Case(case_id="c1"))
        assert lib.count == 1
