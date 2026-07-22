"""评测数据集加载器 — 加载 Golden JSONL 格式的评测用例"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class GoldenCase:
    """单条评测用例"""

    id: str
    input: str
    expected: dict = field(default_factory=dict)


class GoldenDataset:
    """评测数据集 — 从 JSONL 文件加载"""

    def __init__(self, cases: list[GoldenCase]):
        self._cases = cases

    def __len__(self) -> int:
        return len(self._cases)

    def __getitem__(self, i: int) -> GoldenCase:
        return self._cases[i]

    def __iter__(self):
        return iter(self._cases)

    def __repr__(self) -> str:
        return f"GoldenDataset({len(self._cases)} cases)"

    @classmethod
    def from_jsonl(cls, path: str) -> GoldenDataset:
        """从 JSONL 文件加载，坏行静默跳过"""
        cases: list[GoldenCase] = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "id" in obj and "input" in obj and "expected" in obj:
                cases.append(GoldenCase(obj["id"], obj["input"], obj["expected"]))
        return cls(cases)

    @classmethod
    def from_directory(cls, dir_path: str, glob: str = "*.jsonl") -> GoldenDataset:
        """从目录下所有 JSONL 文件合并加载"""
        all_cases: list[GoldenCase] = []
        for f in sorted(Path(dir_path).glob(glob)):
            all_cases.extend(cls.from_jsonl(str(f))._cases)
        return cls(all_cases)
