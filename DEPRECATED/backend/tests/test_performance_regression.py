"""性能回归测试 — 确保关键操作延迟不退化"""

import time
import pytest
from fastapi.testclient import TestClient

from lemma.api.server import app


@pytest.fixture
def client():
    return TestClient(app)


AUTH_HEADERS = {"X-API-Key": "dev-key-change-in-production"}


@pytest.mark.parametrize("endpoint,threshold", [
    ("/api/health", 0.200),
    ("/api/domains", 0.200),
    ("/api/roles", 0.200),
    ("/api/status", 0.200),
    ("/api/cost", 0.200),
    ("/api/performance", 0.200),
])
def test_endpoint_latency(client, endpoint, threshold):
    """端点延迟不应超过阈值"""
    # 预热（第一次调用通常较慢）
    client.get(endpoint, headers=AUTH_HEADERS)

    latencies = []
    for _ in range(3):
        start = time.perf_counter()
        response = client.get(endpoint, headers=AUTH_HEADERS)
        latencies.append(time.perf_counter() - start)
        assert response.status_code == 200, f"{endpoint} returned {response.status_code}"

    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < threshold, (
        f"{endpoint} 平均延迟 {avg_latency*1000:.1f}ms 超过阈值 {threshold*1000:.1f}ms"
    )
