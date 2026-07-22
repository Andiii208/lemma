"""信赖阈值系统单元测试"""
import pytest
from lemma.engine.trust import TrustManager, TrustLevel


class TestTrustManager:
    @pytest.fixture
    def trust_file(self, tmp_path):
        return str(tmp_path / "trust.json")

    def test_default_level(self, trust_file):
        tm = TrustManager(trust_file)
        assert tm.get_trust_level() == TrustLevel.NORMAL

    def test_should_confirm_default(self, trust_file):
        tm = TrustManager(trust_file)
        assert tm.should_confirm("analysis") is True

    def test_five_accepts_reaches_loose(self, trust_file):
        tm = TrustManager(trust_file)
        for _ in range(5):
            tm.record("analysis", accepted=True)
        assert tm.get_trust_level() == TrustLevel.LOOSE

    def test_loose_skips_confirm(self, trust_file):
        tm = TrustManager(trust_file)
        for _ in range(5):
            tm.record("analysis", accepted=True)
        assert tm.should_confirm("analysis") is False

    def test_three_accepts_reaches_relaxed(self, trust_file):
        tm = TrustManager(trust_file)
        for _ in range(3):
            tm.record("analysis", accepted=True)
        assert tm.get_trust_level() == TrustLevel.RELAXED

    def test_two_rejects_tighten(self, trust_file):
        tm = TrustManager(trust_file)
        tm.record("analysis", accepted=False)
        tm.record("analysis", accepted=False)
        assert tm.get_trust_level() == TrustLevel.TIGHTEN
        assert tm.should_confirm("analysis") is True

    def test_corrected_later_resets(self, trust_file):
        tm = TrustManager(trust_file)
        for _ in range(5):
            tm.record("analysis", accepted=True)
        # 即使之前都接受，一次 corrected_later 就重置
        tm.record("analysis", accepted=True, corrected_later=True)
        assert tm.get_trust_level() == TrustLevel.RESET
        assert tm.should_confirm("analysis") is True

    def test_persistence(self, trust_file):
        tm1 = TrustManager(trust_file)
        tm1.record("analysis", accepted=True)
        tm1.record("analysis", accepted=True)
        tm1.record("derivation", accepted=False)
        tm1.record("derivation", accepted=False)  # 2 次拒绝 → TIGHTEN

        tm2 = TrustManager(trust_file)
        assert len(tm2.records) == 4
        assert tm2.get_trust_level() == TrustLevel.TIGHTEN

    def test_reset(self, trust_file):
        tm = TrustManager(trust_file)
        tm.record("analysis", accepted=True)
        tm.record("analysis", accepted=True)
        tm.reset()
        assert len(tm.records) == 0
        assert tm.get_trust_level() == TrustLevel.NORMAL

    def test_max_history(self, trust_file):
        tm = TrustManager(trust_file)
        for i in range(30):
            tm.record(f"phase_{i}", accepted=True)
        # 只保留最近 20 条
        assert len(tm.records) <= 20

    def test_stats(self, trust_file):
        tm = TrustManager(trust_file)
        tm.record("a", accepted=True)
        tm.record("b", accepted=False)
        stats = tm.stats
        assert stats["total_records"] == 2
        assert stats["accepted"] == 1
        assert stats["rejected"] == 1

    def test_corrected_later_in_stats(self, trust_file):
        tm = TrustManager(trust_file)
        tm.record("a", accepted=True, corrected_later=True)
        stats = tm.stats
        assert stats["corrected_later"] == 1
