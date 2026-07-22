#!/usr/bin/env python3
"""
去AI味检测工具 (V8.2)

检测论文 .tex 文件中的AI写作痕迹。
输出 AI 味指数（0-100，越低越好）。

用法：
  python 审稿/check_ai_taste.py 论文/论文_完整版.tex
  python 审稿/check_ai_taste.py --dir 论文/
"""

import argparse
import os
import re
import sys
from collections import Counter


# ── 检测规则 ────────────────────────────────────────────────

# AI 高频词（直接扣分）
AI_PHRASES = [
    "值得注意的是",
    "综上所述",
    "在当今社会",
    "随着科技的发展",
    "随着社会的进步",
    "具有重要意义",
    "发挥着重要作用",
    "取得了显著成效",
    "提供了有力支撑",
    "具有广阔的应用前景",
    "为了解决这一问题",
    "本文提出了一种新的",
    "通过以上分析可以看出",
    "总而言之",
    "由此可见",
    "不难发现",
    "显而易见",
    "众所周知",
]

# 模板化连接词
TEMPLATE_PHRASES = [
    "本文首先",
    "然后",
    "最后",
    "针对问题一",
    "针对问题二",
    "针对问题三",
    "针对问题四",
    "针对问题五",
]

# 问题罗列模式
PROBLEM_LIST_PATTERN = re.compile(
    r"针对问题[一二三四五六七八九十\d]"
)


# ── 检测函数 ────────────────────────────────────────────────

def check_ai_phrases(text: str) -> dict:
    """检测AI高频词"""
    found = []
    for phrase in AI_PHRASES:
        count = text.count(phrase)
        if count > 0:
            found.append({"phrase": phrase, "count": count})
    return {
        "name": "AI高频词",
        "found": found,
        "total": sum(f["count"] for f in found),
        "score": min(100, sum(f["count"] for f in found) * 5),  # 每次出现扣5分
    }


def check_template_phrases(text: str) -> dict:
    """检测模板化连接词"""
    found = []
    for phrase in TEMPLATE_PHRASES:
        count = text.count(phrase)
        if count > 0:
            found.append({"phrase": phrase, "count": count})
    return {
        "name": "模板化连接词",
        "found": found,
        "total": sum(f["count"] for f in found),
        "score": min(100, sum(f["count"] for f in found) * 3),  # 每次出现扣3分
    }


def check_problem_list(text: str) -> dict:
    """检测问题罗列模式"""
    matches = PROBLEM_LIST_PATTERN.findall(text)
    return {
        "name": "问题罗列",
        "found": [{"phrase": m, "count": 1} for m in matches],
        "total": len(matches),
        "score": min(100, max(0, (len(matches) - 3) * 10)),  # 超过3次开始扣分
    }


def check_sentence_repetition(text: str) -> dict:
    """检测句式重复度"""
    # 提取每句话的前5个字符作为句式指纹
    sentences = re.split(r'[。！？\n]', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    if len(sentences) < 5:
        return {"name": "句式重复", "found": [], "total": 0, "score": 0}

    # 统计开头词重复
    starts = [s[:5] for s in sentences]
    counter = Counter(starts)
    repeated = {k: v for k, v in counter.items() if v >= 3}

    return {
        "name": "句式重复",
        "found": [{"phrase": k, "count": v} for k, v in repeated.items()],
        "total": sum(v for v in repeated.values()),
        "score": min(100, sum(v - 2 for v in repeated.values()) * 5),  # 重复3次以上每次扣5分
    }


def check_paragraph_length(text: str) -> dict:
    """检测段落长度分布"""
    paragraphs = text.split("\n\n")
    paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 50]

    if len(paragraphs) < 3:
        return {"name": "段落长度", "found": [], "total": 0, "score": 0}

    lengths = [len(p) for p in paragraphs]
    avg = sum(lengths) / len(lengths)
    std = (sum((l - avg) ** 2 for l in lengths) / len(lengths)) ** 0.5

    # 如果标准差太小，说明段落长度太均匀（AI特征）
    if std < 50:
        return {
            "name": "段落长度",
            "found": [{"phrase": f"段落长度标准差={std:.0f}（过小）", "count": 1}],
            "total": 1,
            "score": 30,
        }

    return {"name": "段落长度", "found": [], "total": 0, "score": 0}


# ── 主函数 ──────────────────────────────────────────────────

def analyze_file(filepath: str) -> dict:
    """分析单个文件"""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    checks = [
        check_ai_phrases(text),
        check_template_phrases(text),
        check_problem_list(text),
        check_sentence_repetition(text),
        check_paragraph_length(text),
    ]

    total_score = min(100, sum(c["score"] for c in checks))
    total_issues = sum(c["total"] for c in checks)

    return {
        "file": filepath,
        "total_score": total_score,
        "total_issues": total_issues,
        "checks": checks,
        "grade": (
            "✅ 优秀" if total_score < 20
            else "🟡 一般" if total_score < 50
            else "🔴 较差"
        ),
    }


def print_report(result: dict) -> None:
    """打印报告"""
    print(f"\n{'=' * 60}")
    print(f"AI味检测报告：{os.path.basename(result['file'])}")
    print(f"{'=' * 60}")
    print(f"AI味指数：{result['total_score']}/100 — {result['grade']}")
    print(f"问题总数：{result['total_issues']}")
    print()

    for check in result["checks"]:
        if check["total"] > 0:
            print(f"  {check['name']}（扣{check['score']}分）：")
            for f in check["found"][:5]:  # 最多显示5个
                print(f"    - \"{f['phrase']}\" × {f['count']}")
            if len(check["found"]) > 5:
                print(f"    ... 还有 {len(check['found']) - 5} 个")
        else:
            print(f"  {check['name']}：✅ 无问题")

    print()


def main():
    parser = argparse.ArgumentParser(description="去AI味检测工具")
    parser.add_argument("file", nargs="?", help="单个 .tex 文件")
    parser.add_argument("--dir", help="目录下所有 .tex 文件")
    parser.add_argument("--threshold", type=int, default=50, help="阈值（默认50）")
    args = parser.parse_args()

    if args.dir:
        files = [
            os.path.join(args.dir, f)
            for f in os.listdir(args.dir)
            if f.endswith(".tex")
        ]
    elif args.file:
        files = [args.file]
    else:
        parser.print_help()
        return

    for filepath in files:
        if os.path.exists(filepath):
            result = analyze_file(filepath)
            print_report(result)
        else:
            print(f"文件不存在：{filepath}")


if __name__ == "__main__":
    main()
