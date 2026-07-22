"""状态机单元测试 — 领域无关版本"""
import pytest
from lemma.engine.domain import DomainProfile, PhaseResult
from lemma.orchestration.state_machine import StateMachine


@pytest.fixture
def sample_profile(tmp_path):
    """创建最小测试领域"""
    domain_dir = tmp_path / "test-domain"
    domain_dir.mkdir()
    (domain_dir / "domain.yaml").write_text("""
id: test
name: 测试
phases:
  - id: idle
    name: 空闲
    order: -1
    progress: 0
    transition: {pass: init}
  - id: init
    name: 初始化
    order: 0
    progress: 5
    transition: {pass: analysis, fail: init}
  - id: analysis
    name: 分析
    order: 1
    progress: 30
    transition: {pass: done, fail: analysis}
  - id: done
    name: 完成
    order: 2
    progress: 100
roles:
  - id: lead
    name: Lead
""", encoding="utf-8")
    return DomainProfile.from_directory(str(domain_dir))


class TestStateMachine:
    def test_initial_state(self, sample_profile):
        sm = StateMachine(profile=sample_profile)
        assert sm.current_phase == "idle"
        assert sm.is_idle

    def test_start_transitions_to_init(self, sample_profile):
        sm = StateMachine(profile=sample_profile)
        sm.transition(PhaseResult(phase_id="idle", success=True))
        assert sm.current_phase == "init"

    def test_normal_phase_progression(self, sample_profile):
        sm = StateMachine(profile=sample_profile)
        sm.transition(PhaseResult(phase_id="idle", success=True))
        assert sm.current_phase == "init"
        sm.transition(PhaseResult(phase_id="init", success=True))
        assert sm.current_phase == "analysis"

    def test_failure_retry(self, sample_profile):
        sm = StateMachine(profile=sample_profile)
        sm.transition(PhaseResult(phase_id="idle", success=True))  # -> init
        sm.transition(PhaseResult(phase_id="init", success=True))  # -> analysis
        sm.transition(PhaseResult(phase_id="analysis", success=False))  # fail -> retry
        assert sm.current_phase == "analysis"

    def test_progress_percentage(self, sample_profile):
        sm = StateMachine(profile=sample_profile)
        assert sm.progress == 0
        sm.transition(PhaseResult(phase_id="idle", success=True))
        assert sm.progress == 5

    def test_to_dict_serialization(self, sample_profile):
        sm = StateMachine(profile=sample_profile)
        sm.transition(PhaseResult(phase_id="idle", success=True))
        data = sm.to_dict()
        assert "current_phase" in data
        assert "history" in data
        assert isinstance(data["history"], list)
        assert data["current_phase"] == "init"

    def test_skip_to_phase(self, sample_profile):
        sm = StateMachine(profile=sample_profile)
        sm.skip_to("analysis")
        assert sm.current_phase == "analysis"

    def test_is_done(self, sample_profile):
        sm = StateMachine(profile=sample_profile)
        assert not sm.is_done
        sm.skip_to("done")
        assert sm.is_done

    def test_phase_name(self, sample_profile):
        sm = StateMachine(profile=sample_profile)
        assert sm.phase_name == "空闲"
        sm.skip_to("analysis")
        assert sm.phase_name == "分析"

    def test_get_phase_result(self, sample_profile):
        sm = StateMachine(profile=sample_profile)
        result = PhaseResult(phase_id="analysis", success=True, summary="test")
        sm.transition(result)
        retrieved = sm.get_phase_result("analysis")
        assert retrieved is not None
        assert retrieved.summary == "test"

    def test_history_tracks_transitions(self, sample_profile):
        sm = StateMachine(profile=sample_profile)
        sm.transition(PhaseResult(phase_id="idle", success=True))
        sm.transition(PhaseResult(phase_id="init", success=True))
        assert len(sm.history) == 2
        assert sm.history[0]["from"] == "idle"
        assert sm.history[0]["to"] == "init"

    def test_to_dict_includes_domain_info(self, sample_profile):
        sm = StateMachine(profile=sample_profile)
        data = sm.to_dict()
        assert data["domain_id"] == "test"
        assert data["domain_name"] == "测试"
