"""API 认证中间件"""

from __future__ import annotations

import os

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key() -> str:
    """获取服务端 API Key"""
    return os.getenv("ULTRAMATH_API_KEY", "")


async def verify_api_key(api_key: str | None = Security(API_KEY_HEADER)) -> str:
    """验证 API Key — 开发模式下跳过验证"""
    # 如果没有配置服务端 API Key，则跳过验证（开发模式）
    server_key = get_api_key()
    if not server_key:
        return api_key or ""

    # 生产模式：严格验证
    if not api_key or api_key != server_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
    return api_key
