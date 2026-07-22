"""Prompt 版本追踪 — 记录每次 prompt 修改"""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


class PromptVersionTracker:
    """追踪领域 prompt 文件的版本变化"""

    def snapshot(self, domains_dir: str) -> dict:
        """对当前所有 prompt 生成版本快照"""
        hashes = {}
        for prompt_file in Path(domains_dir).glob("**/prompts/*.md"):
            content = prompt_file.read_text(encoding="utf-8")
            hashes[str(prompt_file)] = {
                "hash": hashlib.sha256(content.encode()).hexdigest()[:12],
                "length": len(content),
                "timestamp": datetime.now().isoformat(),
            }
        return hashes

    def compare(self, baseline: dict, current: dict) -> list[str]:
        """对比两个快照，返回有变化的文件列表"""
        changed = []
        for path, info in current.items():
            if path not in baseline or baseline[path]["hash"] != info["hash"]:
                changed.append(path)
        return changed

    def save_snapshot(self, domains_dir: str, output_path: str) -> None:
        """保存快照到文件"""
        snapshot = self.snapshot(domains_dir)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(snapshot, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def load_baseline(self, baseline_path: str) -> dict:
        """加载基线快照"""
        path = Path(baseline_path)
        if not path.exists():
            return {}
        result: dict = json.loads(path.read_text(encoding="utf-8"))
        return result
