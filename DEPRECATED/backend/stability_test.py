"""稳定性测试脚本 — 验证系统长时间运行无崩溃"""
import sys
import asyncio
import json
import time
import psutil
import os
from datetime import datetime

sys.path.insert(0, 'src')

API_BASE = "http://127.0.0.1:8765"
WS_URL = "ws://127.0.0.1:8765/ws"

class StabilityMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.health_checks = 0
        self.errors = 0
        self.ws_connections = 0
        self.api_calls = 0

    def log(self, msg: str):
        elapsed = time.time() - self.start_time
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] ({elapsed:.0f}s) {msg}")

    def report(self):
        elapsed = time.time() - self.start_time
        self.log(f"=== 稳定性报告 ===")
        self.log(f"  运行时间: {elapsed:.0f}s ({elapsed/60:.1f}分钟)")
        self.log(f"  健康检查: {self.health_checks} 次")
        self.log(f"  API 调用: {self.api_calls} 次")
        self.log(f"  WS 连接: {self.ws_connections} 次")
        self.log(f"  错误数: {self.errors}")

monitor = StabilityMonitor()


async def health_check(client):
    """健康检查"""
    try:
        r = await client.get(f"{API_BASE}/api/health")
        assert r.json()["status"] == "ok"
        monitor.health_checks += 1
        return True
    except Exception as e:
        monitor.errors += 1
        monitor.log(f"❌ Health check failed: {e}")
        return False


async def test_rest_api(client):
    """测试 REST API 全端点"""
    try:
        # Health
        r = await client.get(f"{API_BASE}/api/health")
        assert r.json()["status"] == "ok"
        monitor.api_calls += 1

        # Roles
        r = await client.get(f"{API_BASE}/api/roles")
        assert len(r.json()["roles"]) == 12
        monitor.api_calls += 1

        # Init
        r = await client.post(f"{API_BASE}/api/project/init",
                              json={"work_dir": "E:/数学建模agent/backend"})
        assert r.json()["status"] == "ok"
        monitor.api_calls += 1

        # Status
        r = await client.get(f"{API_BASE}/api/status")
        assert r.json()["current_role"] == "lead"
        monitor.api_calls += 1

        # Files
        r = await client.get(f"{API_BASE}/api/files")
        assert len(r.json()["files"]) > 0
        monitor.api_calls += 1

        # File read
        r = await client.get(f"{API_BASE}/api/file/start.py")
        assert "UltraMath" in r.json()["content"]
        monitor.api_calls += 1

        # Config
        r = await client.post(f"{API_BASE}/api/config", json={
            "provider": "test", "model": "test", "api_key": "test",
            "base_url": "http://localhost"
        })
        assert r.json()["status"] == "ok"
        monitor.api_calls += 1

        # Reset
        r = await client.post(f"{API_BASE}/api/reset")
        assert r.json()["status"] == "ok"
        monitor.api_calls += 1

        return True
    except Exception as e:
        monitor.errors += 1
        monitor.log(f"❌ REST API test failed: {e}")
        return False


async def test_websocket():
    """测试 WebSocket 连接"""
    import websockets
    try:
        async with websockets.connect(WS_URL, close_timeout=2) as ws:
            monitor.ws_connections += 1

            # Status on connect
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            assert data["type"] == "status"

            # Init
            await ws.send(json.dumps({"type": "init", "work_dir": "E:/数学建模agent/backend"}))
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            assert data["type"] == "initialized"

            # Role switch
            await ws.send(json.dumps({"type": "switch_role", "role": "math"}))
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            assert data["type"] == "role_switched"

            # Invalid JSON handling
            await ws.send("not json")
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            assert data["type"] == "error"

            # Chat
            await ws.send(json.dumps({"type": "chat", "message": "测试", "role": "lead"}))
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            assert data["type"] == "message"

        return True
    except Exception as e:
        monitor.errors += 1
        monitor.log(f"❌ WebSocket test failed: {e}")
        return False


async def test_security():
    """测试安全防护"""
    from httpx import AsyncClient
    try:
        async with AsyncClient(base_url=API_BASE) as client:
            # Path traversal
            r = await client.get("/api/files", params={"path": "../../etc"})
            assert r.status_code in [400, 403]

            # Invalid role
            r = await client.post("/api/chat", json={"message": "test", "role": "invalid"})
            assert r.status_code == 400

            # Empty message
            r = await client.post("/api/chat", json={"message": "", "role": "lead"})
            assert r.status_code == 422

            # Nonexistent file
            r = await client.get("/api/file/nonexistent.txt")
            assert r.status_code == 404

        return True
    except Exception as e:
        monitor.errors += 1
        monitor.log(f"❌ Security test failed: {e}")
        return False


async def check_memory():
    """检查内存使用"""
    try:
        process = psutil.Process(os.getpid())
        mem = process.memory_info()
        rss_mb = mem.rss / 1024 / 1024
        monitor.log(f"📊 内存: {rss_mb:.1f} MB RSS")
        return rss_mb
    except Exception:
        return 0


async def run_stability_test(duration_minutes: float = 90):
    """运行稳定性测试"""
    from httpx import AsyncClient

    monitor.log(f"🚀 开始稳定性测试 (目标: {duration_minutes} 分钟)")

    end_time = time.time() + duration_minutes * 60
    cycle = 0
    peak_memory = 0

    async with AsyncClient(base_url=API_BASE, timeout=30) as client:
        while time.time() < end_time:
            cycle += 1
            monitor.log(f"--- 周期 {cycle} ---")

            # 健康检查
            ok = await health_check(client)
            if not ok:
                monitor.log("⚠️ 后端不健康，等待 10 秒后重试...")
                await asyncio.sleep(10)
                continue

            # REST API 测试
            await test_rest_api(client)

            # WebSocket 测试
            await test_websocket()

            # 安全测试
            await test_security()

            # 内存检查
            mem = await check_memory()
            if mem > peak_memory:
                peak_memory = mem

            # 报告
            if cycle % 5 == 0:
                monitor.report()
                monitor.log(f"  峰值内存: {peak_memory:.1f} MB")

            # 等待下一个周期（每 60 秒一次）
            await asyncio.sleep(60)

    # 最终报告
    monitor.log("🏁 稳定性测试完成!")
    monitor.report()
    monitor.log(f"  峰值内存: {peak_memory:.1f} MB")

    if monitor.errors == 0:
        monitor.log("✅ 零错误！系统稳定运行。")
    else:
        monitor.log(f"⚠️ 共 {monitor.errors} 个错误")


if __name__ == "__main__":
    duration = float(sys.argv[1]) if len(sys.argv) > 1 else 90
    asyncio.run(run_stability_test(duration))
