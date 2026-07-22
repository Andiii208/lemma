"""方程求解工具 — 数学建模领域专属"""
from __future__ import annotations

from .base import Tool, ToolResult


class EquationSolverTool(Tool):
    """使用 SymPy 求解方程/方程组"""

    name = "equation_solver"
    description = "求解数学方程和方程组，支持代数方程、微分方程"
    category = "math"

    def __init__(self, work_dir: str = "."):
        self.work_dir = work_dir

    async def execute(self, equations: list[str] | None = None, variables: list[str] | None = None, **kwargs) -> ToolResult:
        """求解方程"""
        if not equations:
            return ToolResult.fail("必须提供 equations 参数（方程列表）")

        try:
            import sympy as sp
        except ImportError:
            return ToolResult.fail("sympy 未安装，请运行: pip install sympy")

        try:
            parsed_eqs = []
            for eq_str in equations:
                if "=" in eq_str:
                    left, right = eq_str.split("=", 1)
                    parsed_eqs.append(sp.Eq(sp.sympify(left.strip()), sp.sympify(right.strip())))
                else:
                    parsed_eqs.append(sp.sympify(eq_str))

            if variables:
                symbols = [sp.Symbol(v) for v in variables]
            else:
                all_symbols = set()
                for eq in parsed_eqs:
                    if hasattr(eq, 'free_symbols'):
                        all_symbols.update(eq.free_symbols)
                    elif hasattr(eq, 'atoms'):
                        all_symbols.update(eq.atoms(sp.Symbol))
                symbols = sorted(all_symbols, key=lambda s: s.name)

            solution = sp.solve(parsed_eqs, symbols, dict=True)

            output_lines = ["## 方程求解结果\n"]
            if solution:
                for i, sol in enumerate(solution, 1):
                    output_lines.append(f"### 解 {i}")
                    for var, val in sol.items():
                        output_lines.append(f"  {var} = {val}")
            else:
                output_lines.append("未找到解")

            return ToolResult.ok(
                output="\n".join(output_lines),
                solution=str(solution),
                variables=[str(s) for s in symbols],
            )
        except Exception as e:
            return ToolResult.fail(f"求解失败: {e}")

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "equations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": '方程列表，如 ["x + y = 5", "2*x - y = 1"]',
                },
                "variables": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "求解变量，如 ['x', 'y']。不指定则自动推断",
                },
            },
            "required": ["equations"],
        }
