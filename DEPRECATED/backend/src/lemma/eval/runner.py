"""评测 Runner — 批量执行评测并生成报告"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from .dataset import GoldenCase, GoldenDataset
from .llm_judge import LLMJudge
from .report import CaseResult, EvalReport
from .scorers import (
    CompositeScorer,
    KeywordScorer,
    LaTeXScorer,
    LengthScorer,
    ScoreResult,
    StructureScorer,
)

logger = logging.getLogger("ultramath.eval")


def build_scorers(expected: dict) -> list[tuple]:
    """根据 expected 字段构建评分器列表"""
    scorers: list[tuple] = []

    # 关键词评分
    keywords = expected.get("keywords", [])
    if keywords:
        scorers.append((KeywordScorer(keywords), 1.0))

    # 长度评分
    min_length = expected.get("min_length", 0)
    if min_length > 0:
        scorers.append((LengthScorer(min_length=min_length), 0.8))

    # 结构评分
    sections = expected.get("required_sections", [])
    if sections:
        scorers.append((StructureScorer(sections), 1.0))

    # LaTeX 评分（默认开启）
    if expected.get("must_compile", False):
        scorers.append((LaTeXScorer(), 0.6))

    # 如果没有任何评分器，用默认的长度检查
    if not scorers:
        scorers.append((LengthScorer(min_length=100), 1.0))

    return scorers


async def run_agent_for_case(
    domain_id: str,
    case: GoldenCase,
    use_mock: bool = True,
) -> str:
    """为单条 case 运行 agent 并返回产出文本

    Args:
        domain_id: 领域 ID
        case: 评测用例
        use_mock: 是否使用 mock（不调用真实 LLM）
    """
    if use_mock:
        # Mock 模式：返回模拟产出用于测试评测系统本身
        return _mock_output(case)

    # 真实模式：创建 agent 并运行
    from ..engine.agent import AcademicAgent
    from ..engine.domain import DomainProfile
    from ..llm.router import ModelRouter
    from ..tools.registry import ToolRegistry

    domains_base = str(Path(__file__).parent.parent.parent.parent.parent / "domains")
    domain = DomainProfile.from_directory(f"{domains_base}/{domain_id}")

    # 使用默认配置
    from ..llm.backend import LLMConfig

    config = LLMConfig()  # 会从环境变量读取
    router = ModelRouter.from_single_config(config)
    tools = ToolRegistry()

    agent = AcademicAgent("/tmp/eval_workspace", domain, router, tools)

    # 运行并收集输出
    outputs: list[str] = []
    async for event in agent.run_auto(case.input):
        if event.get("type") == "phase_end" and event.get("summary"):
            outputs.append(event["summary"])
        if event.get("type") == "complete":
            break

    return "\n\n".join(outputs) if outputs else "(无输出)"


def _mock_output(case: GoldenCase) -> str:
    """生成模拟产出（基于 expected 的关键词构造）"""
    keywords = case.expected.get("keywords", [])
    sections = case.expected.get("required_sections", ["摘要", "问题分析", "模型建立"])
    min_length = case.expected.get("min_length", 500)

    parts = []
    for section in sections:
        parts.append(f"## {section}\n\n这是关于{section}的内容。")
    if keywords:
        parts.append("## 关键内容\n\n" + "，".join(keywords) + "是本文的核心要素。")

    output = "\n\n".join(parts)
    # 保证达到最小长度
    while len(output) < min_length:
        output += "\n\n补充内容段落，用于满足最低字数要求。"
    return output


async def evaluate(
    domain_id: str,
    dataset: GoldenDataset,
    version: str = "unknown",
    use_mock: bool = True,
    llm_judge: LLMJudge | None = None,
    judge_criteria: str | None = None,
) -> EvalReport:
    """批量评测

    Args:
        domain_id: 领域 ID
        dataset: 评测数据集
        version: 版本标识
        use_mock: 是否使用 mock
        llm_judge: LLM 评分器（可选）
        judge_criteria: LLM 评分标准（可选）

    Returns:
        EvalReport
    """
    report = EvalReport(domain_id=domain_id, version=version)

    for case in dataset:
        logger.info(f"评测用例: {case.id}")

        # 运行 agent 获取产出
        output = await run_agent_for_case(domain_id, case, use_mock=use_mock)

        # 构建评分器并评分
        scorer_tuples = build_scorers(case.expected)
        composite = CompositeScorer(scorer_tuples)
        total_score, score_results = composite.score(output)

        # 可选：LLM 评分
        if llm_judge and judge_criteria:
            try:
                judge_result = await llm_judge.score(output, judge_criteria)
                score_results.append(judge_result)
            except Exception as e:
                logger.warning(f"LLM 评分失败: {e}")

        report.cases.append(CaseResult(
            case_id=case.id,
            scores=score_results,
            output_preview=output[:200],
        ))

    return report


async def evaluate_domain(
    domain_id: str,
    version: str = "unknown",
    use_mock: bool = True,
) -> EvalReport:
    """评测指定领域（从 domains/<id>/golden.jsonl 加载数据集）"""
    golden_path = Path(__file__).parent.parent.parent.parent.parent / "domains" / domain_id / "golden.jsonl"
    if not golden_path.exists():
        logger.warning(f"Golden set 不存在: {golden_path}，跳过评测")
        return EvalReport(domain_id=domain_id, version=version)

    dataset = GoldenDataset.from_jsonl(str(golden_path))
    return await evaluate(domain_id, dataset, version=version, use_mock=use_mock)


# ==================== CLI 入口 ====================


def main():
    """命令行入口: python -m ultramath.eval.runner --domain math-modeling --mock"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="UltraAgent 评测 Runner")
    parser.add_argument("--domain", required=True, help="领域 ID")
    parser.add_argument("--version", default="unknown", help="版本标识")
    parser.add_argument("--mock", action="store_true", default=True, help="使用 mock 模式（默认）")
    parser.add_argument("--no-mock", dest="mock", action="store_false", help="使用真实 LLM")
    parser.add_argument("--output", default=None, help="报告输出路径（默认 docs/eval-report-<domain>.md）")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    report = asyncio.run(evaluate_domain(args.domain, version=args.version, use_mock=args.mock))

    # 输出 Markdown 报告
    md = report.to_markdown()
    output_path = args.output or f"docs/eval-report-{args.domain}.md"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(md, encoding="utf-8")

    print(md)
    print(f"\n报告已保存到: {output_path}")
    sys.exit(0 if report.passed_cases == report.total_cases else 1)


if __name__ == "__main__":
    main()
