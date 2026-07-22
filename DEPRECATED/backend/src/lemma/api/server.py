"""FastAPI 服务器 — 前后端通信桥梁"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import contextlib

from ..agent.role import RoleManager
from ..engine.agent import AcademicAgent
from ..engine.domain import DomainProfile
from ..llm.backend import LLMConfig
from ..llm.router import ModelRouter
from ..tools.code_executor import CodeExecutorTool
from ..tools.data_analyzer import DataAnalyzerTool
from ..tools.equation_solver import EquationSolverTool
from ..tools.evidence_map import EvidenceMapTool
from ..tools.figure_generator import FigureGeneratorTool
from ..tools.file_manager import FileManagerTool
from ..tools.latex_compiler import LatexCompilerTool
from ..tools.quality_checker import QualityCheckerTool
from ..tools.registry import ToolRegistry
from ..tools.source_tracker import SourceTrackerTool
from ..utils.logger import setup_logging
from .auth import verify_api_key

setup_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("lemma.api")


def _get_domains_base() -> Path:
    """解析 domains 目录路径，兼容开发模式和 PyInstaller 打包模式。"""
    # 优先使用环境变量
    env_path = os.getenv("LEMMA_DOMAINS_PATH")
    if env_path:
        return Path(env_path)
    # PyInstaller 打包后 sys._MEIPASS 指向解压临时目录
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        meipass = Path(sys._MEIPASS)
        if (meipass / "domains").exists():
            return meipass / "domains"
        # 回退：resourcesPath 下的 domains（Electron extraResources）
        if hasattr(sys, 'executable'):
            exe_dir = Path(sys.executable).parent.parent  # app.asar/backend/ → app.asar/
            if (exe_dir / "domains").exists():
                return exe_dir / "domains"
    # 开发模式
    return Path(__file__).parent.parent.parent.parent / "domains"

# ==================== 数据模型 ====================


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=100000)
    role: str = Field(default="lead", max_length=50)


class ConfigRequest(BaseModel):
    provider: str = Field(default="openai", max_length=50)
    model: str = Field(default="gpt-4o", max_length=100)
    api_key: str = Field(default="", max_length=500)
    base_url: str = Field(default="https://api.openai.com/v1", max_length=500)
    max_tokens: int = Field(default=4096, ge=256, le=131072)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class ProjectRequest(BaseModel):
    work_dir: str = Field(..., min_length=1, max_length=1000)


class AutoRunRequest(BaseModel):
    work_dir: str = Field(..., min_length=1, max_length=1000)
    problem_text: str = Field(default="", max_length=500000)


# ==================== 全局状态 ====================

app = FastAPI(title="Lemma", version="5.2.0")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器 — 防止未捕获异常导致 500 无信息"""
    logger.error(f"Unhandled error on {request.url}: {exc}", exc_info=True)
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": f"内部服务器错误: {type(exc).__name__}: {str(exc)}"},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "file://"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局 Agent 实例（用锁保护并发访问）
_agent: AcademicAgent | None = None
_agent_lock = asyncio.Lock()
_role_manager: RoleManager | None = None
_ws_connections: list[WebSocket] = []
_ws_lock = asyncio.Lock()


def get_role_manager() -> RoleManager:
    global _role_manager
    if _role_manager is None:
        prompts_dir = str(Path(__file__).parent.parent / "agent" / "prompts")
        _role_manager = RoleManager(prompts_dir)
    return _role_manager


def _validate_work_dir(work_dir: str) -> Path:
    """验证并规范化工作目录"""
    p = Path(work_dir).resolve()
    if not p.exists():
        raise HTTPException(status_code=400, detail=f"目录不存在: {work_dir}")
    if not p.is_dir():
        raise HTTPException(status_code=400, detail=f"不是目录: {work_dir}")
    return p


def _safe_resolve(base: Path, user_path: str) -> Path:
    """安全解析路径，防止路径遍历"""
    if not user_path:
        return base
    if Path(user_path).is_absolute():
        raise HTTPException(status_code=400, detail="不允许绝对路径")
    resolved = (base / user_path).resolve()
    if not str(resolved).startswith(str(base.resolve())):
        raise HTTPException(status_code=403, detail="路径越界")
    return resolved


def create_agent(
    work_dir: str,
    config: ConfigRequest | None = None,
    domain_id: str = "math-modeling",
) -> AcademicAgent:
    """创建 Agent 实例"""
    global _agent

    # 加载领域配置
    domains_base = _get_domains_base()
    domain_dir = domains_base / domain_id
    try:
        domain = DomainProfile.from_directory(str(domain_dir))
    except (FileNotFoundError, Exception) as e:
        logger.warning(f"Failed to load domain '{domain_id}': {e}, falling back to math-modeling")
        domain = DomainProfile.from_directory(str(domains_base / "math-modeling"))

    # 创建 LLM 路由器 - 尝试从 models.yaml 加载
    config_path = Path(__file__).parent.parent.parent / "config" / "models.yaml"
    if config:
        llm_config = LLMConfig(
            provider=config.provider,
            model=config.model,
            api_key=config.api_key,
            base_url=config.base_url,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        )
        router = ModelRouter.from_single_config(llm_config)
    elif config_path.exists():
        try:
            router = ModelRouter.from_config(str(config_path))
        except Exception as e:
            logger.warning(f"Failed to load models.yaml: {e}, using env vars")
            router = _create_router_from_env()
    else:
        router = _create_router_from_env()

    # 可选：级联模型路由（通过环境变量启用）
    if os.environ.get("CASCADE_ENABLED", "").lower() in ("1", "true", "yes"):
        try:
            from ..llm.cascade import CascadeRouter
            cascade_stages = [
                {"model": os.environ.get("CASCADE_MODEL_1", "gpt-4o-mini"), "quality_threshold": 0.7},
                {"model": os.environ.get("CASCADE_MODEL_2", "gpt-4o"), "quality_threshold": 0.95},
            ]
            router = CascadeRouter(cascade_stages)
            logger.info(f"CascadeRouter enabled: {[s['model'] for s in cascade_stages]}")
        except Exception as e:
            logger.warning(f"CascadeRouter fallback to standard router: {e}")

    # 创建工具注册表
    tool_registry = ToolRegistry()
    tool_registry.register(CodeExecutorTool(work_dir))
    tool_registry.register(LatexCompilerTool(work_dir))
    tool_registry.register(FileManagerTool(work_dir))
    tool_registry.register(QualityCheckerTool(work_dir))
    tool_registry.register(FigureGeneratorTool(work_dir))
    tool_registry.register(EquationSolverTool(work_dir))
    tool_registry.register(DataAnalyzerTool(work_dir))
    tool_registry.register(SourceTrackerTool(work_dir))
    tool_registry.register(EvidenceMapTool(work_dir))

    # 创建 Agent
    _agent = AcademicAgent(work_dir, domain, router, tool_registry)

    # 将 CostTracker 注入到所有 LLM backends
    for backend in router.backends.values():
        backend.cost_tracker = _agent.cost_tracker

    # 加载领域知识到 LongTermMemory（RAG 接入）
    knowledge_dir = domains_base / domain_id / "knowledge"
    if knowledge_dir.exists():
        try:
            _agent.long_term.load_from_directory(
                "knowledge", str(knowledge_dir), "*.md"
            )
            logger.info(f"已加载领域知识: {knowledge_dir}")
        except Exception as e:
            logger.warning(f"加载领域知识失败: {e}")

    # 设置 WebSocket 广播回调
    async def broadcast(event_type: str, data: dict):
        msg = json.dumps({"type": event_type, **data}, ensure_ascii=False)
        async with _ws_lock:
            dead = []
            for ws in _ws_connections:
                try:
                    await ws.send_text(msg)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                if ws in _ws_connections:
                    _ws_connections.remove(ws)

    def schedule_broadcast(event_type: str):
        def callback(data: dict):
            asyncio.create_task(broadcast(event_type, data))

        return callback

    _agent.set_callbacks(
        on_message=schedule_broadcast("message"),
        on_phase_change=schedule_broadcast("phase_change"),
        on_tool_call=schedule_broadcast("tool_call"),
    )

    return _agent


def _create_router_from_env() -> ModelRouter:
    """从环境变量创建路由器"""
    llm_config = LLMConfig(
        provider=os.environ.get("LLM_PROVIDER", "openai"),
        model=os.environ.get("LLM_MODEL", "gpt-4o"),
        api_key=os.environ.get("LLM_API_KEY", os.environ.get("OPENAI_API_KEY", "")),
        base_url=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
    )
    return ModelRouter.from_single_config(llm_config)


# ==================== REST API ====================


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "5.2.0"}


@app.get("/api/domains")
async def list_domains():
    """列出所有可用预定义"""
    domains_base = _get_domains_base()
    return {"domains": DomainProfile.list_domains(str(domains_base))}


@app.get("/api/roles")
async def list_roles(api_key: str = Depends(verify_api_key)):
    """列出所有角色"""
    role_mgr = get_role_manager()
    return {"roles": role_mgr.list_roles()}


@app.post("/api/config")
async def update_config(config: ConfigRequest, api_key: str = Depends(verify_api_key)):
    """更新 LLM 配置"""
    global _agent
    async with _agent_lock:
        if _agent:
            router = ModelRouter.from_single_config(
                LLMConfig(
                    provider=config.provider,
                    model=config.model,
                    api_key=config.api_key,
                    base_url=config.base_url,
                    max_tokens=config.max_tokens,
                    temperature=config.temperature,
                )
            )
            _agent.router = router
    return {"status": "ok"}


@app.post("/api/test-connection")
async def test_connection(config: ConfigRequest):
    """测试 LLM 连接"""
    from ..llm.backend import LLMBackend as _LLMBackend

    try:
        backend = _LLMBackend(
            LLMConfig(
                provider=config.provider,
                model=config.model,
                api_key=config.api_key,
                base_url=config.base_url,
            )
        )
        result = await backend.generate([{"role": "user", "content": "Say 'ok'"}])
        if result.finish_reason == "error":
            return {"status": "error", "message": result.content[:200]}
        if "ok" in result.content.lower() or result.finish_reason == "stop":
            return {"status": "success", "message": "连接成功"}
        return {"status": "error", "message": f"模型响应异常: {result.content[:200]}"}
    except Exception as e:
        logger.error(f"Test connection error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)[:200]}


@app.post("/api/project/init")
async def init_project(req: ProjectRequest, api_key: str = Depends(verify_api_key)):
    """初始化项目"""
    global _agent
    work_dir = str(_validate_work_dir(req.work_dir))
    async with _agent_lock:
        _agent = create_agent(work_dir)
    return {"status": "ok", "work_dir": work_dir}


@app.get("/api/status")
async def get_status():
    """获取 Agent 状态"""
    if not _agent:
        return {"status": "not_initialized"}
    return _agent.get_status()


@app.post("/api/chat")
async def chat(req: ChatRequest, api_key: str = Depends(verify_api_key)):
    """与 Agent 对话（非流式）"""
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")

    async with _agent_lock:
        if req.role and not _agent.domain.get_role_by_id(req.role):
            raise HTTPException(status_code=400, detail=f"无效角色: {req.role}")
        if req.role:
            _agent.switch_role(req.role)
        response = await _agent.chat(req.message)
    return {"response": response}


@app.post("/api/auto-run")
async def auto_run(req: AutoRunRequest, api_key: str = Depends(verify_api_key)):
    """启动自动执行"""
    global _agent
    async with _agent_lock:
        if not _agent:
            work_dir = str(_validate_work_dir(req.work_dir))
            _agent = create_agent(work_dir)

    if _agent:
        asyncio.create_task(_run_auto_broadcast(req.problem_text))
        return {"status": "started", "message": "自动执行已启动"}
    return {"status": "error", "message": "Agent 未初始化"}


@app.post("/api/cancel")
async def cancel_run(api_key: str = Depends(verify_api_key)):
    """取消当前自动运行"""
    if _agent:
        _agent.cancel()
        return {"status": "cancelled"}
    return {"status": "no_agent"}


@app.get("/api/files")
async def list_files(path: str = "", api_key: str = Depends(verify_api_key)):
    """列出工作目录文件"""
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")

    target = _safe_resolve(_agent.work_dir, path)
    if not target.exists():
        return {"files": []}

    files = []
    try:
        for item in sorted(target.iterdir()):
            try:
                is_file = item.is_file()
                size = item.stat().st_size if is_file else 0
            except OSError:
                is_file = True
                size = 0
            files.append(
                {
                    "name": item.name,
                    "is_dir": not is_file,
                    "size": size,
                    "path": str(item.relative_to(_agent.work_dir)),
                }
            )
    except PermissionError as err:
        raise HTTPException(status_code=403, detail="无权限访问") from err
    return {"files": files}


@app.get("/api/file/{path:path}")
async def read_file(path: str, api_key: str = Depends(verify_api_key)):
    """读取文件内容"""
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")

    target = _safe_resolve(_agent.work_dir, path)
    if not target.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    if not target.is_file():
        raise HTTPException(status_code=400, detail="不是文件")

    if target.suffix.lower() in [".png", ".jpg", ".jpeg", ".gif", ".svg"]:
        return FileResponse(str(target))

    try:
        content = target.read_text(encoding="utf-8")
        if len(content) > 500000:
            content = content[:500000] + f"\n\n... [文件过大，已截断。总长度: {len(content)} 字符]"
        return {"content": content, "path": path, "size": len(content)}
    except UnicodeDecodeError:
        return {"content": "[二进制文件，无法显示]", "path": path, "size": target.stat().st_size}


@app.post("/api/reset")
async def reset_agent(api_key: str = Depends(verify_api_key)):
    """重置 Agent"""
    global _agent
    async with _agent_lock:
        if _agent:
            _agent.reset()
    return {"status": "ok"}


# ==================== 会话管理 ====================


@app.post("/api/session/save")
async def save_session(api_key: str = Depends(verify_api_key)):
    """保存当前会话"""
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")
    from ..memory.session_store import SessionStore
    store = SessionStore(str(_agent.work_dir))
    session_id = store.save(_agent)
    return {"session_id": session_id, "status": "saved"}


@app.get("/api/sessions")
async def list_sessions(api_key: str = Depends(verify_api_key)):
    """列出所有已保存的会话"""
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")
    from ..memory.session_store import SessionStore
    store = SessionStore(str(_agent.work_dir))
    return {"sessions": store.list_sessions()}


@app.post("/api/session/{session_id}/load")
async def load_session(session_id: str, api_key: str = Depends(verify_api_key)):
    """恢复会话"""
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")
    from ..memory.session_store import SessionStore
    store = SessionStore(str(_agent.work_dir))
    ok = store.load(session_id, _agent)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"status": "loaded", "session_id": session_id}


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str, api_key: str = Depends(verify_api_key)):
    """删除会话"""
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")
    from ..memory.session_store import SessionStore
    store = SessionStore(str(_agent.work_dir))
    ok = store.delete_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"status": "deleted"}


# ==================== 导出 ====================


@app.post("/api/export")
async def export_conversation(format: str = "markdown", api_key: str = Depends(verify_api_key)):
    """导出会话为 Markdown"""
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")
    from ..tools.exporter import DocumentExporter
    exporter = DocumentExporter(str(_agent.work_dir))
    messages = [{"role": m.role, "content": m.content} for m in _agent.memory.get_raw_messages()]
    path = exporter.export_markdown(messages)
    return FileResponse(path, filename="conversation.md")


# ==================== 成本 ====================


@app.get("/api/cost")
async def get_cost(api_key: str = Depends(verify_api_key)):
    """获取 LLM 调用成本"""
    if not _agent:
        return {"cost_usd": 0}
    if hasattr(_agent, 'cost_tracker') and _agent.cost_tracker:
        return _agent.cost_tracker.get_summary()
    return {"cost_usd": 0, "message": "成本追踪未启用"}


@app.get("/api/performance")
async def get_performance(api_key: str = Depends(verify_api_key)):
    """获取性能统计"""
    from ..utils.perf_monitor import get_monitor
    monitor = get_monitor()
    return {"metrics": monitor.get_all_stats()}


# ==================== 评测系统 ====================


@app.post("/api/eval/run")
async def run_evaluation(
    domain_id: str = "math-modeling",
    version: str = "current",
    api_key: str = Depends(verify_api_key),
):
    """运行评测"""
    from ..eval.runner import evaluate_domain
    report = await evaluate_domain(domain_id, version=version, use_mock=True)
    return report.to_dict()


@app.get("/api/eval/domains")
async def list_eval_domains(api_key: str = Depends(verify_api_key)):
    """列出有 golden set 的领域"""
    domains_base = _get_domains_base()
    domains_with_golden = []
    if domains_base.exists():
        for d in domains_base.iterdir():
            if d.is_dir() and (d / "golden.jsonl").exists():
                domains_with_golden.append(d.name)
    return {"domains": domains_with_golden}


@app.get("/api/eval/report/{domain_id}")
async def get_eval_report(domain_id: str, api_key: str = Depends(verify_api_key)):
    """获取评测报告"""
    report_path = Path(__file__).parent.parent.parent.parent / "docs" / f"eval-report-{domain_id}.md"
    if report_path.exists():
        return {"content": report_path.read_text(encoding="utf-8")}
    raise HTTPException(status_code=404, detail="报告不存在")


@app.get("/api/cases")
async def list_cases(
    domain_id: str | None = None,
    min_score: float = 0.0,
    api_key: str = Depends(verify_api_key),
):
    """搜索案例库"""
    from ..knowledge.case_library import CaseLibrary
    lib = CaseLibrary(str(Path(__file__).parent.parent.parent.parent / "data" / "cases"))
    cases = lib.search(domain_id=domain_id, min_score=min_score)
    return {
        "cases": [
            {"case_id": c.case_id, "domain": c.domain_id, "score": c.quality_score}
            for c in cases
        ]
    }


# ==================== 检查点 ====================


@app.get("/api/checkpoint")
async def get_checkpoint(api_key: str = Depends(verify_api_key)):
    """获取当前检查点"""
    if not _agent:
        return {"status": "no_agent"}
    from ..engine.checkpoint import RunCheckpoint
    cp_path = _agent.work_dir / "checkpoint.json"
    cp = RunCheckpoint.load(str(cp_path))
    if cp:
        return {
            "run_id": cp.run_id,
            "domain_id": cp.domain_id,
            "status": cp.status,
            "progress": cp.progress,
            "phases": len(cp.phases),
        }
    return {"status": "no_checkpoint"}


# ==================== HITL ====================


@app.get("/api/hitl/pending")
async def hitl_pending(api_key: str = Depends(verify_api_key)):
    """获取待确认请求"""
    if not _agent:
        return {"requests": []}
    from ..engine.hitl import HITLManager
    mgr = HITLManager(str(_agent.work_dir / "hitl"))
    return {
        "requests": [
            {"request_id": r.request_id, "phase_id": r.phase_id, "message": r.message}
            for r in mgr.get_pending()
        ]
    }


@app.post("/api/hitl/respond")
async def hitl_respond(
    request_id: str = "",
    response: str = "approve",
    api_key: str = Depends(verify_api_key),
):
    """响应 HITL 确认请求"""
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")
    from ..engine.hitl import HITLManager
    mgr = HITLManager(str(_agent.work_dir / "hitl"))
    ok = mgr.respond(request_id, response)
    if not ok:
        raise HTTPException(status_code=404, detail="请求不存在")
    return {"status": "responded"}


# ==================== 知识图谱 ====================


@app.get("/api/knowledge/graph")
async def get_knowledge_graph(
    domain_id: str = "math-modeling",
    api_key: str = Depends(verify_api_key),
):
    """获取领域知识图谱"""
    from ..knowledge.graph import KnowledgeGraph
    graph_path = Path(__file__).parent.parent.parent.parent / "domains" / domain_id / "knowledge_graph.json"
    kg = KnowledgeGraph(persist_path=str(graph_path))
    return {"stats": kg.stats}


@app.get("/api/knowledge/search")
async def search_knowledge(
    query: str = "",
    domain_id: str = "math-modeling",
    api_key: str = Depends(verify_api_key),
):
    """搜索领域知识"""
    from ..knowledge.graph import KnowledgeGraph
    graph_path = Path(__file__).parent.parent.parent.parent / "domains" / domain_id / "knowledge_graph.json"
    kg = KnowledgeGraph(persist_path=str(graph_path))
    results = kg.query(query)
    return {"results": [{"name": e.name, "type": e.entity_type} for e in results]}


# ==================== 文档版本 ====================


@app.get("/api/documents")
async def list_document_versions(api_key: str = Depends(verify_api_key)):
    """列出有版本历史的文档"""
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")
    from ..tools.doc_version import DocumentVersionStore
    store = DocumentVersionStore(str(_agent.work_dir))
    return {"documents": store.list_documents()}


@app.get("/api/document/{doc_name}/versions")
async def get_document_versions(doc_name: str, api_key: str = Depends(verify_api_key)):
    """获取文档版本历史"""
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")
    from ..tools.doc_version import DocumentVersionStore
    store = DocumentVersionStore(str(_agent.work_dir))
    history = store.get_history(doc_name)
    return {
        "versions": [
            {"version_id": v.version_id, "message": v.message, "timestamp": v.timestamp, "size": v.size}
            for v in history
        ]
    }


# ==================== Trace ====================


@app.get("/api/trace/latest")
async def get_latest_trace(api_key: str = Depends(verify_api_key)):
    """获取最新 trace"""
    from ..observability.tracer import get_collector
    collector = get_collector()
    completed = collector.get_completed()
    if completed:
        return completed[-1].to_dict()
    return {"status": "no_traces"}


# ==================== 租户 & 实验 ====================


@app.get("/api/tenant/usage")
async def get_tenant_usage(
    tenant_id: str = "default",
    api_key: str = Depends(verify_api_key),
):
    """获取租户用量"""
    from ..saas.billing import BillingMeter
    meter = BillingMeter(str(Path(__file__).parent.parent.parent.parent / "data" / "billing"))
    return meter.get_usage_today(tenant_id)


@app.get("/api/experiments")
async def list_experiments(api_key: str = Depends(verify_api_key)):
    """列出灰度实验"""
    from ..api.extensions import ExperimentManager
    mgr = ExperimentManager(str(Path(__file__).parent.parent.parent.parent / "data" / "experiments"))
    return {
        "experiments": [
            {"id": e.experiment_id, "name": e.name, "active": e.active}
            for e in mgr.list_all()
        ]
    }


# ==================== WebSocket ====================


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 连接"""
    await websocket.accept()
    async with _ws_lock:
        _ws_connections.append(websocket)

    try:
        if _agent:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "status",
                        "data": _agent.get_status(),
                    },
                    ensure_ascii=False,
                )
            )

        while True:
            data = await websocket.receive_text()

            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "message": "无效的 JSON 格式",
                        },
                        ensure_ascii=False,
                    )
                )
                continue

            msg_type = msg.get("type", "")

            if msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue

            if msg_type == "chat":
                if not _agent:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "Agent 未初始化",
                            },
                            ensure_ascii=False,
                        )
                    )
                    continue

                message = msg.get("message", "")
                if not message or len(message) > 100000:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "消息为空或过长",
                            },
                            ensure_ascii=False,
                        )
                    )
                    continue

                role_id = msg.get("role") or None

                asyncio.create_task(_safe_chat(message, role_id))

            elif msg_type == "stream_chat":
                if not _agent:
                    await websocket.send_text(json.dumps({
                        "type": "error", "message": "Agent 未初始化"
                    }, ensure_ascii=False))
                    continue

                message = msg.get("message", "")
                role_id = msg.get("role")

                asyncio.create_task(_stream_chat_ws(websocket, message, role_id))

            elif msg_type == "auto_run":
                if _agent:
                    problem_text = msg.get("problem_text", "")
                    asyncio.create_task(_run_auto_ws(websocket, problem_text))

            elif msg_type == "cancel":
                if _agent:
                    _agent.cancel()

            elif msg_type == "switch_role":
                if _agent and msg.get("role"):
                    role_id = msg["role"]
                    if _agent.domain.get_role_by_id(role_id):
                        _agent.switch_role(role_id)
                        role_cfg = _agent.get_current_role()
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "role_switched",
                                    "role": role_id,
                                    "name": role_cfg.name if role_cfg else role_id,
                                },
                                ensure_ascii=False,
                            )
                        )
                    else:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "message": f"无效角色: {role_id}",
                                },
                                ensure_ascii=False,
                            )
                        )

            elif msg_type == "init":
                work_dir = msg.get("work_dir", "")
                if not work_dir:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "未指定工作目录",
                            },
                            ensure_ascii=False,
                        )
                    )
                    continue

                try:
                    validated_dir = str(_validate_work_dir(work_dir))
                except HTTPException as e:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "message": str(e.detail),
                            },
                            ensure_ascii=False,
                        )
                    )
                    continue

                config = None
                if msg.get("config"):
                    try:
                        config = ConfigRequest(**msg["config"])
                    except Exception as e:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "message": f"配置无效: {e}",
                                },
                                ensure_ascii=False,
                            )
                        )
                        continue

                domain_id = msg.get("domain_id", "math-modeling")

                async with _agent_lock:
                    create_agent(validated_dir, config, domain_id=domain_id)
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "initialized",
                            "work_dir": validated_dir,
                            "domain_id": _agent.domain.id if _agent else domain_id,
                            "domain": {
                                "id": _agent.domain.id if _agent else domain_id,
                                "name": _agent.domain.name if _agent else domain_id,
                                "phases": [
                                    {"id": p.id, "name": p.name}
                                    for p in (_agent.domain.phases if _agent else [])
                                    if p.id not in ("idle", "done")
                                ],
                                "roles": [
                                    {"id": r.id, "name": r.name, "emoji": r.emoji}
                                    for r in (_agent.domain.roles if _agent else [])
                                ],
                            },
                        },
                        ensure_ascii=False,
                    )
                )

    except WebSocketDisconnect:
        async with _ws_lock:
            if websocket in _ws_connections:
                _ws_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        async with _ws_lock:
            if websocket in _ws_connections:
                _ws_connections.remove(websocket)


async def _safe_chat(message: str, role_id: str | None = None):
    """安全执行聊天（带锁和错误处理）"""
    agent = _agent
    if not agent:
        return
    try:
        async with _agent_lock:
            if role_id:
                agent.switch_role(role_id)
            await agent.chat(message)
    except Exception as e:
        logger.error(f"Chat error: {e}")


async def _stream_chat_ws(websocket: WebSocket, message: str, role_id: str | None = None):
    """流式聊天 — 通过 WebSocket 实时推送 token"""
    agent = _agent
    if not agent:
        return
    try:
        async with _agent_lock:
            if role_id:
                agent.switch_role(role_id)
            agent._ensure_system_message()
            agent.memory.add("user", message)

            backend = agent._get_backend()
            messages = agent.memory.get_messages()

            full_response = ""
            async for chunk in backend.generate_stream(messages):
                if isinstance(chunk, dict):
                    # 工具调用信息
                    continue
                full_response += chunk
                await websocket.send_text(json.dumps({
                    "type": "stream_chunk",
                    "content": chunk,
                }, ensure_ascii=False))

            agent.memory.add("assistant", full_response)

            role = agent.get_current_role()
            await websocket.send_text(json.dumps({
                "type": "stream_end",
                "full_content": full_response,
                "agent_role": agent.current_role_id,
                "agent_name": role.name if role else "",
            }, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Stream chat error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error", "message": str(e)
        }, ensure_ascii=False))


async def _run_auto_ws(websocket: WebSocket, problem_text: str):
    """通过 WebSocket 运行自动流程"""
    if not _agent:
        return
    try:
        async for event in _agent.run_auto(problem_text):
            try:
                await websocket.send_text(json.dumps(event, ensure_ascii=False))
            except Exception:
                break
    except Exception as e:
        logger.error(f"Auto run error: {e}")
        with contextlib.suppress(Exception):
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "message": str(e),
                    },
                    ensure_ascii=False,
                )
            )


async def _run_auto_broadcast(problem_text: str):
    """通过 WebSocket 广播 auto run 进度给所有连接的客户端"""
    if not _agent:
        return
    try:
        async for event in _agent.run_auto(problem_text):
            msg = json.dumps(event, ensure_ascii=False)
            async with _ws_lock:
                dead = []
                for ws in _ws_connections:
                    try:
                        await ws.send_text(msg)
                    except Exception:
                        dead.append(ws)
                for ws in dead:
                    if ws in _ws_connections:
                        _ws_connections.remove(ws)
    except Exception as e:
        logger.error(f"Auto run broadcast error: {e}")


# ==================== 启动 ====================


def start_server(host: str = "127.0.0.1", port: int = 8766):
    """启动服务器"""
    import uvicorn

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    start_server()
