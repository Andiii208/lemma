"""数据分析工具 — 实验报告/文献综述领域专属"""
from __future__ import annotations

from .base import Tool, ToolResult


class DataAnalyzerTool(Tool):
    """统计检验和数据分析"""

    name = "data_analyzer"
    description = "执行统计检验（t检验、方差分析、卡方检验、相关分析），计算效应量"
    category = "analysis"

    def __init__(self, work_dir: str = "."):
        self.work_dir = work_dir

    async def execute(
        self,
        test_type: str = "descriptive",
        data: list[float] | None = None,
        data2: list[float] | None = None,
        groups: list[list[float]] | None = None,
        **kwargs,
    ) -> ToolResult:
        """执行统计分析"""
        try:
            import numpy as np
            from scipy import stats
        except ImportError:
            return ToolResult.fail("scipy/numpy 未安装，请运行: pip install scipy numpy")

        if not data:
            return ToolResult.fail("必须提供 data 参数")

        try:
            arr = np.array(data, dtype=float)
            output_lines = [f"## {test_type} 分析结果\n"]
            output_lines.append(f"- 样本量: {len(arr)}")
            output_lines.append(f"- 均值: {arr.mean():.4f}")
            output_lines.append(f"- 标准差: {arr.std():.4f}")
            output_lines.append(f"- 最小值: {arr.min():.4f}")
            output_lines.append(f"- 最大值: {arr.max():.4f}")

            if test_type == "ttest" and data2:
                arr2 = np.array(data2, dtype=float)
                t_stat, p_value = stats.ttest_ind(arr, arr2)
                pooled_std = np.sqrt((arr.var() + arr2.var()) / 2)
                cohens_d = (arr.mean() - arr2.mean()) / pooled_std if pooled_std > 0 else 0
                output_lines.append(f"\n### 独立样本 t 检验")
                output_lines.append(f"- t 统计量: {t_stat:.4f}")
                output_lines.append(f"- p 值: {p_value:.6f}")
                output_lines.append(f"- Cohen's d: {cohens_d:.4f}")
                output_lines.append(f"- 显著性: {'显著 (p < 0.05)' if p_value < 0.05 else '不显著'}")

            elif test_type == "anova" and groups:
                group_arrays = [np.array(g, dtype=float) for g in groups]
                f_stat, p_value = stats.f_oneway(*group_arrays)
                output_lines.append(f"\n### 单因素方差分析 (ANOVA)")
                output_lines.append(f"- F 统计量: {f_stat:.4f}")
                output_lines.append(f"- p 值: {p_value:.6f}")
                output_lines.append(f"- 组数: {len(groups)}")

            elif test_type == "correlation" and data2:
                arr2 = np.array(data2, dtype=float)
                r, p_value = stats.pearsonr(arr, arr2)
                output_lines.append(f"\n### Pearson 相关分析")
                output_lines.append(f"- 相关系数 r: {r:.4f}")
                output_lines.append(f"- p 值: {p_value:.6f}")
                strength = "强" if abs(r) > 0.7 else "中等" if abs(r) > 0.4 else "弱"
                output_lines.append(f"- 相关强度: {strength}")

            else:
                # 描述性统计
                desc = stats.describe(arr)
                output_lines.append(f"\n### 描述性统计")
                output_lines.append(f"- 偏度: {desc.skewness:.4f}")
                output_lines.append(f"- 峰度: {desc.kurtosis:.4f}")

                # 正态性检验
                if len(arr) >= 8:
                    stat, p_val = stats.shapiro(arr)
                    output_lines.append(f"- Shapiro-Wilk 正态性检验: W={stat:.4f}, p={p_val:.4f}")

            return ToolResult.ok(output="\n".join(output_lines))
        except Exception as e:
            return ToolResult.fail(f"分析失败: {e}")

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "test_type": {
                    "type": "string",
                    "enum": ["descriptive", "ttest", "anova", "correlation"],
                    "description": "检验类型",
                    "default": "descriptive",
                },
                "data": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "数据集 1",
                },
                "data2": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "数据集 2（ttest/correlation 需要）",
                },
                "groups": {
                    "type": "array",
                    "items": {"type": "array", "items": {"type": "number"}},
                    "description": "多组数据（anova 需要）",
                },
            },
            "required": ["data"],
        }
