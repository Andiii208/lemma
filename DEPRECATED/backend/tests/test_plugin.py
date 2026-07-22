"""插件系统测试"""

import pytest
from pathlib import Path
from lemma.tools.plugin import discover_plugins, PluginInfo


class TestPluginDiscovery:
    def test_discover_empty_dir(self, tmp_path):
        plugins = discover_plugins(str(tmp_path))
        assert len(plugins) == 0

    def test_discover_with_valid_plugin(self, tmp_path):
        # 创建模拟插件
        plugin_dir = tmp_path / "my_plugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.yaml").write_text(
            "name: my_plugin\ndescription: A test plugin\nversion: 1.0.0",
            encoding="utf-8",
        )
        (plugin_dir / "tool.py").write_text(
            "def create_tool(work_dir): return None",
            encoding="utf-8",
        )

        plugins = discover_plugins(str(tmp_path))
        assert len(plugins) == 1
        assert plugins[0].name == "my_plugin"
        assert plugins[0].description == "A test plugin"

    def test_discover_skips_incomplete(self, tmp_path):
        # 只有 yaml 没有 tool.py
        plugin_dir = tmp_path / "incomplete"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.yaml").write_text("name: incomplete", encoding="utf-8")

        plugins = discover_plugins(str(tmp_path))
        assert len(plugins) == 0

    def test_discover_nonexistent_dir(self):
        plugins = discover_plugins("/nonexistent/path")
        assert len(plugins) == 0
