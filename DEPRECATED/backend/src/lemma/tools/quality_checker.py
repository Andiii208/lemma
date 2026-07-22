"""质量检查工具 — 集成代码检查、图表审查等"""

from __future__ import annotations

import ast
import py_compile
from pathlib import Path

from .base import Tool, ToolResult


class QualityCheckerTool(Tool):
    """质量检查工具"""

    name = "quality_checker"
    description = "执行质量检查：代码语法检查、AST 分析、LaTeX 编译日志分析。"
    category = "quality"

    def __init__(self, work_dir: str = ".", scripts_dir: str | None = None):
        self.work_dir = Path(work_dir)
        self.scripts_dir = Path(scripts_dir) if scripts_dir else None

    async def execute(self, check_type: str = "syntax", target: str = "", **kwargs) -> ToolResult:
        """执行质量检查"""
        if not target:
            return ToolResult.fail("必须提供 target 参数")

        checkers = {
            "syntax": self._check_syntax,
            "ast": self._check_ast,
            "latex_log": self._check_latex_log,
            "figures": self._check_figures,
        }

        checker = checkers.get(check_type)
        if not checker:
            return ToolResult.fail(f"未知检查类型: {check_type}。可用: {list(checkers.keys())}")

        return await checker(target)

    async def _check_syntax(self, target: str) -> ToolResult:
        """Python 语法检查"""
        target_path = self.work_dir / target
        if not target_path.exists():
            return ToolResult.fail(f"文件不存在: {target}")

        try:
            py_compile.compile(str(target_path), doraise=True)
            return ToolResult.ok(output=f"✅ {target}: 语法正确", check_type="syntax")
        except py_compile.PyCompileError as e:
            return ToolResult.fail(error=f"❌ {target}: {e}", check_type="syntax")

    async def _check_ast(self, target: str) -> ToolResult:
        """AST 深度分析"""
        target_path = self.work_dir / target
        if not target_path.exists():
            return ToolResult.fail(f"文件不存在: {target}")

        try:
            source = target_path.read_text(encoding="utf-8")
            tree = ast.parse(source)

            issues = []
            for node in ast.walk(tree):
                # 检查未使用的变量赋值
                if (
                    isinstance(node, ast.Assign)
                    and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                ):
                    name = node.targets[0].id
                    # 简单检查：单下划线开头的变量通常不需要
                    if name.startswith("_") and not name.startswith("__"):
                        issues.append(f"  ⚠️ 行 {node.lineno}: 变量 '{name}' 可能未使用")

                # 检查裸 except
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    issues.append(f"  ⚠️ 行 {node.lineno}: 裸 except (应指定异常类型)")

                # 检查 print 语句（可能需要替换为 logging）
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "print"
                ):
                    pass  # print 是允许的，不警告

            if issues:
                return ToolResult.ok(
                    output=f"AST 分析 {target}:\n" + "\n".join(issues[:20]),
                    issue_count=len(issues),
                )
            else:
                return ToolResult.ok(output=f"✅ {target}: AST 分析无问题")

        except SyntaxError as e:
            return ToolResult.fail(error=f"语法错误: {e}")
        except Exception as e:
            return ToolResult.fail(error=f"分析失败: {e}")

    async def _check_latex_log(self, target: str) -> ToolResult:
        """检查 LaTeX 编译日志"""
        log_path = self.work_dir / target
        if not log_path.exists():
            return ToolResult.fail(f"日志文件不存在: {target}")

        try:
            content = log_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return ToolResult.fail(f"读取日志失败: {e}")

        errors = [line for line in content.split("\n") if line.startswith("!")]
        warnings = [line for line in content.split("\n") if "Warning" in line]

        result_parts = []
        if errors:
            result_parts.append(f"❌ {len(errors)} 个错误:")
            result_parts.extend(errors[:10])
        if warnings:
            result_parts.append(f"⚠️ {len(warnings)} 个警告:")
            result_parts.extend(warnings[:5])

        if not errors:
            result_parts.insert(0, "✅ LaTeX 编译无错误")

        return ToolResult.ok(
            output="\n".join(result_parts),
            error_count=len(errors),
            warning_count=len(warnings),
        )

    async def _check_figures(self, target: str) -> ToolResult:
        """检查图表质量"""
        target_dir = self.work_dir / target
        if not target_dir.exists():
            return ToolResult.fail(f"目录不存在: {target}")

        png_files = list(target_dir.glob("**/*.png"))
        if not png_files:
            return ToolResult.ok(output="未找到 PNG 图表文件")

        report = [f"📊 图表检查 ({len(png_files)} 个文件):"]
        for png in png_files:
            size_kb = png.stat().st_size / 1024
            status = "✅"
            notes = []
            if size_kb < 10:
                status = "⚠️"
                notes.append("文件过小，可能分辨率不足")
            elif size_kb > 5000:
                status = "⚠️"
                notes.append("文件过大，建议压缩")
            report.append(f"  {status} {png.name} ({size_kb:.0f} KB) {' | '.join(notes)}")

        return ToolResult.ok(output="\n".join(report), figure_count=len(png_files))

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "check_type": {
                    "type": "string",
                    "enum": ["syntax", "ast", "latex_log", "figures"],
                    "description": "检查类型",
                },
                "target": {
                    "type": "string",
                    "description": "检查目标文件或目录路径",
                },
            },
            "required": ["check_type", "target"],
        }
