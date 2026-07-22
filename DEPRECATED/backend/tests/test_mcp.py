"""MCP Server 适配器测试"""

import json
import pytest
from lemma.mcp.server import UltraAgentMCPServer, create_default_server
from lemma.tools.registry import ToolRegistry
from lemma.tools.base import Tool, ToolResult


class MockTool(Tool):
    name = "mock_tool"
    description = "测试工具"
    category = "test"

    def __init__(self, work_dir: str = "."):
        pass

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult.ok(output=f"mock result: {kwargs}")

    def _get_parameters_schema(self) -> dict:
        return {"type": "object", "properties": {"input": {"type": "string"}}}


class TestUltraAgentMCPServer:
    def test_list_tools(self):
        registry = ToolRegistry()
        registry.register(MockTool("/tmp"))
        server = UltraAgentMCPServer(registry)

        tools = server.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "mock_tool"
        assert "description" in tools[0]

    @pytest.mark.asyncio
    async def test_call_tool(self):
        registry = ToolRegistry()
        registry.register(MockTool("/tmp"))
        server = UltraAgentMCPServer(registry)

        result = await server.call_tool("mock_tool", {"input": "test"})
        assert result["isError"] is False
        assert "mock result" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_call_nonexistent_tool(self):
        registry = ToolRegistry()
        server = UltraAgentMCPServer(registry)

        result = await server.call_tool("nonexistent", {})
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_handle_initialize(self):
        registry = ToolRegistry()
        server = UltraAgentMCPServer(registry, server_name="test-server")

        response = await server._handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        })
        assert response["result"]["serverInfo"]["name"] == "test-server"

    @pytest.mark.asyncio
    async def test_handle_tools_list(self):
        registry = ToolRegistry()
        registry.register(MockTool("/tmp"))
        server = UltraAgentMCPServer(registry)

        response = await server._handle_request({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        })
        assert len(response["result"]["tools"]) == 1

    @pytest.mark.asyncio
    async def test_handle_ping(self):
        registry = ToolRegistry()
        server = UltraAgentMCPServer(registry)

        response = await server._handle_request({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "ping",
            "params": {},
        })
        assert response["result"] == {}

    @pytest.mark.asyncio
    async def test_handle_unknown_method(self):
        registry = ToolRegistry()
        server = UltraAgentMCPServer(registry)

        response = await server._handle_request({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "unknown/method",
            "params": {},
        })
        assert response["error"]["code"] == -32601

    def test_create_default_server(self):
        server = create_default_server("/tmp")
        tools = server.list_tools()
        assert len(tools) >= 5  # 至少 5 个内置工具
        names = [t["name"] for t in tools]
        assert "code_executor" in names
        assert "latex_compiler" in names
