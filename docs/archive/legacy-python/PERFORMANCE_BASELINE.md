# Lemma 性能基线

> 测量时间：2026-06-26
> 测量环境：Windows 11, Python 3.11.15, Node 20

## 后端 API 延迟

| 端点 | P50 | P95 | P99 | 备注 |
|------|-----|-----|-----|------|
| GET /api/health | <5ms | <10ms | <20ms | 纯内存操作 |
| GET /api/domains | <5ms | <10ms | <20ms | YAML 解析 |
| GET /api/roles | <5ms | <10ms | <20ms | YAML 解析 |
| GET /api/status | <5ms | <10ms | <20ms | 状态查询 |
| POST /api/chat | 取决于 LLM | - | - | 流式响应 |
| GET /api/files | <50ms | <100ms | <200ms | 磁盘 I/O |
| POST /api/session/save | <100ms | <200ms | <500ms | JSON 写入 |
| GET /api/sessions | <50ms | <100ms | <200ms | 目录扫描 |
| GET /api/cost | <5ms | <10ms | <20ms | 内存查询 |
| GET /api/performance | <5ms | <10ms | <20ms | 内存查询 |

## 工具执行延迟

| 工具 | P50 | P95 | 备注 |
|------|-----|-----|------|
| code_executor | <500ms | <2000ms | 取决于代码复杂度 |
| latex_compiler | <2000ms | <5000ms | 需 TeX Live |
| figure_generator | <1000ms | <3000ms | matplotlib |
| quality_checker | <200ms | <500ms | AST 解析 |
| source_tracker | <50ms | <100ms | JSON 读写 |
| evidence_map | <50ms | <100ms | JSON 读写 |
| data_analyzer | <500ms | <2000ms | scipy 计算 |
| equation_solver | <1000ms | <3000ms | sympy 求解 |

## WebSocket 消息延迟

| 消息类型 | P50 | P95 | 备注 |
|----------|-----|-----|------|
| ping → pong | <5ms | <10ms | 心跳 |
| init → initialized | <500ms | <1000ms | 含 Agent 创建 |
| chat → response | 取决于 LLM | - | 流式响应 |

## 测试执行时间

| 测试套件 | 测试数 | 执行时间 | 备注 |
|----------|--------|----------|------|
| 后端单元测试 | 523+ | ~80s | 含 coverage |
| 前端单元测试 | 49 | ~4s | Vitest |
| E2E 测试 | 38 | ~30s | 集成测试 |

## 前端性能（目标值）

| 指标 | 目标值 | 备注 |
|------|--------|------|
| FCP | <1.5s | First Contentful Paint |
| LCP | <2.5s | Largest Contentful Paint |
| TBT | <200ms | Total Blocking Time |
| CLS | <0.1 | Cumulative Layout Shift |

## 性能规则

- **API 响应延迟**：P95 不得超过 200ms（LLM 调用除外）
- **工具执行延迟**：P95 不得超过 5000ms
- **测试执行时间**：全量测试不得超过 120s
- **前端包大小**：JS bundle < 2MB (gzipped < 500KB)
