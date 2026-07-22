"""API 认证模块测试"""
import pytest
import os
from unittest.mock import patch

from lemma.api.auth import get_api_key, verify_api_key


class TestGetApiKey:
    def test_default_key(self):
        """默认 API key 为 dev-key"""
        with patch.dict(os.environ, {}, clear=False):
            # 移除自定义环境变量（如果存在）
            os.environ.pop("ULTRAMATH_API_KEY", None)
            key = get_api_key()
            assert key == "dev-key-change-in-production"

    def test_custom_key_from_env(self):
        """从环境变量读取自定义 key"""
        with patch.dict(os.environ, {"ULTRAMATH_API_KEY": "my-secret-key"}):
            key = get_api_key()
            assert key == "my-secret-key"


class TestVerifyApiKey:
    @pytest.mark.asyncio
    async def test_valid_key_passes(self):
        """有效 key 应通过验证"""
        with patch("lemma.api.auth.get_api_key", return_value="test-key"):
            result = await verify_api_key("test-key")
            assert result == "test-key"

    @pytest.mark.asyncio
    async def test_invalid_key_raises_401(self):
        """无效 key 应抛出 401"""
        from fastapi import HTTPException
        with patch("lemma.api.auth.get_api_key", return_value="correct-key"):
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key("wrong-key")
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_none_key_raises_401(self):
        """None key 应抛出 401"""
        from fastapi import HTTPException
        with patch("lemma.api.auth.get_api_key", return_value="correct-key"):
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(None)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_key_raises_401(self):
        """空字符串 key 应抛出 401"""
        from fastapi import HTTPException
        with patch("lemma.api.auth.get_api_key", return_value="correct-key"):
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key("")
            assert exc_info.value.status_code == 401
