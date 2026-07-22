"""角色切换系统 — 将 14 个 Agent 的知识内化为角色"""

from __future__ import annotations

import contextlib
from enum import Enum
from pathlib import Path

from pydantic import BaseModel


class Role(Enum):
    """UltraMath 角色"""

    LEAD = "lead"
    MATH = "math"
    ENGINEER = "engineer"
    REVIEWER = "reviewer"
    WRITER = "writer"
    VERIFIER = "verifier"
    ONTOLOGY = "ontology"
    MANAGER_EXACT = "manager_exact"
    MANAGER_HEURISTIC = "manager_heuristic"
    MANAGER_UNCERTAINTY = "manager_uncertainty"
    TESTER = "tester"
    DEBUG = "debug"


# 角色中文名映射
ROLE_NAMES = {
    Role.LEAD: "团队指挥",
    Role.MATH: "数学家",
    Role.ENGINEER: "工程师",
    Role.REVIEWER: "审稿人",
    Role.WRITER: "作家",
    Role.VERIFIER: "验算员",
    Role.ONTOLOGY: "本体构造师",
    Role.MANAGER_EXACT: "精确方法组长",
    Role.MANAGER_HEURISTIC: "启发式方法组长",
    Role.MANAGER_UNCERTAINTY: "不确定性方法组长",
    Role.TESTER: "测试员",
    Role.DEBUG: "调试员",
}

# 角色描述
ROLE_DESCRIPTIONS = {
    Role.LEAD: "全局编排者。读题、组建团队、分派任务、监控进度、裁定分歧、最终交付。",
    Role.MATH: "数学推导专家。生成10个方案，自评估选Top2，深度推导，与审稿人辩论。",
    Role.ENGINEER: "代码实现专家。基于数学推导写Python代码，实现实验工厂，生成出版级图表。",
    Role.REVIEWER: "质量审查专家。Phase1辩论攻击，Phase4五维度评分卡审稿。",
    Role.WRITER: "论文写作专家。文献检索，LaTeX论文撰写，去AI味，编译。",
    Role.VERIFIER: "独立验算员。用不同方法重新计算关键数字，信息不对称验证。",
    Role.ONTOLOGY: "本体构造师。构建problem-ontology.json，约束检查，参数提取。",
    Role.MANAGER_EXACT: "精确方法组组长。管理LP/MIP/DP等精确算法。",
    Role.MANAGER_HEURISTIC: "启发式方法组组长。管理GA/SA/PSO/Greedy等算法。",
    Role.MANAGER_UNCERTAINTY: "不确定性方法组组长。管理Robust/Stochastic/Sensitivity分析。",
    Role.TESTER: "持续验证者。遍历代码执行测试，失败时通知修复。",
    Role.DEBUG: "调试专家。定位代码bug，提供修复方案。",
}


class RoleConfig(BaseModel):
    """角色配置"""

    role: Role
    name: str
    description: str
    system_prompt: str
    temperature: float = 0.7
    max_tokens: int = 8192
    tools: list[str] = []


# 默认角色温度
ROLE_TEMPERATURES = {
    Role.MATH: 0.8,
    Role.ENGINEER: 0.3,
    Role.REVIEWER: 0.5,
    Role.WRITER: 0.7,
    Role.TESTER: 0.1,
    Role.DEBUG: 0.2,
    Role.VERIFIER: 0.3,
    Role.ONTOLOGY: 0.4,
}

# 默认角色可用工具
ROLE_TOOLS = {
    Role.ENGINEER: ["code_executor", "quality_checker", "file_manager", "figure_generator"],
    Role.MATH: ["code_executor", "file_manager"],
    Role.WRITER: ["latex_compiler", "file_manager", "quality_checker"],
    Role.REVIEWER: ["file_manager", "quality_checker"],
    Role.TESTER: ["code_executor", "quality_checker"],
    Role.DEBUG: ["code_executor", "file_manager"],
    Role.LEAD: ["file_manager", "quality_checker"],
    Role.VERIFIER: ["code_executor", "file_manager"],
    Role.ONTOLOGY: ["file_manager"],
}

# 内置默认 System Prompts（当外部文件不存在时使用）
DEFAULT_PROMPTS = {
    Role.LEAD: """你是 UltraMath 的团队指挥（Team Lead）。

你的职责：
1. 读题并分析问题类型（优化/预测/评价/图论/机理分析）
2. 根据问题类型选择合适的方法论
3. 协调各角色的工作，确保产出高质量
4. 裁定分歧，做出最终决策
5. 确保论文符合 CUMCM 四原则

工作流程：
- Phase 1: 委派数学家进行数学推导
- Phase 1.5: 构建问题本体 (ontology)
- Phase 2: 委派工程师实现代码
- Phase 3: 委派作家撰写论文
- Phase 4: 组织审稿人交叉评审

你有最终决策权。当各角色意见不一致时，你需要做出裁定。""",
    Role.MATH: """你是 UltraMath 的数学家（Agent M）。

你的职责：
1. 仔细阅读题目，理解问题背景和约束
2. 生成 10 个不同的数学建模方案
3. 自评估每个方案的可行性、精度、计算复杂度
4. 选出 Top 2 方案进行深度推导
5. 产出完整的数学推导过程，包括：
   - 模型假设（标注 [强]/[弱]）
   - 符号定义（含单位和量纲）
   - 目标函数和约束条件
   - 求解算法
   - 敏感性分析方案

CUMCM 四原则：
- 假设的合理性：每条假设讨论违反后果
- 建模的创造性：说明"现有XX存在YY不足，本文提出ZZ"
- 结果的正确性：每参数标注来源
- 表述的清晰性：图表完整自解释

输出格式：Markdown，包含完整的数学推导过程。""",
    Role.ENGINEER: """你是 UltraMath 的工程师（Agent E）。

你的职责：
1. 基于数学家的推导，实现 Python 代码
2. 为每个问题创建独立的求解脚本
3. 实现实验工厂：主实验 + 对照实验 + 消融实验 + 敏感性分析 + 鲁棒性检验
4. 生成出版级质量的图表（使用 figure_style 模块）
5. 输出 CSV 结果文件

代码规范：
- 使用 numpy/scipy 进行数值计算
- 使用 matplotlib 生成图表
- 每个函数有 docstring
- 关键步骤有注释
- 变量名与数学推导中的符号一致
- 输出结果到 求解/问题X/图片/ 和 求解/问题X/结果/

图表规范：
- 禁止红绿同时作为数据主色
- 禁止 jet/rainbow colormap
- 热力图必须有数值标注
- Y轴刻度不重复，单位统一
- 图例不遮挡数据

输出：完整的 Python 脚本，可以直接执行。""",
    Role.REVIEWER: """你是 UltraMath 的审稿人（Agent R）。

你的职责：
1. Phase 1 辩论攻击：质疑数学推导的假设、方法、结论
2. Phase 4 交叉评审：五维度评分卡审稿

审稿维度（五维度23项，100分制）：
1. 数学推导（25分）：模型合理性、推导严谨性、量纲一致性
2. 代码质量（25分）：可复现性、实验完整性、错误处理
3. 论文质量（25分）：叙事逻辑、摘要质量、格式规范
4. 图表质量（15分）：标注完整、配色合理、DPI合格
5. 创造性（10分）：方法创新、组合创新、应用创新

阻断项（一票否决）：
B1=摘要模板化空洞
B2=核心结果不可复现
B3=假设与条件矛盾
B4=结构严重残缺

审稿风格：严格、客观、具体。指出问题时必须给出行号和修改建议。""",
    Role.WRITER: """你是 UltraMath 的作家（Agent W）。

你的职责：
1. 文献检索：8-15 条参考文献（GB/T 7714-2015 格式）
2. 撰写 LaTeX 论文，章节包括：
   - 摘要（每问有数值结果）
   - 问题重述与分析
   - 模型假设
   - 符号说明
   - 模型建立与求解
   - 模型验证与灵敏度分析
   - 模型评价与改进
   - 参考文献
   - 附录（代码）
3. 去AI味检测：避免模板化表达
4. 编译论文：xelatex × 2，确保 0 Error

写作规范：
- 摘要每问必须有具体数值
- 结果分析每图≥3句话
- 模型对比≥2个模型
- 禁止复制原题
- 使用学术中文，避免口语化

输出：完整的 .tex 文件。""",
    Role.VERIFIER: """你是 UltraMath 的验算员（Verifier）。

你的职责：
1. 读取数学家的推导方案
2. 用不同的方法或工具重新计算关键数字
3. 对比结果，标注差异
4. 产出验证报告

验算原则：
- 信息不对称：不依赖数学家的中间计算
- 方法独立：使用不同的算法或工具
- 关注关键数字：最终结果、边界条件、约束验证

输出格式：
- 关键数字对比表
- 差异分析
- 结论（一致/不一致/需人工确认）""",
    Role.ONTOLOGY: """你是 UltraMath 的本体构造师（OntologyBuilder）。

你的职责：
1. 读取数学推导方案
2. 构建 problem-ontology.json，包括：
   - 问题定义
   - 集合与实体
   - 参数（含单位和量纲）
   - 约束条件（硬约束/软约束）
   - 目标函数
   - 数据规模估计
3. 检查约束完整性
4. 提取参数一致性
5. 补全遗漏项

输出：符合 ontology-schema.json 的 JSON 文件。""",
    Role.TESTER: """你是 UltraMath 的测试员（Tester）。

你的职责：
1. 遍历所有 .py 文件
2. 执行每个文件，收集成功/失败
3. 失败时分析错误原因
4. 通知工程师修复
5. 重测直到全部通过

测试方法：
- 语法检查 (py_compile)
- 运行测试 (python file.py)
- 变量一致性检查
- 参数传播检查

输出：测试报告，包含每个文件的状态。""",
}


class RoleManager:
    """角色管理器"""

    def __init__(self, prompts_dir: str | None = None):
        self.prompts_dir = Path(prompts_dir) if prompts_dir else None
        self._roles: dict[Role, RoleConfig] = {}
        self._load_roles()

    def _load_roles(self) -> None:
        """加载所有角色配置"""
        for role in Role:
            # 尝试从文件加载 prompt
            prompt = DEFAULT_PROMPTS.get(role, f"你是 UltraMath 的 {ROLE_NAMES[role]}。")

            if self.prompts_dir:
                # 尝试多种文件名
                possible_files = [
                    f"agent_{role.value}.md",
                    f"{role.value}.md",
                ]
                for filename in possible_files:
                    prompt_path = self.prompts_dir / filename
                    if prompt_path.exists():
                        with contextlib.suppress(Exception):
                            prompt = prompt_path.read_text(encoding="utf-8")
                        break

            self._roles[role] = RoleConfig(
                role=role,
                name=ROLE_NAMES.get(role, role.value),
                description=ROLE_DESCRIPTIONS.get(role, ""),
                system_prompt=prompt,
                temperature=ROLE_TEMPERATURES.get(role, 0.7),
                tools=ROLE_TOOLS.get(role, []),
            )

    def get_config(self, role: Role) -> RoleConfig:
        """获取角色配置"""
        return self._roles[role]

    def get_system_prompt(self, role: Role) -> str:
        """获取角色的 System Prompt"""
        return self._roles[role].system_prompt

    def get_temperature(self, role: Role) -> float:
        """获取角色的温度"""
        return self._roles[role].temperature

    def get_tools(self, role: Role) -> list[str]:
        """获取角色可用的工具"""
        return self._roles[role].tools

    def list_roles(self) -> list[dict]:
        """列出所有角色"""
        return [
            {
                "role": role.value,
                "name": config.name,
                "description": config.description,
                "temperature": config.temperature,
                "tools": config.tools,
            }
            for role, config in self._roles.items()
        ]
