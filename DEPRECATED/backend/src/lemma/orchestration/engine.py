"""主引擎 — 将所有组件组装为完整的 Agent"""

from __future__ import annotations

import asyncio
import contextlib
import json
from collections.abc import AsyncGenerator, Callable
from datetime import datetime
from pathlib import Path

from ..agent.role import ROLE_NAMES, Role, RoleManager
from ..llm.backend import LLMBackend
from ..llm.router import ModelRouter, TaskType
from ..memory.context import ContextManager
from ..memory.long_term import LongTermMemory
from ..memory.short_term import Message, ShortTermMemory
from ..tools.registry import ToolRegistry
from .state_machine import PHASE_NAMES, Phase, StateMachine
from ..engine.domain import PhaseResult


class UltraMathAgent:
    """UltraMath 自主智能体"""

    def __init__(
        self,
        work_dir: str,
        llm_router: ModelRouter,
        role_manager: RoleManager,
        tool_registry: ToolRegistry,
    ):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

        self.router = llm_router
        self.roles = role_manager
        self.tools = tool_registry

        self.memory = ShortTermMemory(max_tokens=128000)
        self.long_term = LongTermMemory(persist_dir=str(self.work_dir / "data" / "chromadb"))
        self.context = ContextManager(str(work_dir))

        self.state = StateMachine()
        self.current_role = Role.LEAD

        # 事件回调
        self._on_message: Callable | None = None
        self._on_phase_change: Callable | None = None
        self._on_tool_call: Callable | None = None

        # 取消标志
        self._cancel_event = asyncio.Event()

    def set_callbacks(
        self,
        on_message: Callable | None = None,
        on_phase_change: Callable | None = None,
        on_tool_call: Callable | None = None,
    ):
        """设置事件回调（用于 WebSocket 推送）"""
        self._on_message = on_message
        self._on_phase_change = on_phase_change
        self._on_tool_call = on_tool_call

    def cancel(self) -> None:
        """取消当前自动运行"""
        self._cancel_event.set()

    def reset_cancel(self) -> None:
        """重置取消标志"""
        self._cancel_event.clear()

    async def _emit(self, event: str, data: dict) -> None:
        """发送事件"""
        if event == "message" and self._on_message:
            await self._on_message(data)
        elif event == "phase_change" and self._on_phase_change:
            await self._on_phase_change(data)
        elif event == "tool_call" and self._on_tool_call:
            await self._on_tool_call(data)

    def _ensure_system_message(self) -> None:
        """确保有且仅有一个 system message"""
        system_prompt = self._build_system_prompt()
        has_system = any(m.role == "system" for m in self.memory.get_raw_messages())
        if not has_system:
            self.memory.add("system", system_prompt)
        else:
            raw = self.memory.get_raw_messages()
            for i in range(len(raw) - 1, -1, -1):
                if raw[i].role == "system":
                    raw[i].content = system_prompt
                    break

    def _get_backend_for_phase(self) -> LLMBackend:
        """根据当前阶段选择合适的 LLM 后端"""
        phase_task_map = {
            Phase.ANALYSIS: TaskType.MATH_REASONING,
            Phase.DERIVATION: TaskType.MATH_REASONING,
            Phase.ONTOLOGY: TaskType.ONTOLOGY,
            Phase.CODING: TaskType.CODE_GENERATION,
            Phase.TESTING: TaskType.CODE_GENERATION,
            Phase.WRITING: TaskType.PAPER_WRITING,
            Phase.REVIEW: TaskType.REVIEW,
        }
        task_type = phase_task_map.get(self.state.current_phase, TaskType.MATH_REASONING)
        return self.router.get_backend(task_type)

    # ==================== 核心对话接口 ====================

    async def chat(self, user_message: str, role: Role | None = None) -> str:
        """与 Agent 对话（非流式）"""
        if role:
            self.current_role = role

        self._ensure_system_message()
        self.memory.add("user", user_message)

        await self._emit(
            "message",
            {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat(),
            },
        )

        response_text = await self._generate_with_tools()

        self.memory.add("assistant", response_text)

        await self._emit(
            "message",
            {
                "role": "assistant",
                "content": response_text,
                "agent_role": self.current_role.value,
                "agent_name": ROLE_NAMES.get(self.current_role, ""),
                "timestamp": datetime.now().isoformat(),
            },
        )

        return response_text

    async def chat_stream(
        self, user_message: str, role: Role | None = None
    ) -> AsyncGenerator[str, None]:
        """与 Agent 对话（流式），支持工具调用"""
        if role:
            self.current_role = role

        self._ensure_system_message()
        self.memory.add("user", user_message)

        await self._emit(
            "message",
            {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat(),
            },
        )

        backend = self._get_backend_for_phase()
        messages = self.memory.get_messages()
        tools = self.tools.to_openai_tools()

        full_response = ""
        tool_rounds = 0
        max_tool_rounds = 10

        while tool_rounds < max_tool_rounds:
            tool_calls_found = False
            round_content = ""
            tool_calls_buffer: list[dict] = []

            async for chunk_data in backend.generate_stream(
                messages=messages,
                tools=tools if tools else None,
            ):
                if isinstance(chunk_data, dict) and chunk_data.get("type") == "tool_calls":
                    tool_calls_found = True
                    tool_calls_buffer.extend(chunk_data.get("calls", []))
                elif isinstance(chunk_data, str):
                    round_content += chunk_data
                    full_response += chunk_data
                    yield chunk_data

            if not tool_calls_found:
                break

            # 执行工具调用
            tool_rounds += 1
            if round_content:
                messages.append({"role": "assistant", "content": round_content})

            for tc in tool_calls_buffer:
                tool_name = tc["name"]
                try:
                    args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except json.JSONDecodeError:
                    args = {}

                await self._emit(
                    "tool_call",
                    {
                        "name": tool_name,
                        "arguments": args,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                result = await self.tools.execute(tool_name, **args)

                await self._emit(
                    "tool_call",
                    {
                        "name": tool_name,
                        "result": result.to_display(),
                        "success": result.success,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                tool_msg = {
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "content": result.to_display(),
                }
                messages.append(tool_msg)
                yield f"\n\n🔧 {tool_name}: {'✅' if result.success else '❌'}\n"

        self.memory.add("assistant", full_response)

        await self._emit(
            "message",
            {
                "role": "assistant",
                "content": full_response,
                "agent_role": self.current_role.value,
                "agent_name": ROLE_NAMES.get(self.current_role, ""),
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def _generate_with_tools(self) -> str:
        """带工具调用的生成"""
        backend = self._get_backend_for_phase()
        messages = self.memory.get_messages()
        tools = self.tools.to_openai_tools()

        max_rounds = 10
        full_response = ""

        for _ in range(max_rounds):
            response = await backend.generate(
                messages=messages,
                tools=tools if tools else None,
            )

            if response.content:
                full_response += response.content

            if not response.tool_calls:
                break

            # 处理工具调用
            assistant_msg = Message(
                role="assistant",
                content=response.content or "",
                tool_calls=response.tool_calls,
            )
            messages.append(assistant_msg.to_dict())

            for tc in response.tool_calls:
                tool_name = tc["name"]
                try:
                    args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except json.JSONDecodeError:
                    args = {}

                await self._emit(
                    "tool_call",
                    {
                        "name": tool_name,
                        "arguments": args,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                result = await self.tools.execute(tool_name, **args)

                await self._emit(
                    "tool_call",
                    {
                        "name": tool_name,
                        "result": result.to_display(),
                        "success": result.success,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                tool_msg = {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result.to_display(),
                }
                messages.append(tool_msg)

        return full_response or "(无响应)"

    # ==================== 自动执行流程 ====================

    async def run_auto(self, problem_text: str = "") -> AsyncGenerator[dict, None]:
        """自动执行完整的求解流程（流式输出进度）"""
        self.reset_cancel()
        yield {"type": "start", "message": "🚀 UltraMath Agent 开始执行"}

        max_retries = 3
        phase_retries: dict[Phase, int] = {}

        while not self.state.is_done:
            # 检查取消
            if self._cancel_event.is_set():
                yield {"type": "cancelled", "message": "用户取消了自动运行"}
                return

            phase = self.state.current_phase
            phase_name = PHASE_NAMES.get(phase, "未知")

            # 无限循环防护
            retries = phase_retries.get(phase, 0)
            if retries >= max_retries:
                yield {
                    "type": "phase_error",
                    "phase": phase.value,
                    "name": phase_name,
                    "error": f"阶段 {phase_name} 已重试 {max_retries} 次，跳过",
                }
                self.state.transition(PhaseResult(phase=phase, success=True, summary="跳过"))
                continue

            yield {"type": "phase_start", "phase": phase.value, "name": phase_name}

            try:
                result = await self._execute_phase(phase, problem_text)

                # 阶段输出验证
                if result.success:
                    valid, error_msg = self._validate_phase_output(phase)
                    if not valid:
                        result = PhaseResult(
                            phase=phase,
                            success=False,
                            summary=f"验证失败: {error_msg}",
                        )

                if not result.success:
                    phase_retries[phase] = phase_retries.get(phase, 0) + 1

                self.state.transition(result)

                self.context.update_phase(
                    phase.value,
                    phase_name=phase_name,
                    status="completed" if result.success else "failed",
                    summary=result.summary,
                )

                yield {
                    "type": "phase_end",
                    "phase": phase.value,
                    "name": phase_name,
                    "success": result.success,
                    "summary": result.summary,
                    "progress": self.state.progress,
                }
            except Exception as e:
                phase_retries[phase] = phase_retries.get(phase, 0) + 1
                yield {
                    "type": "phase_error",
                    "phase": phase.value,
                    "name": phase_name,
                    "error": str(e),
                }
                self.state.transition(PhaseResult(phase=phase, success=False, summary=f"错误: {e}"))

        yield {
            "type": "complete",
            "message": "✅ 所有阶段执行完成",
            "progress": 100,
        }

    def _validate_phase_output(self, phase: Phase) -> tuple[bool, str]:
        """验证阶段产出物"""
        validators = {
            Phase.ONTOLOGY: self._validate_ontology,
            Phase.CODING: self._validate_coding,
            Phase.WRITING: self._validate_writing,
        }
        validator = validators.get(phase)
        if validator:
            return validator()
        return True, ""

    def _validate_ontology(self) -> tuple[bool, str]:
        """验证本体论输出为有效 JSON"""
        ontology_path = self.work_dir / "求解" / "problem-ontology.json"
        if not ontology_path.exists():
            return False, "problem-ontology.json 未生成"
        try:
            json.loads(ontology_path.read_text(encoding="utf-8"))
            return True, ""
        except json.JSONDecodeError as e:
            return False, f"problem-ontology.json 格式错误: {e}"

    def _validate_coding(self) -> tuple[bool, str]:
        """验证代码文件已生成"""
        solution_dir = self.work_dir / "求解"
        if not solution_dir.exists():
            return False, "求解目录不存在"
        py_files = list(solution_dir.glob("*.py"))
        if not py_files:
            return False, "求解目录中没有 Python 文件"
        return True, ""

    def _validate_writing(self) -> tuple[bool, str]:
        """验证论文文件已生成"""
        paper_dir = self.work_dir / "论文"
        if not paper_dir.exists():
            return False, "论文目录不存在"
        tex_files = list(paper_dir.glob("*.tex"))
        if not tex_files:
            return False, "论文目录中没有 TeX 文件"
        return True, ""

    async def _execute_phase(self, phase: Phase, problem_text: str = "") -> PhaseResult:
        """执行单个阶段，并在关键阶段自动触发反思改进"""
        phase_handlers = {
            Phase.INIT: self._phase_init,
            Phase.ANALYSIS: lambda: self._phase_analysis(problem_text),
            Phase.DERIVATION: self._phase_derivation,
            Phase.ONTOLOGY: self._phase_ontology,
            Phase.CODING: self._phase_coding,
            Phase.TESTING: self._phase_testing,
            Phase.WRITING: self._phase_writing,
            Phase.REVIEW: self._phase_review,
        }
        handler = phase_handlers.get(phase)
        if handler:
            result = await handler()
        else:
            result = PhaseResult(phase=phase, success=True, summary="跳过")

        # 对关键阶段自动触发反思改进（仅在成功时）
        REFLECTIVE_PHASES = {Phase.DERIVATION, Phase.WRITING, Phase.REVIEW}
        if phase in REFLECTIVE_PHASES and result.success:
            try:
                from ..engine.reflector import SelfReflector
                reflector = SelfReflector(self)
                improved = await reflector.reflect_and_improve(
                    result.summary,
                    criteria=None,
                    max_iterations=1,
                )
                if len(improved) > len(result.summary) * 0.8:
                    result.summary = improved
                    logger.info(f"Phase {phase.value}: 反思改进完成")
            except Exception as e:
                logger.warning(f"Phase {phase.value} 反思跳过: {e}")

        return result

    async def _phase_init(self, problem_text: str) -> PhaseResult:
        """Phase 0: 初始化"""
        problem_dir = self.work_dir / "题目"
        if problem_dir.exists():
            files = list(problem_dir.glob("*"))
            if files:
                problem_text = ""
                for f in files:
                    with contextlib.suppress(Exception):
                        problem_text += f.read_text(encoding="utf-8") + "\n"

        if not problem_text:
            return PhaseResult(
                phase=Phase.INIT,
                success=False,
                summary="未找到题目文件。请将题目放入 题目/ 目录。",
            )

        self.memory.add("system", f"以下是待求解的数学建模竞赛题目：\n\n{problem_text[:10000]}")
        return PhaseResult(
            phase=Phase.INIT,
            success=True,
            summary=f"已读取题目 ({len(problem_text)} 字符)",
        )

    async def _phase_analysis(self, problem_text: str) -> PhaseResult:
        """Phase 1: 题目分析"""
        response = await self.chat(
            "请分析这个数学建模竞赛题目。判断题目类型（优化/预测/评价/图论/机理分析），"
            "列出需要求解的子问题，初步评估难度，并建议适用的数学方法。",
            role=Role.LEAD,
        )
        return PhaseResult(phase=Phase.ANALYSIS, success=True, summary=response[:500])

    async def _phase_derivation(self) -> PhaseResult:
        """Phase 2: 数学推导"""
        response = await self.chat(
            "请作为数学家，对这个题目进行完整的数学推导。"
            "生成3个不同的建模方案，评估每个方案的优劣，选择最优方案进行详细推导。"
            "输出包括：假设、符号定义、目标函数、约束条件、求解算法。",
            role=Role.MATH,
        )
        deriv_file = self.work_dir / "求解" / "推导结果.md"
        deriv_file.parent.mkdir(parents=True, exist_ok=True)
        deriv_file.write_text(response, encoding="utf-8")
        return PhaseResult(
            phase=Phase.DERIVATION,
            success=True,
            summary=response[:500],
            artifacts={"推导结果": str(deriv_file)},
        )

    async def _phase_ontology(self) -> PhaseResult:
        """Phase 3: 本体构造"""
        response = await self.chat(
            "请基于前面的数学推导，构建问题本体。输出 JSON 格式，包括："
            "问题定义、集合与实体、参数（含单位和量纲）、约束条件、目标函数。",
            role=Role.ONTOLOGY,
        )
        ontology_file = self.work_dir / "求解" / "problem-ontology.json"
        ontology_file.write_text(response, encoding="utf-8")
        return PhaseResult(
            phase=Phase.ONTOLOGY,
            success=True,
            summary="本体构造完成",
            artifacts={"ontology": str(ontology_file)},
        )

    async def _phase_coding(self) -> PhaseResult:
        """Phase 4: 代码实现"""
        response = await self.chat(
            "请作为工程师，基于数学推导编写 Python 求解代码。要求：\n"
            "1. 为每个子问题创建独立的求解脚本\n"
            "2. 包含完整的数值计算和结果输出\n"
            "3. 生成出版级质量的图表\n"
            "4. 输出 CSV 结果文件\n"
            "请将代码保存到 求解/ 目录。",
            role=Role.ENGINEER,
        )
        return PhaseResult(phase=Phase.CODING, success=True, summary=response[:500])

    async def _phase_testing(self) -> PhaseResult:
        """Phase 5: 测试验证"""
        py_files = list(self.work_dir.glob("求解/**/*.py"))
        if not py_files:
            return PhaseResult(
                phase=Phase.TESTING,
                success=True,
                summary="未找到需要测试的 Python 文件",
            )

        issues = []
        for py_file in py_files:
            result = await self.tools.execute(
                "code_executor",
                filename=str(py_file.relative_to(self.work_dir)),
            )
            if not result.success:
                issues.append(f"{py_file.name}: {result.error}")

        if issues:
            return PhaseResult(
                phase=Phase.TESTING,
                success=False,
                summary=f"测试发现 {len(issues)} 个问题",
                issues=issues,
            )

        return PhaseResult(
            phase=Phase.TESTING,
            success=True,
            summary=f"所有 {len(py_files)} 个文件测试通过",
        )

    async def _phase_writing(self) -> PhaseResult:
        """Phase 6: 论文写作"""
        response = await self.chat(
            "请作为作家，撰写完整的 LaTeX 论文。要求：\n"
            "1. 摘要每问有具体数值结果\n"
            "2. 完整的章节结构\n"
            "3. 引用求解目录中的图表\n"
            "4. 保存到 论文/ 目录",
            role=Role.WRITER,
        )
        return PhaseResult(phase=Phase.WRITING, success=True, summary=response[:500])

    async def _phase_review(self) -> PhaseResult:
        """Phase 7: 交叉审稿"""
        response = await self.chat(
            "请作为审稿人，对整个项目进行五维度评分卡审稿。检查：\n"
            "1. 数学推导的严谨性\n"
            "2. 代码的可复现性\n"
            "3. 论文的叙事质量\n"
            "4. 图表的专业性\n"
            "5. 创造性\n\n"
            "给出评分和具体修改建议。如有阻断项（B1-B4），标注出来。",
            role=Role.REVIEWER,
        )
        review_file = self.work_dir / "审稿结果.md"
        review_file.write_text(response, encoding="utf-8")
        return PhaseResult(
            phase=Phase.REVIEW,
            success=True,
            summary=response[:500],
            artifacts={"审稿结果": str(review_file)},
        )

    # ==================== 辅助方法 ====================

    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        role_config = self.roles.get_config(self.current_role)
        context_info = self.context.get_all_summaries()

        parts = [
            role_config.system_prompt,
            f"\n\n## 当前角色: {role_config.name}",
            f"## 工作目录: {self.work_dir}",
        ]

        if context_info and "尚无" not in context_info:
            parts.append(f"\n## 已完成的工作:\n{context_info}")

        return "\n".join(parts)

    def switch_role(self, role: Role) -> None:
        """切换角色"""
        self.current_role = role

    def get_status(self) -> dict:
        """获取当前状态"""
        return {
            "state": self.state.to_dict(),
            "current_role": self.current_role.value,
            "current_role_name": ROLE_NAMES.get(self.current_role, ""),
            "memory_tokens": self.memory.get_token_count(),
            "memory_messages": self.memory.length,
            "tools": self.tools.tool_names,
            "context": self.context.get_all_summaries(),
        }

    def reset(self) -> None:
        """重置 Agent"""
        self.memory.clear(keep_system=False)
        self.state = StateMachine()
        self.current_role = Role.LEAD
        self.context = ContextManager(str(self.work_dir))
        self.reset_cancel()
