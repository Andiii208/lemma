"""结构化交接协议单元测试"""
from lemma.engine.handoff import (
    HandoffSummary,
    Confidence,
    parse_handoff_from_text,
)


class TestHandoff:
    def test_parse_from_markdown_table(self):
        text = """| 字段 | 内容 |
|------|------|
| 结论 | 模型A优于模型B |
| 置信度 | green |
| 未解决分歧 | 参数X取值存在争议 |
| 关键数据引用 | data.csv, config.json |
| 下游警告 | 线性假设可能不成立 |"""

        handoff = parse_handoff_from_text(text)
        assert handoff is not None
        assert handoff.conclusion == "模型A优于模型B"
        assert handoff.confidence == Confidence.GREEN
        assert "参数X取值存在争议" in handoff.unresolved_disagreements

    def test_parse_no_table_returns_none(self):
        assert parse_handoff_from_text("普通文本，没有表格。") is None

    def test_parse_partial_table(self):
        """缺少字段的表格应仍能解析"""
        text = """| 字段 | 内容 |
|------|------|
| 结论 | 完成测试 |
| 置信度 | yellow |"""

        handoff = parse_handoff_from_text(text)
        assert handoff is not None
        assert handoff.conclusion == "完成测试"
        assert handoff.confidence == Confidence.YELLOW
        assert handoff.unresolved_disagreements == []

    def test_parse_confidence_red(self):
        text = """| 字段 | 内容 |
|------|------|
| 结论 | 结果不可靠 |
| 置信度 | red |
| 下游警告 | 数据存在异常值 |"""

        handoff = parse_handoff_from_text(text)
        assert handoff is not None
        assert handoff.confidence == Confidence.RED
        assert "数据存在异常值" in handoff.downstream_warnings

    def test_parse_without_conclusion_returns_none(self):
        text = """| 字段 | 内容 |
|------|------|
| 置信度 | green |"""
        assert parse_handoff_from_text(text) is None

    def test_to_context_block(self):
        handoff = HandoffSummary(
            agent_role="critic",
            agent_name="审稿人",
            conclusion="代码可以运行但效率低",
            confidence=Confidence.YELLOW,
            downstream_warnings=["需要优化循环"],
            artifacts_produced={"review": "review.md"},
        )
        block = handoff.to_context_block()
        assert "审稿人" in block
        assert "yellow" in block
        assert "需要优化循环" in block
        assert "review.md" in block

    def test_to_context_block_roundtrip(self):
        """to_context_block 的输出应能被 parse_handoff_from_text 解析"""
        original = HandoffSummary(
            agent_role="writer",
            agent_name="作者",
            conclusion="论文初稿完成",
            confidence=Confidence.GREEN,
            downstream_warnings=["需补充实验数据"],
        )
        block = original.to_context_block()
        parsed = parse_handoff_from_text(block)
        assert parsed is not None
        assert parsed.conclusion == "论文初稿完成"
        assert parsed.confidence == Confidence.GREEN

    def test_split_field_by_semicolon(self):
        """分隔符处理：分号"""
        text = """| 字段 | 内容 |
|------|------|
| 结论 | A |
| 未解决分歧 | X; Y; Z |"""
        handoff = parse_handoff_from_text(text)
        assert handoff is not None
        assert len(handoff.unresolved_disagreements) >= 3

    def test_confidence_default_green(self):
        """未知的置信度文本应默认 green"""
        text = """| 字段 | 内容 |
|------|------|
| 结论 | A |
| 置信度 | maybe |"""
        handoff = parse_handoff_from_text(text)
        assert handoff is not None
        assert handoff.confidence == Confidence.GREEN

    def test_empty_text_returns_none(self):
        assert parse_handoff_from_text("") is None
