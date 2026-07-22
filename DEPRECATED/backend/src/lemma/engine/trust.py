"""信赖阈值系统 — 根据用户反馈历史调整确认行为"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class TrustLevel(Enum):
    """信赖级别"""
    LOOSE = "loose"     # 连续 5+ 接受 → 跳过确认
    RELAXED = "relaxed" # 连续 3+ 接受
    NORMAL = "normal"   # 默认
    TIGHTEN = "tighten" # 连续 2 拒绝
    RESET = "reset"     # corrected_later 触发 → 最保守


@dataclass
class TrustRecord:
    """一次信赖记录"""
    phase_id: str
    accepted: bool          # True=接受, False=拒绝
    corrected_later: bool = False  # 后来被纠正
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class TrustManager:
    """信赖管理器"""

    MAX_HISTORY = 20

    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.records: list[TrustRecord] = []
        self._load()

    def record(self, phase_id: str, accepted: bool, corrected_later: bool = False) -> None:
        """记录一次用户反馈"""
        self.records.append(TrustRecord(
            phase_id=phase_id,
            accepted=accepted,
            corrected_later=corrected_later,
        ))
        if len(self.records) > self.MAX_HISTORY:
            self.records = self.records[-self.MAX_HISTORY:]
        self._save()

    def get_trust_level(self) -> TrustLevel:
        """根据最近反馈计算信赖级别"""
        recent = self.records[-10:]

        # corrected_later 立即重置到最保守
        if any(r.corrected_later for r in recent[-3:]):
            return TrustLevel.RESET

        accepts = sum(1 for r in recent if r.accepted)
        rejects = sum(1 for r in recent if not r.accepted)

        if accepts >= 5 and rejects == 0:
            return TrustLevel.LOOSE
        if accepts >= 3 and rejects == 0:
            return TrustLevel.RELAXED
        if rejects >= 2:
            return TrustLevel.TIGHTEN
        return TrustLevel.NORMAL

    def should_confirm(self, phase_id: str) -> bool:
        """判断当前阶段是否需要用户确认"""
        level = self.get_trust_level()
        return level in (TrustLevel.NORMAL, TrustLevel.TIGHTEN, TrustLevel.RESET)

    def reset(self) -> None:
        """清空所有记录"""
        self.records.clear()
        self._save()

    def _save(self) -> None:
        data = [
            {
                "phase_id": r.phase_id,
                "accepted": r.accepted,
                "corrected_later": r.corrected_later,
                "timestamp": r.timestamp,
            }
            for r in self.records
        ]
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load(self) -> None:
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                self.records = [TrustRecord(**r) for r in data]
            except Exception:
                self.records = []

    @property
    def stats(self) -> dict:
        """返回统计摘要"""
        total = len(self.records)
        accepts = sum(1 for r in self.records if r.accepted)
        rejects = total - accepts
        corrections = sum(1 for r in self.records if r.corrected_later)
        return {
            "total_records": total,
            "accepted": accepts,
            "rejected": rejects,
            "corrected_later": corrections,
            "trust_level": self.get_trust_level().value,
        }
