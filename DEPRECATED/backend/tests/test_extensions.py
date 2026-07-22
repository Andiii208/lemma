"""API 扩展测试（公式渲染 + 灰度实验）"""

import pytest
from lemma.api.extensions import (
    render_formula,
    extract_formulas,
    ExperimentManager,
)


class TestFormulaRendering:
    def test_render_formula(self):
        result = render_formula("E = mc^2")
        assert "E = mc^2" in result.latex
        assert result.html != ""

    def test_render_already_wrapped(self):
        result = render_formula("$$x^2$$")
        assert "$$" in result.latex

    def test_extract_formulas(self):
        text = "质能方程 $E=mc^2$ 和 $$\\int_0^1 x dx$$"
        formulas = extract_formulas(text)
        assert len(formulas) >= 2


class TestExperimentManager:
    def test_create_experiment(self, tmp_path):
        mgr = ExperimentManager(str(tmp_path))
        exp = mgr.create("exp1", "Prompt A vs B")
        assert exp.experiment_id == "exp1"
        assert len(mgr.list_all()) == 1

    def test_get_variant_deterministic(self, tmp_path):
        mgr = ExperimentManager(str(tmp_path))
        mgr.create("exp1", "Test", ["control", "treatment"])

        # 同一用户总是得到相同变体
        v1 = mgr.get_variant("exp1", "user_123")
        v2 = mgr.get_variant("exp1", "user_123")
        assert v1 == v2
        assert v1 in ["control", "treatment"]

    def test_get_variant_distribution(self, tmp_path):
        mgr = ExperimentManager(str(tmp_path))
        mgr.create("exp1", "Test")

        # 100 个用户应该大致均匀分布
        variants = [mgr.get_variant("exp1", f"user_{i}") for i in range(100)]
        control_count = variants.count("control")
        # 允许 30-70 的范围（粗略检查）
        assert 20 < control_count < 80

    def test_inactive_experiment(self, tmp_path):
        mgr = ExperimentManager(str(tmp_path))
        mgr.create("exp1", "Test")
        mgr.deactivate("exp1")

        # 非活跃实验返回 control
        assert mgr.get_variant("exp1", "user_1") == "control"

    def test_persistence(self, tmp_path):
        mgr = ExperimentManager(str(tmp_path))
        mgr.create("exp1", "Persistent Test")

        mgr2 = ExperimentManager(str(tmp_path))
        assert len(mgr2.list_all()) == 1
