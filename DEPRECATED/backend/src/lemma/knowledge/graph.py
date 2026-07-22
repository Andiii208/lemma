"""知识图谱 — 实体-关系-属性三元组存储

从 knowledge/*.md 中抽取结构化知识，支持图谱查询。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Entity:
    """实体"""

    entity_id: str = ""
    name: str = ""
    entity_type: str = ""  # concept | method | model | tool | domain
    properties: dict = field(default_factory=dict)
    source: str = ""


@dataclass
class Relation:
    """关系"""

    source_id: str = ""
    target_id: str = ""
    relation_type: str = ""  # uses | requires | improves | similar_to | part_of
    weight: float = 1.0


class KnowledgeGraph:
    """知识图谱"""

    def __init__(self, persist_path: str | None = None):
        self.entities: dict[str, Entity] = {}
        self.relations: list[Relation] = []
        self._persist_path = Path(persist_path) if persist_path else None

        if self._persist_path and self._persist_path.exists():
            self._load()

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.entity_id] = entity

    def add_relation(self, relation: Relation) -> None:
        self.relations.append(relation)

    def find_entity(self, name: str) -> Entity | None:
        """按名称查找实体"""
        for e in self.entities.values():
            if e.name == name or name in e.name:
                return e
        return None

    def get_related(self, entity_id: str, relation_type: str | None = None) -> list[tuple[Entity, Relation]]:
        """获取与某实体相关的实体"""
        results = []
        for rel in self.relations:
            if rel.source_id == entity_id:
                if relation_type and rel.relation_type != relation_type:
                    continue
                target = self.entities.get(rel.target_id)
                if target:
                    results.append((target, rel))
        return results

    def query(self, keyword: str) -> list[Entity]:
        """关键词搜索实体"""
        keyword_lower = keyword.lower()
        return [
            e for e in self.entities.values()
            if keyword_lower in e.name.lower() or keyword_lower in e.entity_type.lower()
        ]

    def load_from_markdown(self, file_path: str) -> int:
        """从 Markdown 文件抽取知识（简单启发式）"""
        content = Path(file_path).read_text(encoding="utf-8")
        count = 0

        # 抽取标题作为概念实体
        for match in re.finditer(r"^#{1,3}\s+(.+)$", content, re.MULTILINE):
            title = match.group(1).strip()
            entity_id = f"concept_{hash(title) % 10000:04d}"
            if entity_id not in self.entities:
                self.add_entity(Entity(
                    entity_id=entity_id,
                    name=title,
                    entity_type="concept",
                    source=file_path,
                ))
                count += 1

        # 抽取列表项中的方法/模型
        for match in re.finditer(r"^[-*]\s+\*\*(.+?)\*\*[:\s]*(.*)$", content, re.MULTILINE):
            name = match.group(1).strip()
            desc = match.group(2).strip()
            entity_id = f"method_{hash(name) % 10000:04d}"
            if entity_id not in self.entities:
                self.add_entity(Entity(
                    entity_id=entity_id,
                    name=name,
                    entity_type="method",
                    properties={"description": desc},
                    source=file_path,
                ))
                count += 1

        return count

    def save(self, path: str | None = None) -> None:
        """保存图谱到 JSON"""
        save_path = Path(path) if path else self._persist_path
        if not save_path:
            return

        data = {
            "entities": [
                {
                    "entity_id": e.entity_id,
                    "name": e.name,
                    "entity_type": e.entity_type,
                    "properties": e.properties,
                    "source": e.source,
                }
                for e in self.entities.values()
            ],
            "relations": [
                {
                    "source_id": r.source_id,
                    "target_id": r.target_id,
                    "relation_type": r.relation_type,
                    "weight": r.weight,
                }
                for r in self.relations
            ],
        }
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load(self) -> None:
        """从 JSON 加载图谱"""
        if not self._persist_path or not self._persist_path.exists():
            return

        data = json.loads(self._persist_path.read_text(encoding="utf-8"))
        for e_data in data.get("entities", []):
            self.add_entity(Entity(**e_data))
        for r_data in data.get("relations", []):
            self.add_relation(Relation(**r_data))

    @property
    def stats(self) -> dict:
        return {
            "entities": len(self.entities),
            "relations": len(self.relations),
            "types": list(set(e.entity_type for e in self.entities.values())),
        }
