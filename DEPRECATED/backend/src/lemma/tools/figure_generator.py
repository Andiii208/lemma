"""图表生成工具 — 基于 figure_style 模块"""

from __future__ import annotations

import asyncio
import contextlib
import uuid
from pathlib import Path

from .base import Tool, ToolResult


class FigureGeneratorTool(Tool):
    """图表生成工具"""

    name = "figure_generator"
    description = (
        "使用 figure_style 模块生成出版级质量的图表。支持折线图、柱状图、热力图、散点图等。"
    )
    category = "visualization"

    def __init__(self, work_dir: str = "."):
        self.work_dir = Path(work_dir)

    async def execute(
        self, code: str = "", output_name: str = "figure.png", **kwargs
    ) -> ToolResult:
        """执行图表生成代码"""
        if not code:
            return ToolResult.fail("必须提供 code 参数")

        # 使用 UUID 避免并发冲突
        temp_name = f"_fig_gen_{uuid.uuid4().hex[:8]}.py"

        wrapped_code = f"""import sys
sys.path.insert(0, r'{self.work_dir}')
try:
    from figure_style import setup_style, COLORS, fix_label, bar_comparison, line_comparison
except ImportError:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

{code}

plt.tight_layout()
plt.savefig(r'{self.work_dir / output_name}', dpi=200, bbox_inches='tight', facecolor='white')
print(f"图表已保存: {output_name}")
plt.close('all')
"""
        tmp_path = self.work_dir / temp_name
        tmp_path.write_text(wrapped_code, encoding="utf-8")

        try:
            proc = await asyncio.create_subprocess_exec(
                "python",
                str(tmp_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.work_dir),
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            output_path = self.work_dir / output_name
            if proc.returncode == 0 and output_path.exists():
                size_kb = output_path.stat().st_size / 1024
                return ToolResult.ok(
                    output=f"✅ 图表已生成: {output_name} ({size_kb:.0f} KB)\n{stdout_text}",
                    figure_path=str(output_path),
                    size_kb=size_kb,
                )
            else:
                return ToolResult.fail(
                    error=f"图表生成失败:\n{stderr_text}",
                    output=stdout_text,
                )
        except TimeoutError:
            return ToolResult.fail(error="图表生成超时 (120s)")
        finally:
            if tmp_path.exists():
                with contextlib.suppress(OSError):
                    tmp_path.unlink()

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "matplotlib 绑图代码（不需要 import 和 plt.savefig）",
                },
                "output_name": {
                    "type": "string",
                    "description": "输出文件名",
                    "default": "figure.png",
                },
            },
            "required": ["code"],
        }
