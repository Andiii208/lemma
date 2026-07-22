"""Lemma 后端启动脚本"""
import sys
import os
from pathlib import Path

# 添加 src 到 Python 路径
backend_dir = Path(__file__).resolve().parent
src_dir = str(backend_dir / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

def main():
    import uvicorn
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8765"))

    print(f"""
╔══════════════════════════════════════════════╗
║  Lemma Backend v5.2.0                        ║
║  http://{host}:{port}                         ║
║  WebSocket: ws://{host}:{port}/ws             ║
║  API Docs: http://{host}:{port}/docs          ║
╚══════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "lemma.api.server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
    )

if __name__ == "__main__":
    main()
