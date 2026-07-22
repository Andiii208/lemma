"""自我进化模块测试"""

import pytest
from lemma.evolve.prompt_object import OptimizablePrompt
from lemma.evolve.mutator import Mutator


class TestOptimizablePrompt:
    def test_rendered(self):
        p = OptimizablePrompt(
            template="请分析{input}，使用{method}",
            slots={"input": "问题", "method": "排队论"},
        )
        assert p.rendered == "请分析问题，使用排队论"

    def test_prompt_id_stable(self):
        p = OptimizablePrompt(template="test", slots={"a": "1"})
        id1 = p.prompt_id
        id2 = p.prompt_id
        assert id1 == id2

    def test_clone(self):
        p = OptimizablePrompt(name="test", template="hello", version=5)
        c = p.clone()
        c.template = "changed"
        assert p.template == "hello"
        assert c.version == 5

    def test_save_and_load(self, tmp_path):
        p = OptimizablePrompt(template="Hello {name}", slots={"name": "World"})
        path = str(tmp_path / "prompt.md")
        p.save(path)

        loaded = OptimizablePrompt.from_file(path, name="test")
        assert "Hello World" in loaded.template

    def test_empty_slots(self):
        p = OptimizablePrompt(template="No slots here")
        assert p.rendered == "No slots here"


class TestMutator:
    def test_mutate_produces_variant(self):
        import random
        random.seed(42)
        m = Mutator()
        original = OptimizablePrompt(
            template="请分析问题\n\n请建立模型\n\n请求解",
        )
        variant = m.mutate(original)
        # 变异体应该有变化（模板或内容不同）
        assert variant.parent_id == original.prompt_id

    def test_mutate_preserves_original(self):
        m = Mutator()
        original = OptimizablePrompt(template="原始内容")
        original_template = original.template
        _ = m.mutate(original)
        assert original.template == original_template

    def test_mutate_all_strategies(self):
        m = Mutator()
        p = OptimizablePrompt(template="请分析问题\n\n---\n\n请建立模型\n\n---\n\n请设计算法")
        # 测试所有变异策略都不会崩溃
        for _ in range(20):
            variant = m.mutate(p)
            assert len(variant.template) > 0
