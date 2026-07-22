"""90分钟稳定性监控 — 输出到日志文件"""
import sys
import asyncio
import json
import time
import os
from datetime import datetime

sys.path.insert(0, 'src')

LOG_FILE = "E:/数学建模agent/backend/stability.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

async def main():
    from httpx import AsyncClient
    import websockets

    # Clear log
    with open(LOG_FILE, "w") as f:
        f.write("")

    log("🚀 稳定性监控启动 (90分钟)")
    start = time.time()
    end_time = start + 90 * 60  # 90 minutes
    cycle = 0
    total_checks = 0
    total_errors = 0

    while time.time() < end_time:
        cycle += 1
        elapsed = time.time() - start
        log(f"--- 周期 {cycle} ({elapsed/60:.1f}分钟) ---")

        try:
            async with AsyncClient(base_url="http://127.0.0.1:8765", timeout=30) as client:
                # Health
                r = await client.get("/api/health")
                assert r.json()["status"] == "ok"
                total_checks += 1

                # Init
                r = await client.post("/api/project/init", json={"work_dir": "E:/数学建模agent/backend"})
                assert r.json()["status"] == "ok"
                total_checks += 1

                # Roles
                r = await client.get("/api/roles")
                assert len(r.json()["roles"]) == 12
                total_checks += 1

                # Status
                r = await client.get("/api/status")
                assert r.json()["current_role"] == "lead"
                total_checks += 1

                # Files
                r = await client.get("/api/files")
                assert len(r.json()["files"]) > 0
                total_checks += 1

                # File read
                r = await client.get("/api/file/start.py")
                assert "UltraMath" in r.json()["content"]
                total_checks += 1

                # Config
                r = await client.post("/api/config", json={
                    "provider": "test", "model": "test", "api_key": "test", "base_url": "http://localhost"
                })
                assert r.json()["status"] == "ok"
                total_checks += 1

                # Reset
                r = await client.post("/api/reset")
                assert r.json()["status"] == "ok"
                total_checks += 1

                # Security: path traversal
                r = await client.get("/api/files", params={"path": "../../etc"})
                assert r.status_code in [400, 403]
                total_checks += 1

                # Security: invalid role
                r = await client.post("/api/chat", json={"message": "test", "role": "invalid"})
                assert r.status_code == 400
                total_checks += 1

                log(f"  REST API: 10/10 ✅")

        except Exception as e:
            total_errors += 1
            log(f"  ❌ REST API error: {e}")

        # WebSocket
        try:
            async with websockets.connect("ws://127.0.0.1:8765/ws", close_timeout=2) as ws:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(msg)
                assert data["type"] == "status"

                await ws.send(json.dumps({"type": "init", "work_dir": "E:/数学建模agent/backend"}))
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                assert json.loads(msg)["type"] == "initialized"

                await ws.send(json.dumps({"type": "switch_role", "role": "math"}))
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                assert json.loads(msg)["type"] == "role_switched"

                await ws.send("bad json")
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                assert json.loads(msg)["type"] == "error"

                await ws.send(json.dumps({"type": "chat", "message": "test", "role": "lead"}))
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                assert json.loads(msg)["type"] == "message"

            total_checks += 5
            log(f"  WebSocket: 5/5 ✅")

        except Exception as e:
            total_errors += 1
            log(f"  ❌ WebSocket error: {e}")

        # Summary every 5 cycles
        if cycle % 5 == 0:
            elapsed_min = elapsed / 60
            log(f"📊 汇总: {elapsed_min:.1f}分钟 | {cycle}周期 | {total_checks}次检查 | {total_errors}次错误")

        # Wait 60 seconds
        await asyncio.sleep(60)

    # Final report
    elapsed = time.time() - start
    log("=" * 50)
    log(f"🏁 稳定性监控完成!")
    log(f"  运行时间: {elapsed/60:.1f} 分钟")
    log(f"  总周期: {cycle}")
    log(f"  总检查: {total_checks}")
    log(f"  总错误: {total_errors}")
    log(f"  状态: {'✅ 零错误' if total_errors == 0 else f'⚠️ {total_errors} 错误'}")
    log("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
