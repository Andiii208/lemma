"""LaTeX 编译工具 — 编译 .tex 为 .pdf"""

from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path

from .base import Tool, ToolResult


class LatexCompilerTool(Tool):
    """LaTeX 编译工具"""

    name = "latex_compiler"
    description = "编译 LaTeX (.tex) 文件为 PDF。使用 xelatex 引擎，支持中文。"
    category = "document"

    def __init__(self, work_dir: str = "."):
        self.work_dir = Path(work_dir)

    async def execute(self, tex_file: str = "", passes: int = 2, **kwargs) -> ToolResult:
        """编译 LaTeX 文件"""
        if not tex_file:
            return ToolResult.fail("必须提供 tex_file 参数")

        tex_path = self.work_dir / tex_file
        if not tex_path.exists():
            return ToolResult.fail(f"文件不存在: {tex_file}")

        errors = []
        all_logs = []
        for i in range(passes):
            try:
                proc = await asyncio.create_subprocess_exec(
                    "xelatex",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    str(tex_path.name),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(self.work_dir),
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=180)
                log = stdout.decode("utf-8", errors="replace")
                all_logs.append(f"=== Pass {i + 1} ===\n{log[-2000:]}")

                if proc.returncode != 0:
                    errors.append(f"Pass {i + 1} failed (exit {proc.returncode})")
            except TimeoutError:
                errors.append(f"Pass {i + 1} 超时 (180s)")

        log_path = tex_path.with_suffix(".log")
        log_content = ""
        if log_path.exists():
            with contextlib.suppress(Exception):
                log_content = log_path.read_text(encoding="utf-8", errors="replace")

        error_count = log_content.count("! ") if log_content else len(errors)
        pdf_path = tex_path.with_suffix(".pdf")

        if pdf_path.exists() and error_count == 0:
            return ToolResult.ok(
                output=f"编译成功: {pdf_path.name}",
                pdf_path=str(pdf_path),
                error_count=0,
                passes=passes,
            )
        else:
            error_lines = (
                [line for line in log_content.split("\n") if line.startswith("!")]
                if log_content
                else []
            )
            # 包含具体错误信息（如超时）
            detail = "; ".join(errors) if errors else f"{error_count} 个错误"
            return ToolResult.fail(
                error=f"编译失败: {detail}",
                error_details=error_lines[:10],
                log_tail=log_content[-3000:] if log_content else "\n".join(all_logs),
            )

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "tex_file": {
                    "type": "string",
                    "description": "LaTeX 文件路径（相对于工作目录）",
                },
                "passes": {
                    "type": "integer",
                    "description": "编译次数（默认 2 次，用于解决交叉引用）",
                    "default": 2,
                },
            },
            "required": ["tex_file"],
        }
