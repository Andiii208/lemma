"""级联模型路由器 — 先用便宜模型，不满意再升级"""
from __future__ import annotations

import json
import logging
from typing import Any

from .backend import LLMBackend, LLMConfig
from .router import ModelRouter

logger = logging.getLogger(__name__)


class CascadeRouter(ModelRouter):
    """级联路由器 — 多模型逐级升级"""

    def __init__(self, stages: list[dict[str, Any]]):
        """
        stages: [{"model": "gpt-4o-mini", "quality_threshold": 0.7}, ...]
        """
        self.stages = stages
        self._backends: dict[str, LLMBackend] = {}

    @property
    def backends(self) -> dict[str, LLMBackend]:
        """兼容 ModelRouter 接口"""
        return self._backends

    def _get_backend_for_model(self, model: str) -> LLMBackend:
        if model not in self._backends:
            config = LLMConfig(model=model)
            self._backends[model] = LLMBackend(config)
        return self._backends[model]

    async def generate_with_fallback(
        self, messages: list[dict], tools: list[dict] | None = None,
        use_llm_judge: bool = False,
    ):
        """级联生成：从便宜模型开始，质量不达标则升级

        Args:
            messages: 对话消息列表
            tools: 可用的工具列表（可选）
            use_llm_judge: 是否使用 LLM Judge 评估质量（默认 False 使用启发式）
        """
        last_response = None
        for stage in self.stages:
            model = stage["model"]
            threshold = stage.get("quality_threshold", 0.7)

            backend = self._get_backend_for_model(model)
            response = await backend.generate(messages, tools=tools)

            if use_llm_judge:
                # 使用最便宜模型做 judge（cost 极低）
                judge_backend = self._get_backend_for_model(self.stages[0]["model"])
                quality = await self._llm_judge_quality(response.content, judge_backend)
            else:
                quality = self._estimate_quality(response.content)

            logger.info(f"Cascade: {model} quality={quality:.2f} (threshold={threshold})")

            if quality >= threshold:
                return response

            last_response = response
            logger.info(f"Cascade: {model} quality insufficient, upgrading...")

        return last_response

    @staticmethod
    async def _llm_judge_quality(text: str, backend: LLMBackend | None = None) -> float:
        """使用轻量 LLM 评判响应质量（比启发式更准确）

        对文本进行五维度评分（逻辑性/完整性/清晰度/实用性/创新性），
        每个维度 0-2 分，归一化到 0-1。
        如果 LLM 调用失败，回退到启发式评分。
        """
        if not backend:
            return CascadeRouter._estimate_quality(text)

        if not text or len(text) < 30:
            return 0.0

        judge_prompt = [
            {"role": "system", "content": "你是一个质量评估器。对以下回答进行五维度评分，每个维度 0-2 分。只输出 JSON。"},
            {"role": "user", "content": f"""评估以下回答质量：

回答（前 3000 字符）：
{text[:3000]}

按 JSON 格式输出：
{{"逻辑性": 0-2, "完整性": 0-2, "清晰度": 0-2, "实用性": 0-2, "创新性": 0-2}}"""},
        ]
        try:
            resp = await backend.generate(judge_prompt)
            # 从响应中提取 JSON 部分
            content = resp.content
            brace_start = content.find("{")
            brace_end = content.rfind("}") + 1
            if brace_start >= 0 and brace_end > brace_start:
                scores = json.loads(content[brace_start:brace_end])
                score_sum = sum(int(v) for v in scores.values() if isinstance(v, (int, float)))
                return min(1.0, score_sum / 10.0)
        except Exception as e:
            logger.debug(f"LLM Judge failed, falling back to heuristic: {e}")

        return CascadeRouter._estimate_quality(text)

    @staticmethod
    def _estimate_quality(text: str) -> float:
        """粗略评估响应质量（启发式，零成本）"""
        if not text or len(text) < 50:
            return 0.0

        score = min(1.0, len(text) / 2000) * 0.3  # 长度分
        if "##" in text or "###" in text:
            score += 0.2  # 有结构
        if "|" in text and "---" in text:
            score += 0.15  # 有表格
        if "```" in text:
            score += 0.15  # 有代码
        if any(c in text for c in "，。！？；："):
            score += 0.1  # 有中文内容
        return min(1.0, score)
