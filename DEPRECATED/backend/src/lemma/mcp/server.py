"""MCP Server 适配器 — 将 UltraAgent 工具暴露为 MCP tools

使用方式:
    python -m ultramath.mcp.server --work-dir /path/to/workspace

外部 MCP client（如 Claude Desktop）可通过 stdio 协议连接。
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from ..tools.base import Tool
from ..tools.registry import ToolRegistry

logger = logging.getLogger("ultramath.mcp")


class UltraAgentMCPServer:
    """UltraAgent MCP Server — 将工具注册表暴露为 MCP tools"""

    def __init__(self, registry: ToolRegistry, server_name: str = "ultraagent"):
        self.registry = registry
        self.server_name = server_name

    def list_tools(self) -> list[dict[str, Any]]:
        """列出所有工具（MCP ListTools 格式）"""
        tools = []
        for tool in self.registry._tools.values():
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool._get_parameters_schema(),
            })
        return tools

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """调用工具（MCP CallTool 格式）"""
        try:
            result = await self.registry.execute(name, **arguments)
            return {
                "content": [{"type": "text", "text": result.to_display()}],
                "isError": not result.success,
            }
        except Exception as e:
            logger.error(f"Tool call failed: {name} - {e}")
            return {
                "content": [{"type": "text", "text": f"工具调用失败: {e}"}],
                "isError": True,
            }

    async def run_stdio(self) -> None:
        """通过 stdio 运行 MCP server（JSON-RPC over stdin/stdout）"""
        import sys

        logger.info(f"MCP Server '{self.server_name}' 启动 (stdio)")

        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                if not line:
                    break

                request = json.loads(line.strip())
                response = await self._handle_request(request)

                if response is not None:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()

            except json.JSONDecodeError:
                continue
            except Exception as e:
                logger.error(f"MCP error: {e}")
                break

    async def _handle_request(self, request: dict) -> dict | None:
        """处理 JSON-RPC 请求"""
        method = request.get("method", "")
        req_id = request.get("id")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {
                        "name": self.server_name,
                        "version": "5.1.0",
                    },
                },
            }

        elif method == "notifications/initialized":
            return None  # 通知不需要响应

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.list_tools()},
            }

        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = await self.call_tool(tool_name, arguments)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Unknown method: {method}"},
            }


def create_default_server(work_dir: str) -> UltraAgentMCPServer:
    """创建默认的 MCP server（注册所有内置工具）"""
    from ..tools.code_executor import CodeExecutorTool
    from ..tools.data_analyzer import DataAnalyzerTool
    from ..tools.equation_solver import EquationSolverTool
    from ..tools.figure_generator import FigureGeneratorTool
    from ..tools.file_manager import FileManagerTool
    from ..tools.latex_compiler import LatexCompilerTool
    from ..tools.quality_checker import QualityCheckerTool

    registry = ToolRegistry()
    registry.register(CodeExecutorTool(work_dir))
    registry.register(LatexCompilerTool(work_dir))
    registry.register(FileManagerTool(work_dir))
    registry.register(QualityCheckerTool(work_dir))
    registry.register(FigureGeneratorTool(work_dir))
    registry.register(EquationSolverTool(work_dir))
    registry.register(DataAnalyzerTool(work_dir))

    return UltraAgentMCPServer(registry)


# ==================== CLI 入口 ====================


def main():
    """MCP Server CLI: python -m ultramath.mcp.server --work-dir /path"""
    import argparse

    parser = argparse.ArgumentParser(description="UltraAgent MCP Server")
    parser.add_argument("--work-dir", default=".", help="工作目录")
    parser.add_argument("--name", default="ultraagent", help="Server 名称")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    server = create_default_server(args.work_dir)
    server.server_name = args.name
    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    main()
