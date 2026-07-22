"""评测数据集加载器测试"""

import json
import pytest
from lemma.eval.dataset import GoldenDataset, GoldenCase


class TestGoldenDataset:
    def test_load_jsonl(self, tmp_path):
        f = tmp_path / "golden.jsonl"
        f.write_text(
            json.dumps({"id": "t1", "input": "问题", "expected": {"keywords": ["模型"]}}),
            encoding="utf-8",
        )
        ds = GoldenDataset.from_jsonl(str(f))
        assert len(ds) == 1
        assert ds[0].id == "t1"
        assert ds[0].expected["keywords"] == ["模型"]

    def test_load_multiple_lines(self, tmp_path):
        f = tmp_path / "golden.jsonl"
        lines = [
            json.dumps({"id": "t1", "input": "a", "expected": {}}),
            json.dumps({"id": "t2", "input": "b", "expected": {"keywords": ["x"]}}),
        ]
        f.write_text("\n".join(lines), encoding="utf-8")
        ds = GoldenDataset.from_jsonl(str(f))
        assert len(ds) == 2
        assert ds[1].id == "t2"

    def test_empty_file_returns_empty(self, tmp_path):
        f = tmp_path / "empty.jsonl"
        f.write_text("")
        assert len(GoldenDataset.from_jsonl(str(f))) == 0

    def test_invalid_line_skipped(self, tmp_path):
        f = tmp_path / "bad.jsonl"
        f.write_text("not json\n" + json.dumps({"id": "x", "input": "", "expected": {}}))
        ds = GoldenDataset.from_jsonl(str(f))
        assert len(ds) == 1

    def test_missing_fields_skipped(self, tmp_path):
        f = tmp_path / "incomplete.jsonl"
        f.write_text(json.dumps({"id": "x"}) + "\n" + json.dumps({"id": "y", "input": "q", "expected": {}}))
        ds = GoldenDataset.from_jsonl(str(f))
        assert len(ds) == 1
        assert ds[0].id == "y"

    def test_iterable(self, tmp_path):
        f = tmp_path / "golden.jsonl"
        f.write_text("\n".join([
            json.dumps({"id": f"t{i}", "input": "", "expected": {}}) for i in range(3)
        ]))
        ds = GoldenDataset.from_jsonl(str(f))
        ids = [c.id for c in ds]
        assert ids == ["t0", "t1", "t2"]

    def test_from_directory(self, tmp_path):
        (tmp_path / "a.jsonl").write_text(json.dumps({"id": "a1", "input": "", "expected": {}}))
        (tmp_path / "b.jsonl").write_text(json.dumps({"id": "b1", "input": "", "expected": {}}))
        ds = GoldenDataset.from_directory(str(tmp_path))
        assert len(ds) == 2

    def test_repr(self, tmp_path):
        f = tmp_path / "golden.jsonl"
        f.write_text(json.dumps({"id": "t1", "input": "", "expected": {}}))
        ds = GoldenDataset.from_jsonl(str(f))
        assert "1 cases" in repr(ds)
