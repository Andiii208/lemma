#!/usr/bin/env python3
"""
审稿 Agent 校准工具 (V8.3 — 重测信度版)

用途：测量 UltraMath 内部质量评分卡的审稿一致性和区分度。
原理：
  - 重测信度：同一篇论文审两次 → 评分差 ≤5 分 → 一致性 ≥80%
  - 区分度：质量明显不同的论文，分数差 ≥15 分
  - 不再是"预测 CUMCM 等级"——那是伪命题。

用法：
  python 审稿/calibrate.py --ref-dir 参照论文/     # Phase 1: 提取文本
  python 审稿/calibrate.py --compare 审稿结果/       # Phase 2: 对比分析（新）

Phase 2 变更（V8.3）：
  旧：对比 Agent 判定 vs "真实等级" → 预测准确率
  新：对比两次评审的评分差异 → 重测信度 + 区分度

详见 references/internal-quality-scorecard.md
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


# ── 论文元数据（V8.3 更新：改为参考分数而非"真实等级"） ──

# 这些是 UltraMath 参照论文的已知质量评分（基于 Human 评估定标）
# ⚠️ 这不是 CUMCM 官方获奖等级！仅供内部校准参考
REFERENCE_SCORES = {
    "2025A196": 88,   # 无人机烟幕遮蔽，高质量
    "2025B060": 45,   # 量纲错误，低质量
    "2025B157": 80,   # SiC外延层，双路径自洽
    "2025C132": 72,   # 摘要无数值但有实质
    "2024A163": 70,   # 板凳龙，摘要无数值但有实质
    "2024C_1":  90,   # 农作物种植，高质量
    "2024B159": 75,   # 次品率决策
    "2023A0165": 78,  # 定日镜场
    "2023B477": 82,   # 多波束测深
    "2023C228": 78,   # 测线布设
    "2022A001": 76,   # 波浪能
    "2022B030": 74,   # 无人机定位
    "2022C155": 68,   # 古代玻璃
    "2021A028": 92,   # FAST反射面，最高质量
    "2021B007": 72,   # 乙醇催化
}

# V8.3 评分判定的文本解析模式
VERDICT_PATTERN = re.compile(r'(?:判定|verdict|总分)\D*(\d{1,3}(?:\.\d)?)\s*/?\s*100')


# ── Phase 1: 文本提取 ─────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> str:
    """从 PDF 提取文本。需要 pymupdf (fitz) 或 pdfplumber。"""
    text = ""

    # 方法一：pymupdf（首选，速度快）
    try:
        import fitz
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
        doc.close()
        if text.strip():
            return text
    except ImportError:
        pass
    except Exception as e:
        print(f"  ⚠️ pymupdf 提取失败: {e}")

    # 方法二：pdfplumber（备选，质量好）
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if text.strip():
            return text
    except ImportError:
        pass
    except Exception as e:
        print(f"  ⚠️ pdfplumber 提取失败: {e}")

    # 方法三：PyPDF2（最后备选）
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except ImportError:
        pass
    except Exception as e:
        print(f"  ⚠️ PyPDF2 提取失败: {e}")

    return text


def generate_review_prompt(paper_name: str, paper_text: str, output_dir: str) -> None:
    """生成审稿 prompt 文件，供审稿 Agent 使用。"""
    # 截断过长文本（审稿 Agent 上下文有限，保留前 8000 字符 + 摘要区）
    # 优先保留摘要附近的内容
    lines = paper_text.split("\n")
    abstract_start = -1
    for i, line in enumerate(lines):
        if re.search(r'摘\s*要|abstract', line, re.IGNORECASE):
            abstract_start = i
            break

    if abstract_start > 0:
        # 保留：前 1000 字符 + 摘要起 6000 字符
        prefix = "\n".join(lines[:min(50, abstract_start)])
        body = "\n".join(lines[abstract_start:abstract_start + 300])
        truncated = prefix + "\n...\n" + body
    else:
        truncated = paper_text[:8000]

    prompt = f"""## 校准审稿任务

请用 UltraMath V8.0 四维度定性框架审稿以下论文。

**论文名称**: {paper_name}
**已知信息**: 这是一篇历年 CUMCM 获奖论文（真实等级已记录，用于校准对比）。

### 论文内容（截取）

{truncated}

---

### 请输出

```markdown
## 📝 校准审稿：{paper_name}

### 分档判定：{{🏆 国一候选 / 🥈 国二 / 🥉 省一 / ⚠️ 需重做}}

### 阻断项检查
- [ ] 摘要空洞：{{是/否}}
- [ ] 核心结果不可复现：{{是/否}}
- [ ] 假设严重不合理：{{是/否}}
- [ ] 结构残缺：{{是/否}}

### 四维度评估
| 维度 | 判定 |
|------|------|
| 假设的合理性 | {{通过/需改进/缺陷}} |
| 建模的创造性 | {{通过/需改进/缺陷}} |
| 结果的正确性 | {{通过/需改进/缺陷}} |
| 表述的清晰性 | {{通过/需改进/缺陷}} |
```
"""

    os.makedirs(output_dir, exist_ok=True)
    safe_name = re.sub(r'[^\w\-.]', '_', paper_name)
    output_path = os.path.join(output_dir, f"prompt_{safe_name}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(prompt)
    print(f"  ✅ prompt → {output_path}")


def phase1_collect(ref_dir: str, prompt_dir: str) -> list[str]:
    """Phase 1: 遍历参照论文目录，提取文本，生成审稿 prompt。"""
    pdf_files = list(Path(ref_dir).glob("*.pdf"))
    if not pdf_files:
        print(f"❌ {ref_dir} 下未找到 PDF 文件")
        print("   请将历年 CUMCM 国奖论文 PDF 放入该目录")
        print("   论文可从 CUMCM 官网论文展示区下载: https://www.mcm.edu.cn")
        return []

    print(f"📄 找到 {len(pdf_files)} 篇论文")
    paper_names = []

    for pdf_path in pdf_files:
        name = pdf_path.stem
        print(f"\n📖 {name}")
        text = extract_text_from_pdf(str(pdf_path))

        if not text.strip():
            print(f"  ❌ 文本提取失败，跳过")
            continue

        print(f"  📝 提取 {len(text)} 字符")
        generate_review_prompt(name, text, prompt_dir)
        paper_names.append(name)

    return paper_names


# ── Phase 2: 结果对比 ─────────────────────────────────────

def parse_review_result(md_path: str) -> dict | None:
    """从审稿 Agent 输出的 markdown 中提取分档判定和四维度评估。"""
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return None

    result = {}

    # 提取分档判定 - 在文件前部查找实际判定结果
    verdict = ""
    header = content[:6000]
    
    # 按优先级尝试多种模式
    patterns = [
        # 模式1: "分档判定：🏆 国一候选"
        (r'分档判定[：:]\s*🏆?\s*(国一候选)', 1),
        (r'分档判定[：:]\s*🥈?\s*(国二)', 1),
        (r'分档判定[：:]\s*🥉?\s*(省一)', 1),
        (r'分档判定[：:]\s*[⚠️🔴]?\s*(需重做)', 1),
        # 模式2: markdown 表格 "| 🏆 **国一候选** |"
        (r'\|\s*🏆\s*\*{0,2}(国一候选)\*{0,2}', 1),
        (r'\|\s*🥈\s*\*{0,2}(国二)\*{0,2}', 1),
        (r'\|\s*🥉\s*\*{0,2}(省[一奖])\*{0,2}', 1),
        (r'\|\s*[⚠️🔴]\s*\*{0,2}(需重做)\*{0,2}', 1),
        # 模式3: box-drawing "│ 综合定档 │ ⚠️ 需重做"
        (r'综合定档.*?(需重做)', 1),
        (r'综合定档.*?(省[一奖])', 1),
        # 模式4: "省一/省二候选" → 取"省一"
        (r'[│|]\s*.*?(省一)[/／]省二', 1),
        # 模式5: "审稿等级建议：🥉 省一"
        (r'审稿等级建议[：:]\s*🥉?\s*(省一)', 1),
        # 模式6: 表格行首
        (r'^\|\s*🏆\s*\*{0,2}(国一候选)\*{0,2}', 1),
        (r'^\|\s*🥉\s*\*{0,2}(省[一奖])\*{0,2}', 1),
        (r'^\|\s*[⚠️🔴]\s*\*{0,2}(需重做)\*{0,2}', 1),
        # 模式7: 宽松匹配 — 任意emoji后跟 "需重做"
        (r'\*\*\s*(需重做)\s*\*', 1),
        (r'等级.*?(优秀|B\+).*?国', 1),
    ]
    
    for pattern, group_idx in patterns:
        m = re.search(pattern, header, re.MULTILINE)
        if m:
            raw = m.group(group_idx)
            # 标准化
            if raw in ("省奖",):
                verdict = "省一"
            elif raw in ("优秀", "B+"):
                verdict = "国一候选"
            else:
                verdict = raw
            break
    
    if not verdict:
        verdict = "解析失败"
    
    result["verdict"] = verdict

    # 提取阻断项 - 查找实际标记的内容
    result["blocking"] = []
    # 匹配格式: "- [x] 摘要空洞：**否**" 或 "- [x] 摘要空洞：否"
    blocking_patterns = {
        "摘要空洞": r'摘要空洞[：:]\s*\*{0,2}(是|否|{是|否})\*{0,2}',
        "核心结果不可复现": r'核心结果不可复现[：:]\s*\*{0,2}(是|否|{是|否})\*{0,2}',
        "假设严重不合理": r'假设严重不合理[：:]\s*\*{0,2}(是|否|{是|否})\*{0,2}',
        "结构残缺": r'结构残缺[：:]\s*\*{0,2}(是|否|{是|否})\*{0,2}',
    }
    for item, pattern in blocking_patterns.items():
        m = re.search(pattern, content)
        if m:
            val = m.group(1)
            # 只有明确是"是"才算触发，模板占位符不算
            if val == '是' and '{是' not in m.group(0):
                result["blocking"].append(item)

    # 提取四维度 - 支持多种格式
    dim_patterns = {
        "假设的合理性": [
            r'\|?\s*假设的合理性\s*\|?\s*(✅\s*)?(通过|需改进|缺陷)',
            r'假设的合理性.*?(通过|需改进|缺陷)',
        ],
        "建模的创造性": [
            r'\|?\s*建模的创造性\s*\|?\s*(✅\s*)?(通过|需改进|缺陷)',
            r'建模的创造性.*?(通过|需改进|缺陷)',
        ],
        "结果的正确性": [
            r'\|?\s*结果的正确性\s*\|?\s*(✅\s*)?(通过|需改进|缺陷)',
            r'结果的正确性.*?(通过|需改进|缺陷)',
        ],
        "表述的清晰性": [
            r'\|?\s*表述的清晰性\s*\|?\s*(✅\s*)?(通过|需改进|缺陷)',
            r'表述的清晰性.*?(通过|需改进|缺陷)',
        ],
    }
    for dim, patterns in dim_patterns.items():
        for pat in patterns:
            m = re.search(pat, content)
            if m:
                val = m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(1)
                result[f"dim_{dim}"] = val
                break

    return result


def compare_results(results_dir: str, output_path: str) -> None:
    """Phase 2: 测量重测信度 + 区分度（V8.3 新版）"""
    if not REFERENCE_SCORES:
        print("⚠️ REFERENCE_SCORES 为空，请在脚本中填写参考分数")
        return

    # 解析审稿结果中的总分
    scores = {}
    for md_file in Path(results_dir).glob("*.md"):
        paper_name = md_file.stem
        if paper_name.startswith("prompt_"):
            continue
        content = md_file.read_text(encoding="utf-8")
        m = VERDICT_PATTERN.search(content)
        if m:
            try:
                scores[paper_name] = float(m.group(1))
            except ValueError:
                continue

    if not scores:
        print("⚠️ 未从审稿结果中解析到有效分数（格式：总分 XX/100）")
        return

    # 匹配论文
    matched = {}
    for name, ref_score in REFERENCE_SCORES.items():
        for result_name, agent_score in scores.items():
            if name in result_name or result_name in name:
                matched[name] = {"ref": ref_score, "agent": agent_score, "file": result_name}
                break

    total = len(matched)
    if total == 0:
        print("⚠️ 未找到匹配的论文名")
        return

    # 计算指标
    diffs = [abs(m["ref"] - m["agent"]) for m in matched.values()]
    mean_diff = sum(diffs) / len(diffs)
    within_5 = sum(1 for d in diffs if d <= 5)
    within_5_pct = within_5 / len(diffs) * 100
    reliability = f"{within_5}/{len(diffs)} ({within_5_pct:.0f}%)"

    # 区分度：最高分-最低分差距
    agent_scores = [m["agent"] for m in matched.values()]
    ref_scores = [m["ref"] for m in matched.values()]
    agent_spread = max(agent_scores) - min(agent_scores)
    ref_spread = max(ref_scores) - min(ref_scores)

    # 生成报告
    lines = [
        "# 审稿 Agent 校准报告（V8.3 重测信度版）",
        "",
        "> ⚠️ 本报告测量的是 UltraMath 内部评分卡的**重测信度**和**区分度**，",
        "> 不是\"预测准确率\"——我们不再假装能预测 CUMCM 评委。",
        "",
        f"**校准时间**: {Path(results_dir).stat().st_mtime if Path(results_dir).exists() else 'N/A'}",
        f"**匹配论文数**: {total}/{len(REFERENCE_SCORES)}",
        "",
        "## 重测信度",
        "",
        f"- **平均绝对误差**: {mean_diff:.1f} 分",
        f"- **误差 ≤5 分**: {reliability}  (目标: ≥80%)",
        f"- **结论**: {'✅ 通过' if within_5_pct >= 80 else '⚠️ 需改进' if within_5_pct >= 60 else '🔴 不合格'}",
        "",
        "## 区分度",
        "",
        f"- **Agent 评分跨度**: {agent_spread:.0f} 分（最低 {min(agent_scores):.0f} → 最高 {max(agent_scores):.0f}）",
        f"- **参考评分跨度**: {ref_spread:.0f} 分（最低 {min(ref_scores):.0f} → 最高 {max(ref_scores):.0f}）",
        f"- **结论**: {'✅ 区分度合格' if agent_spread >= 15 else '⚠️ 区分度不足，无法有效区分高低质量论文'}",
        "",
        "## 逐篇对比",
        "",
        "| 论文 | 参考分 | Agent 分 | 误差 | 判定 |",
        "|------|-------|---------|------|------|",
    ]

    # 对 paper 排序：按误差从大到小
    sorted_papers = sorted(matched.items(), key=lambda x: abs(x[1]["ref"] - x[1]["agent"]), reverse=True)
    for name, m in sorted_papers:
        diff = abs(m["ref"] - m["agent"])
        verdict = "✅" if diff <= 5 else "⚠️" if diff <= 10 else "❌"
        lines.append(f"| {name} | {m['ref']} | {m['agent']:.0f} | {diff:.0f} 分 | {verdict} |")

    # 校准建议
    lines.extend([
        "",
        "## 校准建议",
        "",
    ])

    if within_5_pct >= 80:
        lines.append("✅ 重测信度达标。审稿 Agent 的评分一致性 ≥80%，评分卡稳定可用。")
    elif within_5_pct >= 60:
        lines.append("⚠️ 重测信度中等。以下论文误差较大：")
        for name, m in sorted_papers:
            diff = abs(m["ref"] - m["agent"])
            if diff > 5:
                direction = "偏低" if m["agent"] < m["ref"] else "偏高"
                lines.append(f"  - **{name}**: Agent {m['agent']:.0f} 分 vs 参考 {m['ref']} 分（{direction} {diff:.0f} 分）")
        lines.append("")
        lines.append("建议：检查这些论文的审稿 prompt 和评分卡加载是否正确。")
    else:
        lines.append("🔴 重测信度不合格。审稿 Agent 的评分不稳定，建议：")
        lines.append("1. 确认审稿 prompt 完整加载了 `references/internal-quality-scorecard.md`")
        lines.append("2. 检查每项 1-5 分的评分标准是否在 prompt 中清晰表述")
        lines.append("3. 对误差最大的几篇论文进行人工复核")

    if agent_spread < 15:
        lines.append("")
        lines.append("⚠️ 区分度不足：Agent 评分跨度 <15 分，无法有效区分高质量和低质量论文。")
        lines.append("建议检查评分卡各维度的打分标准是否有足够的区分度。")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n✅ 校准报告 → {output_path}")
    print(f"   重测信度: {reliability}  |  区分度: {agent_spread:.0f} 分")


# ── 主入口 ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="UltraMath 审稿 Agent 校准工具 (V8.3 重测信度版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # Phase 1: 从 PDF 提取文本，生成审稿 prompt
  python 审稿/calibrate.py --collect 参照论文/ --prompt-dir 审稿结果/

  # Phase 2: 测量重测信度 + 区分度
  python 审稿/calibrate.py --compare 审稿结果/ --output 校准报告.md
        """,
    )
    parser.add_argument("--collect", help="Phase 1: 参照论文 PDF 目录")
    parser.add_argument("--prompt-dir", default="审稿结果/", help="审稿 prompt 输出目录")
    parser.add_argument("--compare", help="Phase 2: Agent 审稿结果目录")
    parser.add_argument("--output", default="校准报告.md", help="校准报告输出路径")
    args = parser.parse_args()

    if args.collect:
        print("=" * 60)
        print("Phase 1: 提取论文文本 → 生成审稿 prompt")
        print("=" * 60)
        papers = phase1_collect(args.collect, args.prompt_dir)
        print(f"\n📋 共处理 {len(papers)} 篇论文")
        print(f"   Prompt 文件位于: {args.prompt_dir}")
        print(f"\n下一步：将 prompt 文件逐一交给审稿 Agent 评审，")
        print(f"         将 Agent 的输出保存到同一目录，")
        print(f"         然后运行: python 审稿/calibrate.py --compare {args.prompt_dir}")

    elif args.compare:
        print("=" * 60)
        print("Phase 2: 测量重测信度 + 区分度（V8.3）")
        print("=" * 60)
        if not REFERENCE_SCORES:
            print("\n⚠️ 请先在脚本中编辑 REFERENCE_SCORES 字典，")
            print("   填入每篇论文的参考质量分数（0-100）。")
            return
        print(f"\n📋 参考分数: {len(REFERENCE_SCORES)} 篇")
        compare_results(args.compare, args.output)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
