#!/usr/bin/env python3
"""
UltraMath 算法效率检查脚本 — V9.0

用途: Phase 1 → 2 交接门禁。
验证 Agent M 产生的推导文件是否包含算法效率评估，以及推荐算法是否合理。

使用:
    python scripts/check_efficiency.py                                 # 扫描 求解/ 下所有推导
    python scripts/check_efficiency.py --dir 端到端测试/2024C/求解     # 指定目录
    python scripts/check_efficiency.py --derivation Q2_derivation.md   # 指定文件

返回状态码:
    0 = PASS (可进入 Phase 2)
    1 = WARN (有建议改进项)
    2 = BLOCK (必须重写推导)
"""

import argparse
import os
import re
import sys
from pathlib import Path

# ── 配置 ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent  # E:/数学建模/
VAR_THRESHOLD = 10_000        # 超过此变量数必须用分解算法
TIME_WARN_THRESHOLD = 300     # 估计求解时间 >5 分钟报 WARN

ALGORITHM_PRIORITY = [
    "解析解", "解析",
    "LP", "QP", "线性规划", "二次规划",
    "Benders", "列生成", "交替优化", "分解",
    "采样", "SAA", "渐进", "近似",
]
BRUTE_FORCE_KEYWORDS = [
    "全部展开", "全场景", "暴力", "brute", "单一大 MILP",
    "将全部场景展开", "所有场景", "全部组合",
]

# ── 检查项 ───────────────────────────────────────────────────────────

def check_efficiency_table(text: str, source: str) -> list[dict]:
    """检查是否含 ⚡ 计算可行性评估 表"""
    results = []
    if "⚡" in text:
        results.append({
            "item": "效率评估表存在性",
            "status": "PASS",
            "detail": f"{source}: 包含 ⚡ 计算可行性评估 表",
        })
    elif re.search(r'(?i)计算可行性|效率评估|算法选择', text):
        results.append({
            "item": "效率评估表存在性",
            "status": "WARN",
            "detail": f"{source}: 无 ⚡ 标识，但含类似章节",
        })
    else:
        results.append({
            "item": "效率评估表存在性",
            "status": "FAIL",
            "detail": f"{source}: 缺少 ⚡ 计算可行性评估 表（Agent M 可能未遵循 prompt）",
        })
    return results


def check_variable_scale(text: str, source: str) -> list[dict]:
    """估算变量/约束规模，判断是否超过阈值"""
    results = []
    var_patterns = [
        r'(?i)变量[数]?\s*[≈:=~]\s*([\d,]+)',
        r'(?i)变量[数]?\s*[:：]\s*≈?\s*([\d,]+)',
        r'(?i)\bN\s*=\s*(\d+)\b',
        r'(?i)场景[数]?\s*[≈:=~]\s*(\d+)',
    ]
    var_match = None
    for p in var_patterns:
        m = re.search(p, text)
        if m:
            val = int(m.group(1).replace(",", ""))
            if m.group(0).startswith(("N", "场景")) or m.group(0).startswith("场景"):
                # Not directly variable count, but scale indicator
                if "N" in m.group(0) or "场景" in m.group(0):
                    var_match = ("scenario", val)
            else:
                var_match = ("vars", val)
            break

    # Also look for explicit variable estimate in model classification section
    var_match_section = re.search(r'(?i)(?:变量[数]|variable)\s*[:：≈]\s*([\d,]+)', text)
    constraint_match = re.search(r'(?i)(?:约束[数]|constraint)\s*[:：≈]\s*([\d,]+)', text)

    var_val = int(var_match_section.group(1).replace(",", "")) if var_match_section else None

    results.append({
        "item": "变量规模估算",
        "status": "INFO",
        "detail": f"{source}: 估算变量数 ≈ {var_val:,}" if var_val else f"{source}: 未找到显式变量数",
    })

    if var_val and var_val > VAR_THRESHOLD:
        results.append({
            "item": "变量规模超标",
            "status": "WARN",
            "detail": f"变量数 {var_val:,} > {VAR_THRESHOLD:,}，建议使用分解或采样算法",
        })

    if constraint_match:
        cons_val = int(constraint_match.group(1).replace(",", ""))
        results.append({
            "item": "约束规模",
            "status": "INFO",
            "detail": f"{source}: 约束数 ≈ {cons_val:,}",
        })

    return results


def check_algorithm_choice(text: str, source: str) -> list[dict]:
    """检查推荐算法是否为暴力展开，以及是否有替代方案"""
    results = []

    # Check for brute force keywords
    for kw in BRUTE_FORCE_KEYWORDS:
        if kw.lower() in text.lower():
            results.append({
                "item": "暴力展开检测",
                "status": "FAIL",
                "detail": f"{source}: 检测到关键词「{kw}」，疑似暴力展开——禁止！",
            })
            break
    else:
        # Check if decomposition/approximation mentioned
        has_decomp = False
        for algo in ALGORITHM_PRIORITY:
            if algo.lower() in text.lower():
                has_decomp = True
                results.append({
                    "item": "高效算法存在性",
                    "status": "PASS",
                    "detail": f"{source}: 提及高效算法「{algo}」",
                })
                break

        if not has_decomp:
            results.append({
                "item": "高效算法存在性",
                "status": "WARN",
                "detail": f"{source}: 未检测到分解/采样/近似等高效算法",
            })

    # Check for alternative algorithm section
    if re.search(r'(?i)替代|降维|可选方案|备选', text):
        results.append({
            "item": "替代方案",
            "status": "PASS",
            "detail": f"{source}: 有备选/降维/替代方案讨论",
        })

    return results


def check_time_estimate(text: str, source: str) -> list[dict]:
    """检查是否有求解时间预估"""
    results = []
    time_pat = re.search(r'(?i)(\d+)\s*(s|秒|分|min|h|小时)', text)
    if time_pat:
        val = int(time_pat.group(1))
        unit = time_pat.group(2)
        if "分" in unit or "min" in unit.lower():
            seconds = val * 60
        elif "h" in unit.lower() or "小时" in unit:
            seconds = val * 3600
        else:
            seconds = val

        if seconds > TIME_WARN_THRESHOLD:
            results.append({
                "item": "求解时间预估",
                "status": "WARN",
                "detail": f"{source}: 预估求解时间约 {val}{unit}（>{TIME_WARN_THRESHOLD}s），建议优化",
            })
        else:
            results.append({
                "item": "求解时间预估",
                "status": "PASS",
                "detail": f"{source}: 预估求解时间约 {val}{unit}，在可接受范围内",
            })
    else:
        results.append({
            "item": "求解时间预估",
            "status": "WARN",
            "detail": f"{source}: 未提供求解时间估算",
        })
    return results


# ── 主流程 ───────────────────────────────────────────────────────────

def check_derivation_file(filepath: Path) -> list[dict]:
    """对单个推导文件执行全部效率检查"""
    text = filepath.read_text(encoding="utf-8", errors="replace")
    fname = filepath.name
    results = []

    results.extend(check_efficiency_table(text, fname))
    results.extend(check_variable_scale(text, fname))
    results.extend(check_algorithm_choice(text, fname))
    results.extend(check_time_estimate(text, fname))

    return results


def main():
    parser = argparse.ArgumentParser(description="UltraMath 算法效率检查")
    parser.add_argument("--dir", default=None, help="推导文件目录 (默认: 自动搜索求解/模型推导/)")
    parser.add_argument("--derivation", default=None, help="单个推导文件路径")
    args = parser.parse_args()

    if args.derivation:
        files = [Path(args.derivation)]
    elif args.dir:
        files = sorted(Path(args.dir).rglob("*.md"))
    else:
        # Auto-search: typical Phase 1 output locations
        search_dirs = [
            ROOT / "求解" / "模型推导",
            ROOT / "求解",
            ROOT / "端到端测试",
        ]
        files = []
        for d in search_dirs:
            if d.exists():
                files.extend(sorted(d.rglob("*.md")))

    if not files:
        print("❌ 未找到推导文件 (.md)")
        sys.exit(2)

    all_results = []
    for f in files:
        # Skip non-derivation files
        if any(skip in f.name for skip in ["TeamLead", "交叉验证", "审稿", "方案_", "CLAUDE", "SKILL"]):
            continue
        all_results.extend(check_derivation_file(f))

    # ── Aggregate ──
    passes = [r for r in all_results if r["status"] == "PASS"]
    warns = [r for r in all_results if r["status"] == "WARN"]
    fails = [r for r in all_results if r["status"] == "FAIL"]
    infos = [r for r in all_results if r["status"] == "INFO"]

    # ── Print report ──
    print("=" * 60)
    print("🔍 UltraMath 算法效率检查报告")
    print("=" * 60)

    if infos:
        print(f"\n📋 信息 ({len(infos)} 项):")
        for r in infos:
            print(f"  ℹ️  {r['detail']}")

    if passes:
        print(f"\n✅ 通过 ({len(passes)} 项):")
        for r in passes:
            print(f"  ✅ {r['detail']}")

    if warns:
        print(f"\n⚠️ 警告 ({len(warns)} 项):")
        for r in warns:
            print(f"  ⚠️  {r['detail']}")

    if fails:
        print(f"\n❌ 失败 ({len(fails)} 项):")
        for r in fails:
            print(f"  ❌ {r['detail']}")

    print("\n" + "=" * 60)
    verdict = "PASS" if not fails and not warns else \
              "WARN" if not fails else \
              "BLOCK"
    # 门禁分级标注：本脚本全部为基于正则+文本模式匹配的自动判定
    gate_tier = "[脚本验证]"
    gate_explain = "所有检查项均基于正则匹配和文本模式分析，可复现、无LLM参与"
    print(f"判定: {'✅ ' if verdict == 'PASS' else '⚠️ ' if verdict == 'WARN' else '🔴 '}{verdict}  {gate_tier}")
    print(f"  ℹ️  {gate_explain}")

    if verdict == "PASS":
        print("→ 可进入 Phase 2（代码生成）")
        sys.exit(0)
    elif verdict == "WARN":
        print("→ 建议 Agent M 补充效率评估信息后再启动 Phase 2")
        sys.exit(1)
    else:
        print("→ 🔴 BLOCKED！Agent M 需重写推导，选择高效分解/近似算法")
        print("  禁止将全部场景/组合暴力展开进单一 MILP")
        sys.exit(2)


if __name__ == "__main__":
    main()
