"""共享测试夹具"""
import sys
from pathlib import Path

# 将 src 目录添加到 Python 路径
_src_dir = str(Path(__file__).parent.parent / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

import pytest
from unittest.mock import AsyncMock, MagicMock

from lemma.memory.short_term import ShortTermMemory
from lemma.tools.registry import ToolRegistry
from lemma.tools.base import Tool, ToolResult
from lemma.agent.role import RoleManager


@pytest.fixture
def tmp_work_dir(tmp_path):
    """创建临时工作目录结构"""
    (tmp_path / "求解").mkdir()
    (tmp_path / "数据").mkdir()
    (tmp_path / "论文").mkdir()
    (tmp_path / "题目").mkdir()
    return str(tmp_path)


@pytest.fixture
def mock_llm_config():
    """模拟 LLM 配置"""
    from lemma.llm.backend import LLMConfig
    return LLMConfig(
        provider="test",
        model="test-model",
        api_key="test-key",
        base_url="http://localhost:1234/v1",
    )


@pytest.fixture
def memory():
    """短期记忆实例"""
    return ShortTermMemory(max_tokens=1000)


@pytest.fixture
def tool_registry(tmp_work_dir):
    """工具注册表"""
    registry = ToolRegistry()
    return registry


@pytest.fixture
def role_manager():
    """角色管理器"""
    return RoleManager()
