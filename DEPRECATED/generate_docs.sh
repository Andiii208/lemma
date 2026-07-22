#!/bin/bash
# UltraAgent 文档自动生成脚本
# 生成 OpenAPI 规范和覆盖率报告

set -e

echo "==> 生成 OpenAPI 文档..."
cd backend
PYTHONPATH=src python -c "
import json
from ultramath.api.server import app
spec = app.openapi()
with open('../docs/openapi.json', 'w') as f:
    json.dump(spec, f, indent=2, ensure_ascii=False)
print(f'  端点数: {len(spec[\"paths\"])}')
"

echo "==> 运行后端测试并生成覆盖率..."
PYTHONPATH=src python -m pytest tests/ --cov=src/ultramath --cov-report=term -q 2>&1 | tail -5

echo "==> 文档生成完成"
