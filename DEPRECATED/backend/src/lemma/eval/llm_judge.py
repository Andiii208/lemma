"""LLM-as-Judge — 使用 LLM 评分产出质量（带磁盘缓存防成本爆炸）"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .scorers import ScoreResult


def _cache_key(output: str, criteria: str) -> str:
    """生成缓存键"""
    content = f"{output[:2000]}||{criteria}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


class LLMJudge:
    """LLM 评分器 — 使用 LLM 对产出进行质量评分

    缓存策略：(output_hash, criteria_hash) → score，避免重复调用。
    """

    def __init__(self, cache_dir: str | None = None, model: str = "gpt-4o-mini"):
        self.model = model
        self._cache_dir = Path(cache_dir) if cache_dir else None
        self._memory_cache: dict[str, ScoreResult] = {}
        self._cache_hits = 0
        self._cache_misses = 0

        if self._cache_dir:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cached(self, key: str) -> ScoreResult | None:
        """从缓存获取（内存 → 磁盘）"""
        if key in self._memory_cache:
            self._cache_hits += 1
            return self._memory_cache[key]

        if self._cache_dir:
            cache_file = self._cache_dir / f"{key}.json"
            if cache_file.exists():
                try:
                    data = json.loads(cache_file.read_text(encoding="utf-8"))
                    result = ScoreResult(**data)
                    self._memory_cache[key] = result
                    self._cache_hits += 1
                    return result
                except (json.JSONDecodeError, TypeError):
                    pass

        return None

    def _set_cache(self, key: str, result: ScoreResult) -> None:
        """写入缓存（内存 + 磁盘）"""
        self._memory_cache[key] = result
        if self._cache_dir:
            cache_file = self._cache_dir / f"{key}.json"
            cache_file.write_text(
                json.dumps({
                    "name": result.name,
                    "score": result.score,
                    "passed": result.passed,
                    "detail": result.detail,
                }, ensure_ascii=False),
                encoding="utf-8",
            )

    async def score(self, output: str, criteria: str) -> ScoreResult:
        """使用 LLM 评分

        Args:
            output: 被评内容
            criteria: 评分标准（自然语言描述）

        Returns:
            ScoreResult
        """
        key = _cache_key(output, criteria)
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        self._cache_misses += 1

        prompt = f"""请根据以下标准对文本质量评分（0.0-1.0），并简要说明原因。

## 评分标准
{criteria}

## 被评文本
{output[:3000]}

请严格按 JSON 格式返回：
{{"score": 0.0-1.0, "reason": "简要原因"}}"""

        try:
            from ..llm.backend import LLMBackend, LLMConfig

            backend = LLMBackend(LLMConfig(
                model=self.model,
                api_key="",  # 由调用方注入
            ))
            response = await backend.generate([{"role": "user", "content": prompt}])

            # 解析 JSON 响应
            text = response.content.strip()
            # 提取 JSON 部分
            json_match = __import__("re").search(r'\{[^}]+\}', text)
            if json_match:
                data = json.loads(json_match.group())
                score = float(data.get("score", 0.5))
                reason = data.get("reason", "")
            else:
                score = 0.5
                reason = "无法解析 LLM 评分响应"

            result = ScoreResult("llm_judge", score, score >= 0.6, detail=reason)
        except Exception as e:
            result = ScoreResult("llm_judge", 0.0, False, detail=f"评分失败: {e}")

        self._set_cache(key, result)
        return result

    @property
    def cache_stats(self) -> dict:
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "memory_size": len(self._memory_cache),
        }
