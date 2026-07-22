# Lemma 前端设计升级 — Agent 角色化可视化系统

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将前端从"开发者工具风"升级为"简洁高级 + 手绘角色化"的设计语言。每个 Agent 角色（数学家、工程师、作家等）获得独特的手绘简笔风格形象，Pipeline 变为可视化冒险地图，用户可以直接与角色化 Agent 交互。

**Architecture:** 分 4 个阶段。阶段一建立设计令牌系统和手绘角色 SVG 资产 → 阶段二角色化所有 Agent 展示（聊天头像 + 侧栏花名册）→ 阶段三 Pipeline 升级为"冒险地图"节点图 → 阶段四用户-Agent 交互系统（ping、私信、思维流）。

**Tech Stack:** React 18, TypeScript, Tailwind CSS 3.4, Framer Motion（已有依赖）, 纯 SVG 角色绘制（无外部美术资源）, CSS 关键帧动画

---

## 设计语言定义

### 视觉风格：手绘极简 + 游戏感

| 维度 | 当前 | 目标 |
|------|------|------|
| **图标** | Emoji（🧬⚡🎯） | 手绘 SVG 角色（简笔线条 + 柔和填充） |
| **配色** | 单一蓝色 + 灰阶 | 主色保留深蓝底，每个角色一个标志色（见下表） |
| **圆角** | `rounded-lg/xl/2xl` 混用 | 统一 `rounded-2xl`（16px）为主，`rounded-full` 仅状态点 |
| **动画** | 几乎无 | Framer Motion 驱动的角色浮动、进度脉动、消息入场 |
| **质感** | 纯色 + 半透明白 | 微噪点底纹 + 手绘描边 + 柔光阴影 |
| **排版** | 12-13px 密集 | 正文 14px，标题 16-18px，更呼吸 |

### Agent 角色色板

每个角色有专属标志色，用于头像、状态光晕、进度条：

| 角色 | 标志色 | Tailwind | 含义 |
|------|--------|----------|------|
| 主编/指挥 | 靛蓝 | `indigo-400` | 统筹 |
| 数学家 | 紫 | `violet-400` | 逻辑 |
| 工程师 | 青 | `cyan-400` | 构建 |
| 审稿人 | 琥珀 | `amber-400` | 评审 |
| 作家 | 玫红 | `rose-400` | 创意 |
| 验算员 | 翠绿 | `emerald-400` | 验证 |
| 研究员 | 天蓝 | `sky-400` | 探索 |
| 分析师 | 橙 | `orange-400` | 数据 |

---

## 阶段一：设计基础 — 令牌系统 + 角色资产（预计 2-3 天）

---

### Task 1.1: 建立设计令牌系统

**Files:**
- Modify: `frontend/src/index.css`
- Modify: `frontend/tailwind.config.js`
- Create: `frontend/src/styles/agent-theme.ts`

**目标:** 统一所有颜色到语义令牌，添加角色色板，定义手绘描边样式。

- [ ] **Step 1: 更新 index.css 设计令牌**

```css
@layer base {
  :root {
    /* 基础色 — 更深沉 */
    --color-bg: #080b14;
    --color-bg-secondary: #0f1420;
    --color-bg-tertiary: #1a1f2e;
    --color-text: #e8eaed;
    --color-text-secondary: #8b92a5;
    --color-text-muted: #5a6072;
    --color-border: #1a1f2e;
    --color-border-strong: #2a3041;
    
    /* 主色 */
    --color-primary: #6366f1;       /* indigo-500 */
    --color-primary-hover: #4f46e5;
    --color-primary-glow: rgba(99, 102, 241, 0.15);
    
    /* 角色标志色 */
    --agent-lead: #818cf8;          /* indigo-400 */
    --agent-math: #a78bfa;          /* violet-400 */
    --agent-engineer: #22d3ee;      /* cyan-400 */
    --agent-reviewer: #fbbf24;      /* amber-400 */
    --agent-writer: #fb7185;        /* rose-400 */
    --agent-verifier: #34d399;      /* emerald-400 */
    --agent-researcher: #38bdf8;    /* sky-400 */
    --agent-analyst: #fb923c;       /* orange-400 */
    
    /* 状态 */
    --color-success: #10b981;
    --color-warning: #f59e0b;
    --color-error: #ef4444;
    
    /* 手绘描边 */
    --stroke-sketch: 2.5;
    --shadow-soft: 0 4px 20px rgba(0, 0, 0, 0.3);
    --shadow-glow: 0 0 30px var(--color-primary-glow);
  }
  
  /* 微噪点底纹 */
  body {
    background-color: var(--color-bg);
    background-image: 
      radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.03), transparent 50%),
      radial-gradient(circle at 80% 80%, rgba(168, 85, 247, 0.02), transparent 50%);
  }
}
```

- [ ] **Step 2: 更新 tailwind.config.js 扩展配置**

```javascript
module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'agent-lead': '#818cf8',
        'agent-math': '#a78bfa',
        'agent-engineer': '#22d3ee',
        'agent-reviewer': '#fbbf24',
        'agent-writer': '#fb7185',
        'agent-verifier': '#34d399',
        'agent-researcher': '#38bdf8',
        'agent-analyst': '#fb923c',
      },
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'float-slow': 'float 5s ease-in-out infinite',
        'pulse-ring': 'pulse-ring 2s cubic-bezier(0.4,0,0.6,1) infinite',
        'thinking': 'thinking 1.5s ease-in-out infinite',
        'spark': 'spark 0.6s ease-out',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        'pulse-ring': {
          '0%': { transform: 'scale(0.8)', opacity: '0.8' },
          '100%': { transform: 'scale(1.4)', opacity: '0' },
        },
        thinking: {
          '0%, 100%': { opacity: '0.3', transform: 'scale(0.9)' },
          '50%': { opacity: '1', transform: 'scale(1.05)' },
        },
        spark: {
          '0%': { transform: 'scale(0) rotate(0deg)', opacity: '1' },
          '100%': { transform: 'scale(1.2) rotate(180deg)', opacity: '0' },
        },
      },
    },
  },
  plugins: [],
}
```

- [ ] **Step 3: 创建角色色板 TypeScript 模块**

创建 `frontend/src/styles/agent-theme.ts`：

```typescript
export interface AgentTheme {
  id: string
  name: string
  color: string        // 标志色
  colorSoft: string    // 柔和背景色 (10% opacity)
  glow: string         // 光晕色
  gradient: string     // 头像渐变
}

export const AGENT_THEMES: Record<string, AgentTheme> = {
  lead:       { id: 'lead',       name: '主编',     color: '#818cf8', colorSoft: 'rgba(129,140,248,0.1)',  glow: 'rgba(129,140,248,0.25)',  gradient: 'from-indigo-400 to-indigo-600' },
  math:       { id: 'math',       name: '数学家',   color: '#a78bfa', colorSoft: 'rgba(167,139,250,0.1)',  glow: 'rgba(167,139,250,0.25)',  gradient: 'from-violet-400 to-purple-600' },
  engineer:   { id: 'engineer',   name: '工程师',   color: '#22d3ee', colorSoft: 'rgba(34,211,238,0.1)',   glow: 'rgba(34,211,238,0.25)',   gradient: 'from-cyan-400 to-teal-600' },
  reviewer:   { id: 'reviewer',   name: '审稿人',   color: '#fbbf24', colorSoft: 'rgba(251,191,36,0.1)',   glow: 'rgba(251,191,36,0.25)',   gradient: 'from-amber-400 to-orange-600' },
  writer:     { id: 'writer',     name: '作家',     color: '#fb7185', colorSoft: 'rgba(251,113,133,0.1)',  glow: 'rgba(251,113,133,0.25)',  gradient: 'from-rose-400 to-pink-600' },
  verifier:   { id: 'verifier',   name: '验算员',   color: '#34d399', colorSoft: 'rgba(52,211,153,0.1)',   glow: 'rgba(52,211,153,0.25)',   gradient: 'from-emerald-400 to-green-600' },
  researcher: { id: 'researcher', name: '研究员',   color: '#38bdf8', colorSoft: 'rgba(56,189,248,0.1)',   glow: 'rgba(56,189,248,0.25)',   gradient: 'from-sky-400 to-blue-600' },
  analyst:    { id: 'analyst',    name: '分析师',   color: '#fb923c', colorSoft: 'rgba(251,146,60,0.1)',   glow: 'rgba(251,146,60,0.25)',   gradient: 'from-orange-400 to-red-600' },
}

export function getAgentTheme(roleId: string): AgentTheme {
  return AGENT_THEMES[roleId] || AGENT_THEMES.lead
}
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/index.css frontend/tailwind.config.js frontend/src/styles/agent-theme.ts
git commit -m "feat: establish design token system with agent color palette"
```

---

### Task 1.2: 创建手绘 Agent 角色 SVG 组件

**Files:**
- Create: `frontend/src/components/agents/AgentAvatar.tsx`
- Create: `frontend/src/components/agents/sprites/` (8 个角色 SVG)
- Create: `frontend/src/__tests__/AgentAvatar.test.tsx`

**设计:** 每个 Agent 是一个纯 SVG 手绘角色（元气骑士/简笔画风格）。用 `stroke-width: 2.5` 的粗线条 + 圆头线帽 + 柔和填充。不需要外部图片资源。

- [ ] **Step 1: 创建 AgentAvatar 组件容器**

```tsx
// frontend/src/components/agents/AgentAvatar.tsx
import React from 'react'
import { motion } from 'framer-motion'
import { getAgentTheme } from '../../styles/agent-theme'
import { LeadSprite, MathSprite, EngineerSprite, ReviewerSprite, WriterSprite, VerifierSprite } from './sprites'

interface AgentAvatarProps {
  roleId: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
  state?: 'idle' | 'thinking' | 'active' | 'sleeping'
  className?: string
}

const SIZES: Record<string, { box: number; ring: number }> = {
  sm: { box: 32, ring: 36 },
  md: { box: 44, ring: 50 },
  lg: { box: 64, ring: 72 },
  xl: { box: 96, ring: 108 },
}

const SPRITE_MAP: Record<string, React.FC<{ className?: string }>> = {
  lead: LeadSprite,
  math: MathSprite,
  engineer: EngineerSprite,
  reviewer: ReviewerSprite,
  writer: WriterSprite,
  verifier: VerifierSprite,
}

export default function AgentAvatar({ roleId, size = 'md', state = 'idle', className = '' }: AgentAvatarProps) {
  const theme = getAgentTheme(roleId)
  const Sprite = SPRITE_MAP[roleId] || LeadSprite
  const { box, ring } = SIZES[size]
  
  return (
    <div className={`relative inline-flex items-center justify-center ${className}`} style={{ width: ring, height: ring }}>
      {/* 光晕环 */}
      {(state === 'active' || state === 'thinking') && (
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{ boxShadow: `0 0 20px ${theme.glow}` }}
          animate={state === 'thinking' ? { scale: [1, 1.15, 1], opacity: [0.4, 0.8, 0.4] } : {}}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
      )}
      
      {/* 角色容器 */}
      <motion.div
        className="relative rounded-2xl flex items-center justify-center overflow-hidden"
        style={{
          width: box,
          height: box,
          background: `linear-gradient(135deg, ${theme.colorSoft}, transparent)`,
          border: `1.5px solid ${theme.color}40`,
        }}
        animate={
          state === 'idle' ? { y: [0, -4, 0] } :
          state === 'thinking' ? { rotate: [-2, 2, -2] } :
          state === 'active' ? { scale: [1, 1.05, 1] } :
          {}
        }
        transition={{ duration: state === 'idle' ? 3 : 2, repeat: Infinity, ease: 'easeInOut' }}
      >
        <Sprite className="w-3/4 h-3/4" />
      </motion.div>
      
      {/* 状态徽章 */}
      {state === 'thinking' && (
        <motion.div
          className="absolute -top-1 -right-1 text-xs"
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 1, repeat: Infinity }}
        >
          💭
        </motion.div>
      )}
      {state === 'sleeping' && (
        <div className="absolute -top-1 -right-1 text-xs opacity-50">💤</div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: 创建 6 个角色 SVG 精灵**

每个精灵是一个独立的 React 组件，导出纯 SVG。风格统一：粗线条 + 圆头帽 + 柔和填充。以下给出完整代码。

创建 `frontend/src/components/agents/sprites/LeadSprite.tsx`（主编 — 戴帽子的指挥官）：

```tsx
import React from 'react'

export default function LeadSprite({ className = '' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* 帽子 */}
      <path d="M20 22 L32 14 L44 22 L42 26 L22 26 Z" fill="#818cf8" fillOpacity="0.3" stroke="#818cf8" strokeWidth="2.5" strokeLinejoin="round"/>
      <circle cx="32" cy="16" r="2.5" fill="#818cf8"/>
      {/* 脸 */}
      <circle cx="32" cy="34" r="12" fill="#818cf8" fillOpacity="0.15" stroke="#818cf8" strokeWidth="2.5" strokeLinecap="round"/>
      {/* 眼睛 */}
      <circle cx="28" cy="33" r="1.5" fill="#818cf8"/>
      <circle cx="36" cy="33" r="1.5" fill="#818cf8"/>
      {/* 嘴 */}
      <path d="M29 38 Q32 40 35 38" stroke="#818cf8" strokeWidth="2" strokeLinecap="round" fill="none"/>
      {/* 身体 */}
      <path d="M24 44 Q32 42 40 44 L42 54 Q32 56 22 54 Z" fill="#818cf8" fillOpacity="0.2" stroke="#818cf8" strokeWidth="2.5" strokeLinejoin="round"/>
      {/* 星徽 */}
      <path d="M32 47 L33 49 L35 49 L33.5 50.5 L34 52.5 L32 51 L30 52.5 L30.5 50.5 L29 49 L31 49 Z" fill="#818cf8"/>
    </svg>
  )
}
```

创建 `frontend/src/components/agents/sprites/MathSprite.tsx`（数学家 — 戴眼镜、拿粉笔）：

```tsx
import React from 'react'

export default function MathSprite({ className = '' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* 头发 */}
      <path d="M22 24 Q24 16 32 15 Q40 16 42 24" stroke="#a78bfa" strokeWidth="2.5" strokeLinecap="round" fill="#a78bfa" fillOpacity="0.2"/>
      {/* 脸 */}
      <circle cx="32" cy="30" r="12" fill="#a78bfa" fillOpacity="0.15" stroke="#a78bfa" strokeWidth="2.5"/>
      {/* 眼镜 */}
      <circle cx="27" cy="29" r="4" stroke="#a78bfa" strokeWidth="2" fill="none"/>
      <circle cx="37" cy="29" r="4" stroke="#a78bfa" strokeWidth="2" fill="none"/>
      <line x1="31" y1="29" x2="33" y2="29" stroke="#a78bfa" strokeWidth="2"/>
      {/* 眼睛 */}
      <circle cx="27" cy="29" r="1" fill="#a78bfa"/>
      <circle cx="37" cy="29" r="1" fill="#a78bfa"/>
      {/* 嘴 */}
      <path d="M29 35 Q32 37 35 35" stroke="#a78bfa" strokeWidth="2" strokeLinecap="round" fill="none"/>
      {/* 身体 */}
      <path d="M24 40 Q32 38 40 40 L42 54 Q32 56 22 54 Z" fill="#a78bfa" fillOpacity="0.15" stroke="#a78bfa" strokeWidth="2.5" strokeLinejoin="round"/>
      {/* π 符号 */}
      <text x="32" y="50" textAnchor="middle" fontSize="8" fill="#a78bfa" fontFamily="serif" fontStyle="italic">π</text>
    </svg>
  )
}
```

创建 `frontend/src/components/agents/sprites/EngineerSprite.tsx`（工程师 — 安全帽 + 扳手）：

```tsx
import React from 'react'

export default function EngineerSprite({ className = '' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* 安全帽 */}
      <path d="M20 22 Q20 14 32 13 Q44 14 44 22" stroke="#22d3ee" strokeWidth="2.5" fill="#22d3ee" fillOpacity="0.2" strokeLinecap="round"/>
      <line x1="18" y1="22" x2="46" y2="22" stroke="#22d3ee" strokeWidth="2.5" strokeLinecap="round"/>
      {/* 脸 */}
      <circle cx="32" cy="30" r="11" fill="#22d3ee" fillOpacity="0.15" stroke="#22d3ee" strokeWidth="2.5"/>
      {/* 眼睛 */}
      <circle cx="28" cy="29" r="1.5" fill="#22d3ee"/>
      <circle cx="36" cy="29" r="1.5" fill="#22d3ee"/>
      {/* 嘴 */}
      <path d="M29 35 Q32 36 35 35" stroke="#22d3ee" strokeWidth="2" strokeLinecap="round" fill="none"/>
      {/* 身体 */}
      <path d="M24 40 Q32 38 40 40 L42 54 Q32 56 22 54 Z" fill="#22d3ee" fillOpacity="0.15" stroke="#22d3ee" strokeWidth="2.5" strokeLinejoin="round"/>
      {/* 扳手 */}
      <path d="M44 44 L50 38" stroke="#22d3ee" strokeWidth="2.5" strokeLinecap="round"/>
      <circle cx="51" cy="37" r="3" stroke="#22d3ee" strokeWidth="2" fill="none"/>
    </svg>
  )
}
```

创建 `frontend/src/components/agents/sprites/ReviewerSprite.tsx`（审稿人 — 放大镜）：

```tsx
import React from 'react'

export default function ReviewerSprite({ className = '' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* 头发 */}
      <path d="M22 22 Q24 14 32 14 Q40 14 42 22" stroke="#fbbf24" strokeWidth="2.5" fill="#fbbf24" fillOpacity="0.15" strokeLinecap="round"/>
      {/* 脸 */}
      <circle cx="32" cy="30" r="11" fill="#fbbf24" fillOpacity="0.12" stroke="#fbbf24" strokeWidth="2.5"/>
      {/* 眉毛（严肃） */}
      <line x1="25" y1="26" x2="30" y2="27" stroke="#fbbf24" strokeWidth="2" strokeLinecap="round"/>
      <line x1="34" y1="27" x2="39" y2="26" stroke="#fbbf24" strokeWidth="2" strokeLinecap="round"/>
      {/* 眼睛 */}
      <circle cx="28" cy="30" r="1.5" fill="#fbbf24"/>
      <circle cx="36" cy="30" r="1.5" fill="#fbbf24"/>
      {/* 嘴 */}
      <line x1="29" y1="36" x2="35" y2="36" stroke="#fbbf24" strokeWidth="2" strokeLinecap="round"/>
      {/* 身体 */}
      <path d="M24 40 Q32 38 40 40 L42 54 Q32 56 22 54 Z" fill="#fbbf24" fillOpacity="0.12" stroke="#fbbf24" strokeWidth="2.5" strokeLinejoin="round"/>
      {/* 放大镜 */}
      <circle cx="47" cy="45" r="4" stroke="#fbbf24" strokeWidth="2" fill="none"/>
      <line x1="50" y1="48" x2="54" y2="52" stroke="#fbbf24" strokeWidth="2.5" strokeLinecap="round"/>
    </svg>
  )
}
```

创建 `frontend/src/components/agents/sprites/WriterSprite.tsx`（作家 — 羽毛笔）：

```tsx
import React from 'react'

export default function WriterSprite({ className = '' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* 长发 */}
      <path d="M20 24 Q18 16 32 14 Q46 16 44 24 Q46 34 44 40 L42 38 Q44 28 40 26 L24 26 Q20 28 22 38 L20 40 Q18 34 20 24" fill="#fb7185" fillOpacity="0.2" stroke="#fb7185" strokeWidth="2.5" strokeLinejoin="round"/>
      {/* 脸 */}
      <circle cx="32" cy="30" r="10" fill="#fb7185" fillOpacity="0.12" stroke="#fb7185" strokeWidth="2.5"/>
      {/* 眼睛 */}
      <path d="M27 29 Q28 28 29 29" stroke="#fb7185" strokeWidth="2" strokeLinecap="round" fill="none"/>
      <path d="M35 29 Q36 28 37 29" stroke="#fb7185" strokeWidth="2" strokeLinecap="round" fill="none"/>
      {/* 微笑 */}
      <path d="M29 35 Q32 37 35 35" stroke="#fb7185" strokeWidth="2" strokeLinecap="round" fill="none"/>
      {/* 身体 */}
      <path d="M24 40 Q32 38 40 40 L42 54 Q32 56 22 54 Z" fill="#fb7185" fillOpacity="0.12" stroke="#fb7185" strokeWidth="2.5" strokeLinejoin="round"/>
      {/* 羽毛笔 */}
      <path d="M44 42 L50 36" stroke="#fb7185" strokeWidth="2.5" strokeLinecap="round"/>
      <path d="M48 34 Q52 32 54 36 Q52 38 48 38" fill="#fb7185" fillOpacity="0.3" stroke="#fb7185" strokeWidth="2"/>
    </svg>
  )
}
```

创建 `frontend/src/components/agents/sprites/VerifierSprite.tsx`（验算员 — 计算器）：

```tsx
import React from 'react'

export default function VerifierSprite({ className = '' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* 头发 */}
      <path d="M22 24 Q24 15 32 14 Q40 15 42 24" stroke="#34d399" strokeWidth="2.5" fill="#34d399" fillOpacity="0.15" strokeLinecap="round"/>
      {/* 脸 */}
      <circle cx="32" cy="30" r="11" fill="#34d399" fillOpacity="0.12" stroke="#34d399" strokeWidth="2.5"/>
      {/* 认真眯眼 */}
      <path d="M25 29 Q27 28 29 29" stroke="#34d399" strokeWidth="2" strokeLinecap="round" fill="none"/>
      <path d="M35 29 Q37 28 39 29" stroke="#34d399" strokeWidth="2" strokeLinecap="round" fill="none"/>
      {/* 嘴 */}
      <path d="M29 35 L35 35" stroke="#34d399" strokeWidth="2" strokeLinecap="round"/>
      {/* 身体 */}
      <path d="M24 40 Q32 38 40 40 L42 54 Q32 56 22 54 Z" fill="#34d399" fillOpacity="0.12" stroke="#34d399" strokeWidth="2.5" strokeLinejoin="round"/>
      {/* 勾号 */}
      <path d="M29 46 L31 48 L36 43" stroke="#34d399" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
    </svg>
  )
}
```

创建 `frontend/src/components/agents/sprites/index.ts`：

```typescript
export { default as LeadSprite } from './LeadSprite'
export { default as MathSprite } from './MathSprite'
export { default as EngineerSprite } from './EngineerSprite'
export { default as ReviewerSprite } from './ReviewerSprite'
export { default as WriterSprite } from './WriterSprite'
export { default as VerifierSprite } from './VerifierSprite'
```

- [ ] **Step 3: 编写 AgentAvatar 测试**

```tsx
// frontend/src/__tests__/AgentAvatar.test.tsx
import { render } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import AgentAvatar from '../components/agents/AgentAvatar'

describe('AgentAvatar', () => {
  it('renders without crash', () => {
    const { container } = render(<AgentAvatar roleId="math" />)
    expect(container.querySelector('svg')).toBeTruthy()
  })
  it('renders all known roles', () => {
    for (const role of ['lead', 'math', 'engineer', 'reviewer', 'writer', 'verifier']) {
      const { container } = render(<AgentAvatar roleId={role} />)
      expect(container.querySelector('svg')).toBeTruthy()
    }
  })
  it('renders unknown role as lead', () => {
    const { container } = render(<AgentAvatar roleId="nonexistent" />)
    expect(container.querySelector('svg')).toBeTruthy()
  })
})
```

- [ ] **Step 4: 运行测试**

```bash
cd frontend && npx vitest run
```

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/agents/ frontend/src/styles/ frontend/src/__tests__/AgentAvatar.test.tsx
git commit -m "feat: add hand-drawn agent character SVG sprites and AgentAvatar component"
```

---

## 阶段二：角色化展示 — 聊天 + 侧栏（预计 2-3 天）

---

### Task 2.1: ChatPanel 角色化头像

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx`

**目标:** 将消息气泡中的字母头像替换为对应角色的 AgentAvatar，添加角色状态指示。

- [ ] **Step 1: 导入 AgentAvatar 和主题**

在 ChatPanel.tsx 顶部添加：

```tsx
import AgentAvatar from './agents/AgentAvatar'
import { getAgentTheme } from '../styles/agent-theme'
```

- [ ] **Step 2: 替换 MessageBubble 中的头像**

将原来的 `<div className="w-7 h-7 rounded-lg bg-gradient-to-br ...">AI</div>` 替换为：

```tsx
const theme = getAgentTheme(message.agentRole || 'lead')

// 头像区域
<AgentAvatar
  roleId={message.agentRole || 'lead'}
  size="sm"
  state="idle"
/>
```

对于正在思考的 typing indicator，使用：

```tsx
<AgentAvatar
  roleId={agentStatus.currentRole}
  size="sm"
  state="thinking"
/>
```

- [ ] **Step 3: 更新角色选择器为带头像的下拉**

将 ROLES 数组保留作为 fallback，但在下拉菜单中用 AgentAvatar 替代 emoji：

```tsx
{showRoles && (
  <div className="absolute top-full left-0 mt-1 bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-2xl shadow-2xl z-50 py-1.5 min-w-[200px]">
    {roles.map(role => (
      <button
        key={role.id}
        onClick={() => { onSwitchRole(role.id); setShowRoles(false) }}
        className={`w-full flex items-center gap-2.5 px-3 py-2 text-sm transition-colors rounded-xl mx-1 ${
          currentRole === role.id
            ? `bg-white/[0.05]`
            : 'hover:bg-white/[0.03]'
        }`}
        style={currentRole === role.id ? { boxShadow: `inset 0 0 0 1.5px ${getAgentTheme(role.id).color}40` } : {}}
      >
        <AgentAvatar roleId={role.id} size="sm" state={currentRole === role.id ? 'active' : 'idle'} />
        <span style={{ color: currentRole === role.id ? getAgentTheme(role.id).color : undefined }}>
          {role.name}
        </span>
      </button>
    ))}
  </div>
)}
```

角色选择按钮本身也显示当前角色的头像：

```tsx
<button onClick={() => setShowRoles(!showRoles)} className="...">
  <AgentAvatar roleId={currentRole} size="sm" state="idle" />
  <span className="text-xs font-medium">{currentRoleName}</span>
  <svg className="w-3 h-3 text-[var(--color-text-secondary)]" ...>
</button>
```

- [ ] **Step 4: 消息气泡添加角色色边框**

```tsx
<div className={`inline-block rounded-2xl px-4 py-2.5 text-sm max-w-[85%] ${
  isUser
    ? 'bg-[var(--color-primary)] text-white rounded-tr-md'
    : 'rounded-tl-md border'
}`} style={!isUser ? {
  backgroundColor: theme.colorSoft,
  borderColor: `${theme.color}30`,
} : {}}>
```

- [ ] **Step 5: 运行测试并提交**

```bash
cd frontend && npx vitest run
git add .
git commit -m "feat: role-colorize chat messages with agent avatars and themed bubbles"
```

---

### Task 2.2: Sidebar Agent 花名册面板

**Files:**
- Modify: `frontend/src/components/Sidebar.tsx`
- Create: `frontend/src/components/AgentRoster.tsx`

**目标:** 在侧栏底部添加一个"Agent 花名册"，显示所有角色，当前激活角色高亮。

- [ ] **Step 1: 创建 AgentRoster 组件**

```tsx
// frontend/src/components/AgentRoster.tsx
import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import AgentAvatar from './agents/AgentAvatar'
import { getAgentTheme } from '../styles/agent-theme'

interface AgentRosterProps {
  roles: { id: string; name: string }[]
  activeRoleId: string
  isRunning: boolean
  onAgentClick?: (roleId: string) => void
}

export default function AgentRoster({ roles, activeRoleId, isRunning, onAgentClick }: AgentRosterProps) {
  return (
    <div className="px-3 py-2.5 border-t border-[var(--color-border)]">
      <div className="text-[9px] text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Agent 团队</div>
      <div className="grid grid-cols-3 gap-1.5">
        {roles.map(role => {
          const theme = getAgentTheme(role.id)
          const isActive = role.id === activeRoleId
          const state = isActive && isRunning ? 'thinking' : isActive ? 'active' : 'sleeping'
          
          return (
            <motion.button
              key={role.id}
              onClick={() => onAgentClick?.(role.id)}
              className="relative flex flex-col items-center gap-1 py-1.5 rounded-xl transition-colors hover:bg-white/[0.04]"
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.95 }}
            >
              <AgentAvatar roleId={role.id} size="sm" state={state as 'idle' | 'thinking' | 'active' | 'sleeping'} />
              <span className="text-[9px] text-center leading-tight" style={{ color: isActive ? theme.color : 'var(--color-text-muted)' }}>
                {role.name}
              </span>
              {isActive && (
                <motion.div
                  className="absolute inset-0 rounded-xl pointer-events-none"
                  style={{ boxShadow: `inset 0 0 0 1.5px ${theme.color}40` }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                />
              )}
            </motion.button>
          )
        })}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: 在 Sidebar 中集成 AgentRoster**

在 Sidebar.tsx 的"当前角色"卡片上方添加：

```tsx
import AgentRoster from './AgentRoster'

// 在 nav 和 状态区之间
{agentStatus.initialized && roles.length > 0 && (
  <AgentRoster
    roles={roles}
    activeRoleId={agentStatus.currentRole}
    isRunning={isRunning}
    onAgentClick={onSwitchRole}
  />
)}
```

- [ ] **Step 3: 更新 Sidebar props 接受 roles 和 onSwitchRole**

```tsx
interface SidebarProps {
  // ... existing
  roles: { id: string; name: string }[]
  isRunning: boolean
  onSwitchRole: (roleId: string) => void
}
```

- [ ] **Step 4: 从 App.tsx 传递 roles 数据**

```tsx
<Sidebar
  // ... existing
  roles={roles}
  isRunning={isRunning}
  onSwitchRole={switchRole}
/>
```

- [ ] **Step 5: 运行测试并提交**

---

## 阶段三：Pipeline 冒险地图可视化（预计 3-4 天）

---

### Task 3.1: 创建 AdventureMap 节点图组件

**Files:**
- Create: `frontend/src/components/AdventureMap.tsx`
- Modify: `frontend/src/components/PipelinePanel.tsx`

**目标:** 将 PipelinePanel 从扁平列表升级为"冒险地图"——节点用 AgentAvatar，连接线用手绘风格 SVG 路径，活跃节点有粒子动画。

- [ ] **Step 1: 创建 AdventureMap 组件**

```tsx
// frontend/src/components/AdventureMap.tsx
import React from 'react'
import { motion } from 'framer-motion'
import AgentAvatar from './agents/AgentAvatar'
import { getAgentTheme } from '../styles/agent-theme'
import { PhaseInfo } from '../App'

interface AdventureMapProps {
  phases: PhaseInfo[]
  activePhase: string | null
}

// 每个 phase 关联一个 agent 角色（从 phase→role 映射）
const PHASE_AGENT_MAP: Record<number, string> = {
  0: 'lead',       // 初始化 → 主编
  1: 'lead',       // 分析 → 主编
  2: 'math',       // 推导 → 数学家
  3: 'math',       // 本体 → 数学家
  4: 'engineer',   // 编码 → 工程师
  5: 'verifier',   // 测试 → 验算员
  6: 'writer',     // 写作 → 作家
  7: 'reviewer',   // 审稿 → 审稿人
}

export default function AdventureMap({ phases, activePhase }: AdventureMapProps) {
  const activePhases = phases.filter(p => p.id >= 0)  // 排除 idle/done
  
  return (
    <div className="relative py-8 px-4">
      {/* SVG 连接线层 */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
        {activePhases.slice(0, -1).map((phase, i) => {
          const next = activePhases[i + 1]
          const y1 = getNodeY(i, activePhases.length)
          const y2 = getNodeY(i + 1, activePhases.length)
          const isCompleted = phase.status === 'completed'
          
          return (
            <motion.path
              key={`line-${phase.id}`}
              d={`M 50% ${y1} Q 55% ${(y1+y2)/2} 50% ${y2}`}
              fill="none"
              stroke={isCompleted ? '#34d399' : 'var(--color-border-strong)'}
              strokeWidth="2"
              strokeDasharray="4 4"
              strokeLinecap="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: isCompleted ? 1 : 0.3 }}
              transition={{ duration: 0.8 }}
            />
          )
        })}
      </svg>
      
      {/* 节点层 */}
      <div className="relative space-y-6" style={{ zIndex: 1 }}>
        {activePhases.map((phase, i) => {
          const roleId = PHASE_AGENT_MAP[phase.id] || 'lead'
          const theme = getAgentTheme(roleId)
          const isActive = String(phase.id) === activePhase
          const isCompleted = phase.status === 'completed'
          const isFailed = phase.status === 'failed'
          
          const state = isActive ? 'thinking' : isCompleted ? 'idle' : 'sleeping'
          
          return (
            <motion.div
              key={phase.id}
              className="flex items-center gap-4 relative"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              {/* 节点头像 */}
              <div className="relative flex-shrink-0">
                <AgentAvatar roleId={roleId} size="lg" state={state as 'idle' | 'thinking' | 'sleeping'} />
                {isCompleted && (
                  <motion.div
                    className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center text-white text-xs"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 300 }}
                  >
                    ✓
                  </motion.div>
                )}
                {isFailed && (
                  <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-red-500 flex items-center justify-center text-white text-xs">
                    ✗
                  </div>
                )}
              </div>
              
              {/* 阶段信息卡 */}
              <motion.div
                className="flex-1 rounded-2xl p-4 border transition-all"
                style={{
                  backgroundColor: isActive ? theme.colorSoft : 'rgba(255,255,255,0.02)',
                  borderColor: isActive ? `${theme.color}40` : 'var(--color-border)',
                }}
                animate={isActive ? { boxShadow: `0 0 25px ${theme.glow}` } : {}}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium" style={{ color: isActive ? theme.color : 'var(--color-text)' }}>
                    {phase.name}
                  </span>
                  <span className="text-[10px] text-[var(--color-text-muted)] font-mono">
                    Phase {phase.id}
                  </span>
                </div>
                {phase.summary && (
                  <p className="text-xs text-[var(--color-text-secondary)] line-clamp-2 mt-1">
                    {phase.summary}
                  </p>
                )}
              </motion.div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}

function getNodeY(index: number, total: number): number {
  // 近似 Y 坐标（用于 SVG 路径）
  const cardHeight = 88 // lg avatar (72) + gap (16)
  const startY = 60 // padding top
  return startY + index * cardHeight + 36 // avatar center
}
```

- [ ] **Step 2: 在 PipelinePanel 中使用 AdventureMap 替代 PhaseCard 列表**

```tsx
import AdventureMap from './AdventureMap'

// 替换 phases.map → PhaseCard 部分
<AdventureMap
  phases={phases}
  activePhase={isRunning ? phases.find(p => p.status === 'running')?.id?.toString() || null : null}
/>
```

- [ ] **Step 3: 提交**

```bash
git add .
git commit -m "feat: replace flat phase list with AdventureMap node-graph visualization"
```

---

## 阶段四：用户-Agent 交互系统（预计 2-3 天）

---

### Task 4.1: Agent "思维流"浮窗

**Files:**
- Create: `frontend/src/components/AgentThoughts.tsx`
- Modify: `frontend/src/components/ChatPanel.tsx`

**目标:** 当一个 Agent 正在工作时，用户可以点击它的头像查看它的"思维过程"（实时 LLM 输出流）。

- [ ] **Step 1: 创建 AgentThoughts 浮窗组件**

```tsx
// frontend/src/components/AgentThoughts.tsx
import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import AgentAvatar from './agents/AgentAvatar'
import { getAgentTheme } from '../styles/agent-theme'

interface AgentThoughtsProps {
  roleId: string
  roleName: string
  visible: boolean
  onClose: () => void
  thoughts: string[]
}

export default function AgentThoughts({ roleId, roleName, visible, onClose, thoughts }: AgentThoughtsProps) {
  const theme = getAgentTheme(roleId)
  
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className="fixed bottom-24 right-6 w-80 z-50"
          initial={{ opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.95 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        >
          <div
            className="rounded-2xl border overflow-hidden backdrop-blur-xl"
            style={{
              backgroundColor: 'rgba(15, 20, 32, 0.95)',
              borderColor: `${theme.color}30`,
              boxShadow: `0 8px 40px ${theme.glow}`,
            }}
          >
            {/* 头部 */}
            <div className="flex items-center gap-3 p-3 border-b" style={{ borderColor: `${theme.color}20` }}>
              <AgentAvatar roleId={roleId} size="sm" state="thinking" />
              <div className="flex-1">
                <div className="text-sm font-medium" style={{ color: theme.color }}>{roleName}</div>
                <div className="text-[10px] text-[var(--color-text-muted)]">正在思考…</div>
              </div>
              <button onClick={onClose} className="text-[var(--color-text-muted)] hover:text-[var(--color-text)] text-lg">×</button>
            </div>
            
            {/* 思维流 */}
            <div className="p-3 max-h-48 overflow-y-auto space-y-1.5">
              {thoughts.length === 0 ? (
                <div className="text-xs text-[var(--color-text-muted)] text-center py-4">等待思维流…</div>
              ) : (
                thoughts.map((thought, i) => (
                  <motion.div
                    key={i}
                    className="text-xs text-[var(--color-text-secondary)] leading-relaxed"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.1 }}
                  >
                    {thought}
                  </motion.div>
                ))
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
```

- [ ] **Step 2: 在 ChatPanel 中添加点击头像打开思维流**

```tsx
const [thoughtsAgent, setThoughtsAgent] = useState<string | null>(null)

// 在 MessageBubble 的头像上添加 onClick
<AgentAvatar
  roleId={message.agentRole || 'lead'}
  size="sm"
  state="idle"
  className="cursor-pointer hover:scale-110 transition-transform"
/>
// 注意：AgentAvatar 需要包裹一个可点击的 div
```

- [ ] **Step 3: 提交**

---

### Task 4.2: Agent 快捷操作菜单

**Files:**
- Create: `frontend/src/components/AgentQuickMenu.tsx`
- Modify: `frontend/src/components/AgentRoster.tsx`

**目标:** 用户右键或长按 AgentRoster 中的角色，弹出快捷操作菜单（"向TA提问"、"查看产出物"、"切换为TA"）。

- [ ] **Step 1: 创建 AgentQuickMenu**

```tsx
// frontend/src/components/AgentQuickMenu.tsx
import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { getAgentTheme } from '../styles/agent-theme'

interface AgentQuickMenuProps {
  roleId: string
  x: number
  y: number
  visible: boolean
  onClose: () => void
  onAsk: (roleId: string) => void
  onViewArtifacts: (roleId: string) => void
  onSwitch: (roleId: string) => void
}

const ACTIONS = [
  { id: 'ask',       label: '💬 向 TA 提问',     desc: '直接与该角色对话' },
  { id: 'artifacts', label: '📦 查看 TA 的产出',  desc: '该角色创建的文件' },
  { id: 'switch',    label: '🔄 切换为 TA',       desc: '设为当前激活角色' },
]

export default function AgentQuickMenu({ roleId, x, y, visible, onClose, onAsk, onViewArtifacts, onSwitch }: AgentQuickMenuProps) {
  const theme = getAgentTheme(roleId)
  
  return (
    <AnimatePresence>
      {visible && (
        <>
          <div className="fixed inset-0 z-40" onClick={onClose} />
          <motion.div
            className="fixed z-50 w-56 rounded-2xl border overflow-hidden backdrop-blur-xl py-1.5"
            style={{
              left: x, top: y,
              backgroundColor: 'rgba(15, 20, 32, 0.97)',
              borderColor: `${theme.color}30`,
              boxShadow: `0 8px 40px rgba(0,0,0,0.4), 0 0 20px ${theme.glow}`,
            }}
            initial={{ opacity: 0, scale: 0.9, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: -10 }}
            transition={{ duration: 0.15 }}
          >
            <div className="px-3 py-1.5 text-[10px] uppercase tracking-wider" style={{ color: theme.color }}>
              {theme.name}
            </div>
            {ACTIONS.map(action => (
              <button
                key={action.id}
                onClick={() => {
                  if (action.id === 'ask') onAsk(roleId)
                  if (action.id === 'artifacts') onViewArtifacts(roleId)
                  if (action.id === 'switch') onSwitch(roleId)
                  onClose()
                }}
                className="w-full flex flex-col items-start px-3 py-2 hover:bg-white/[0.04] transition-colors text-left"
              >
                <span className="text-xs font-medium text-[var(--color-text)]">{action.label}</span>
                <span className="text-[10px] text-[var(--color-text-muted)]">{action.desc}</span>
              </button>
            ))}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
```

- [ ] **Step 2: 在 AgentRoster 中集成右键菜单**

```tsx
const [menuState, setMenuState] = useState<{ roleId: string; x: number; y: number } | null>(null)

// 在每个角色按钮上
onContextMenu={(e) => {
  e.preventDefault()
  setMenuState({ roleId: role.id, x: e.clientX, y: e.clientY })
}}

// 渲染菜单
<AgentQuickMenu
  roleId={menuState?.roleId || 'lead'}
  x={menuState?.x || 0}
  y={menuState?.y || 0}
  visible={!!menuState}
  onClose={() => setMenuState(null)}
  onAsk={(id) => { /* 切换到该角色并发送预设消息 */ }}
  onViewArtifacts={(id) => { /* 切换到文件视图并筛选 */ }}
  onSwitch={(id) => onAgentClick?.(id)}
/>
```

- [ ] **Step 3: 提交**

```bash
git add .
git commit -m "feat: add agent quick-action menu (ask/artifacts/switch) with context menu"
```

---

## 总结：执行路线

```
阶段一 (2-3天)          阶段二 (2-3天)
设计基础 ─────────────→ 角色化展示
├─ 设计令牌系统          ├─ ChatPanel 角色头像
├─ 8 个角色色板          ├─ 角色化消息气泡
└─ 6 个手绘 SVG 角色     └─ 侧栏 Agent 花名册

阶段三 (3-4天)          阶段四 (2-3天)
冒险地图 ─────────────→ 交互系统
├─ AdventureMap 节点图   ├─ 思维流浮窗
├─ 手绘连接线路径        ├─ 右键快捷菜单
└─ 粒子/光晕动画         └─ 直接 Agent 对话
```

| 里程碑 | 验收标准 |
|--------|----------|
| M1: 设计基础 | 8 色板可用，6 个 SVG 角色渲染无误，AgentAvatar 测试通过 |
| M2: 角色化 | 消息显示角色专属头像和颜色，侧栏显示 Agent 团队花名册 |
| M3: 冒险地图 | Pipeline 变为可视化节点图，活跃角色有动画 |
| M4: 交互 | 用户可点击头像查看思维流，右键 Agent 弹出操作菜单 |

**预估总工期：9-13 天**
