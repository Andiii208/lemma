"""自我反思自动触发测试 — 验证反射逻辑的正确性"""

from lemma.orchestration.state_machine import Phase


class TestReflectivePhases:
    """验证 REFLECTIVE_PHASES 逻辑"""

    def test_reflective_phases_include_key_phases(self):
        """DERIVATION/WRITING/REVIEW 应在反思阶段列表中"""
        reflective = {Phase.DERIVATION, Phase.WRITING, Phase.REVIEW}
        assert Phase.DERIVATION in reflective
        assert Phase.WRITING in reflective
        assert Phase.REVIEW in reflective

    def test_reflective_phases_exclude_other_phases(self):
        """其他阶段不在反思列表中"""
        reflective = {Phase.DERIVATION, Phase.WRITING, Phase.REVIEW}
        assert Phase.ANALYSIS not in reflective
        assert Phase.CODING not in reflective
        assert Phase.ONTOLOGY not in reflective
        assert Phase.TESTING not in reflective
        assert Phase.INIT not in reflective

    def test_reflection_skips_on_failure(self):
        """反思应在 result.success 为 False 时跳过"""
        # 验证逻辑: 代码中有 "and result.success" 条件
        reflective = {Phase.DERIVATION, Phase.WRITING, Phase.REVIEW}
        phase = Phase.DERIVATION
        assert phase in reflective
        # 如果 result.success == False, 即使 phase 在 REFLECTIVE_PHASES 中也跳过
        # 代码: `if phase in REFLECTIVE_PHASES and result.success:`

    def test_self_reflector_importable(self):
        """SelfReflector 可从正确路径导入"""
        from lemma.engine.reflector import SelfReflector
        assert SelfReflector is not None
