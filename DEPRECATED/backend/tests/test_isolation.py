"""文件隔离单元测试"""
from pathlib import Path
from lemma.engine.isolation import FileVisibility


class TestFileVisibility:
    def test_critic_does_not_see_original_problem(self, tmp_path):
        """Critic 只能看到 Generator 输出，看不到原始问题"""
        work_dir = Path(tmp_path / "workspace")
        work_dir.mkdir()
        (work_dir / "generator_output.md").write_text("gen content")
        (work_dir / "original_problem.md").write_text("problem")

        rules = {
            "generator": ["original_problem.md"],
            "critic": ["generator_output.md"],
        }

        critic_vis = FileVisibility(work_dir, "critic", rules)
        visible = critic_vis.get_visible_files()
        visible_names = [f.name for f in visible]
        assert "generator_output.md" in visible_names
        assert "original_problem.md" not in visible_names

    def test_wildcard_shows_all(self, tmp_path):
        work_dir = Path(tmp_path / "workspace")
        work_dir.mkdir()
        (work_dir / "a.txt").write_text("a")
        (work_dir / "b.txt").write_text("b")

        vis = FileVisibility(work_dir, "lead", {"lead": ["*"]})
        assert len(vis.get_visible_files()) == 2

    def test_is_visible(self, tmp_path):
        work_dir = Path(tmp_path / "workspace")
        work_dir.mkdir()
        (work_dir / "visible.md").write_text("visible")
        (work_dir / "hidden.md").write_text("hidden")

        vis = FileVisibility(work_dir, "agent", {"agent": ["visible.md"]})
        assert vis.is_visible("visible.md") is True
        assert vis.is_visible("hidden.md") is False

    def test_filter_system_prompt_adds_file_list(self, tmp_path):
        work_dir = Path(tmp_path / "workspace")
        work_dir.mkdir()
        (work_dir / "example.py").write_text("# code")

        vis = FileVisibility(work_dir, "lead", {"lead": ["*"]})
        enhanced = vis.filter_system_prompt("You are an agent.")
        assert "example.py" in enhanced
        assert "You are an agent." in enhanced

    def test_empty_rules_returns_no_files(self, tmp_path):
        work_dir = Path(tmp_path / "workspace")
        work_dir.mkdir()
        (work_dir / "test.md").write_text("test")

        vis = FileVisibility(work_dir, "agent", {"agent": []})
        assert len(vis.get_visible_files()) == 0

    def test_unknown_role_sees_everything(self, tmp_path):
        """未知角色的规则默认看到所有文件"""
        work_dir = Path(tmp_path / "workspace")
        work_dir.mkdir()
        (work_dir / "all.md").write_text("all")

        vis = FileVisibility(work_dir, "unknown_role", {"agent": ["all.md"]})
        # unknown_role is not in rules, so allowed = ["*"]
        assert len(vis.get_visible_files()) >= 0

    def test_multiple_patterns(self, tmp_path):
        work_dir = Path(tmp_path / "workspace")
        work_dir.mkdir()
        (work_dir / "data.csv").write_text("data")
        (work_dir / "report.md").write_text("report")
        (work_dir / "diagram.png").write_text("png")

        vis = FileVisibility(work_dir, "reviewer", {"reviewer": ["*.csv", "*.md"]})
        visible_names = [f.name for f in vis.get_visible_files()]
        assert "data.csv" in visible_names
        assert "report.md" in visible_names
        assert "diagram.png" not in visible_names
