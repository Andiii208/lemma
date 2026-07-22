# 审稿编排 — V8.2 全链路质量版

> V8.2 变更：阻断项四级化 + 三阶段审稿流程 + 写作质量门禁。
> 详见 `审稿框架V8.2系统级优化方案.md`。

## V8.2 关键变更

| 维度 | V7.0 | V8.2 |
|------|------|------|
| 评分体系 | 105 分制（AI 自创） | 四维度定性分档（CUMCM 官方溯源） |
| 阻断项 | 二元（阻断/不阻断） | 四级（BLOCK/MAJOR/MINOR/NOTE） |
| 审稿范围 | 仅摘要 | 摘要 + 5-8 个关键页 |
| 创造性判断 | 无标准 | 三级定义 + 9 个真实案例 |
| 写作质量 | 无检查 | 4 个质量门禁 + AI味检测 |
| 终止条件 | total_score < 70 | 🔴 BLOCK 级阻断项触发 |

## 三轮审稿流程

```
Round 1 (delegate_task): 数学审稿 → 输出 求解/审稿_R1_数学.json
    ↓ 如果有 severity=BLOCK 且 fixer="Agent_M"
Agent M 修复 → Agent W 重编译

Round 2 (delegate_task): 代码审稿 → 输出 求解/审稿_R2_代码.json
    ↓ 如果有 severity=BLOCK 且 fixer="Agent_E"
Agent E 修复 → 重跑代码 → Agent W 重编译

Round 3 (delegate_task): 论文审稿（V8.1 三阶段）→ 输出 求解/审稿_R3_论文.md
    阶段 0：结构识别（关键页定位）
    阶段 1：摘要初审（阻断项四级判断）
    阶段 2：关键页验证（验证摘要声明）
    ↓ 如果 verdict = ⚠️ 需重做
Agent W 修复 → 重编译
```

## 参考

- `审稿/审稿_论文.md` — V8.1 四维度框架 + 三阶段流程
- `审稿/审稿_数学.md` — 数学审稿清单
- `审稿/审稿_代码.md` — 代码审稿清单
- `references/blocking_levels.md` — 阻断项四级定义
- `references/creativity_examples.md` — 创造性三级案例库
- `references/figure_patterns.md` — 图表模式库
- `审稿/check_ai_taste.py` — 去AI味检测脚本
