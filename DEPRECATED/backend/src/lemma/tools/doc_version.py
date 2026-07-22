"""文档版本管理 — 基于内容哈希的版本树"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class DocVersion:
    """文档版本"""

    version_id: str = ""  # sha256[:12]
    doc_name: str = ""
    content_hash: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    message: str = ""
    size: int = 0


class DocumentVersionStore:
    """文档版本存储 — 每个文档维护一个版本链"""

    def __init__(self, store_dir: str):
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._versions_dir = self.store_dir / ".versions"
        self._versions_dir.mkdir(exist_ok=True)

    def _content_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]

    def _doc_dir(self, doc_name: str) -> Path:
        d = self._versions_dir / doc_name.replace("/", "_").replace("\\", "_")
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _history_file(self, doc_name: str) -> Path:
        return self._doc_dir(doc_name) / "history.jsonl"

    def save_version(self, doc_name: str, content: str, message: str = "") -> DocVersion:
        """保存文档新版本"""
        content_hash = self._content_hash(content)
        doc_dir = self._doc_dir(doc_name)

        # 保存内容文件
        content_file = doc_dir / f"{content_hash}.txt"
        content_file.write_text(content, encoding="utf-8")

        # 创建版本记录
        version = DocVersion(
            version_id=content_hash,
            doc_name=doc_name,
            content_hash=content_hash,
            message=message or f"保存于 {datetime.now().strftime('%H:%M:%S')}",
            size=len(content),
        )

        # 追加到历史
        history_file = self._history_file(doc_name)
        with open(history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(version), ensure_ascii=False) + "\n")

        return version

    def get_history(self, doc_name: str) -> list[DocVersion]:
        """获取文档版本历史"""
        history_file = self._history_file(doc_name)
        if not history_file.exists():
            return []

        versions: list[DocVersion] = []
        for line in history_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                versions.append(DocVersion(**data))
            except (json.JSONDecodeError, TypeError):
                continue
        return versions

    def get_version_content(self, doc_name: str, version_id: str) -> str | None:
        """获取指定版本的文档内容"""
        content_file = self._doc_dir(doc_name) / f"{version_id}.txt"
        if content_file.exists():
            return content_file.read_text(encoding="utf-8")
        return None

    def diff(self, doc_name: str, version_a: str, version_b: str) -> dict:
        """对比两个版本的差异"""
        content_a = self.get_version_content(doc_name, version_a) or ""
        content_b = self.get_version_content(doc_name, version_b) or ""

        lines_a = content_a.splitlines()
        lines_b = content_b.splitlines()

        added = [l for l in lines_b if l not in lines_a]
        removed = [l for l in lines_a if l not in lines_b]

        return {
            "version_a": version_a,
            "version_b": version_b,
            "lines_added": len(added),
            "lines_removed": len(removed),
            "added_preview": added[:20],
            "removed_preview": removed[:20],
            "size_a": len(content_a),
            "size_b": len(content_b),
        }

    def list_documents(self) -> list[str]:
        """列出所有有版本历史的文档"""
        docs = []
        for d in self._versions_dir.iterdir():
            if d.is_dir() and (d / "history.jsonl").exists():
                docs.append(d.name)
        return sorted(docs)
