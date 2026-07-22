"""断点续跑检查点测试"""

import json
import pytest
from lemma.engine.checkpoint import (
    RunCheckpoint,
    PhaseCheckpoint,
    create_checkpoint_from_phases,
)


class TestRunCheckpoint:
    def test_create_from_phases(self):
        cp = create_checkpoint_from_phases("math-modeling", "test input", ["a", "b", "c"])
        assert cp.domain_id == "math-modeling"
        assert len(cp.phases) == 3
        assert cp.remaining_phases == ["a", "b", "c"]
        assert cp.progress == 0.0

    def test_progress_calculation(self):
        cp = RunCheckpoint(phases=[
            PhaseCheckpoint("a", status="completed"),
            PhaseCheckpoint("b", status="running"),
            PhaseCheckpoint("c", status="pending"),
        ])
        assert cp.progress == pytest.approx(1 / 3)
        assert cp.completed_phases == ["a"]
        assert cp.remaining_phases == ["b", "c"]

    def test_save_and_load(self, tmp_path):
        cp = create_checkpoint_from_phases("test", "input", ["p1", "p2"])
        cp.phases[0].status = "completed"
        cp.phases[0].summary = "done"

        path = str(tmp_path / "checkpoint_test.json")
        cp.save(path)

        loaded = RunCheckpoint.load(path)
        assert loaded is not None
        assert loaded.run_id == cp.run_id
        assert loaded.domain_id == "test"
        assert loaded.phases[0].status == "completed"
        assert loaded.phases[0].summary == "done"
        assert loaded.phases[1].status == "pending"

    def test_load_nonexistent(self):
        assert RunCheckpoint.load("/nonexistent/path.json") is None

    def test_load_invalid_json(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not json")
        assert RunCheckpoint.load(str(path)) is None

    def test_list_checkpoints(self, tmp_path):
        cp1 = create_checkpoint_from_phases("test", "in1", ["a"])
        cp1.save(str(tmp_path / "checkpoint_001.json"))

        cp2 = create_checkpoint_from_phases("test", "in2", ["b"])
        cp2.save(str(tmp_path / "checkpoint_002.json"))

        (tmp_path / "other.txt").write_text("ignore me")

        checkpoints = RunCheckpoint.list_checkpoints(str(tmp_path))
        assert len(checkpoints) == 2

    def test_failed_phases(self):
        cp = RunCheckpoint(phases=[
            PhaseCheckpoint("a", status="completed"),
            PhaseCheckpoint("b", status="failed"),
            PhaseCheckpoint("c", status="pending"),
        ])
        assert cp.failed_phases == ["b"]
        assert cp.remaining_phases == ["b", "c"]  # failed also remaining
