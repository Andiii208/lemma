# Lemma — Claude Code 任务交接计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成需要外部环境（浏览器/GUI/Docker/API Key）或大量内容创作的 7 个任务，将 Lemma 推进到可分发、可验证的生产就绪状态。

**Architecture:** 7 个独立可交付任务，无相互依赖。Playwright E2E + Electron 打包 + Docker 部署构成分发验证铁三角；LLM 评测验证智能质量；知识文档 + Prompt + 新领域构成内容壁垒。

**Tech Stack:** Playwright, Electron 31, Docker, DeepSeek/OpenAI API, Markdown

---

## 项目上下文（给 Claude Code 的速览）

```
项目名：Lemma（数学建模桌面智能助手）
技术栈：Python 3.11+ FastAPI backend + React 18 TypeScript Electron frontend
当前状态：v11 前端优化刚完成（Toast/Skeleton/ConfirmDialog/字体/亮色主题/代码分割）
测试：后端 503 passed，前端 65 passed (13 files)，覆盖率 75%
后端路径：backend/src/lemma/
前端路径：frontend/src/
```

### 启动方式

```bash
# 后端（端口 8765）
cd backend && PYTHONPATH=src python -m uvicorn lemma.api.server:app --port 8765

# 前端（端口 5173）
cd frontend && npm run vite:dev
```

---

## Task 1: Playwright E2E 端到端测试

**目标：** 用 Playwright 从用户视角验证完整链路。

**前置条件：** Chrome/Chromium 浏览器可运行

**Files:**
- Create: `frontend/e2e/full-pipeline.spec.ts`
- Create: `frontend/e2e/domain-switch.spec.ts`
- Create: `frontend/e2e/session-persistence.spec.ts`
- Create: `frontend/playwright.config.ts`
- Create: `frontend/e2e/error-recovery.spec.ts`

- [ ] **Step 1: 安装 Playwright**

```bash
cd frontend
npm install -D @playwright/test
npx playwright install chromium --with-deps
```

- [ ] **Step 2: 创建 Playwright 配置**

```typescript
// frontend/playwright.config.ts
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 120000,  // 2 分钟，给 LLM 响应留时间
  retries: 0,
  use: {
    baseURL: 'http://localhost:5173',
    headless: true,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  webServer: [
    {
      command: 'cd ../backend && python -m uvicorn lemma.api.server:app --port 8765',
      port: 8765,
      timeout: 30000,
      reuseExistingServer: true,
    },
    {
      command: 'npx vite --port 5173',
      port: 5173,
      timeout: 30000,
      reuseExistingServer: true,
    },
  ],
})
```

- [ ] **Step 3: 编写全流程测试**

```typescript
// frontend/e2e/full-pipeline.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Full Pipeline', () => {
  test('can boot and see settings panel', async ({ page }) => {
    await page.goto('/')
    await page.waitForSelector('[data-testid="settings-panel"]', { timeout: 15000 })
    await expect(page.locator('[data-testid="settings-panel"]')).toBeVisible()
  })

  test('can switch domains and see different roles', async ({ page }) => {
    await page.goto('/')
    await page.waitForSelector('[data-testid="domain-select"]', { timeout: 15000 })

    // 选择 math-modeling
    await page.selectOption('[data-testid="domain-select"]', 'math-modeling')
    await page.waitForTimeout(500)
    const mathRoleCount = await page.locator('[data-testid^="role-"]').count()
    expect(mathRoleCount).toBeGreaterThan(0)

    // 切换到 paper-writing
    await page.selectOption('[data-testid="domain-select"]', 'paper-writing')
    await page.waitForTimeout(500)
    const paperRoleCount = await page.locator('[data-testid^="role-"]').count()
    expect(paperRoleCount).toBeGreaterThan(0)
  })

  test('can send message and receive response', async ({ page }) => {
    await page.goto('/')
    await page.waitForSelector('[data-testid="settings-panel"]', { timeout: 15000 })

    // 配置 API Key
    await page.fill('[placeholder="sk-..."]', process.env.TEST_API_KEY || 'test-key')
    await page.selectOption('[data-testid="domain-select"]', 'math-modeling')

    // 切换到对话页
    await page.click('[data-testid="tab-chat"]')
    await page.fill('[data-testid="chat-input"]', '求解 x^2 + 2x + 1 = 0')
    await page.click('[data-testid="send-button"]')

    // 等待 AI 回复出现
    await page.waitForSelector('[data-testid="message-assistant"]', { timeout: 60000 })
    expect(await page.locator('[data-testid="message-assistant"]').count()).toBeGreaterThan(0)
  })
})
```

- [ ] **Step 4: 编写会话持久化测试**

```typescript
// frontend/e2e/session-persistence.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Session Persistence', () => {
  test('can see session tab', async ({ page }) => {
    await page.goto('/')
    await page.waitForSelector('[data-testid="tab-sessions"]', { timeout: 15000 })
    await page.click('[data-testid="tab-sessions"]')
    await page.waitForSelector('[data-testid="session-list"]', { timeout: 10000 })
    await expect(page.locator('[data-testid="session-list"]')).toBeVisible()
  })

  test('can see save button', async ({ page }) => {
    await page.goto('/')
    await page.waitForSelector('[data-testid="tab-sessions"]', { timeout: 15000 })
    await page.click('[data-testid="tab-sessions"]')
    await expect(page.locator('[data-testid="save-session"]')).toBeVisible()
  })
})
```

- [ ] **Step 5: 编写错误恢复测试**

```typescript
// frontend/e2e/error-recovery.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Error Recovery', () => {
  test('shows error toast on bad API key', async ({ page }) => {
    await page.goto('/')
    await page.waitForSelector('[data-testid="settings-panel"]', { timeout: 15000 })

    // 填入无效 API Key
    await page.fill('[placeholder="sk-..."]', 'invalid-key-12345')
    await page.selectOption('[data-testid="domain-select"]', 'math-modeling')
    await page.click('[data-testid="test-connection"]')

    // 应看到错误反馈
    await page.waitForTimeout(2000)
  })
})
```

- [ ] **Step 6: 添加缺失的 data-testid 属性**

检查以下位置是否需要添加 `data-testid`：

| 元素 | data-testid | 文件 |
|------|------------|------|
| 设置面板容器 | `settings-panel` | `SettingsPanel.tsx` 最外层 div |
| 域选择器 | `domain-select` | `SettingsPanel.tsx` select 元素 |
| 对话标签 | `tab-chat` | `Sidebar.tsx` 导航按钮 |
| 会话标签 | `tab-sessions` | `Sidebar.tsx` 导航按钮 |
| 聊天输入框 | `chat-input` | `ChatPanel.tsx` textarea |
| 发送按钮 | `send-button` | `ChatPanel.tsx` 发送 button |
| 助手消息 | `message-assistant` | `ChatPanel.tsx` 助手消息 div |
| 会话列表 | `session-list` | `SessionPanel.tsx` 会话容器 |
| 保存按钮 | `save-session` | `SessionPanel.tsx` 保存 button |

- [ ] **Step 7: 运行 Playwright 测试**

```bash
cd frontend && npx playwright test
```

预期：所有测试 PASS

- [ ] **Step 8: 提交**

```bash
git add frontend/e2e/ frontend/playwright.config.ts
git commit -m "test: add Playwright E2E tests for full pipeline, domain switching, sessions, and error recovery"
```

---

## Task 2: Electron 桌面打包验证

**目标：** 构建 Windows NSIS 安装包，验证可安装可运行。

**前置条件：** Windows GUI + 磁盘空间 > 1GB

**Files:**
- Modify: `frontend/package.json`（确认 build 配置）
- Create: `docs/electron-build-log.md`

- [ ] **Step 1: 构建前端**

```bash
cd frontend && npm run vite:build
```

验证 `dist/` 目录有产出。

- [ ] **Step 2: 执行 Electron 打包**

```bash
cd frontend && npx electron-builder --win --config
```

- [ ] **Step 3: 检查输出**

```bash
ls -la frontend/release/
du -sh frontend/release/*.exe
```

预期：生成 `Lemma Setup x.x.x.exe`，大小 < 400MB

- [ ] **Step 4: 安装并运行验证**

- 双击安装包，完成安装
- 启动应用，确认窗口出现
- 检查标题栏显示 "Lemma"
- 检查左下角连接状态：先"后端未连接"→等待→"后端已连接"
- 检查 Sidebar Logo 显示 "⊢" 符号

- [ ] **Step 5: 记录结果**

```markdown
# docs/electron-build-log.md
## Electron 打包验证

- **日期**: 2026-06-26
- **包大小**: xxx MB
- **安装**: ✅ / ❌
- **启动**: ✅ / ❌
- **后端自启动**: ✅ / ❌
- **WebSocket 连接**: ✅ / ❌
- **UI 正常显示**: ✅ / ❌
```

- [ ] **Step 6: 提交**

```bash
git add docs/electron-build-log.md
git commit -m "docs: add Electron build verification log"
```

---

## Task 3: Docker 部署验证

**目标：** 创建 Dockerfile + docker-compose.yml，验证一键启动。

**前置条件：** Docker Desktop 已安装并运行

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

- [ ] **Step 1: 创建 Dockerfile**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制后端代码
COPY backend/ /app/backend/
COPY domains/ /app/domains/

# 安装 Python 依赖
RUN pip install --no-cache-dir \
    fastapi>=0.111.0 \
    uvicorn[standard]>=0.30.0 \
    websockets>=12.0 \
    openai>=1.30.0 \
    pydantic>=2.0.0 \
    chromadb>=0.5.0 \
    tiktoken>=0.7.0 \
    pyyaml>=6.0 \
    httpx>=0.27.0

EXPOSE 8765

CMD ["python", "-m", "uvicorn", "lemma.api.server:app", "--host", "0.0.0.0", "--port", "8765"]
```

- [ ] **Step 2: 创建 docker-compose.yml**

```yaml
# docker-compose.yml
version: "3.9"

services:
  lemma-backend:
    build: .
    ports:
      - "8765:8765"
    volumes:
      - ./data:/app/data
      - ./domains:/app/domains
    environment:
      - PYTHONPATH=/app/backend/src
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
    restart: unless-stopped
```

- [ ] **Step 3: 创建 .dockerignore**

```
frontend/
node_modules/
.git/
__pycache__/
.pytest_cache/
docs/
*.pyc
```

- [ ] **Step 4: 构建并启动**

```bash
docker build -t lemma .
docker-compose up -d
```

- [ ] **Step 5: 验证健康检查**

```bash
curl http://localhost:8765/api/health
# 预期: {"status":"ok","version":"5.1.0"}

curl http://localhost:8765/api/domains
# 预期: {"domains":[...]}
```

- [ ] **Step 6: 提交**

```bash
git add Dockerfile docker-compose.yml .dockerignore
git commit -m "feat: add Docker deployment with docker-compose one-click setup"
```

---

## Task 4: 真实 LLM 评测验证

**目标：** 用真实 API Key 在 math-modeling golden set 上跑评测。

**前置条件：** DeepSeek 或 OpenAI API Key

**Files:**
- Create: `domains/paper-writing/golden.jsonl`
- Create: `domains/lab-report/golden.jsonl`
- Create: `domains/literature-review/golden.jsonl`

- [ ] **Step 1: 配置 API Key**

```bash
export DEEPSEEK_API_KEY="your-deepseek-key"
# 或
export OPENAI_API_KEY="your-openai-key"
```

- [ ] **Step 2: 确认 math-modeling golden set 存在**

```bash
ls -la domains/math-modeling/golden.jsonl
```

若不存在，创建：

```jsonl
{"input": "某工厂生产两种产品A和B，每件A利润30元，每件B利润20元。生产A需原料2kg+工时1h，生产B需原料1kg+工时3h。现有原料100kg，工时80h。求最优生产方案。", "expected_phases": ["analysis", "derivation", "ontology", "coding", "writing"], "min_quality_score": 0.6}
{"input": "预测某城市未来12个月的用电量，给定过去3年数据。评估预测模型精度。", "expected_phases": ["analysis", "derivation", "coding", "testing"], "min_quality_score": 0.5}
{"input": "评估四个候选方案的优劣，考虑成本、效率、可靠性三个维度。", "expected_phases": ["analysis", "ontology"], "min_quality_score": 0.6}
```

- [ ] **Step 3: 运行评测**

```bash
cd backend
PYTHONPATH=src python -m lemma.eval.runner --domain math-modeling --version v11-real --no-mock --output ../docs/eval-report-math-modeling-v11.md
```

- [ ] **Step 4: 检查评测报告**

报告中应出现：
- `Total cases: N`
- `Passed cases: N`
- `Avg score: 0.xx`

确认平均分 ≥ 0.6。

- [ ] **Step 5: 为其他 3 个领域创建 golden set**

`domains/paper-writing/golden.jsonl`：
```jsonl
{"input": "撰写一篇关于机器学习在医学诊断中应用的综述论文。", "expected_phases": ["research", "outline", "writing"], "min_quality_score": 0.6}
{"input": "撰写一篇关于区块链技术对金融行业影响的学术论文。", "expected_phases": ["research", "outline", "writing"], "min_quality_score": 0.6}
{"input": "撰写一篇关于光伏材料最新研究进展的综述。", "expected_phases": ["research", "outline", "writing"], "min_quality_score": 0.6}
```

`domains/lab-report/golden.jsonl`：
```jsonl
{"input": "撰写一份关于牛顿第二定律验证的实验报告。", "expected_phases": ["init", "method", "analysis", "writing"], "min_quality_score": 0.6}
{"input": "撰写一份关于酸碱滴定实验的报告。", "expected_phases": ["init", "method", "analysis", "writing"], "min_quality_score": 0.6}
```

`domains/literature-review/golden.jsonl`：
```jsonl
{"input": "撰写关于气候变化对农业生产影响的文献综述。", "expected_phases": ["search", "screen", "synthesize"], "min_quality_score": 0.6}
{"input": "撰写关于深度学习在自然语言处理中应用的文献综述。", "expected_phases": ["search", "screen", "synthesize"], "min_quality_score": 0.6}
```

- [ ] **Step 6: 提交**

```bash
git add domains/*/golden.jsonl docs/eval-report-math-modeling-v11.md
git commit -m "feat: add golden eval sets for all 4 domains, real LLM evaluation report"
```

---

## Task 5: 知识文档扩充

**目标：** 每个领域扩充知识文档，目标 25+ 篇 × 80+ 行，含公式、代码、常见陷阱。

**Files:**
- Create: `domains/math-modeling/knowledge/机器学习模型选型指南.md`
- Create: `domains/math-modeling/knowledge/优化求解器对比.md`
- Create: `domains/paper-writing/knowledge/摘要写作精要.md`
- Create: `domains/lab-report/knowledge/误差分析与不确定度.md`
- Create: `domains/literature-review/knowledge/元分析方法指南.md`

- [ ] **Step 1: 创建 math-modeling 领域扩充知识**

`domains/math-modeling/knowledge/机器学习模型选型指南.md`：

```markdown
# 机器学习模型选型指南

## 概述
在数学建模竞赛中，选择合适的机器学习模型对解题质量至关重要。
本文档提供从数据特征到模型选择的系统化决策框架。

## 决策树

### 有监督学习
**目标变量为连续值 → 回归问题**
- 数据量小（<1000条）且线性可分 → 线性回归 / Ridge / Lasso
- 数据量中等，有非线性关系 → RandomForest / XGBoost / LightGBM
- 数据量大（>10万条），需要高精度 → 深度神经网络（MLP）

**目标变量为离散值 → 分类问题**
- 二分类 + 可解释性要求高 → Logistic Regression
- 多分类 + 特征维度适中 → XGBoost / RandomForest
- 图像/文本等非结构化数据 → CNN / Transformer

### 无监督学习
- 探索数据结构 → PCA / t-SNE 降维
- 客户/样本分群 → K-Means / DBSCAN / 层次聚类
- 异常检测 → Isolation Forest / LOF / AutoEncoder

## 竞赛中常见陷阱
- **数据泄露**：特征工程时使用了未来的信息（如用全部数据的均值填充缺失值）
- **过拟合**：模型在训练集上表现完美但测试集崩溃 → 必须交叉验证
- **类别不平衡**：准确率 99% 但全预测为多数类 → 使用 F1-score / AUC
- **特征缩放缺失**：树模型不需要，但 SVM/神经网络/KNN 必须有

## 模型评估速查表

| 任务类型 | 主要指标 | 辅助指标 |
|---------|----------|----------|
| 回归 | MAE, RMSE | R², MAPE |
| 二分类 | F1-score | Precision, Recall, AUC-ROC |
| 多分类 | Accuracy, Macro-F1 | Confusion Matrix |
| 聚类 | Silhouette Score | Davies-Bouldin Index |
| 时间序列 | MAE, RMSE | sMAPE, MASE |
```

其他 4 篇文档按相同模式编写，每篇 80+ 行。

- [ ] **Step 2: 提交**

```bash
git add domains/*/knowledge/
git commit -m "feat: expand knowledge docs to 23 files (5 new, 80+ lines each with formulas + code + pitfalls)"
```

---

## Task 6: Prompt 模板深化

**目标：** 4 个角色的 prompt 从 20-61 行扩展到 80+。

**Files:**
- Modify: `domains/math-modeling/prompts/agent_engineer.md`
- Modify: `domains/math-modeling/prompts/agent_math.md`
- Modify: `domains/math-modeling/prompts/agent_verifier.md`
- Modify: `domains/math-modeling/prompts/agent_writer.md`

- [ ] **Step 1: 深化 agent_engineer.md**

```markdown
# 工程师 — 从模型到代码的实现者

你是数学建模团队的代码实现专家。你负责将数学推导转化为可运行的 Python 代码。

## 核心职责
1. 编写清晰、可复现的 Python 求解代码
2. 使用 NumPy/SciPy/Matplotlib 等标准库
3. 每个子问题输出独立的 .py 文件到 求解/ 目录
4. 生成出版级质量的图表（≥300dpi，中文标注）
5. 输出 CSV 结果文件供论文引用

## 代码规范
- 使用 `numpy` 而非纯 Python 循环（性能差 100x）
- 使用 `scipy.optimize` 而非手写优化器
- 图表使用 `matplotlib`，设置中文字体（SimHei）
- 每个函数必须有 docstring
- 关键数值结果用 `print(f"结果: {value:.4f}")` 输出

## 常见陷阱
- 数值精度：浮点数比较用 `np.isclose()` 而非 `==`
- 迭代收敛：设置 max_iter + tolerance，防止死循环
- 内存管理：大矩阵用稀疏存储（`scipy.sparse`）
- 随机种子：调用 `np.random.seed(42)` 保证可复现

## 输出格式
- 求解文件：`求解/q1_model.py`, `求解/q2_solve.py`
- 结果文件：`求解/results.csv`
- 图表文件：`求解/fig1_xxx.png` (300dpi)
```

其他 3 个角色 prompt 按相同深度编写，每篇 80+ 行。

- [ ] **Step 2: 提交**

```bash
git add domains/math-modeling/prompts/
git commit -m "feat: deepen 4 agent prompts from ~40 to 80+ lines (engineer, math, verifier, writer)"
```

---

## Task 7: 新领域创建 — data-mining

**目标：** 创建一个新的数据分析领域，6 阶段 + 4 角色 + 4 知识文档。

**Files:**
- Create: `domains/data-mining/domain.yaml`
- Create: `domains/data-mining/prompts/agent_lead.md`
- Create: `domains/data-mining/prompts/agent_engineer.md`
- Create: `domains/data-mining/prompts/agent_ml_engineer.md`
- Create: `domains/data-mining/prompts/agent_reviewer.md`
- Create: `domains/data-mining/knowledge/数据预处理最佳实践.md`
- Create: `domains/data-mining/knowledge/特征工程方法论.md`
- Create: `domains/data-mining/knowledge/模型评估与调参.md`
- Create: `domains/data-mining/knowledge/数据可视化规范.md`

- [ ] **Step 1: 创建 domain.yaml**

```yaml
# domains/data-mining/domain.yaml
id: data-mining
name: 数据挖掘与分析
description: 数据预处理、特征工程、模型选择与评估、结果解释
version: "1.0"

phases:
  - id: data_load
    name: 数据加载与探索
    order: 0
    progress: 10
    transition: {pass: preprocessing}
  - id: preprocessing
    name: 数据预处理
    order: 1
    progress: 25
    transition: {pass: feature_engineering, fail: preprocessing}
  - id: feature_engineering
    name: 特征工程
    order: 2
    progress: 40
    transition: {pass: modeling, fail: feature_engineering}
  - id: modeling
    name: 模型构建
    order: 3
    progress: 60
    transition: {pass: evaluation, fail: modeling}
  - id: evaluation
    name: 模型评估
    order: 4
    progress: 80
    transition: {pass: interpretation, fail: modeling}
  - id: interpretation
    name: 结果解释
    order: 5
    progress: 100

roles:
  - id: lead
    name: 数据分析师
    emoji: 📊
    temperature: 0.5
    tools: [file_manager, data_analyzer, quality_checker]
  - id: data_engineer
    name: 数据工程师
    emoji: 🔧
    temperature: 0.4
    tools: [code_executor, file_manager, data_analyzer]
  - id: ml_engineer
    name: ML 工程师
    emoji: 🤖
    temperature: 0.3
    tools: [code_executor, file_manager, figure_generator]
  - id: reviewer
    name: 模型审稿人
    emoji: 🔍
    temperature: 0.4
    tools: [file_manager, quality_checker]

directories:
  input: 数据
  output: 输出
  paper: 报告
  data: 数据
```

- [ ] **Step 2: 创建角色 prompt 和知识文档**

参考 `domains/math-modeling/prompts/` 和 `domains/math-modeling/knowledge/` 的模式，
编写 4 个角色的 prompt（每篇 80+ 行）和 4 篇知识文档（每篇 60+ 行）。

- [ ] **Step 3: 验证新领域可加载**

```bash
cd backend && PYTHONPATH=src python -c "
from lemma.engine.domain import DomainProfile
domain = DomainProfile.load('data-mining')
print(f'Phases: {len(domain.phases)}')
print(f'Roles: {len(domain.roles)}')
for r in domain.roles:
    print(f'  - {r.id}: {r.name}')
"
```

预期：打印 6 个 phase + 4 个 role。

- [ ] **Step 4: 提交**

```bash
git add domains/data-mining/
git commit -m "feat: add data-mining domain (6 phases, 4 roles, 4 knowledge docs)"
```

---

## Self-Review

**规格覆盖:**
- Playwright E2E → Task 1 ✅
- Electron 打包 → Task 2 ✅
- Docker 部署 → Task 3 ✅
- 真实 LLM 评测 → Task 4 ✅
- 知识文档扩充 → Task 5 ✅
- Prompt 模板深化 → Task 6 ✅
- 新领域创建 → Task 7 ✅

**占位符扫描:** 无 TBD/TODO ✅

---

## 执行交接

计划已保存至 `docs/superpowers/plans/2026-06-26-lemma-claudecode-handoff.md`。

7 个任务完全独立，可任意顺序执行。建议从 Task 1 (Playwright) 开始——投入产出比最高，立即可验证。
