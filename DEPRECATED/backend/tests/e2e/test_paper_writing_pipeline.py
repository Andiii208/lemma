"""端到端集成测试 — paper-writing 领域"""
import pytest
import os
from pathlib import Path

from lemma.engine.agent import AcademicAgent
from lemma.engine.domain import DomainProfile
from lemma.llm.router import ModelRouter
from lemma.llm.backend import LLMConfig
from lemma.tools.registry import ToolRegistry
from lemma.tools.file_manager import FileManagerTool


@pytest.fixture
def paper_domain():
    """加载 paper-writing 领域"""
    domain_dir = Path(__file__).parent.parent.parent.parent / "domains" / "paper-writing"
    return DomainProfile.from_directory(str(domain_dir))


@pytest.fixture
def agent(tmp_path, paper_domain):
    """创建 AcademicAgent 实例"""
    config = LLMConfig(api_key="test-key-not-real", model="gpt-4o")
    router = ModelRouter.from_single_config(config)
    tools = ToolRegistry()
    tools.register(FileManagerTool(str(tmp_path)))
    return AcademicAgent(
        work_dir=str(tmp_path),
        domain=paper_domain,
        llm_router=router,
        tool_registry=tools,
    )


class TestDomainLoading:
    """领域加载测试（不需要真实 LLM）"""

    def test_paper_domain_loads_all_handlers(self, paper_domain):
        assert 'outline' in paper_domain.phase_handlers
        assert 'drafting' in paper_domain.phase_handlers
        assert 'formatting' in paper_domain.phase_handlers
        assert 'review' in paper_domain.phase_handlers

    def test_paper_domain_has_four_roles(self, paper_domain):
        assert len(paper_domain.roles) == 4
        role_ids = [r.id for r in paper_domain.roles]
        assert 'lead' in role_ids
        assert 'writer' in role_ids
        assert 'reviewer' in role_ids
        assert 'formatter' in role_ids

    def test_paper_domain_role_prompts_loaded(self, paper_domain):
        """角色的 system_prompt 应从 prompts/ 目录自动加载"""
        lead = paper_domain.get_role_by_id('lead')
        assert lead is not None
        assert len(lead.system_prompt) > 0
        assert '主编' in lead.system_prompt or 'Lead' in lead.system_prompt

    def test_paper_domain_transitions(self, paper_domain):
        assert paper_domain.get_transition('outline', success=True) == 'drafting'
        assert paper_domain.get_transition('drafting', success=True) == 'formatting'
        assert paper_domain.get_transition('formatting', success=True) == 'review'
        assert paper_domain.get_transition('review', success=True) == 'done'
        assert paper_domain.get_transition('review', success=False) == 'drafting'


class TestAgentCreation:
    """Agent 创建测试"""

    def test_agent_has_correct_domain(self, agent):
        assert agent.domain.id == 'paper-writing'
        assert agent.domain.name == '学术论文写作'

    def test_agent_creates_directories(self, agent):
        """应根据 domain.directories 创建目录"""
        for dir_name in agent.domain.directories.values():
            assert (agent.work_dir / dir_name).exists()

    def test_agent_initial_role_is_first(self, agent):
        assert agent.current_role_id == agent.domain.roles[0].id

    def test_agent_status(self, agent):
        status = agent.get_status()
        assert 'state' in status
        assert 'current_role' in status
        assert 'current_role_name' in status
        assert status['current_role'] == 'lead'


class TestAllDomains:
    """所有领域基础测试"""

    @pytest.fixture(params=['math-modeling', 'paper-writing', 'lab-report', 'literature-review'])
    def domain(self, request):
        domain_dir = Path(__file__).parent.parent.parent.parent / "domains" / request.param
        return DomainProfile.from_directory(str(domain_dir)), request.param

    def test_domain_has_phases(self, domain):
        profile, name = domain
        assert len(profile.get_phase_ids()) >= 4  # 至少 idle + 2 phases + done

    def test_domain_has_roles(self, domain):
        profile, name = domain
        assert len(profile.roles) >= 1

    def test_domain_has_transitions(self, domain):
        profile, name = domain
        # 每个非 done 阶段都应有 transition
        for phase in profile.phases:
            if phase.id != 'done':
                assert len(phase.transition) > 0, f"Phase {phase.id} has no transitions"

    def test_domain_list_all(self):
        domains_dir = Path(__file__).parent.parent.parent.parent / "domains"
        domains = DomainProfile.list_domains(str(domains_dir))
        assert len(domains) >= 4
        ids = [d['id'] for d in domains]
        assert 'math-modeling' in ids
        assert 'paper-writing' in ids
        assert 'lab-report' in ids
        assert 'literature-review' in ids
