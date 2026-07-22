"""文件管理工具 — 读写文件"""

from __future__ import annotations

from pathlib import Path

from .base import Tool, ToolResult


class FileManagerTool(Tool):
    """文件管理工具"""

    name = "file_manager"
    description = "读取、写入、列出文件。支持读取文本文件、写入内容、列出目录。"
    category = "filesystem"

    def __init__(self, work_dir: str = "."):
        self.work_dir = Path(work_dir)

    async def execute(
        self,
        action: str = "read",
        path: str = "",
        content: str = "",
        encoding: str = "utf-8",
        **kwargs,
    ) -> ToolResult:
        """执行文件操作"""
        if not path:
            return ToolResult.fail("必须提供 path 参数")

        target = self.work_dir / path
        # 安全检查：不允许访问父目录
        try:
            target.resolve().relative_to(self.work_dir.resolve())
        except ValueError:
            return ToolResult.fail(f"路径越界: {path}")

        if action == "read":
            return await self._read(target, encoding)
        elif action == "write":
            return await self._write(target, content, encoding)
        elif action == "list":
            return await self._list(target)
        elif action == "exists":
            return ToolResult.ok(output=str(target.exists()))
        elif action == "mkdir":
            target.mkdir(parents=True, exist_ok=True)
            return ToolResult.ok(output=f"目录已创建: {path}")
        else:
            return ToolResult.fail(f"未知操作: {action}")

    async def _read(self, path: Path, encoding: str) -> ToolResult:
        if not path.exists():
            return ToolResult.fail(f"文件不存在: {path.name}")
        try:
            content = path.read_text(encoding=encoding)
            if len(content) > 50000:
                content = content[:50000] + f"\n... [截断, 总长度 {len(content)} 字符]"
            return ToolResult.ok(output=content, filename=path.name, size=path.stat().st_size)
        except UnicodeDecodeError:
            return ToolResult.fail(f"无法以 {encoding} 编码读取文件")
        except Exception as e:
            return ToolResult.fail(f"读取失败: {e}")

    async def _write(self, path: Path, content: str, encoding: str) -> ToolResult:
        if not content:
            return ToolResult.fail("写入操作需要 content 参数")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding=encoding)
            return ToolResult.ok(
                output=f"已写入: {path.name} ({len(content)} 字符)",
                filename=path.name,
                size=len(content),
            )
        except Exception as e:
            return ToolResult.fail(f"写入失败: {e}")

    async def _list(self, path: Path) -> ToolResult:
        if not path.exists():
            return ToolResult.fail(f"目录不存在: {path.name}")
        if path.is_file():
            return ToolResult.ok(output=f"[文件] {path.name}")
        entries = []
        for item in sorted(path.iterdir()):
            prefix = "📁" if item.is_dir() else "📄"
            size = f" ({item.stat().st_size} bytes)" if item.is_file() else ""
            entries.append(f"{prefix} {item.name}{size}")
        return ToolResult.ok(output="\n".join(entries) or "(空目录)")

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["read", "write", "list", "exists", "mkdir"],
                    "description": "操作类型",
                },
                "path": {
                    "type": "string",
                    "description": "文件或目录路径（相对于工作目录）",
                },
                "content": {
                    "type": "string",
                    "description": "写入的内容（仅 write 操作需要）",
                },
                "encoding": {
                    "type": "string",
                    "description": "文件编码",
                    "default": "utf-8",
                },
            },
            "required": ["action", "path"],
        }
