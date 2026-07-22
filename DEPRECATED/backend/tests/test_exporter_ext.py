"""扩展导出器测试（JSON + HTML）"""

import json
import pytest
from lemma.tools.exporter import DocumentExporter


class TestExporterExtended:
    def test_export_json(self, tmp_path):
        exporter = DocumentExporter(str(tmp_path))
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        path = exporter.export_json(messages)
        assert path.endswith(".json")
        data = json.loads(open(path, encoding="utf-8").read())
        assert len(data) == 2
        assert data[0]["role"] == "user"

    def test_export_html(self, tmp_path):
        exporter = DocumentExporter(str(tmp_path))
        messages = [{"role": "user", "content": "Test"}]
        path = exporter.export_html(messages, title="Test Export")
        assert path.endswith(".html")
        content = open(path, encoding="utf-8").read()
        assert "Test Export" in content
        assert "user-message" in content

    def test_export_markdown(self, tmp_path):
        exporter = DocumentExporter(str(tmp_path))
        messages = [{"role": "user", "content": "Hello"}]
        path = exporter.export_markdown(messages)
        assert path.endswith(".md")
