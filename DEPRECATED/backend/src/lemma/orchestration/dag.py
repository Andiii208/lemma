"""DAG 规划器 — 动态任务图的构建与调度

替代线性流水线，支持并行执行、节点级重试、断点续跑。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class DAGNode:
    """DAG 任务节点"""

    node_id: str = field(default_factory=lambda: uuid4().hex[:8])
    name: str = ""
    phase_id: str = ""
    status: NodeStatus = NodeStatus.PENDING
    dependencies: list[str] = field(default_factory=list)  # node_ids
    max_retries: int = 3
    retry_count: int = 0
    result: str = ""
    error: str = ""

    @property
    def is_ready(self) -> bool:
        """是否满足执行条件（所有依赖已完成）"""
        return self.status == NodeStatus.PENDING and not self.dependencies


class DAG:
    """有向无环图 — 任务调度"""

    def __init__(self):
        self.nodes: dict[str, DAGNode] = {}

    def add_node(self, node: DAGNode) -> None:
        self.nodes[node.node_id] = node

    def create_node(self, name: str, phase_id: str = "", dependencies: list[str] | None = None) -> DAGNode:
        node = DAGNode(name=name, phase_id=phase_id, dependencies=dependencies or [])
        self.add_node(node)
        return node

    def get_ready_nodes(self) -> list[DAGNode]:
        """获取所有可执行的节点（依赖已满足）"""
        ready = []
        for node in self.nodes.values():
            if node.status != NodeStatus.PENDING:
                continue
            deps_met = all(
                self.nodes[dep].status == NodeStatus.COMPLETED
                for dep in node.dependencies
                if dep in self.nodes
            )
            if deps_met:
                ready.append(node)
        return ready

    def mark_completed(self, node_id: str, result: str = "") -> None:
        node = self.nodes.get(node_id)
        if node:
            node.status = NodeStatus.COMPLETED
            node.result = result

    def mark_failed(self, node_id: str, error: str = "") -> None:
        node = self.nodes.get(node_id)
        if node:
            node.retry_count += 1
            if node.retry_count >= node.max_retries:
                node.status = NodeStatus.FAILED
                node.error = error
            # 否则保持 PENDING 状态等待重试

    def skip_node(self, node_id: str) -> None:
        node = self.nodes.get(node_id)
        if node:
            node.status = NodeStatus.SKIPPED

    @property
    def is_complete(self) -> bool:
        return all(
            n.status in (NodeStatus.COMPLETED, NodeStatus.FAILED, NodeStatus.SKIPPED)
            for n in self.nodes.values()
        )

    @property
    def progress(self) -> float:
        if not self.nodes:
            return 0.0
        done = sum(1 for n in self.nodes.values() if n.status in (NodeStatus.COMPLETED, NodeStatus.SKIPPED))
        return done / len(self.nodes)

    @property
    def failed_nodes(self) -> list[DAGNode]:
        return [n for n in self.nodes.values() if n.status == NodeStatus.FAILED]

    def to_dict(self) -> dict:
        return {
            "nodes": [
                {
                    "node_id": n.node_id,
                    "name": n.name,
                    "phase_id": n.phase_id,
                    "status": n.status.value,
                    "dependencies": n.dependencies,
                    "retry_count": n.retry_count,
                }
                for n in self.nodes.values()
            ],
            "progress": self.progress,
            "is_complete": self.is_complete,
        }

    def topological_order(self) -> list[str]:
        """返回拓扑排序（用于串行执行）"""
        visited: set[str] = set()
        order: list[str] = []

        def visit(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)
            node = self.nodes.get(node_id)
            if node:
                for dep in node.dependencies:
                    visit(dep)
                order.append(node_id)

        for nid in self.nodes:
            visit(nid)
        return order


async def execute_dag(
    dag: DAG,
    executor: "callable",
    max_parallel: int = 3,
) -> DAG:
    """并行执行 DAG

    Args:
        dag: DAG 实例
        executor: async def(node: DAGNode) -> str  执行函数
        max_parallel: 最大并行数
    """
    semaphore = asyncio.Semaphore(max_parallel)

    async def run_node(node: DAGNode):
        async with semaphore:
            node.status = NodeStatus.RUNNING
            try:
                result = await executor(node)
                dag.mark_completed(node.node_id, result)
            except Exception as e:
                dag.mark_failed(node.node_id, str(e))

    while not dag.is_complete:
        ready = dag.get_ready_nodes()
        if not ready:
            # 检查是否有正在运行的
            running = [n for n in dag.nodes.values() if n.status == NodeStatus.RUNNING]
            if not running:
                break  # 死锁或全部失败
            await asyncio.sleep(0.1)
            continue

        tasks = [asyncio.create_task(run_node(node)) for node in ready]
        await asyncio.gather(*tasks, return_exceptions=True)

    return dag
