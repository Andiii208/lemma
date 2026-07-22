"""Prompt 版本追踪 — 记录每次 prompt 修改"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


class PromptVersionTracker:
    """追踪所有 prompt 文件的版本变化"""

    def __init__(self, history_path: str = ".ultraagent/prompt_versions.jsonl"):
        self.history_path = Path(history_path)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

    def snapshot(self, domains_dir: str) -> dict:
        """对当前所有 prompt 生成版本快照"""
        hashes = {}
        for prompt_file in sorted(Path(domains_dir).glob("**/prompts/*.md")):
            try:
                content = prompt_file.read_text(encoding="utf-8")
                rel_path = str(prompt_file.relative_to(domains_dir))
                hashes[rel_path] = {
                    "hash": hashlib.sha256(content.encode()).hexdigest()[:12],
                    "length": len(content),
                    "lines": content.count("\n") + 1,
                    "timestamp": datetime.now().isoformat(),
                }
            except Exception:
                continue
        return hashes

    def record(self, domains_dir: str, label: str = "") -> dict:
        """记录当前快照到历史"""
        snap = self.snapshot(domains_dir)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "label": label,
            "file_count": len(snap),
            "files": snap,
        }
        with open(self.history_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return snap

    def get_history(self, limit: int = 10) -> list[dict]:
        """获取最近的版本历史"""
        if not self.history_path.exists():
            return []
        lines = self.history_path.read_text(encoding="utf-8").strip().split("\n")
        entries = []
        for line in lines[-limit:]:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries

    @staticmethod
    def compare(baseline: dict, current: dict) -> list[str]:
        """对比两个快照，返回有变化的文件列表"""
        changed = []
        for path, info in current.items():
            if path not in baseline:
                changed.append(f"+ {path} (新增)")
            elif baseline[path]["hash"] != info["hash"]:
                changed.append(f"~ {path} (修改)")
        for path in baseline:
            if path not in current:
                changed.append(f"- {path} (删除)")
        return changed
