"""领域配置加载测试"""
import pytest
from pathlib import Path
from lemma.engine.domain import DomainProfile, PhaseConfig, RoleConfig


class TestPhaseConfig:
    def test_minimal_phase(self):
        p = PhaseConfig(id="test", name="测试", order=0)
        assert p.id == "test"
        assert p.name == "测试"
        assert p.order == 0
        assert p.progress == 0.0

    def test_phase_with_transition(self):
        p = PhaseConfig(id="a", name="A", order=0, progress=10,
                         transition={"pass": "b", "fail": "a"})
        assert p.transition["pass"] == "b"


class TestRoleConfig:
    def test_minimal_role(self):
        r = RoleConfig(id="lead", name="领队")
        assert r.id == "lead"
        assert r.name == "领队"
        assert r.temperature == 0.5


class TestDomainProfile:
    def test_load_from_directory(self, tmp_path):
        domain_dir = tmp_path / "test-domain"
        domain_dir.mkdir()
        (domain_dir / "domain.yaml").write_text("""
id: test
name: 测试领域
phases:
  - id: idle
    name: 空闲
    order: -1
    progress: 0
    transition: {pass: init}
  - id: init
    name: 初始化
    order: 0
    progress: 10
    transition: {pass: done}
  - id: done
    name: 完成
    order: 1
    progress: 100
roles:
  - id: lead
    name: 领队
    temperature: 0.5
    tools: []
""", encoding="utf-8")

        profile = DomainProfile.from_directory(str(domain_dir))
        assert profile.id == "test"
        assert profile.name == "测试领域"
        assert len(profile.phases) == 3
        assert len(profile.roles) == 1

    def test_get_transition(self, tmp_path):
        domain_dir = tmp_path / "test-transition"
        domain_dir.mkdir()
        (domain_dir / "domain.yaml").write_text("""
id: test
name: 测试
phases:
  - id: a
    name: A
    order: 0
    progress: 0
    transition: {pass: b, fail: a}
  - id: b
    name: B
    order: 1
    progress: 100
roles:
  - id: lead
    name: Lead
""", encoding="utf-8")

        profile = DomainProfile.from_directory(str(domain_dir))
        assert profile.get_transition("a", success=True) == "b"
        assert profile.get_transition("a", success=False) == "a"
        assert profile.get_transition("nonexistent", success=True) == "nonexistent"

    def test_get_phase_ids_sorted(self, tmp_path):
        domain_dir = tmp_path / "test-sorted"
        domain_dir.mkdir()
        (domain_dir / "domain.yaml").write_text("""
id: test
name: 测试
phases:
  - id: c
    name: C
    order: 2
  - id: a
    name: A
    order: 0
  - id: b
    name: B
    order: 1
roles:
  - id: lead
    name: Lead
""", encoding="utf-8")

        profile = DomainProfile.from_directory(str(domain_dir))
        assert profile.get_phase_ids() == ["a", "b", "c"]

    def test_auto_loads_prompts_from_md(self, tmp_path):
        domain_dir = tmp_path / "test-prompts"
        domain_dir.mkdir()
        prompts_dir = domain_dir / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "agent_lead.md").write_text("You are a helpful assistant.", encoding="utf-8")
        (domain_dir / "domain.yaml").write_text("""
id: test
name: 测试
phases:
  - id: idle
    name: 空闲
    order: -1
roles:
  - id: lead
    name: Lead
""", encoding="utf-8")

        profile = DomainProfile.from_directory(str(domain_dir))
        role = profile.get_role_by_id("lead")
        assert role is not None
        assert role.system_prompt == "You are a helpful assistant."

    def test_auto_loads_phase_handlers(self, tmp_path):
        domain_dir = tmp_path / "test-handlers"
        domain_dir.mkdir()
        prompts_dir = domain_dir / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "phase_init.md").write_text("执行初始化阶段。", encoding="utf-8")
        (domain_dir / "domain.yaml").write_text("""
id: test
name: 测试
phases:
  - id: init
    name: 初始化
    order: 0
    progress: 50
    transition: {pass: done}
  - id: done
    name: 完成
    order: 1
    progress: 100
roles:
  - id: lead
    name: Lead
""", encoding="utf-8")

        profile = DomainProfile.from_directory(str(domain_dir))
        assert "init" in profile.phase_handlers
        assert profile.phase_handlers["init"] == "执行初始化阶段。"

    def test_list_domains(self, tmp_path):
        domains_dir = tmp_path / "domains"
        domains_dir.mkdir()
        d1 = domains_dir / "math"
        d1.mkdir()
        (d1 / "domain.yaml").write_text("id: math\nname: 数学建模\nphases: []\nroles: []")
        d2 = domains_dir / "paper"
        d2.mkdir()
        (d2 / "domain.yaml").write_text("id: paper\nname: 论文写作\nphases: []\nroles: []")

        domains = DomainProfile.list_domains(str(domains_dir))
        assert len(domains) == 2
        ids = [d["id"] for d in domains]
        assert "math" in ids
        assert "paper" in ids

    def test_get_phase_by_id_nonexistent(self, tmp_path):
        domain_dir = tmp_path / "test-nonexistent"
        domain_dir.mkdir()
        (domain_dir / "domain.yaml").write_text("""
id: test
name: 测试
phases:
  - id: a
    name: A
    order: 0
roles:
  - id: lead
    name: Lead
""", encoding="utf-8")

        profile = DomainProfile.from_directory(str(domain_dir))
        assert profile.get_phase_by_id("nonexistent") is None
        assert profile.get_role_by_id("nonexistent") is None

    def test_missing_domain_yaml_raises(self):
        with pytest.raises(FileNotFoundError):
            DomainProfile.from_directory("/nonexistent/path")
