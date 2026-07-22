"""API 扩展端点 — 公式渲染、知识图谱查询、灰度实验"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FormulaResult:
    """公式渲染结果"""

    latex: str = ""
    html: str = ""
    explanation: str = ""


def render_formula(latex: str) -> FormulaResult:
    """渲染 LaTeX 公式为 KaTeX HTML"""
    # 基础 HTML 包装（前端用 KaTeX 渲染，这里只做验证和包装）
    clean_latex = latex.strip()
    if not clean_latex.startswith("$"):
        clean_latex = f"$${clean_latex}$$"

    return FormulaResult(
        latex=clean_latex,
        html=f'<span class="katex">{clean_latex}</span>',
        explanation="",
    )


def extract_formulas(text: str) -> list[str]:
    """从文本中提取所有 LaTeX 公式"""
    patterns = [
        r"\$\$(.+?)\$\$",  # display math
        r"\$(.+?)\$",      # inline math
        r"\\begin\{equation\}(.+?)\\end\{equation\}",
    ]
    formulas = []
    for pattern in patterns:
        formulas.extend(re.findall(pattern, text, re.DOTALL))
    return formulas


@dataclass
class Experiment:
    """灰度实验"""

    experiment_id: str = ""
    name: str = ""
    description: str = ""
    variants: list[str] = field(default_factory=lambda: ["control", "treatment"])
    traffic_split: dict[str, float] = field(default_factory=lambda: {"control": 0.5, "treatment": 0.5})
    active: bool = True
    metric: str = "eval_score"


class ExperimentManager:
    """灰度实验管理器"""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._experiments_file = self.data_dir / "experiments.jsonl"
        self._experiments: dict[str, Experiment] = {}
        self._load()

    def _load(self) -> None:
        if not self._experiments_file.exists():
            return
        for line in self._experiments_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                exp = Experiment(**data)
                self._experiments[exp.experiment_id] = exp
            except (json.JSONDecodeError, TypeError):
                continue

    def create(self, experiment_id: str, name: str, variants: list[str] | None = None) -> Experiment:
        exp = Experiment(
            experiment_id=experiment_id,
            name=name,
            variants=variants or ["control", "treatment"],
        )
        self._experiments[experiment_id] = exp
        self._save(exp)
        return exp

    def get_variant(self, experiment_id: str, user_id: str) -> str:
        """确定性地分配用户到变体（基于哈希）"""
        exp = self._experiments.get(experiment_id)
        if not exp or not exp.active:
            return "control"

        # 基于 user_id 的哈希确定性分配
        hash_val = hash(f"{experiment_id}:{user_id}") % 100
        cumulative = 0.0
        for variant, split in exp.traffic_split.items():
            cumulative += split * 100
            if hash_val < cumulative:
                return variant
        return exp.variants[0]

    def list_all(self) -> list[Experiment]:
        return list(self._experiments.values())

    def deactivate(self, experiment_id: str) -> bool:
        exp = self._experiments.get(experiment_id)
        if not exp:
            return False
        exp.active = False
        self._save_all()
        return True

    def _save(self, exp: Experiment) -> None:
        with open(self._experiments_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "experiment_id": exp.experiment_id,
                "name": exp.name,
                "variants": exp.variants,
                "traffic_split": exp.traffic_split,
                "active": exp.active,
                "metric": exp.metric,
            }, ensure_ascii=False) + "\n")

    def _save_all(self) -> None:
        self._experiments_file.write_text(
            "\n".join(
                json.dumps({
                    "experiment_id": e.experiment_id,
                    "name": e.name,
                    "variants": e.variants,
                    "traffic_split": e.traffic_split,
                    "active": e.active,
                    "metric": e.metric,
                }, ensure_ascii=False)
                for e in self._experiments.values()
            ) + "\n",
            encoding="utf-8",
        )
