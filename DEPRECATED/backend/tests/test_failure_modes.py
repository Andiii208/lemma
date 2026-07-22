"""失败模式库测试"""

import pytest
from lemma.knowledge.failure_modes import FailureModeLibrary, FailureMode


class TestFailureModeLibrary:
    def test_add_and_search(self, tmp_path):
        lib = FailureModeLibrary(str(tmp_path / "failures.jsonl"))
        lib.add(FailureMode(
            mode_id="f1",
            category="sandbox_escape",
            description="getattr bypass",
            severity="critical",
        ))
        assert lib.count == 1

        results = lib.search(category="sandbox_escape")
        assert len(results) == 1

    def test_search_filter(self, tmp_path):
        lib = FailureModeLibrary(str(tmp_path / "failures.jsonl"))
        lib.add(FailureMode(mode_id="f1", category="a", severity="high"))
        lib.add(FailureMode(mode_id="f2", category="b", severity="low"))

        assert len(lib.search(severity="high")) == 1
        assert len(lib.search(category="a")) == 1

    def test_mark_fixed(self, tmp_path):
        lib = FailureModeLibrary(str(tmp_path / "failures.jsonl"))
        lib.add(FailureMode(mode_id="f1", category="test", fixed=False))
        assert lib.unfixed_count == 1

        lib.mark_fixed("f1")
        assert lib.unfixed_count == 0

        # 重新加载验证持久化
        lib2 = FailureModeLibrary(str(tmp_path / "failures.jsonl"))
        assert lib2.unfixed_count == 0

    def test_empty_library(self, tmp_path):
        lib = FailureModeLibrary(str(tmp_path / "empty.jsonl"))
        assert lib.count == 0
        assert lib.search() == []
