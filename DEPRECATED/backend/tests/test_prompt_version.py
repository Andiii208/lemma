"""Prompt 版本追踪测试"""

import json
import pytest
from pathlib import Path
from lemma.engine.prompt_version import PromptVersionTracker


class TestPromptVersionTracker:
    def test_snapshot_returns_dict(self, tmp_path):
        prompts_dir = tmp_path / "domains" / "test" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "agent_lead.md").write_text("# Lead Agent", encoding="utf-8")

        tracker = PromptVersionTracker()
        snap = tracker.snapshot(str(tmp_path / "domains"))
        assert len(snap) >= 1

    def test_snapshot_includes_hash(self, tmp_path):
        prompts_dir = tmp_path / "domains" / "test" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "agent_lead.md").write_text("# Lead", encoding="utf-8")

        tracker = PromptVersionTracker()
        snap = tracker.snapshot(str(tmp_path / "domains"))
        for key, val in snap.items():
            assert "hash" in val
            assert "length" in val
            assert "timestamp" in val
            assert len(val["hash"]) == 12

    def test_compare_detects_changes(self, tmp_path):
        prompts_dir = tmp_path / "domains" / "test" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "agent_lead.md").write_text("# V1", encoding="utf-8")

        tracker = PromptVersionTracker()
        baseline = tracker.snapshot(str(tmp_path / "domains"))

        # 修改文件
        (prompts_dir / "agent_lead.md").write_text("# V2 Changed", encoding="utf-8")
        current = tracker.snapshot(str(tmp_path / "domains"))

        changes = tracker.compare(baseline, current)
        assert len(changes) >= 1

    def test_compare_no_changes(self, tmp_path):
        prompts_dir = tmp_path / "domains" / "test" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "agent_lead.md").write_text("# Stable", encoding="utf-8")

        tracker = PromptVersionTracker()
        baseline = tracker.snapshot(str(tmp_path / "domains"))
        current = tracker.snapshot(str(tmp_path / "domains"))

        assert tracker.compare(baseline, current) == []

    def test_save_and_load_snapshot(self, tmp_path):
        prompts_dir = tmp_path / "domains" / "test" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "agent_lead.md").write_text("# Test", encoding="utf-8")

        tracker = PromptVersionTracker()
        snap = tracker.snapshot(str(tmp_path / "domains"))

        output_path = str(tmp_path / "snapshot.json")
        tracker.save_snapshot(str(tmp_path / "domains"), output_path)

        loaded = tracker.load_baseline(output_path)
        assert len(loaded) == len(snap)

    def test_load_nonexistent_returns_empty(self):
        tracker = PromptVersionTracker()
        assert tracker.load_baseline("/nonexistent/path.json") == {}
