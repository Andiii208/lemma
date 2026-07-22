"""AcademicAgent — 领域无关的通用学术写作引擎"""
from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator, Callable
from datetime import datetime
from pathlib import Path

from ..llm.backend import LLMBackend
from ..llm.cost_tracker import CostTracker
from ..llm.router import ModelRouter, TaskType
from ..memory.context import ContextManager
from ..memory.long_term import LongTermMemory
from ..memory.short_term import Message, ShortTermMemory
from ..observability.tracer import trace_span, start_trace, finish_trace
from ..orchestration.state_machine import StateMachine
from ..tools.registry import ToolRegistry
from .checkpoint import RunCheckpoint, create_checkpoint_from_phases
from .domain import DomainProfile, PhaseResult, RoleConfig
from .handoff import parse_handoff_from_text
from .isolation import FileVisibility
from .trust import TrustManager


class AcademicAgent:
    """通用学术写作 Agent — 由 DomainProfile 驱动所有领域特定行为"""

    # 阶段 → 任务类型映射（可根据领域重写）
    DEFAULT_PHASE_TASK_MAP: dict[str, TaskType] = {}

    def __init__(
        self,
        work_dir: str,
        domain: DomainProfile,
        llm_router: ModelRouter,
        tool_registry: ToolRegistry,
    ):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.domain = domain
        self.router = llm_router
        self.tools = tool_registry

        self.memory = ShortTermMemory(max_tokens=128000)
        self.long_term = LongTermMemory(persist_dir=str(self.work_dir / "data" / "chromadb"))
        self.context = ContextManager(str(work_dir))

        self.state = StateMachine(profile=domain)
        self.current_role_id = domain.roles[0].id if domain.roles else "lead"

        # 事件回调
        self._on_message: Callable | None = None
        self._on_phase_change: Callable | None = None
        self._on_tool_call: Callable | None = None

        # 取消标志
        self._cancel_event = asyncio.Event()

        # 根据 domain.directories 创建必要目录
        for dir_name in domain.directories.values():
            (self.work_dir / dir_name).mkdir(parents=True, exist_ok=True)

        # 阶段 → 任务类型映射
        self._phase_task_map: dict[str, TaskType] = dict(self.DEFAULT_PHASE_TASK_MAP)

        # 信赖系统
        self.trust = TrustManager(str(self.work_dir / "trust.json"))

        # 文件可见性（信息不对称）
        isolation_rules: dict[str, list[str]] = {}
        self.file_visibility = FileVisibility(self.work_dir, self.current_role_id, isolation_rules)

        # 确认等待
        self._confirm_event = asyncio.Event()

        # 阶段超时（默认 5 分钟）
        self.phase_timeout_seconds: int = 300

        # 成本追踪
        self.cost_tracker = CostTracker(str(self.work_dir))

        # 自我反思器（后续接入）
        from .reflector import SelfReflector
        self.reflector = SelfReflector(self)

    # ========== 回调 & 生命周期 ==========

    def set_callbacks(
        self,
        on_message: Callable | None = None,
        on_phase_change: Callable | None = None,
        on_tool_call: Callable | None = None,
    ) -> None:
        self._on_message = on_message
        self._on_phase_change = on_phase_change
        self._on_tool_call = on_tool_call

    def cancel(self) -> None:
        self._cancel_event.set()

    def reset_cancel(self) -> None:
        self._cancel_event.clear()

    def confirm(self, accepted: bool = True, phase_id: str | None = None) -> None:
        """用户确认/拒绝当前阶段"""
        self.trust.record(phase_id or self.state.current_phase, accepted=accepted)
        self._confirm_event.set()

    async def _wait_confirmation(self) -> None:
        """等待用户确认"""
        self._confirm_event.clear()
        await self._confirm_event.wait()

    async def _emit(self, event: str, data: dict) -> None:
        if event == "message" and self._on_message:
            await self._on_message(data)
        elif event == "phase_change" and self._on_phase_change:
            await self._on_phase_change(data)
        elif event == "tool_call" and self._on_tool_call:
            await self._on_tool_call(data)

    # ========== 角色管理 ==========

    def switch_role(self, role_id: str) -> None:
        if self.domain.get_role_by_id(role_id):
            self.current_role_id = role_id
            # 更新文件可见性
            self.file_visibility = FileVisibility(self.work_dir, role_id, {})

    def get_current_role(self) -> RoleConfig | None:
        return self.domain.get_role_by_id(self.current_role_id)

    # ========== 系统提示 ==========

    def _build_system_prompt(self) -> str:
        role = self.get_current_role()
        if not role:
            return "You are an academic assistant."

        context_info = self.context.get_all_summaries()
        parts = [
            f"## 领域: {self.domain.name}",
            role.system_prompt,
            f"\n\n## 当前角色: {role.name}",
            f"## 工作目录: {self.work_dir}",
        ]
        if context_info and "暂无" not in context_info:
            parts.append(f"\n## 已完成的工作:\n{context_info}")

        # RAG 知识检索：基于最近用户消息查询领域知识库
        last_user_msg = self._get_last_user_message()
        if last_user_msg:
            knowledge_chunks = self._retrieve_knowledge(last_user_msg)
            if knowledge_chunks:
                parts.append("\n## 领域知识参考\n" + "\n---\n".join(knowledge_chunks))

        return "\n".join(parts)

    def _get_last_user_message(self) -> str | None:
        """获取最近一条用户消息"""
        raw = self.memory.get_raw_messages()
        for msg in reversed(raw):
            if msg.role == "user":
                return msg.content
        return None

    def _retrieve_knowledge(self, query: str, top_k: int = 3) -> list[str]:
        """从 LongTermMemory 检索相关知识片段"""
        if not hasattr(self, 'long_term') or not self.long_term:
            return []

        results = []
        for collection in ["knowledge_models", "knowledge_references", "knowledge_reviews"]:
            try:
                hits = self.long_term.query(collection, query, n_results=top_k)
                for hit in hits:
                    content = hit.get("content", "")
                    if content and len(content) > 30:
                        results.append(content[:800])
            except Exception:
                pass
        return results[:top_k]

    def _ensure_system_message(self) -> None:
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

    # ========== LLM 后端选择 ==========

    # 自适应参数映射 — 根据阶段自动调整 temperature 和 max_tokens
    PHASE_TEMPERATURE_MAP: dict[str, float] = {
        "analysis": 0.7,   # 分析阶段需要创造性
        "derivation": 0.5,  # 推导需要严谨
        "coding": 0.3,      # 编码需要精确
        "writing": 0.6,     # 写作需要流畅
        "review": 0.4,      # 审稿需要批判性
    }

    PHASE_MAX_TOKENS_MAP: dict[str, int] = {
        "analysis": 4096,
        "derivation": 8192,
        "coding": 16384,
        "writing": 16384,
        "review": 4096,
    }

    def _get_backend(self) -> LLMBackend:
        return self.router.get_default_backend()

    def _get_backend_for_phase(self) -> LLMBackend:
        task_type = self._phase_task_map.get(self.state.current_phase)
        if task_type:
            return self.router.get_backend(task_type)
        return self.router.get_default_backend()

    def _apply_phase_params(self, backend: LLMBackend) -> None:
        """根据当前阶段自适应调整参数"""
        phase = self.state.current_phase
        if phase in self.PHASE_TEMPERATURE_MAP:
            backend.config.temperature = self.PHASE_TEMPERATURE_MAP[phase]
        if phase in self.PHASE_MAX_TOKENS_MAP:
            backend.config.max_tokens = self.PHASE_MAX_TOKENS_MAP[phase]

    # ========== 对话接口 ==========

    @trace_span("chat")
    async def chat(self, user_message: str) -> str:
        """与 Agent 对话（非流式），自动解析交接表"""
        self._ensure_system_message()
        self.memory.add("user", user_message)

        await self._emit("message", {
            "role": "user", "content": user_message,
            "timestamp": datetime.now().isoformat(),
        })

        response_text = await self._generate_with_tools()
        self.memory.add("assistant", response_text)

        # 尝试解析交接表并存入上下文
        handoff = parse_handoff_from_text(response_text)
        if handoff:
            self.context.update_phase(
                self.state.current_phase,
                phase_name=self.state.phase_name,
                summary=handoff.conclusion,
            )

        role = self.get_current_role()
        await self._emit("message", {
            "role": "assistant", "content": response_text,
            "agent_role": self.current_role_id,
            "agent_name": role.name if role else "",
            "timestamp": datetime.now().isoformat(),
        })
        return response_text

    async def _generate_with_tools(self) -> str:
        """带工具调用的生成（最多 10 轮工具调用）"""
        backend = self._get_backend()
        self._apply_phase_params(backend)
        tools = self.tools.to_openai_tools()
        max_rounds = 10
        full_response = ""

        for _ in range(max_rounds):
            messages = self.memory.get_messages()  # 每轮重新获取最新消息
            response = await backend.generate(
                messages=messages, tools=tools if tools else None,
            )
            if response.content:
                full_response += response.content
            if not response.tool_calls:
                break

            # 将 assistant 消息写入 memory
            assistant_msg = Message(
                role="assistant", content=response.content or "",
                tool_calls=response.tool_calls,
            )
            self.memory.add_message(assistant_msg)

            for tc in response.tool_calls:
                tool_name = tc["name"]
                try:
                    args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except json.JSONDecodeError:
                    args = {}

                await self._emit("tool_call", {
                    "name": tool_name, "arguments": args,
                    "timestamp": datetime.now().isoformat(),
                })

                result = await self.tools.execute(tool_name, **args)

                await self._emit("tool_call", {
                    "name": tool_name,
                    "result": result.to_display(),
                    "success": result.success,
                    "timestamp": datetime.now().isoformat(),
                })

                # 将工具结果写入 memory
                self.memory.add("tool", result.to_display(), tool_call_id=tc["id"])

        return full_response or "(无响应)"

    # ========== 自动执行流程 ==========

    async def run_auto(self, input_text: str = "") -> AsyncGenerator[dict, None]:
        """自动执行完整的领域求解流程（流式输出进度）
        
        支持递归分解：使用栈管理待处理问题。Agent 可以通过输出分解表来请求拆分子问题。
        """
        self.reset_cancel()
        _trace = start_trace(f"run_auto:{self.domain.id}")
        yield {"type": "start", "message": f"🚀 {self.domain.name} 开始执行", "domain": self.domain.id}

        max_retries = 3
        phase_retries: dict[str, int] = {}
        max_depth = 5

        # 初始化栈：(phase_id, input_text, depth)
        phase_ids = self.domain.get_phase_ids()
        problem_stack: list[tuple[str, str, int]] = []
        for pid in phase_ids:
            if pid not in ("idle", "done"):
                problem_stack.append((pid, input_text, 0))

        # 创建检查点
        active_phases = [pid for pid in phase_ids if pid not in ("idle", "done")]
        checkpoint = create_checkpoint_from_phases(
            domain_id=self.domain.id,
            input_text=input_text[:2000],
            phase_ids=active_phases,
        )

        while problem_stack:
            if self._cancel_event.is_set():
                yield {"type": "cancelled", "message": "用户取消了自动运行"}
                return

            phase_id, problem_text, depth = problem_stack.pop(0)

            if depth >= max_depth:
                yield {
                    "type": "phase_skip", "phase": phase_id,
                    "reason": f"超过最大递归深度 {max_depth}",
                }
                continue

            phase_cfg = self.domain.get_phase_by_id(phase_id)
            if not phase_cfg:
                continue

            yield {
                "type": "phase_start",
                "phase": phase_id, "name": phase_cfg.name,
                "depth": depth,
            }

            try:
                result = await self._execute_phase(phase_id, problem_text)

                # 检查是否请求分解
                decompose = result.metadata.get("decompose", [])
                if decompose:
                    for sub in reversed(decompose):
                        problem_stack.insert(0, (sub["phase"], sub["question"], depth + 1))
                    yield {
                        "type": "decomposed", "phase": phase_id,
                        "name": phase_cfg.name,
                        "sub_problems": len(decompose),
                    }
                    continue

                # 验证
                if result.success:
                    for validator in self.domain.validators:
                        if validator.phase == phase_id:
                            valid, msg = self._run_validator(validator)
                            if not valid:
                                result = PhaseResult(
                                    phase_id=phase_id, success=False,
                                    summary=f"验证失败: {msg}",
                                )
                                break

                if not result.success:
                    phase_retries[phase_id] = phase_retries.get(phase_id, 0) + 1
                    if phase_retries.get(phase_id, 0) >= max_retries:
                        yield {
                            "type": "phase_skip", "phase": phase_id,
                            "name": phase_cfg.name,
                            "reason": f"重试 {max_retries} 次失败，跳过",
                        }
                        continue

                self.state.transition(PhaseResult(
                    phase_id=phase_id, success=result.success,
                    summary=result.summary,
                ))
                self.context.update_phase(
                    phase_id, phase_name=phase_cfg.name,
                    status="completed" if result.success else "failed",
                    summary=result.summary,
                )

                # 更新检查点
                for cp in checkpoint.phases:
                    if cp.phase_id == phase_id:
                        cp.status = "completed" if result.success else "failed"
                        cp.summary = result.summary[:200]
                        cp.completed_at = datetime.now().isoformat()
                        break
                checkpoint.save(str(self.work_dir / "checkpoint.json"))

                yield {
                    "type": "phase_end", "phase": phase_id, "name": phase_cfg.name,
                    "success": result.success, "summary": result.summary,
                    "progress": self.state.progress,
                }
            except Exception as e:
                phase_retries[phase_id] = phase_retries.get(phase_id, 0) + 1
                yield {
                    "type": "phase_error", "phase": phase_id, "name": phase_cfg.name,
                    "error": str(e),
                }

        # 到达 done 阶段
        checkpoint.status = "completed"
        checkpoint.save(str(self.work_dir / "checkpoint.json"))
        finish_trace(_trace)
        yield {"type": "complete", "message": "✅ 所有阶段执行完成", "progress": 100}

    @trace_span("execute_phase")
    async def _execute_phase(self, phase_id: str, input_text: str = "") -> PhaseResult:
        """执行单个阶段 — 使用 domain.phase_handlers 中的 prompt 模板
        
        支持递归分解：如果 LLM 响应中包含 [DECOMPOSE] 标记，则解析为子问题。
        """
        phase_cfg = self.domain.get_phase_by_id(phase_id)
        if not phase_cfg:
            return PhaseResult(phase_id=phase_id, success=True, summary="无处理程序")

        template = self.domain.phase_handlers.get(phase_id)
        if not template:
            return PhaseResult(phase_id=phase_id, success=True, summary=f"阶段 {phase_cfg.name} 跳过")

        prompt = template.format(
            input_text=input_text[:10000],
            context_sections=self.context.get_all_summaries() or "",
            output_dir=self.domain.directories.get("output", "output"),
            paper_dir=self.domain.directories.get("paper", "paper"),
        )

        try:
            response = await asyncio.wait_for(
                self.chat(prompt),
                timeout=self.phase_timeout_seconds,
            )

            # 检查是否包含分解请求
            if "[DECOMPOSE]" in response:
                decompose_list = self._parse_decompose(response)
                if decompose_list:
                    metadata = {"decompose": decompose_list}
                    return PhaseResult(
                        phase_id=phase_id, success=True,
                        summary=f"已分解为 {len(decompose_list)} 个子问题",
                        metadata=metadata,
                    )

            # 自我反思：对输出进行轻量检查
            try:
                response = await self.reflector.quick_reflect(response)
            except Exception:
                pass  # 反思失败不影响主流程

            return PhaseResult(phase_id=phase_id, success=True, summary=response[:500])
        except asyncio.TimeoutError:
            return PhaseResult(
                phase_id=phase_id, success=False,
                summary=f"阶段超时（{self.phase_timeout_seconds}秒）",
            )

    @staticmethod
    def _parse_decompose(text: str) -> list[dict]:
        """解析 [DECOMPOSE] 标记，提取子问题列表
        
        [DECOMPOSE]
        - sub_phase: analysis
          question: 这个问题的核心假设是什么？
        - sub_phase: derivation
          question: 哪个求解方案更适合？
        [/DECOMPOSE]
        """
        import re
        
        decompose_list: list[dict] = []
        if "[DECOMPOSE]" not in text:
            return decompose_list
        
        start = text.find("[DECOMPOSE]")
        end = text.find("[/DECOMPOSE]")
        if end == -1:
            return decompose_list
        
        block = text[start + len("[DECOMPOSE]"):end].strip()
        
        # 解析每个子问题
        items = re.split(r'(?=^-\s+)', block, flags=re.MULTILINE)
        for item in items:
            if not item.strip() or not item.startswith("-"):
                continue
            phase_match = re.search(r'sub_phase[:\s]+(\S+)', item)
            question_match = re.search(r'question[:\s]+(.+)', item)
            if phase_match:
                ph = phase_match.group(1)
                qs = question_match.group(1).strip() if question_match else ""
                decompose_list.append({"phase": ph, "question": qs})
        
        return decompose_list

    def _run_validator(self, v_cfg) -> tuple[bool, str]:
        """运行验证器"""
        output_dir = self.domain.directories.get("output", "output")
        paper_dir = self.domain.directories.get("paper", "paper")
        path_str = v_cfg.path.format(output_dir=output_dir, paper_dir=paper_dir)
        target = self.work_dir / path_str

        if v_cfg.check == "json":
            if not target.exists():
                return False, f"{target.name} 未生成"
            try:
                json.loads(target.read_text(encoding="utf-8"))
                return True, ""
            except json.JSONDecodeError as e:
                return False, f"JSON 格式错误: {e}"
        elif v_cfg.check == "files_exist":
            glob_str = v_cfg.glob.format(output_dir=output_dir, paper_dir=paper_dir)
            matched = list(self.work_dir.glob(glob_str))
            if not matched:
                return False, f"未生成匹配 {glob_str} 的文件"
            return True, ""
        return True, ""

    # ========== 工具方法 ==========

    def get_status(self) -> dict:
        role = self.get_current_role()
        return {
            "state": self.state.to_dict(),
            "current_role": self.current_role_id,
            "current_role_name": role.name if role else "",
            "memory_tokens": self.memory.get_token_count(),
            "memory_messages": self.memory.length,
            "tools": self.tools.tool_names,
            "context": self.context.get_all_summaries(),
        }

    def reset(self) -> None:
        self.memory.clear(keep_system=False)
        self.state = StateMachine(profile=self.domain)
        self.current_role_id = self.domain.roles[0].id if self.domain.roles else "lead"
        self.context = ContextManager(str(self.work_dir))
        self.reset_cancel()
