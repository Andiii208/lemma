"""知识加载器 — 将知识文件加载到向量记忆"""

from __future__ import annotations

import contextlib
from pathlib import Path

from ..memory.long_term import LongTermMemory


class KnowledgeLoader:
    """知识加载器"""

    def __init__(self, data_dir: str, long_term: LongTermMemory):
        self.data_dir = Path(data_dir)
        self.long_term = long_term

    def load_all(self) -> dict[str, int]:
        """加载所有知识到向量库"""
        stats = {}

        loaders = [
            ("knowledge_models", "models", "*.md"),
            ("knowledge_references", "references", "*.md"),
            ("knowledge_reviews", "reviews", "*.md"),
        ]

        for collection, subdir, glob in loaders:
            dir_path = self.data_dir / subdir
            if dir_path.exists():
                count = self.long_term.load_from_directory(collection, str(dir_path), glob)
                stats[collection] = count
            else:
                stats[collection] = 0

        return stats

    def query_knowledge(self, query: str, n_results: int = 5) -> list[dict]:
        """查询知识库"""
        all_results = []
        for collection in ["knowledge_models", "knowledge_references", "knowledge_reviews"]:
            results = self.long_term.query(collection, query, n_results)
            for r in results:
                r["collection"] = collection
            all_results.extend(results)

        all_results.sort(key=lambda x: x.get("distance", 999))
        return all_results[:n_results]

    def get_model_library(self) -> dict[str, str]:
        """获取模型库目录"""
        models_dir = self.data_dir / "models"
        if not models_dir.exists():
            return {}
        result = {}
        for f in models_dir.glob("*.md"):
            with contextlib.suppress(Exception):
                result[f.stem] = f.read_text(encoding="utf-8")
        return result
