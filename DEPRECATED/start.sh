#!/bin/bash
echo "========================================"
echo "  UltraMath Agent - 启动"
echo "========================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR/backend/src"

echo "[1/2] 启动后端 (端口 8765)..."
cd "$SCRIPT_DIR/backend"
python start.py &
BACKEND_PID=$!

echo "[2/2] 启动前端 (端口 5173)..."
cd "$SCRIPT_DIR/frontend"
sleep 3
npx vite &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "  启动完成！"
echo "  前端: http://localhost:5173"
echo "  后端: http://localhost:8765"
echo "  API文档: http://localhost:8765/docs"
echo "========================================"
echo ""
echo "按 Ctrl+C 停止所有服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
