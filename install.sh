#!/bin/bash
set -e

echo "========================================"
echo "  Lemma 一键安装 (Electron)"
echo "========================================"
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "[1/4] 检查 Node.js..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}[错误] 未找到 Node.js，请先安装 Node.js 18+${NC}"
    echo "  下载地址: https://nodejs.org/"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "  找到 Node.js ${GREEN}$NODE_VERSION${NC}"

echo "[2/4] 安装依赖 (npm ci)..."
npm ci
echo -e "  ${GREEN}依赖安装完成${NC}"

echo "[3/4] 类型检查 (npm run typecheck)..."
npm run typecheck
echo -e "  ${GREEN}类型检查通过${NC}"

echo "[4/4] 构建 Electron 应用 (npm run electron:build)..."
npm run electron:build
echo -e "  ${GREEN}构建完成${NC}"

echo ""
echo "========================================"
echo -e "  ${GREEN}安装完成！${NC}"
echo "========================================"
