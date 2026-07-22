"""阶段上下文 — Phase 间传递关键信息"""

from __future__ import annotations

import contextlib
import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel


class PhaseContext(BaseModel):
    """阶段上下文"""

    phase: str = ""
    phase_name: str = ""
    status: str = "pending"
    started_at: str = ""
    completed_at: str = ""
    artifacts: dict[str, str] = {}
    summary: str = ""
    decisions: list[str] = []
    issues: list[str] = []
    metrics: dict[str, float] = {}


class ProjectContext(BaseModel):
    """项目全局上下文"""

    problem_dir: str = ""
    problem_type: str = ""
    problem_summary: str = ""
    phases: dict[str, PhaseContext] = {}
    created_at: str = ""
    updated_at: str = ""


class ContextManager:
    """阶段上下文管理器"""

    def __init__(self, work_dir: str):
        self.work_dir = Path(work_dir)
        self.context_file = self.work_dir / "agent-context.json"
        self.project = ProjectContext(
            problem_dir=str(work_dir),
            created_at=datetime.now().isoformat(),
        )
        self._load()

    def _load(self) -> None:
        """从文件加载"""
        if self.context_file.exists():
            try:
                data = json.loads(self.context_file.read_text(encoding="utf-8"))
                self.project = ProjectContext(**data)
            except Exception:
                pass

    def save(self) -> None:
        """保存到文件"""
        self.project.updated_at = datetime.now().isoformat()
        with contextlib.suppress(Exception):
            self.context_file.write_text(
                self.project.model_dump_json(indent=2),
                encoding="utf-8",
            )

    def update_phase(self, phase: str, phase_name: str = "", **kwargs) -> None:
        """更新阶段状态"""
        if phase not in self.project.phases:
            self.project.phases[phase] = PhaseContext(
                phase=phase,
                phase_name=phase_name,
                started_at=datetime.now().isoformat(),
            )
        ctx = self.project.phases[phase]
        for k, v in kwargs.items():
            if hasattr(ctx, k):
                setattr(ctx, k, v)
        if kwargs.get("status") == "completed":
            ctx.completed_at = datetime.now().isoformat()
        self.save()

    def add_artifact(self, phase: str, name: str, path: str) -> None:
        """添加产物"""
        if phase not in self.project.phases:
            self.project.phases[phase] = PhaseContext(phase=phase)
        self.project.phases[phase].artifacts[name] = path
        self.save()

    def add_decision(self, phase: str, decision: str) -> None:
        """添加决策记录"""
        if phase not in self.project.phases:
            self.project.phases[phase] = PhaseContext(phase=phase)
        self.project.phases[phase].decisions.append(decision)
        self.save()

    def add_issue(self, phase: str, issue: str) -> None:
        """添加问题记录"""
        if phase not in self.project.phases:
            self.project.phases[phase] = PhaseContext(phase=phase)
        self.project.phases[phase].issues.append(issue)
        self.save()

    def get_phase_context(self, phase: str) -> PhaseContext | None:
        """获取阶段上下文"""
        return self.project.phases.get(phase)

    def get_phase_summary(self, phase: str) -> str:
        """获取阶段摘要"""
        ctx = self.project.phases.get(phase)
        if not ctx:
            return f"Phase {phase}: 未开始"
        parts = [f"Phase {phase} ({ctx.phase_name}): {ctx.status}"]
        if ctx.summary:
            parts.append(f"  摘要: {ctx.summary}")
        if ctx.decisions:
            parts.append(f"  决策: {len(ctx.decisions)} 项")
        if ctx.issues:
            parts.append(f"  问题: {len(ctx.issues)} 项")
        return "\n".join(parts)

    def get_all_summaries(self) -> str:
        """获取所有阶段摘要"""
        lines = []
        for phase_num in sorted(self.project.phases.keys()):
            lines.append(self.get_phase_summary(phase_num))
        return "\n".join(lines) if lines else "尚无阶段记录"

    def set_problem_info(self, problem_type: str, summary: str) -> None:
        """设置问题信息"""
        self.project.problem_type = problem_type
        self.project.problem_summary = summary
        self.save()

    # ==================== 检查点 ====================

    def save_checkpoint(self, agent_state: dict) -> None:
        """保存完整检查点"""
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "agent_state": agent_state,
            "phases": [ctx.model_dump() for ctx in self.project.phases.values()],
        }
        checkpoint_path = self.context_file.parent / "checkpoint.json"
        with contextlib.suppress(Exception):
            checkpoint_path.write_text(
                json.dumps(checkpoint, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    def restore_checkpoint(self) -> dict | None:
        """恢复检查点"""
        checkpoint_path = self.context_file.parent / "checkpoint.json"
        if not checkpoint_path.exists():
            return None
        try:
            return json.loads(checkpoint_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def cleanup_old_checkpoints(self, max_age_days: int = 7) -> int:
        """清理过期检查点"""
        checkpoint_path = self.context_file.parent / "checkpoint.json"
        if not checkpoint_path.exists():
            return 0
        age = datetime.now() - datetime.fromtimestamp(checkpoint_path.stat().st_mtime)
        if age.days > max_age_days:
            with contextlib.suppress(Exception):
                checkpoint_path.unlink()
                return 1
        return 0
