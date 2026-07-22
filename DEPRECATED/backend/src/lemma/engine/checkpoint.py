"""断点续跑 — run_auto 的进度持久化与恢复"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class PhaseCheckpoint:
    """单阶段检查点"""

    phase_id: str
    status: str = "pending"  # pending | running | completed | failed | skipped
    summary: str = ""
    output_preview: str = ""
    started_at: str = ""
    completed_at: str = ""
    error: str = ""
    depth: int = 0


@dataclass
class RunCheckpoint:
    """整次运行的检查点"""

    run_id: str = ""
    domain_id: str = ""
    input_text: str = ""
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    phases: list[PhaseCheckpoint] = field(default_factory=list)
    current_phase_index: int = 0
    status: str = "running"  # running | completed | cancelled | failed

    @property
    def completed_phases(self) -> list[str]:
        return [p.phase_id for p in self.phases if p.status == "completed"]

    @property
    def failed_phases(self) -> list[str]:
        return [p.phase_id for p in self.phases if p.status == "failed"]

    @property
    def remaining_phases(self) -> list[str]:
        return [p.phase_id for p in self.phases if p.status in ("pending", "running", "failed")]

    @property
    def progress(self) -> float:
        if not self.phases:
            return 0.0
        done = sum(1 for p in self.phases if p.status in ("completed", "skipped"))
        return done / len(self.phases)

    def save(self, path: str) -> None:
        """保存检查点到 JSON 文件"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str) -> RunCheckpoint | None:
        """从 JSON 文件加载检查点"""
        p = Path(path)
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            phases = [PhaseCheckpoint(**ph) for ph in data.get("phases", [])]
            return cls(
                run_id=data.get("run_id", ""),
                domain_id=data.get("domain_id", ""),
                input_text=data.get("input_text", ""),
                started_at=data.get("started_at", ""),
                phases=phases,
                current_phase_index=data.get("current_phase_index", 0),
                status=data.get("status", "running"),
            )
        except (json.JSONDecodeError, TypeError, KeyError):
            return None

    @classmethod
    def list_checkpoints(cls, directory: str) -> list[RunCheckpoint]:
        """列出目录下所有检查点"""
        checkpoints = []
        for f in Path(directory).glob("checkpoint_*.json"):
            cp = cls.load(str(f))
            if cp:
                checkpoints.append(cp)
        return sorted(checkpoints, key=lambda c: c.started_at, reverse=True)


def create_checkpoint_from_phases(
    domain_id: str,
    input_text: str,
    phase_ids: list[str],
    run_id: str = "",
) -> RunCheckpoint:
    """从阶段列表创建检查点"""
    from datetime import datetime
    from uuid import uuid4

    return RunCheckpoint(
        run_id=run_id or uuid4().hex[:12],
        domain_id=domain_id,
        input_text=input_text,
        started_at=datetime.now().isoformat(),
        phases=[PhaseCheckpoint(phase_id=pid) for pid in phase_ids],
        current_phase_index=0,
        status="running",
    )
