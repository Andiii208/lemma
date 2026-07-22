# 领域开发指南

## 概述

Lemma 通过 Domain Profile 支持多领域。创建新领域只需：
1. 创建领域目录和 `domain.yaml`
2. 编写角色 prompt 文件
3. （可选）添加知识文档和模板

系统启动时会自动扫描 `domains/` 目录，无需注册。

## 目录结构

```
domains/
  my-domain/
    domain.yaml              # 必需：领域配置
    prompts/
      agent_lead.md          # 必需：角色 prompt
      agent_writer.md        # 每个角色一个文件
    knowledge/               # 可选：领域知识
    templates/               # 可选：文档模板
```

## domain.yaml 格式

```yaml
id: my-domain                # 唯一标识（目录名）
name: 我的领域               # 显示名称
description: 这是一个示例领域
version: "1.0"

# 阶段定义
phases:
  - id: idle                 # 空闲阶段（必需）
    name: 空闲
    order: -1
    progress: 0
    transition: {pass: start}

  - id: start
    name: 开始
    order: 0
    progress: 20
    transition: {pass: middle, fail: start}

  - id: middle
    name: 中间
    order: 1
    progress: 60
    transition: {pass: done, fail: middle}

  - id: done                 # 完成阶段（必需）
    name: 完成
    order: 2
    progress: 100

# 角色定义
roles:
  - id: lead                 # 角色 ID（对应 prompts/agent_lead.md）
    name: 领队
    emoji: 🎯
    temperature: 0.5
    tools: [file_manager]    # 该角色可使用的工具

  - id: writer
    name: 写手
    emoji: ✍️
    temperature: 0.7
    tools: [file_manager, latex_compiler]

# 目录约定
directories:
  input: input               # 输入目录
  output: output             # 输出目录
  paper: paper               # 论文目录

# 阶段验证器（可选）
validators:
  - phase: middle
    check: files_exist
    glob: "{output_dir}/*.py"
  - phase: done
    check: json
    path: "{output_dir}/result.json"

# 阶段处理器 prompt 模板
phase_handlers:
  start: |
    请开始处理以下输入：
    {input_text}
    {context_sections}
  middle: |
    请继续完成中间阶段的工作。
    {context_sections}
```

## 角色 Prompt 文件

每个角色在 `prompts/agent_<role_id>.md` 中定义 system prompt。

### Prompt 编写规范

1. **角色定义**: 第一行用 `# 角色名` 标题
2. **职责说明**: 列出该角色的核心职责
3. **工作原则**: 定义行为约束
4. **交接格式**: 定义标准化的输出格式

### 交接格式模板

每个角色的 prompt 末尾应包含交接表格式：

```markdown
## 交接格式
每次完成阶段后，输出以下表格：

| 字段 | 内容 |
|------|------|
| 结论 | [一句话总结] |
| 置信度 | green/yellow/red |
| 未解决分歧 | [如有] |
| 下游警告 | [如有] |
```

## 阶段处理器（Phase Handlers）

阶段处理器定义每个阶段发送给 LLM 的 prompt 模板。

### 模板变量

- `{input_text}`: 用户输入的原始文本
- `{context_sections}`: 已完成阶段的上下文摘要
- `{output_dir}`: 输出目录名
- `{paper_dir}`: 论文目录名

### 编写建议

1. **明确指令**: 告诉 LLM 具体要做什么
2. **结构化输出**: 要求 LLM 按特定格式输出
3. **引用上下文**: 使用 `{context_sections}` 引用前序工作
4. **设置边界**: 明确该阶段的范围，避免越界

## 验证器（Validators）

验证器在阶段完成后检查产出物。

### 验证类型

- `json`: 验证文件是有效 JSON
- `files_exist`: 验证匹配 glob 模式的文件存在

### 路径变量

- `{output_dir}`: 替换为 `directories.output` 的值
- `{paper_dir}`: 替换为 `directories.paper` 的值

## 工具系统

可用工具列表：
- `file_manager`: 文件读写列表
- `code_executor`: Python 代码执行（带沙箱）
- `latex_compiler`: LaTeX 编译
- `quality_checker`: 质量检查
- `figure_generator`: 图表生成

在角色定义中通过 `tools` 字段指定可用工具。

## 测试新领域

1. 创建领域目录和文件
2. 运行验证脚本：

```python
from ultramath.engine.domain import DomainProfile
p = DomainProfile.from_directory('domains/my-domain')
print(f"Phases: {p.get_phase_ids()}")
print(f"Roles: {[r.id for r in p.roles]}")
print(f"Handlers: {list(p.phase_handlers.keys())}")
```

3. 启动后端，在前端选择新领域测试
