"""代码执行工具 — 安全执行 Python 代码（含 AST 沙箱检查）"""

from __future__ import annotations

import asyncio
import contextlib
import os
import uuid
from pathlib import Path

from .base import Tool, ToolResult
from .sandbox import SecurityChecker

# 默认允许的科学计算模块
DEFAULT_ALLOWED_MODULES = {
    "numpy",
    "scipy",
    "matplotlib",
    "pandas",
    "sklearn",
    "sympy",
    "statsmodels",
}


class CodeExecutorTool(Tool):
    """Python 代码执行工具"""

    name = "code_executor"
    description = "执行 Python 代码并返回输出。支持 matplotlib 图表生成、数值计算等。"
    category = "computation"

    def __init__(self, work_dir: str = ".", timeout: float = 300.0):
        self.work_dir = Path(work_dir).resolve()
        self.timeout = timeout

    def _safe_path(self, filename: str) -> Path:
        """安全解析路径，防止路径遍历"""
        if Path(filename).is_absolute():
            raise ValueError(f"不允许绝对路径: {filename}")
        resolved = (self.work_dir / filename).resolve()
        if not str(resolved).startswith(str(self.work_dir)):
            raise ValueError(f"路径越界: {filename}")
        return resolved

    async def execute(self, code: str = "", filename: str | None = None, **kwargs) -> ToolResult:
        """执行 Python 代码（带安全检查）"""
        if not code and not filename:
            return ToolResult.fail("必须提供 code 或 filename")

        if filename:
            try:
                code_path = self._safe_path(filename)
            except ValueError as e:
                return ToolResult.fail(str(e))
            if not code_path.exists():
                return ToolResult.fail(f"文件不存在: {filename}")
            code = code_path.read_text(encoding="utf-8")
        else:
            # 使用唯一文件名避免并发冲突
            unique_name = f"_exec_{uuid.uuid4().hex[:8]}.py"
            code_path = self.work_dir / unique_name
            code_path.write_text(code, encoding="utf-8")

        # AST 安全检查
        checker = SecurityChecker(allowed_modules=DEFAULT_ALLOWED_MODULES)
        errors = checker.check(code)
        if errors:
            if not filename and code_path.exists():
                with contextlib.suppress(OSError):
                    code_path.unlink()
            return ToolResult.fail(f"安全检查未通过: {'; '.join(errors)}")

        proc = None
        try:
            env = os.environ.copy()
            env["MPLBACKEND"] = "Agg"
            # 移除敏感环境变量
            for key in list(env.keys()):
                key_lower = key.lower()
                if any(
                    s in key_lower for s in ("key", "secret", "token", "password", "auth")
                ) and key not in ("MPLBACKEND",):
                    env.pop(key, None)

            proc = await asyncio.create_subprocess_exec(
                "python",
                str(code_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.work_dir),
                env=env,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
            stdout_text = stdout.decode("utf-8", errors="replace").strip()
            stderr_text = stderr.decode("utf-8", errors="replace").strip()

            if proc.returncode == 0:
                output = stdout_text
                if stderr_text:
                    output += f"\n[stderr]\n{stderr_text}"
                return ToolResult.ok(
                    output=output or "执行成功 (无输出)",
                    return_code=0,
                    filename=str(code_path.name),
                )
            else:
                return ToolResult.fail(
                    error=stderr_text or "未知错误",
                    output=stdout_text,
                    return_code=proc.returncode,
                )
        except TimeoutError:
            if proc:
                try:
                    proc.kill()
                    await proc.wait()
                except Exception:
                    pass
            return ToolResult.fail(error=f"代码执行超时 ({self.timeout}s)")
        except FileNotFoundError:
            return ToolResult.fail(error="Python 解释器未找到")
        finally:
            if not filename and code_path.exists():
                with contextlib.suppress(OSError):
                    code_path.unlink()

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "要执行的 Python 代码",
                },
                "filename": {
                    "type": "string",
                    "description": "已存在的 Python 文件路径（相对于工作目录）",
                },
            },
            "required": [],
        }
