"""文档版本管理测试"""

import pytest
from lemma.tools.doc_version import DocumentVersionStore


class TestDocumentVersionStore:
    def test_save_and_get_history(self, tmp_path):
        store = DocumentVersionStore(str(tmp_path))
        v1 = store.save_version("paper.md", "# Title\n\nContent v1", "初始版本")
        v2 = store.save_version("paper.md", "# Title\n\nContent v2", "修改内容")

        history = store.get_history("paper.md")
        assert len(history) == 2
        assert history[0].message == "初始版本"
        assert history[1].message == "修改内容"

    def test_get_version_content(self, tmp_path):
        store = DocumentVersionStore(str(tmp_path))
        v = store.save_version("doc.md", "Hello World")

        content = store.get_version_content("doc.md", v.version_id)
        assert content == "Hello World"

    def test_get_nonexistent_version(self, tmp_path):
        store = DocumentVersionStore(str(tmp_path))
        assert store.get_version_content("doc.md", "nonexistent") is None

    def test_diff(self, tmp_path):
        store = DocumentVersionStore(str(tmp_path))
        v1 = store.save_version("doc.md", "line1\nline2\nline3")
        v2 = store.save_version("doc.md", "line1\nline2 modified\nline3\nline4")

        diff = store.diff("doc.md", v1.version_id, v2.version_id)
        assert diff["lines_added"] > 0
        assert diff["size_a"] != diff["size_b"]

    def test_dedup_same_content(self, tmp_path):
        store = DocumentVersionStore(str(tmp_path))
        store.save_version("doc.md", "same content")
        store.save_version("doc.md", "same content")

        history = store.get_history("doc.md")
        assert len(history) == 2  # 两次都记录
        # 但内容文件只有一份
        assert history[0].version_id == history[1].version_id

    def test_list_documents(self, tmp_path):
        store = DocumentVersionStore(str(tmp_path))
        store.save_version("a.md", "content a")
        store.save_version("b.md", "content b")

        docs = store.list_documents()
        assert "a.md" in docs
        assert "b.md" in docs

    def test_empty_history(self, tmp_path):
        store = DocumentVersionStore(str(tmp_path))
        assert store.get_history("nonexistent.md") == []
