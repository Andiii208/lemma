# Changelog

All notable changes to Lemma will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-07-22

### Added
- **Domain Registry**: 基于 Zod schema 的领域配置加载系统
- **Session Lifecycle**: 完整的会话 CRUD + 原子写入
- **SDK Bridge**: Claude Agent SDK 封装，支持流式响应和错误恢复
- **安全边界**: 多层安全机制（contextIsolation、sandbox、路径授权）
- **AuthorizedPaths**: 文件路径授权系统
- **Chat Dispatcher**: 聊天消息分发器，支持 API Key 验证
- **5 个学术领域**: math-modeling、paper-writing、lab-report、literature-review、data-mining
- **SECURITY.md**: 安全策略和漏洞报告渠道
- **CODEOWNERS**: 代码所有权配置

### Changed
- 技术栈修正: Electron 43 → Electron 39, Vite 6 → Vite 5
- 架构文档更新: 移除旧 Python 架构引用，记录当前 Node.js 架构
- 贡献指南更新: 移除 Python/backend 要求，补充 npm ci/test/lint/typecheck 流程
- 旧版文档归档: openapi.json、QUALITY_BASELINE.md、PERFORMANCE_BASELINE.md、electron-build-log.md 移入 docs/archive/legacy-python/

### Removed
- Electron 43 虚假声明
- Python/backend 开发环境要求
- 旧架构（FastAPI + WebSocket）引用

## [5.2.0] - 2026-06-26

### Added
- **Toast 通知系统**: react-hot-toast 4种类型，全局捕获成功/错误/警告/信息
- **Skeleton 骨架屏**: 3种变体（card/text/circle），替换所有"加载中…"文本
- **ConfirmDialog 确认框**: 破坏性操作（删除会话）二次确认，Escape关闭+焦点捕获
- **学术字体系统**: Crimson Pro (标题衬线) + Atkinson Hyperlegible (正文)
- **Logo 升级**: ⊢ 符号品牌进化，Emoji 全部替换为 lucide-react SVG 图标
- **亮色/暗色双主题**: Sun/Moon 切换器 + 系统主题 @media 跟随 + localStorage 持久化
- **页面转场动画**: framer-motion ViewTransition，200ms crossfade + slide
- **SVG 可访问性**: 8个 Agent 角色全部添加 `role="img"` + `aria-label`
- **高对比度模式**: `@media (prefers-contrast: high)` CSS 变量覆盖
- **代码分割**: React.lazy + Suspense 6个次要视图懒加载
- **Vite 构建优化**: manualChunks 拆分 vendor 包
- **mypy 类型检查**: 9个核心模块零类型错误
- **模糊测试器测试**: 9个测试，100% 覆盖率
- **LLM Judge 测试**: 11个测试，82% 覆盖率（含缓存 + mock）

### Changed
- 品牌更名：UltraAgent/UltraMath → Lemma
- Python 包名：ultramath → lemma

### Fixed
- RAG Collection Name 不匹配导致知识检索不工作
- 前端视图切换无转场动画
- SVG sprite 缺少 `role="img"` 可访问性标记
- tool_forge.py 类型错误、plugin.py 空安全修复

## [5.1.0] - 2026-06-24

### Added
- **Multi-Agent 辩论机制** (`debate.py`)：两个角色独立回答，lead 裁决合并
- **自适应参数**：根据阶段自动调整 temperature 和 max_tokens
- **成本预估**：`CostTracker.estimate_run_cost()` 预估 auto_run 成本
- **Prompt 版本追踪** (`prompt_version.py`)：追踪 prompt 文件变化
- **知识库强化**：4 个领域共 19 篇知识文档
- **一键安装脚本**：`install.bat`（Windows）+ `install.sh`（Linux/Mac）
- **领域市场入口**：SettingsPanel 添加领域市场链接
- **可访问性增强**：Skip Link、focus-visible 样式、reduced-motion 支持
- **knowledge_loader 测试**：8 个新测试

### Changed
- ChatPanel 移除硬编码 DEFAULT_ROLES，改用 AgentAvatar 组件
- FileViewer 文件图标从 emoji 替换为 Lucide 图标
- PipelinePanel 按钮从 emoji 替换为 Lucide 图标
- SettingsPanel 领域选择标题移除 emoji

### Fixed
- 版本号统一为 v5.1.0（server.py、Sidebar、pyproject.toml、package.json）

## [5.0.0] - 2026-06-23

### Added
- **AcademicAgent 引擎**：领域无关的通用学术写作引擎
- **DomainProfile 系统**：从 YAML 配置加载领域、阶段、角色
- **4 个领域配置**：math-modeling、paper-writing、lab-report、literature-review
- **8 个角色 SVG 精灵**：Lead、Math、Engineer、Reviewer、Writer、Verifier、Researcher、Analyst
- **9 个工具**：CodeExecutor、LatexCompiler、FileManager、QualityChecker、FigureGenerator、EquationSolver、DataAnalyzer、SourceTracker、EvidenceMap
- **流式聊天**：token-by-token 实时渲染
- **会话管理**：保存/恢复/列表/删除
- **导出系统**：Markdown 格式导出
- **成本追踪**：实时显示 LLM 调用费用
- **RAG 知识检索**：基于 ChromaDB 的领域知识注入
- **CascadeRouter**：可选的级联模型路由
- **SelfReflector**：每阶段自动轻量反思
- **Handoff 协议**：自动解析交接表
- **TrustManager**：信赖阈值控制
- **FileVisibility**：信息不对称机制
- **CI/CD**：GitHub Actions 配置
- **Docker 部署**：Dockerfile + docker-compose.yml
- **Electron 打包**：Windows NSIS 配置
- **文档**：ARCHITECTURE.md、USER_GUIDE.md、DOMAIN_DEVELOPMENT.md

### Testing
- 183 个后端测试（单元 + E2E）
- 7 个前端测试
- 50% 代码覆盖率

## [4.0.0] - 2026-06-22

### Added
- 初始版本发布
- 基础 FastAPI 后端
- React + TypeScript 前端
- WebSocket 通信
- 基础数学建模功能

---

## Version History Summary

| Version | Date | Key Changes |
|---------|------|-------------|
| 0.2.0 | 2026-07-22 | 文档治理重写、技术栈修正、Domain Registry、安全边界、旧文档归档 |
| 5.2.0 | 2026-06-26 | Toast 通知、骨架屏、双主题、代码分割 |
| 5.1.0 | 2026-06-24 | Multi-Agent 辩论、自适应参数、知识库强化、可访问性 |
| 5.0.0 | 2026-06-23 | AcademicAgent 引擎、4 领域、9 工具、流式聊天 |
| 4.0.0 | 2026-06-22 | 初始版本 |
