"""状态机 — 通用状态机，阶段从 DomainProfile 加载"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..engine.domain import DomainProfile, PhaseResult


# 老的 Phase 枚举保留，但不再是核心状态机的一部分
class Phase(Enum):
    """执行阶段（旧枚举，保持向后兼容）"""
    IDLE = -1
    INIT = 0
    ANALYSIS = 1
    DERIVATION = 2
    ONTOLOGY = 3
    CODING = 4
    TESTING = 5
    WRITING = 6
    REVIEW = 7
    DONE = 8


PHASE_NAMES = {
    Phase.IDLE: "空闲",
    Phase.INIT: "初始化",
    Phase.ANALYSIS: "题目分析",
    Phase.DERIVATION: "数学推导",
    Phase.ONTOLOGY: "本体构造",
    Phase.CODING: "代码实现",
    Phase.TESTING: "测试验证",
    Phase.WRITING: "论文写作",
    Phase.REVIEW: "交叉审稿",
    Phase.DONE: "完成",
}


def math_modeling_profile() -> DomainProfile:
    """创建一个与旧 Phase 枚举兼容的 DomainProfile"""
    from ..engine.domain import DomainProfile
    return DomainProfile(
        id="math-modeling",
        name="数学建模竞赛",
        description="向后兼容模式",
        version="2.0",
        phases=[
            {"id": "idle", "name": "空闲", "order": -1, "progress": 0,
             "transition": {"pass": "init"}},
            {"id": "init", "name": "初始化", "order": 0, "progress": 5,
             "transition": {"pass": "analysis", "fail": "init"}},
            {"id": "analysis", "name": "题目分析", "order": 1, "progress": 15,
             "transition": {"pass": "derivation", "fail": "analysis"}},
            {"id": "derivation", "name": "数学推导", "order": 2, "progress": 30,
             "transition": {"pass": "ontology", "fail": "derivation"}},
            {"id": "ontology", "name": "本体构造", "order": 3, "progress": 40,
             "transition": {"pass": "coding", "fail": "ontology"}},
            {"id": "coding", "name": "代码实现", "order": 4, "progress": 55,
             "transition": {"pass": "testing", "fail": "coding"}},
            {"id": "testing", "name": "测试验证", "order": 5, "progress": 65,
             "transition": {"pass": "writing", "fail": "coding"}},
            {"id": "writing", "name": "论文写作", "order": 6, "progress": 80,
             "transition": {"pass": "review", "fail": "writing"}},
            {"id": "review", "name": "交叉审稿", "order": 7, "progress": 90,
             "transition": {"pass": "done", "fail": "writing"}},
            {"id": "done", "name": "完成", "order": 8, "progress": 100},
        ],
        roles=[
            {"id": "lead", "name": "团队指挥", "temperature": 0.5},
            {"id": "math", "name": "数学家", "temperature": 0.8},
            {"id": "engineer", "name": "工程师", "temperature": 0.3},
            {"id": "reviewer", "name": "审稿人", "temperature": 0.4},
            {"id": "writer", "name": "作家", "temperature": 0.6},
        ],
        directories={"input": "题目", "output": "求解", "paper": "论文", "data": "数据"},
    )


# ==================== 新版状态机 ====================


@dataclass
class StateMachine:
    """通用状态机 — 阶段和转换规则由 DomainProfile 定义"""

    profile: DomainProfile
    current_phase: str = "idle"
    history: list[dict] = field(default_factory=list)
    _phase_results: dict[str, PhaseResult] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """确保 current_phase 是 profile 中的有效阶段"""
        if not self.profile.get_phase_by_id(self.current_phase):
            phase_ids = self.profile.get_phase_ids()
            self.current_phase = phase_ids[0] if phase_ids else "idle"

    def transition(self, result: PhaseResult) -> str:
        """根据阶段结果执行状态转换"""
        self._phase_results[result.phase_id] = result

        next_phase = self.profile.get_transition(
            result.phase_id,
            success=result.success and result.gate_passed,
        )

        current_cfg = self.profile.get_phase_by_id(result.phase_id)
        next_cfg = self.profile.get_phase_by_id(next_phase)

        self.history.append({
            "from": result.phase_id,
            "from_name": current_cfg.name if current_cfg else result.phase_id,
            "to": next_phase,
            "to_name": next_cfg.name if next_cfg else next_phase,
            "success": result.success,
            "summary": result.summary,
        })
        self.current_phase = next_phase
        return next_phase

    def skip_to(self, phase_id: str) -> None:
        """跳转到指定阶段"""
        if self.profile.get_phase_by_id(phase_id):
            self.current_phase = phase_id

    # --- 属性 ---

    @property
    def is_done(self) -> bool:
        return self.current_phase == "done"

    @property
    def is_idle(self) -> bool:
        return self.current_phase == "idle"

    @property
    def progress(self) -> float:
        phase = self.profile.get_phase_by_id(self.current_phase)
        return phase.progress if phase else 0.0

    @property
    def phase_name(self) -> str:
        phase = self.profile.get_phase_by_id(self.current_phase)
        return phase.name if phase else "未知"

    def get_phase_result(self, phase_id: str) -> PhaseResult | None:
        return self._phase_results.get(phase_id)

    def to_dict(self) -> dict:
        return {
            "current_phase": self.current_phase,
            "current_phase_name": self.phase_name,
            "progress": self.progress,
            "is_done": self.is_done,
            "domain_id": self.profile.id,
            "domain_name": self.profile.name,
            "history": self.history,
        }
