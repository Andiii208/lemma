"""DAG 规划器测试"""

import asyncio
import pytest
from lemma.orchestration.dag import DAG, DAGNode, NodeStatus, execute_dag


class TestDAG:
    def test_create_node(self):
        dag = DAG()
        n = dag.create_node("分析", phase_id="analysis")
        assert n.name == "分析"
        assert len(dag.nodes) == 1

    def test_ready_nodes_no_deps(self):
        dag = DAG()
        dag.create_node("a")
        dag.create_node("b")
        ready = dag.get_ready_nodes()
        assert len(ready) == 2

    def test_ready_nodes_with_deps(self):
        dag = DAG()
        n1 = dag.create_node("a")
        n2 = dag.create_node("b", dependencies=[n1.node_id])
        dag.create_node("c", dependencies=[n1.node_id])

        ready = dag.get_ready_nodes()
        assert len(ready) == 1
        assert ready[0].node_id == n1.node_id

        dag.mark_completed(n1.node_id)
        ready = dag.get_ready_nodes()
        assert len(ready) == 2

    def test_mark_completed(self):
        dag = DAG()
        n = dag.create_node("test")
        dag.mark_completed(n.node_id, "done")
        assert n.status == NodeStatus.COMPLETED
        assert n.result == "done"

    def test_mark_failed_retries(self):
        dag = DAG()
        n = dag.create_node("test")
        n.max_retries = 2

        dag.mark_failed(n.node_id, "err1")
        assert n.status == NodeStatus.PENDING  # 还能重试
        assert n.retry_count == 1

        dag.mark_failed(n.node_id, "err2")
        assert n.status == NodeStatus.FAILED  # 超过重试次数

    def test_skip_node(self):
        dag = DAG()
        n = dag.create_node("test")
        dag.skip_node(n.node_id)
        assert n.status == NodeStatus.SKIPPED

    def test_is_complete(self):
        dag = DAG()
        dag.create_node("a")
        dag.create_node("b")
        assert dag.is_complete is False

        for n in dag.nodes.values():
            dag.mark_completed(n.node_id)
        assert dag.is_complete is True

    def test_progress(self):
        dag = DAG()
        dag.create_node("a")
        dag.create_node("b")
        assert dag.progress == 0.0

        nodes = list(dag.nodes.values())
        dag.mark_completed(nodes[0].node_id)
        assert dag.progress == 0.5

    def test_topological_order(self):
        dag = DAG()
        n1 = dag.create_node("a")
        n2 = dag.create_node("b", dependencies=[n1.node_id])
        n3 = dag.create_node("c", dependencies=[n2.node_id])

        order = dag.topological_order()
        assert order.index(n1.node_id) < order.index(n2.node_id)
        assert order.index(n2.node_id) < order.index(n3.node_id)

    def test_to_dict(self):
        dag = DAG()
        dag.create_node("test", phase_id="analysis")
        d = dag.to_dict()
        assert len(d["nodes"]) == 1
        assert d["nodes"][0]["name"] == "test"

    @pytest.mark.asyncio
    async def test_execute_dag(self):
        dag = DAG()
        n1 = dag.create_node("step1")
        n2 = dag.create_node("step2", dependencies=[n1.node_id])
        n3 = dag.create_node("step3", dependencies=[n2.node_id])

        execution_order = []

        async def executor(node: DAGNode) -> str:
            execution_order.append(node.name)
            return f"done: {node.name}"

        await execute_dag(dag, executor, max_parallel=1)
        assert dag.is_complete
        assert execution_order == ["step1", "step2", "step3"]

    @pytest.mark.asyncio
    async def test_execute_dag_parallel(self):
        dag = DAG()
        dag.create_node("a")
        dag.create_node("b")
        dag.create_node("c")

        async def executor(node: DAGNode) -> str:
            return "ok"

        await execute_dag(dag, executor, max_parallel=3)
        assert dag.is_complete
