"""评测 Runner 测试"""

import json
import pytest
from lemma.eval.dataset import GoldenDataset, GoldenCase
from lemma.eval.runner import build_scorers, run_agent_for_case, evaluate
from lemma.eval.report import EvalReport, CaseResult
from lemma.eval.scorers import ScoreResult


class TestBuildScorers:
    def test_keywords_and_length(self):
        expected = {"keywords": ["优化"], "min_length": 100}
        scorers = build_scorers(expected)
        assert len(scorers) == 2

    def test_empty_expected(self):
        scorers = build_scorers({})
        assert len(scorers) == 1  # 默认 LengthScorer

    def test_must_compile_adds_latex(self):
        expected = {"must_compile": True}
        scorers = build_scorers(expected)
        names = [type(s).__name__ for s, _ in scorers]
        assert "LaTeXScorer" in names


class TestMockOutput:
    @pytest.mark.asyncio
    async def test_mock_output_contains_keywords(self):
        case = GoldenCase("t1", "问题", {"keywords": ["模型", "优化"], "min_length": 500})
        output = await run_agent_for_case("math-modeling", case, use_mock=True)
        assert "模型" in output
        assert "优化" in output
        assert len(output) >= 500

    @pytest.mark.asyncio
    async def test_mock_output_respects_sections(self):
        case = GoldenCase("t1", "问题", {"required_sections": ["摘要", "求解"]})
        output = await run_agent_for_case("math-modeling", case, use_mock=True)
        assert "摘要" in output
        assert "求解" in output


class TestEvaluate:
    @pytest.mark.asyncio
    async def test_evaluate_returns_report(self, tmp_path):
        # 创建测试数据集
        f = tmp_path / "golden.jsonl"
        lines = [
            json.dumps({"id": "t1", "input": "问题1", "expected": {"keywords": ["模型"], "min_length": 100}}),
            json.dumps({"id": "t2", "input": "问题2", "expected": {"keywords": ["优化"], "min_length": 100}}),
        ]
        f.write_text("\n".join(lines), encoding="utf-8")
        dataset = GoldenDataset.from_jsonl(str(f))

        report = await evaluate("math-modeling", dataset, version="test", use_mock=True)
        assert report.total_cases == 2
        assert report.avg_score > 0
        assert len(report.cases) == 2


class TestEvalReport:
    def test_to_markdown(self):
        report = EvalReport(domain_id="test", version="v1")
        report.cases = [
            CaseResult("t1", [ScoreResult("keyword", 0.8, True, "2/3 命中")]),
            CaseResult("t2", [ScoreResult("keyword", 0.5, False, "1/3 命中")]),
        ]
        md = report.to_markdown()
        assert "评测报告: test" in md
        assert "v1" in md
        assert "t1" in md
        assert "t2" in md

    def test_save_and_load(self, tmp_path):
        report = EvalReport(domain_id="test", version="v1")
        report.cases = [
            CaseResult("t1", [ScoreResult("keyword", 0.8, True)])
        ]
        path = str(tmp_path / "report.json")
        report.save(path)

        loaded = EvalReport.load(path)
        assert loaded.domain_id == "test"
        assert loaded.total_cases == 1
        assert loaded.cases[0].case_id == "t1"

    def test_compare(self):
        old = EvalReport(domain_id="test", version="v1")
        old.cases = [
            CaseResult("t1", [ScoreResult("k", 0.5, False)]),
            CaseResult("t2", [ScoreResult("k", 0.8, True)]),
        ]

        new = EvalReport(domain_id="test", version="v2")
        new.cases = [
            CaseResult("t1", [ScoreResult("k", 0.8, True)]),  # 改善
            CaseResult("t2", [ScoreResult("k", 0.6, True)]),  # 回退
        ]

        diff = new.compare(old)
        assert len(diff["improved"]) == 1
        assert diff["improved"][0]["case_id"] == "t1"
        assert len(diff["regressed"]) == 1
        assert diff["regressed"][0]["case_id"] == "t2"
