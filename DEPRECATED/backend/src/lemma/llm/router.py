"""多模型路由器 — 按任务类型选择最优模型"""

from __future__ import annotations

import logging
from enum import Enum

import yaml

from .backend import LLMBackend, LLMConfig

logger = logging.getLogger("ultramath.router")


class TaskType(Enum):
    """任务类型"""

    MATH_REASONING = "math_reasoning"
    CODE_GENERATION = "code_generation"
    PAPER_WRITING = "paper_writing"
    REVIEW = "review"
    ONTOLOGY = "ontology"
    QUICK_CHECK = "quick_check"


class ModelRouter:
    """模型路由器"""

    def __init__(self, backends: dict[str, LLMBackend], routing: dict[TaskType, str]):
        self.backends = backends
        self.routing = routing

    def get_backend(self, task_type: TaskType) -> LLMBackend:
        """根据任务类型获取对应的后端"""
        model_name = self.routing.get(task_type, "default")
        return self.backends.get(model_name, self.backends["default"])

    def get_default_backend(self) -> LLMBackend:
        """获取默认后端"""
        return self.backends["default"]

    @classmethod
    def from_config(cls, config_path: str) -> ModelRouter:
        """从配置文件创建路由器"""
        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        backends = {}
        for name, backend_cfg in cfg.get("backends", {}).items():
            backends[name] = LLMBackend(LLMConfig(**backend_cfg))

        routing = {}
        for task_str, model_name in cfg.get("routing", {}).items():
            try:
                routing[TaskType(task_str)] = model_name
            except ValueError:
                logger.warning(f"Unknown task type in routing config: {task_str}")

        if "default" not in backends:
            first_key = next(iter(backends))
            backends["default"] = backends[first_key]

        return cls(backends=backends, routing=routing)

    @classmethod
    def from_single_config(cls, config: LLMConfig) -> ModelRouter:
        """从单一配置创建路由器"""
        backend = LLMBackend(config)
        backends = {"default": backend}
        routing = {task: "default" for task in TaskType}
        return cls(backends=backends, routing=routing)
