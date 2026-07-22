"""固化模式单元测试"""
import json
import pytest
from lemma.engine.solidify import solidify_session


class TestSolidify:
    def test_solidify_creates_domain_structure(self, tmp_path):
        source = tmp_path / "workspace"
        source.mkdir()
        (source / "agent-context.json").write_text(json.dumps({
            "phases": {
                "0": {"phase_name": "初始化", "status": "completed"},
                "1": {"phase_name": "分析", "status": "completed"},
            },
        }), encoding="utf-8")

        domains_dir = tmp_path / "domains"
        domains_dir.mkdir()

        result = solidify_session(str(source), "my-domain", str(domains_dir))
        target = domains_dir / "my-domain"

        assert target.exists()
        assert (target / "domain.yaml").exists()
        assert (target / "prompts").exists()
        assert (target / "knowledge").exists()
        assert (target / "templates").exists()

    def test_solidify_existing_domain_raises(self, tmp_path):
        domains_dir = tmp_path / "domains"
        domains_dir.mkdir()
        existing = domains_dir / "existing"
        existing.mkdir()
        (existing / "domain.yaml").write_text("id: existing", encoding="utf-8")

        source = tmp_path / "workspace"
        source.mkdir()

        with pytest.raises(FileExistsError):
            solidify_session(str(source), "existing", str(domains_dir))

    def test_solidify_without_context_file(self, tmp_path):
        """没有 context 文件也应能正常创建结构"""
        source = tmp_path / "empty-workspace"
        source.mkdir()

        domains_dir = tmp_path / "domains"
        domains_dir.mkdir()

        result = solidify_session(str(source), "empty-domain", str(domains_dir))
        assert (domains_dir / "empty-domain").exists()
        assert (domains_dir / "empty-domain" / "domain.yaml").exists()

    def test_solidify_produces_valid_yaml(self, tmp_path):
        source = tmp_path / "workspace"
        source.mkdir()
        (source / "agent-context.json").write_text(json.dumps({
            "phases": {
                "0": {"phase_name": "搜索"},
                "1": {"phase_name": "筛选"},
                "2": {"phase_name": "综合"},
            },
        }), encoding="utf-8")

        domains_dir = tmp_path / "domains"
        domains_dir.mkdir()

        result = solidify_session(str(source), "lit-review", str(domains_dir))
        yaml_content = (domains_dir / "lit-review" / "domain.yaml").read_text(encoding="utf-8")
        assert "lit-review" in yaml_content
        assert "搜索" in yaml_content
        assert "筛选" in yaml_content
        assert "综合" in yaml_content
        assert "idle" in yaml_content
        assert "done" in yaml_content

    def test_solidify_copies_prompts(self, tmp_path):
        source = tmp_path / "workspace"
        source.mkdir()
        (source / "agent-context.json").write_text(json.dumps({"phases": {"0": {"phase_name": "A"}}}))

        prompts_dir = source / "agent_prompts"
        prompts_dir.mkdir()
        (prompts_dir / "agent_lead.md").write_text("You are lead.", encoding="utf-8")

        domains_dir = tmp_path / "domains"
        domains_dir.mkdir()

        result = solidify_session(str(source), "with-prompts", str(domains_dir))
        target_prompt = domains_dir / "with-prompts" / "prompts" / "agent_lead.md"
        assert target_prompt.exists()
        assert target_prompt.read_text() == "You are lead."
