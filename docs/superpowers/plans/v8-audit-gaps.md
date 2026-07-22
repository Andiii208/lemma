# v8 计划执行审计报告

> 审计时间：2026-06-25

## API 端点审计

### v8 Task 2.x 新增端点

| 端点 | 预期状态 | 实际状态 | 备注 |
|------|----------|----------|------|
| `POST /api/eval/run` | 应有 | ✅ 已实现 |  |
| `GET /api/eval/report/{domain_id}` | 应有 | ✅ **已补全** | v8 遗漏于 2026-06-25 修复 |
| `GET /api/eval/domains` | 应有 | ✅ 已实现 |  |
| `GET /api/checkpoint` | 应有 | ✅ 已实现 |  |
| `GET /api/hitl/pending` | 应有 | ✅ 已实现 |  |
| `POST /api/hitl/respond` | 应有 | ✅ 已实现 |  |
| `GET /api/knowledge/graph` | 应有 | ✅ 已实现 |  |
| `GET /api/knowledge/search` | 应有 | ✅ 已实现 |  |
| `GET /api/cases` | 应有 | ✅ **已补全** | v8 遗漏于 2026-06-25 修复 |
| `GET /api/documents` | 应有 | ✅ 已实现 |  |
| `GET /api/document/{name}/versions` | 应有 | ✅ 已实现 |  |
| `GET /api/trace/latest` | 应有 | ✅ 已实现 |  |
| `GET /api/tenant/usage` | 应有 | ✅ 已实现 |  |
| `GET /api/experiments` | 应有 | ✅ 已实现 |  |

**结论：** 14 个端点中 12 个原地完成，2 个在 v9 阶段一补全。

## 前端组件 API 对接审计

| 组件 | 数据源 | 状态 | 备注 |
|------|--------|------|------|
| `TraceViewer.tsx` | `GET /api/trace/latest` | ✅ 真实 API | 含 fetch + useEffect |
| `ConfirmationCard.tsx` | `GET /api/hitl/pending` + `POST /api/hitl/respond` | ✅ 真实 API | 5 秒轮询 |
| `DocumentVersions.tsx` | `GET /api/documents` + `GET /api/document/{name}/versions` | ✅ 真实 API | 双 useEffect |

**结论：** 三个组件均使用真实 API 数据源，未被 mock。

## 前端测试质量审计

| 文件 | 断言数 | 状态 |
|------|--------|------|
| `Sidebar.test.tsx` | 11 | ✅ |
| `ChatPanel.test.tsx` | 7 | ✅ |
| `PipelinePanel.test.tsx` | 6 | ✅ |
| `SettingsPanel.test.tsx` | 5 | ✅ |

**结论：** 所有测试文件 ≥ 5 个断言，质量合格。

## 总结

| 项目 | 数量 |
|------|------|
| v8 端点已实现 | 14/14 (含 2 个已补全) |
| 前端组件对接真实 API | 3/3 |
| 前端测试 ≥ 5 断言 | 4/4 |
| 修复的 v8 遗漏 | 2 个 (eval/report, cases) |
