# Contributing to Lemma

感谢你对 Lemma 的兴趣！我们欢迎各种形式的贡献。

## 如何贡献

### 报告 Bug

1. 在 [GitHub Issues](https://github.com/lemma/lemma/issues) 搜索是否已有相同问题
2. 如果没有，创建新 Issue，包含：
   - 清晰的标题和描述
   - 复现步骤
   - 预期行为 vs 实际行为
   - 环境信息（OS、Node.js 版本）
   - 错误日志（如有）

### 提出新功能

1. 先在 Discussions 中讨论你的想法
2. 获得认可后，创建 Feature Request Issue
3. 描述使用场景和预期行为

### 提交代码

1. Fork 本仓库
2. 创建你的特性分支：`git checkout -b feature/amazing-feature`
3. 提交你的修改：`git commit -m 'feat: add amazing feature'`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 创建 Pull Request

## 开发环境设置

### 前置要求

- Node.js 20+
- Git

### 安装开发环境

```bash
# 克隆仓库
git clone https://github.com/lemma/lemma.git
cd lemma

# 安装依赖
npm ci
```

### 开发命令

```bash
# 启动开发模式（Vite + Electron）
npm run electron:dev

# 仅前端开发
npm run dev
```

### 代码质量

```bash
# 类型检查
npm run typecheck

# Lint
npm run lint

# 测试
npm test

# 测试覆盖率
npm run test:coverage
```

### 构建

```bash
# 构建前端
npm run build

# 打包桌面应用
npm run electron:build
```

## 代码风格

**TypeScript**
- 使用 ESLint：`npm run lint`
- 遵循 React Hooks 规范
- 使用 TypeScript 严格模式

**提交规范**

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具链相关

### 示例

```
feat(agent): add domain registry system

- Create registry.ts for YAML-based domain loading
- Add Zod schema validation
- Support 5 academic domains

Closes #123
```

## 创建新领域

Lemma 支持通过领域配置扩展功能。创建新领域的步骤：

### 1. 创建领域目录

```
domains/
  your-domain/
    domain.yaml           # 领域配置
    prompts/
      coordinator.md      # 协调者 prompt
    knowledge/
      topic1.md           # 领域知识文档
```

### 2. 编写 domain.yaml

```yaml
id: your-domain
name: 你的领域名称
description: 领域描述
version: "1.0"

phases:
  - id: idle
    name: 空闲
    order: -1
    progress: 0
    transition: {pass: analysis}

  - id: analysis
    name: 分析
    order: 0
    progress: 20
    transition: {pass: writing, fail: analysis}

  - id: writing
    name: 写作
    order: 1
    progress: 80
    transition: {pass: review, fail: writing}

  - id: review
    name: 审稿
    order: 2
    progress: 90
    transition: {pass: done, fail: writing}

  - id: done
    name: 完成
    order: 3
    progress: 100

roles:
  - id: lead
    name: 主编
    emoji: 🎯
    temperature: 0.5
    tools: [file_manager]

directories:
  input: 输入
  output: 输出
```

### 3. 编写角色 Prompt

每个角色需要一个 `coordinator.md` 或 `agent_<role_id>.md` 文件，定义其系统提示词。

### 4. 添加领域知识（可选）

在 `knowledge/` 目录下创建 Markdown 文档。

## Pull Request 流程

1. 确保所有测试通过：`npm test`
2. 确保类型检查通过：`npm run typecheck`
3. 确保 Lint 通过：`npm run lint`
4. 更新文档（如有必要）
5. 更新 CHANGELOG.md
6. 填写 PR 模板
7. 等待 Code Review
8. 合并到 main 分支

### PR 模板

```markdown
## 描述
简要描述你的修改

## 修改类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 重构
- [ ] 其他

## 测试
- [ ] 测试通过：`npm test`
- [ ] 类型检查通过：`npm run typecheck`
- [ ] Lint 通过：`npm run lint`
- [ ] 手动测试通过

## 相关 Issue
Closes #(issue number)

## 截图（如有 UI 变更）
```

## 行为准则

- 尊重所有参与者
- 接受建设性批评
- 专注于对社区最有利的事情
- 对他人表示同理心

## 许可证

通过贡献代码，你同意你的贡献将在 MIT 许可下发布。

## 联系方式

- GitHub Issues: 用于 Bug 报告和功能请求
- GitHub Discussions: 用于一般讨论和问题

感谢你的贡献！🎉
