"""长期记忆 — 基于向量检索的知识库"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

try:
    import chromadb
    from chromadb.config import Settings

    _HAS_CHROMA = True
except ImportError:
    _HAS_CHROMA = False


class LongTermMemory:
    """长期记忆 — ChromaDB 向量存储（降级为文件搜索）"""

    def __init__(self, persist_dir: str = "./data/chromadb"):
        self.persist_dir = Path(persist_dir)
        self._use_chroma = _HAS_CHROMA
        self._client = None
        self._collections: dict[str, Any] = {}
        self._file_store: dict[str, list[dict]] = {}  # 降级存储

        if _HAS_CHROMA:
            try:
                self.persist_dir.mkdir(parents=True, exist_ok=True)
                self._client = chromadb.PersistentClient(
                    path=str(self.persist_dir),
                    settings=Settings(anonymized_telemetry=False),
                )
            except Exception:
                self._use_chroma = False

    def get_or_create_collection(self, name: str):
        """获取或创建集合"""
        if self._use_chroma and self._client:
            if name not in self._collections:
                self._collections[name] = self._client.get_or_create_collection(name=name)
            return self._collections[name]
        return None

    def add_documents(
        self,
        collection_name: str,
        documents: list[str],
        metadatas: list[dict] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        """添加文档"""
        if ids is None:
            ids = [hashlib.md5(doc.encode()).hexdigest()[:16] for doc in documents]

        if self._use_chroma:
            try:
                collection = self.get_or_create_collection(collection_name)
                if collection:
                    collection.add(
                        documents=documents, metadatas=metadatas or [{}] * len(documents), ids=ids
                    )
                    return
            except Exception:
                pass

        # 降级到文件存储
        if collection_name not in self._file_store:
            self._file_store[collection_name] = []
        for i, doc in enumerate(documents):
            self._file_store[collection_name].append(
                {
                    "id": ids[i] if i < len(ids) else str(i),
                    "content": doc,
                    "metadata": metadatas[i] if metadatas and i < len(metadatas) else {},
                }
            )

    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
    ) -> list[dict]:
        """查询相关文档"""
        if self._use_chroma:
            try:
                collection = self.get_or_create_collection(collection_name)
                if collection and collection.count() > 0:
                    results = collection.query(
                        query_texts=[query_text], n_results=min(n_results, collection.count())
                    )
                    docs = []
                    for i, doc in enumerate(results["documents"][0]):
                        docs.append(
                            {
                                "content": doc,
                                "metadata": results["metadatas"][0][i]
                                if results["metadatas"]
                                else {},
                                "distance": results["distances"][0][i]
                                if results["distances"]
                                else 0,
                            }
                        )
                    return docs
            except Exception:
                pass

        # 降级：关键词搜索（支持中文）
        store = self._file_store.get(collection_name, [])
        if not store:
            return []

        query_lower = query_text.lower()
        # 按空格和标点分词，同时保留中文连续字符作为关键词
        import re

        keywords = re.findall(r"[\u4e00-\u9fff]+|[a-z0-9]+", query_lower)
        if not keywords:
            keywords = [query_lower]

        scored = []
        for item in store:
            content_lower = item["content"].lower()
            # 关键词匹配评分
            score = sum(content_lower.count(kw) for kw in keywords if len(kw) >= 2)
            if score > 0:
                scored.append({**item, "distance": 1.0 / (score + 1)})

        scored.sort(key=lambda x: x["distance"])
        # 如果没有匹配，返回前 n_results 个文档
        if not scored and store:
            return [{**item, "distance": 1.0} for item in store[:n_results]]
        return scored[:n_results]

    def load_from_directory(
        self,
        collection_name: str,
        dir_path: str,
        glob: str = "*.md",
    ) -> int:
        """从目录加载文档"""
        path = Path(dir_path)
        if not path.exists():
            return 0

        documents = []
        metadatas = []
        ids = []
        for i, f in enumerate(path.glob(glob)):
            try:
                content = f.read_text(encoding="utf-8")
                documents.append(content)
                metadatas.append({"source": str(f), "filename": f.name})
                ids.append(f"{collection_name}_{i}")
            except Exception:
                continue

        if documents:
            self.add_documents(collection_name, documents, metadatas, ids)
        return len(documents)

    @property
    def is_chroma_available(self) -> bool:
        return self._use_chroma
