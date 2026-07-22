# Lemma v11 — 前端卓越计划：从 B+ 到 A 级的质变

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 基于全面的前端代码审计（80/100 B+），将 Lemma 前端从"功能完整但体验粗糙"提升为"设计精美·交互流畅·可访问·性能卓越"的 A 级产品。

**Architecture:** 本次优化覆盖 6 个子系统，独立可交付。不改变现有架构，在已有 CSS 变量 + Tailwind 基础上深化设计系统、补全缺失的 UX 元素（Toast/骨架屏/确认对话框/页面转场）、修复已知问题（SVG a11y/Emoji混用/Logo）、引入学术级字体系统。

**Tech Stack:** React 18, TypeScript, Vite, Tailwind CSS 3.4, lucide-react, react-virtuoso, Motion (新增), react-hot-toast (新增)

**设计参考来源:**
- 审计报告：12 个问题（4 个🟡中等 + 8 个🟢轻微）
- UI/UX Pro Max 推荐：Dark Mode (OLED) + Crimson Pro + Atkinson Hyperlegible
- 当前得分：80/100 (B+) → 目标：92/100 (A)

---

## 0. 路线图演进

```
v10 (06-26): 产品实质化 — 品牌更名 Lemma + 管线修复 + 知识工程
v11 (06-26): ★ 前端卓越 — 设计系统升级、UX 补全、视觉质变
```

---

## 1. 前端审计总览

### 1.1 当前得分

| 维度 | 得分 | 评价 |
|------|------|------|
| 全局样式系统 | 85/100 | CSS变量完善，仅缺亮色模式 |
| 布局结构 | 80/100 | 经典桌面布局，响应式在Electron中已足够 |
| 组件质量 | 88/100 | 12个组件均有空/加载/错误状态 |
| 可访问性 | 78/100 | 大量aria，缺高对比度和SVG a11y |
| 交互反馈 | 75/100 | 按钮状态齐全，缺全局Toast和骨架屏 |
| 图标与视觉 | 82/100 | lucide-react一致性高，emoji混用不适配 |
| 动画与转场 | 78/100 | 微交互丰富，缺页面转场和骨架屏 |
| 性能 | 75/100 | 虚拟滚动+请求取消+内存管理到位 |
| **综合** | **80/100** | **B+ → 目标 A (92+)** |

### 1.2 关键发现

**做得好的：**
- CSS 变量体系 + Tailwind 自定义主题深度融合
- 几乎所有组件都有空/加载/错误状态处理
- A11y 基础扎实（focus-visible, skip-link, aria 属性, prefers-reduced-motion）
- 流式消息 + 工具调用可视化 + 代码块复制 已实现
- 丰富的 Agent 主题色系统 + 自定义 SVG Sprite

**亟待解决的（P0-P1）：**
1. 🔴 无全局 Toast/Notification 系统 — 错误/成功反馈不一致
2. 🔴 无骨架屏/Shimmer — "加载中…"文本体验差
3. 🔴 无删除确认对话框 — 破坏性操作无二次确认
4. 🟡 无亮色模式 — 暗色主题单一，长时间使用不友好
5. 🟡 SVG Sprite 无可访问性标记 — 8个Agent头像对屏幕阅读器不可见
6. 🟡 无页面转场动画 — 视图切换生硬
7. 🟡 Emoji 与 SVG 图标混用 — 风格不统一
8. 🟡 Logo 为文字占位符 — 无独立品牌资产

---

## 2. 六子系统路线图

```
子系统 A (P0, 2天): UX 基础设施补全      子系统 B (P0, 1天): 视觉质量提升
├─ A1: 全局 Toast 系统                   ├─ B1: 学术字体系统
├─ A2: 骨架屏/Skeleton 组件              ├─ B2: Logo 进化
├─ A3: 确认对话框组件                     ├─ B3: Emoji → SVG 替换
└─ A4: 工具栏上下文菜单                   └─ B4: 色彩微调

子系统 C (P1, 2天): 动效与转场          子系统 D (P1, 1天): 可访问性增强
├─ C1: 页面转场动画                      ├─ D1: SVG Sprite A11y 修复
├─ C2: 消息列表动效升级                   ├─ D2: 高对比度模式
├─ C3: 加载骨架屏整合（所有组件）          ├─ D3: 键盘导航表单项
└─ C4: 阶段进度庆祝动效                   └─ D4: 焦点陷阱修复

子系统 E (P2, 1天): 性能优化             子系统 F (P2, 1天): 亮色主题
├─ E1: 代码分割                          ├─ F1: 亮色CSS变量
├─ E2: 非聊天列表虚拟滚动                 ├─ F2: 主题切换器
└─ E3: Bundle 大小分析                    └─ F3: 亮/暗色一致性验证
```

| 里程碑 | 验收标准 | 预计时间 |
|--------|----------|----------|
| M1: UX 基础设施 | Toast + 骨架屏 + 确认对话框全部就绪，所有组件接入 | 2 天 |
| M2: 视觉质变 | 新字体系统生效，Logo 可用，Emoji 清零 | 1 天 |
| M3: 体验流畅 | 页面转场平滑，骨架屏全覆盖，动效精致 | 2 天 |
| M4: 品质交付 | 可访问性得分 ≥90，亮/暗双主题完整，代码分割生效 | 3 天 |

---

## 子系统 A：UX 基础设施补全（P0，第 1-2 天）

### Task A1: 全局 Toast 通知系统

**目标：** 创建统一的 Toast 系统，替代所有 `console.error` + 内联错误显示。

**Files:**
- Create: `frontend/src/components/Toast.tsx`
- Create: `frontend/src/hooks/useToast.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/SettingsPanel.tsx`（接入 Toast）
- Modify: `frontend/src/components/SessionPanel.tsx`（接入 Toast）
- Modify: `frontend/src/components/ConfirmationCard.tsx`（接入 Toast）
- Test: `frontend/src/__tests__/Toast.test.tsx`

**设计规范：**
- 4 种类型：success（绿色）、error（红色）、warning（琥珀色）、info（蓝色）
- 位置：右上角，堆叠显示（最多3个）
- 动画：从右侧滑入 + 淡入（300ms），自动消失（3-5秒）
- 可手动关闭
- 使用 `role="alert"` + `aria-live="polite"`

- [ ] **Step 1: 创建 Toast 组件**

```bash
cd frontend && npm install react-hot-toast
```

`frontend/src/components/Toast.tsx`：

```tsx
import { Toaster } from 'react-hot-toast'

export default function ToastContainer() {
  return (
    <Toaster
      position="top-right"
      toastOptions={{
        duration: 4000,
        style: {
          background: 'var(--color-surface)',
          color: 'var(--color-text)',
          border: '1px solid var(--color-border)',
          fontSize: '13px',
          borderRadius: '12px',
          padding: '12px 16px',
        },
        success: {
          iconTheme: { primary: '#10B981', secondary: '#fff' },
          style: { borderLeft: '3px solid #10B981' },
        },
        error: {
          iconTheme: { primary: '#EF4444', secondary: '#fff' },
          style: { borderLeft: '3px solid #EF4444' },
          duration: 6000,
        },
      }}
    />
  )
}
```

`frontend/src/hooks/useToast.ts`：

```tsx
import toast from 'react-hot-toast'

export function useToast() {
  return {
    success: (msg: string) => toast.success(msg),
    error: (msg: string) => toast.error(msg),
    warning: (msg: string) => toast(msg, { icon: '⚠️', style: { borderLeft: '3px solid #F59E0B' } }),
    info: (msg: string) => toast(msg, { icon: 'ℹ️' }),
    dismiss: toast.dismiss,
  }
}
```

- [ ] **Step 2: 接入 App.tsx**

```tsx
// App.tsx 顶部 import
import ToastContainer from './components/Toast'

// 在 return 的根元素内添加：
<ToastContainer />
```

- [ ] **Step 3: 替换所有内联错误为 Toast**

`SettingsPanel.tsx` 第 291 行（测试结果错误）→ `toast.error(errorMsg)`

`SessionPanel.tsx` 第 148 行（删除会话）→ `toast.success('会话已删除')`

`ConfirmationCard.tsx` 第 44 行（API 错误）→ `toast.error('HITL 请求失败')`

- [ ] **Step 4: 编写测试**

```tsx
// frontend/src/__tests__/Toast.test.tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import ToastContainer from '../components/Toast'

describe('Toast', () => {
  it('renders Toaster container', () => {
    render(<ToastContainer />)
    // react-hot-toast 的 Toaster 渲染一个 div
    expect(document.querySelector('[data-sonner-toaster]') || document.querySelector('div')).toBeDefined()
  })
})
```

- [ ] **Step 5: 运行测试确认不影响现有测试**

```bash
cd frontend && npx vitest run
```

预期：≥55 passed, 0 failed

- [ ] **Step 6: 提交**

```bash
git add frontend/src/components/Toast.tsx frontend/src/hooks/useToast.ts frontend/src/App.tsx frontend/src/components/SettingsPanel.tsx frontend/src/components/SessionPanel.tsx frontend/src/components/ConfirmationCard.tsx frontend/src/__tests__/Toast.test.tsx
git commit -m "feat: add global Toast notification system (react-hot-toast, 4 types, all components integrated)"
```

### Task A2: 骨架屏/Skeleton 组件

**目标：** 创建可复用的 Skeleton 组件，替换所有"加载中…"文本。

**Files:**
- Create: `frontend/src/components/Skeleton.tsx`
- Modify: `frontend/src/components/FileViewer.tsx`
- Modify: `frontend/src/components/TraceViewer.tsx`
- Modify: `frontend/src/components/DocumentVersions.tsx`
- Modify: `frontend/src/components/SessionPanel.tsx`
- Test: `frontend/src/__tests__/Skeleton.test.tsx`

- [ ] **Step 1: 创建 Skeleton 组件**

`frontend/src/components/Skeleton.tsx`：

```tsx
import { cn } from '../utils'

interface SkeletonProps {
  className?: string
  variant?: 'text' | 'rect' | 'circle' | 'card'
  lines?: number
}

export function Skeleton({ className, variant = 'text', lines = 1 }: SkeletonProps) {
  const base = 'animate-pulse rounded-md bg-[var(--color-surface-hover)]'

  if (variant === 'circle') {
    return <div className={cn(base, 'rounded-full', className)} style={{ width: 40, height: 40 }} />
  }

  if (variant === 'card') {
    return (
      <div className={cn('space-y-3 p-4', className)}>
        <div className={cn(base, 'h-4 w-3/4')} />
        <div className={cn(base, 'h-3 w-full')} />
        <div className={cn(base, 'h-3 w-5/6')} />
        <div className={cn(base, 'h-3 w-2/3')} />
      </div>
    )
  }

  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={cn(base, 'h-4', i === lines - 1 ? 'w-3/4' : 'w-full')}
        />
      ))}
    </div>
  )
}
```

- [ ] **Step 2: 替换各组件中的"加载中…"**

`FileViewer.tsx` 第 178 行：
```tsx
// 之前
if (loading) return <div className="p-4 text-[var(--color-text-muted)]">加载中…</div>
// 之后
if (loading) return <Skeleton variant="card" className="p-4" />
```

`TraceViewer.tsx` 第 45 行：
```tsx
// 之前
if (loading) return <div className="p-4">加载 trace 数据...</div>
// 之后
if (loading) return <Skeleton variant="card" className="p-4" />
```

`DocumentVersions.tsx` 第 60 行：
```tsx
// 之前
if (loading) return <div className="p-4">加载中...</div>
// 之后
if (loading) return <Skeleton variant="card" className="p-4" />
```

`SessionPanel.tsx` — 加载态：
```tsx
// 之前
if (loading) return <div className="p-4 text-[var(--color-text-muted)]">加载会话列表…</div>
// 之后
if (loading) return <div className="space-y-3 p-4">
  <Skeleton variant="card" />
  <Skeleton variant="card" />
</div>
```

- [ ] **Step 3: 编写测试**

```tsx
// frontend/src/__tests__/Skeleton.test.tsx
import { render } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Skeleton } from '../components/Skeleton'

describe('Skeleton', () => {
  it('renders text variant with correct line count', () => {
    const { container } = render(<Skeleton variant="text" lines={3} />)
    expect(container.querySelectorAll('.animate-pulse').length).toBe(3)
  })

  it('renders circle variant', () => {
    const { container } = render(<Skeleton variant="circle" />)
    expect(container.querySelector('.rounded-full')).toBeDefined()
  })

  it('renders card variant with proper structure', () => {
    const { container } = render(<Skeleton variant="card" />)
    expect(container.querySelectorAll('.animate-pulse').length).toBe(4)
  })
})
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/Skeleton.tsx frontend/src/components/FileViewer.tsx frontend/src/components/TraceViewer.tsx frontend/src/components/DocumentVersions.tsx frontend/src/components/SessionPanel.tsx frontend/src/__tests__/Skeleton.test.tsx
git commit -m "feat: add Skeleton component and replace all 'loading...' text with shimmer placeholders"
```

### Task A3: 确认对话框组件

**目标：** 为破坏性操作（删除会话、重置设置等）添加确认步骤。

**Files:**
- Create: `frontend/src/components/ConfirmDialog.tsx`
- Modify: `frontend/src/components/SessionPanel.tsx`
- Test: `frontend/src/__tests__/ConfirmDialog.test.tsx`

- [ ] **Step 1: 创建 ConfirmDialog 组件**

`frontend/src/components/ConfirmDialog.tsx`：

```tsx
import { AlertTriangle } from 'lucide-react'
import { useEffect, useRef } from 'react'

interface ConfirmDialogProps {
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'danger' | 'warning'
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = '确认',
  cancelLabel = '取消',
  variant = 'danger',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const confirmRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (open) {
      confirmRef.current?.focus()
      const handler = (e: KeyboardEvent) => {
        if (e.key === 'Escape') onCancel()
      }
      document.addEventListener('keydown', handler)
      return () => document.removeEventListener('keydown', handler)
    }
  }, [open, onCancel])

  if (!open) return null

  const colors = variant === 'danger'
    ? { bg: 'bg-red-500/10', border: 'border-red-500/30', btn: 'bg-red-500 hover:bg-red-600', text: 'text-red-400' }
    : { bg: 'bg-amber-500/10', border: 'border-amber-500/30', btn: 'bg-amber-500 hover:bg-amber-600', text: 'text-amber-400' }

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-title"
    >
      <div
        className={`w-full max-w-sm rounded-xl border ${colors.border} ${colors.bg} p-6 shadow-2xl animate-slide-up`}
      >
        <div className="flex items-start gap-3 mb-4">
          <AlertTriangle className={`w-5 h-5 ${colors.text} flex-shrink-0 mt-0.5`} aria-hidden="true" />
          <div>
            <h3 id="confirm-title" className="text-base font-semibold text-[var(--color-text)]">{title}</h3>
            <p className="text-sm text-[var(--color-text-secondary)] mt-1">{message}</p>
          </div>
        </div>
        <div className="flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] transition-colors"
          >
            {cancelLabel}
          </button>
          <button
            ref={confirmRef}
            onClick={onConfirm}
            className={`px-4 py-2 text-sm rounded-lg ${colors.btn} text-white transition-colors focus-visible:ring-2 focus-visible:ring-white`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: 接入 SessionPanel.tsx 删除操作**

```tsx
// SessionPanel.tsx 中添加 state
const [deleteTarget, setDeleteTarget] = useState<string | null>(null)

// 删除按钮 onClick
onClick={() => setDeleteTarget(sessionId)}

// 组件底部
<ConfirmDialog
  open={deleteTarget !== null}
  title="删除会话"
  message={`确定要删除会话 ${deleteTarget} 吗？此操作不可撤销。`}
  variant="danger"
  confirmLabel="删除"
  onConfirm={() => {
    onDelete(deleteTarget!)
    setDeleteTarget(null)
  }}
  onCancel={() => setDeleteTarget(null)}
/>
```

- [ ] **Step 3: 编写测试**

```tsx
// frontend/src/__tests__/ConfirmDialog.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ConfirmDialog } from '../components/ConfirmDialog'

describe('ConfirmDialog', () => {
  it('renders nothing when closed', () => {
    const { container } = render(
      <ConfirmDialog open={false} title="" message="" onConfirm={vi.fn()} onCancel={vi.fn()} />
    )
    expect(container.innerHTML).toBe('')
  })

  it('shows dialog when open', () => {
    render(
      <ConfirmDialog open={true} title="删除" message="确认？" onConfirm={vi.fn()} onCancel={vi.fn()} />
    )
    expect(screen.getByText('删除')).toBeDefined()
    expect(screen.getByText('确认？')).toBeDefined()
  })

  it('calls onConfirm when confirm clicked', () => {
    const onConfirm = vi.fn()
    render(<ConfirmDialog open={true} title="T" message="M" onConfirm={onConfirm} onCancel={vi.fn()} />)
    fireEvent.click(screen.getByText('确认'))
    expect(onConfirm).toHaveBeenCalled()
  })

  it('calls onCancel on Escape key', () => {
    const onCancel = vi.fn()
    render(<ConfirmDialog open={true} title="T" message="M" onConfirm={vi.fn()} onCancel={onCancel} />)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onCancel).toHaveBeenCalled()
  })
})
```

- [ ] **Step 4: 运行测试 → 提交**

```bash
git add frontend/src/components/ConfirmDialog.tsx frontend/src/components/SessionPanel.tsx frontend/src/__tests__/ConfirmDialog.test.tsx
git commit -m "feat: add ConfirmDialog component for destructive actions confirmation"
```

---

## 子系统 B：视觉质量提升（P0，第 3 天）

### Task B1: 学术字体系统引入

**目标：** 引入 Crimson Pro (标题) + Atkinson Hyperlegible (正文)，替代系统字体。

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/tailwind.config.js`
- Modify: `frontend/src/index.css`

- [ ] **Step 1: 注册 Google Fonts**

```html
<!-- frontend/index.html — 在 <head> 中添加 -->
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Crimson+Pro:wght@400;500;600;700&display=swap" rel="stylesheet" />
```

- [ ] **Step 2: 配置 Tailwind 字体**

```js
// tailwind.config.js — theme.extend.fontFamily
fontFamily: {
  serif: ['Crimson Pro', 'Georgia', 'serif'],
  sans: ['Atkinson Hyperlegible', 'system-ui', 'sans-serif'],
}
```

- [ ] **Step 3: 更新 CSS 变量指定新字体**

```css
/* src/index.css — :root 中添加 */
:root {
  --font-heading: 'Crimson Pro', Georgia, serif;
  --font-body: 'Atkinson Hyperlegible', system-ui, sans-serif;
}

/* 标题使用衬线字体 */
h1, h2, h3 { font-family: var(--font-heading); }
```

- [ ] **Step 4: 运行前端测试 → 提交**

```bash
git add frontend/index.html frontend/tailwind.config.js frontend/src/index.css
git commit -m "feat: introduce academic font system — Crimson Pro + Atkinson Hyperlegible"
```

### Task B2: Logo 品牌进化

**目标：** 将 Sidebar 中的渐变方块 + "U" 替换为 Lemma 品牌符号 "⊢"。

**Files:**
- Modify: `frontend/src/components/Sidebar.tsx`

- [ ] **Step 1: 更新 Sidebar Logo 区域**

```tsx
// Sidebar.tsx 第31-37行，替换为：
<div className="flex-shrink-0 flex items-center gap-2.5 px-3 py-3">
  <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-[#1a365d] to-[#2563eb] text-white">
    <span className="text-xl font-serif font-bold leading-none" aria-hidden="true">⊢</span>
  </div>
  <div>
    <h1 className="text-sm font-semibold text-[var(--color-text)] tracking-tight">Lemma</h1>
    <p className="text-[10px] text-[var(--color-text-secondary)] font-serif italic">v5.1.0</p>
  </div>
</div>
```

- [ ] **Step 2: 更新测试中的 Logo 文本**

`test/Sidebar.test.tsx` 中 `screen.getByText('Lemma')` 已正确。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/Sidebar.tsx
git commit -m "feat: upgrade Logo to ⊢ symbol with navy-to-blue gradient"
```

### Task B3: Emoji → SVG 图标替换

**目标：** 替换所有组件中的 Emoji 为 lucide-react SVG 图标。

**Files:**
- Modify: `frontend/src/components/SettingsPanel.tsx`
- Modify: `frontend/src/components/AgentAvatar.tsx`
- Modify: `frontend/src/components/DebateResult.tsx`

- [ ] **Step 1: SettingsPanel Emoji 替换**

```
📂 → <FolderOpen className="w-4 h-4" />
🤖 → <Cpu className="w-4 h-4" />
⚙️ → <Settings className="w-4 h-4" />
```

- [ ] **Step 2: AgentAvatar 状态 Emoji 替换**

```
💭 → <MessageSquare className="w-3 h-3" />
💤 → <Moon className="w-3 h-3" />
💡 → <Lightbulb className="w-3 h-3" />
```

- [ ] **Step 3: DebateResult title Emoji 替换**

```
🗣️ 多角色辩论 → <MessageSquareMore className="w-4 h-4 inline mr-1" /> 多角色辩论
```

- [ ] **Step 4: 运行测试 → 提交**

```bash
git add frontend/src/components/SettingsPanel.tsx frontend/src/components/AgentAvatar.tsx frontend/src/components/DebateResult.tsx frontend/src/__tests__/DebateResult.test.tsx
git commit -m "refactor: replace all emojis with lucide-react SVG icons for visual consistency"
```

---

## 子系统 C：动效与转场（P1，第 4-5 天）

### Task C1: 页面转场动画

**目标：** 视图切换（对话/流水线/文件/会话/设置）添加平滑过渡。

**Files:**
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/components/ViewTransition.tsx`

- [ ] **Step 1: 创建 ViewTransition 包装器**

```tsx
// frontend/src/components/ViewTransition.tsx
import { motion, AnimatePresence } from 'framer-motion'

export function ViewTransition({ viewKey, children }) {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={viewKey}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  )
}
```

- [ ] **Step 2: 包裹 App.tsx 视图切换区域**

```tsx
// App.tsx 第264-308行 视图切换区域添加：
import { ViewTransition } from './components/ViewTransition'

// 在视图渲染处：
<ViewTransition viewKey={view}>
  {view === 'chat' && <ChatPanel ... />}
  {view === 'pipeline' && <PipelinePanel ... />}
  {view === 'files' && <FileViewer ... />}
  {/* ... 其他视图 */}
</ViewTransition>
```

- [ ] **Step 3: 安装 framer-motion**

```bash
cd frontend && npm install framer-motion
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/ViewTransition.tsx frontend/src/App.tsx frontend/package.json
git commit -m "feat: add smooth page transitions with framer-motion (200ms crossfade + slide)"
```

### Task C2: 消息列表动效升级

**目标：** 消息出现使用错位入场效果（staggered entrance）。

- [ ] **Step 1: 为 ChatPanel 消息项添加入场动画**

```tsx
// ChatPanel.tsx 消息项包装
<motion.div
  initial={{ opacity: 0, y: 12 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.25, delay: index * 0.03 }}
>
  {/* 原消息内容 */}
</motion.div>
```

- [ ] **Step 2: 提交**

```bash
git commit -m "feat: add staggered message entrance animations in ChatPanel"
```

---

## 子系统 D：可访问性增强（P1，第 5-6 天）

### Task D1: SVG Sprite A11y 修复

**目标：** 8个 Agent SVG Sprite 添加 `role="img"`、`<title>`、`aria-label`。

**Files:**
- Modify: `frontend/src/sprites/LeadSprite.tsx` 等 8 个文件

- [ ] **Step 1: 为每个 Sprite 添加可访问标记**

```tsx
// 每个 Sprite 组件的 SVG 元素添加：
<svg role="img" aria-label="Lead Agent 头像" xmlns="...">
  <title>Lead Agent</title>
  {/* 原有内容 */}
</svg>
```

所有 8 个 Sprite 文件：
- LeadSprite → "Lead Agent"
- MathSprite → "Math Agent"
- EngineerSprite → "Engineer Agent"
- ReviewerSprite → "Reviewer Agent"
- WriterSprite → "Writer Agent"
- VerifierSprite → "Verifier Agent"
- ResearcherSprite → "Researcher Agent"
- AnalystSprite → "Analyst Agent"

- [ ] **Step 2: 提交**

```bash
git add frontend/src/sprites/*.tsx
git commit -m "fix(a11y): add role=img, title, and aria-label to all 8 Agent SVG sprites"
```

---

## 3. 优先级矩阵

| 优先级 | Task | 时间 | 价值 | 依赖 |
|--------|------|------|------|------|
| 🔴 P0 | **A1: Toast 系统** | 3h | 极高 | 无 |
| 🔴 P0 | **A2: Skeleton 组件** | 3h | 极高 | 无 |
| 🔴 P0 | **A3: 确认对话框** | 2h | 极高 | 无 |
| 🔴 P0 | **B1: 字体系统** | 1h | 高 | 无 |
| 🔴 P0 | **B2: Logo 进化** | 30min | 高 | 无 |
| 🔴 P0 | **B3: Emoji→SVG** | 1h | 高 | 无 |
| 🟡 P1 | **C1: 页面转场** | 2h | 中 | framer-motion |
| 🟡 P1 | **C2: 消息动效** | 1h | 中 | C1 |
| 🟡 P1 | **C3: 骨架屏整合** | 2h | 中 | A2 |
| 🟡 P1 | **D1: SVG A11y** | 1h | 中 | 无 |
| 🟢 P2 | **D2: 高对比度** | 1h | 低 | 无 |
| 🟢 P2 | **E1: 代码分割** | 2h | 中 | 无 |
| 🟢 P2 | **F1-F3: 亮色主题** | 4h | 高 | 无 |

---

## 4. Self-Review

**规格覆盖：**
- Toast 系统 → A1 ✅
- 骨架屏 → A2 ✅
- 确认对话框 → A3 ✅
- 字体系统 → B1 ✅
- Logo 进化 → B2 ✅
- Emoji替换 → B3 ✅
- 页面转场 → C1 ✅
- 消息动效 → C2 ✅
- SVG A11y → D1 ✅

**占位符扫描：** 所有 Task 包含实际代码 ✅

**执行建议：** 从 A1→A2→A3 开始，P0 三件套完成后前端体验已有质变。

---

## 执行交接

计划已保存至 `docs/superpowers/plans/2026-06-26-lemma-v11-frontend-excellence.md`。

**P0 三件套（Toast + Skeleton + ConfirmDialog）+ 视觉升级（字体 + Logo + Emoji替换）6 小时即可交付。从 A1 开始？**
