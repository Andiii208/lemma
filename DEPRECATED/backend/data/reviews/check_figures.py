#!/usr/bin/env python3
"""
UltraMath V7.0 — 图表质量自动审查脚本
===================================
扫描 求解/ 目录下所有 PNG 图, 按 10 分制打分并输出报告。

审查维度:
  1. 标注完整性 (3分) — 标题/轴标签/图例/数值标注
  2. 配色科学性 (3分) — 色盲安全/colormap正确/对比度
  3. 排版审美   (2分) — DPI/字体/bbox/留白
  4. 技术规范   (2分) — 文件大小/格式/尺寸合理

用法:
  python 审稿/check_figures.py <求解目录>
  python 审稿/check_figures.py E:/数学建模/测试/求解/

输出:
  <求解目录>/图表质量报告.md
"""

import os, sys, re, json, warnings
from pathlib import Path
from datetime import datetime
warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════

# 色盲不安全的配色对 (禁止同时出现的色相组合)
COLORBLIND_UNSAFE_PAIRS = [
    ('red', 'green'),
    ('#EE6677', '#228833'),  # Paul Tol Bright red + green
    ('#CC3311', '#117733'),
    ('#B85042', '#7E9B7E'),  # 暖色调 陶土红 + 鼠尾草绿
]

# 推荐 colormap 列表
RECOMMENDED_CMAPS = {'cividis', 'viridis', 'plasma', 'inferno', 'magma',
                     'RdBu_r', 'RdBu', 'coolwarm', 'PiYG', 'PRGn'}

# 最小文件大小 (低于此值认为图表异常)
MIN_FILE_SIZE_KB = 5

# 合理尺寸范围 (像素)
MIN_WIDTH = 600
MIN_HEIGHT = 400


# ═══════════════════════════════════════════════════════════════
# 检查函数
# ═══════════════════════════════════════════════════════════════

def check_dpi(filepath):
    """检查 DPI"""
    try:
        from PIL import Image
        img = Image.open(filepath)
        dpi = img.info.get('dpi', (72, 72))
        width, height = img.size
        return {
            'dpi_x': dpi[0],
            'dpi_y': dpi[1],
            'width': width,
            'height': height,
            'score': 2.0 if dpi[0] >= 150 else (1.0 if dpi[0] >= 96 else 0),
            'issues': [] if dpi[0] >= 150 else [f'DPI={dpi[0]:.0f} < 150']
        }
    except Exception as e:
        return {'dpi_x': 0, 'dpi_y': 0, 'width': 0, 'height': 0,
                'score': 0, 'issues': [f'无法读取: {e}']}


def check_file_size(filepath):
    """检查文件大小"""
    size_kb = os.path.getsize(filepath) / 1024
    issues = []
    score = 2.0
    if size_kb < MIN_FILE_SIZE_KB:
        issues.append(f'文件过小 ({size_kb:.1f}KB < {MIN_FILE_SIZE_KB}KB), 可能空白或损坏')
        score = 0
    elif size_kb < 10:
        issues.append(f'文件偏小 ({size_kb:.1f}KB), 信息量可能不足')
        score = 1.0
    return {'size_kb': round(size_kb, 1), 'score': score, 'issues': issues}


def check_dimensions(filepath):
    """检查尺寸"""
    try:
        from PIL import Image
        img = Image.open(filepath)
        w, h = img.size
        issues = []
        score = 1.0
        if w < MIN_WIDTH or h < MIN_HEIGHT:
            issues.append(f'尺寸过小 ({w}×{h})')
            score = 0
        return {'width': w, 'height': h, 'score': score, 'issues': issues}
    except Exception:
        return {'width': 0, 'height': 0, 'score': 0, 'issues': ['无法读取尺寸']}


def check_py_source(figure_name, solve_dir):
    """检查对应 .py 源码中的图表质量信号

    按图文件名匹配对应的 问题X_求解.py:
      图1_*.png → 问题1/问题1_求解.py
      图2_*.png → 问题2/问题2_求解.py
    找不到对应文件时回退到扫描全部 .py。
    """
    issues = []
    score = 1.0  # ⚠️ V6.2: 基础分从 3.0→1.0, 好图加分而非坏图扣分
    details = {}

    # ── 1. 按文件名匹配对应的 .py ──
    # 从图名推断问题号: 问题1/图片/图3_xxx.png → 问题1
    match = re.match(r'问题(\d+)', figure_name)
    if not match:
        match = re.search(r'问题(\d+)', solve_dir.replace('\\', '/'))

    matched_py = None
    if match:
        qnum = match.group(1)
        candidate = os.path.join(solve_dir, f'问题{qnum}', f'问题{qnum}_求解.py')
        if os.path.exists(candidate):
            matched_py = candidate

    # ── 2. 读取源码 ──
    if matched_py:
        try:
            with open(matched_py, 'r', encoding='utf-8') as fh:
                all_code = fh.read()
        except Exception:
            all_code = ''
    else:
        # 回退: 扫描所有 .py
        all_code = ''
        for root, _, files in os.walk(solve_dir):
            for f in files:
                if f.endswith('.py') and '求解' in f:
                    try:
                        with open(os.path.join(root, f), 'r', encoding='utf-8') as fh:
                            all_code += fh.read()
                    except Exception:
                        continue
        if not all_code:
            return {'score': 0, 'issues': ['未找到 Python 源码, 无法检查标注'],
                    'details': {}}

    # ── 3. 检查项 (加分制) ──
    details['matched_py'] = matched_py

    # +1.0: 使用了 figure_style
    if 'figure_style' in all_code:
        details['uses_figure_style'] = True
        score += 1.0
    else:
        details['uses_figure_style'] = False
        issues.append('未导入 figure_style 模块')

    # +0.5: 有标题
    if re.search(r'set_title|suptitle', all_code):
        details['has_title'] = True
        score += 0.5
    else:
        details['has_title'] = False
        issues.append('图可能缺少标题')

    # +0.5: 有轴标签
    if re.search(r'set_[xy]label', all_code):
        details['has_axis_labels'] = True
        score += 0.5
    else:
        details['has_axis_labels'] = False
        issues.append('图可能缺少轴标签')

    # 热力图数值标注检查
    if 'imshow' in all_code or 'heatmap' in all_code:
        if re.search(r'(ax\.text|annotate|heatmap_with_values)', all_code):
            score += 0.5  # 热力图有标注
        else:
            issues.append('热力图缺少数值标注')
            score -= 0.5

    # 检查 colormap
    cmaps_found = re.findall(r"cmap\s*=\s*['\"]([^'\"]+)['\"]", all_code)
    details['cmaps_used'] = list(set(cmaps_found))
    bad_cmaps = [c for c in cmaps_found if c not in RECOMMENDED_CMAPS and c not in {'gray', 'Greys'}]
    if bad_cmaps:
        issues.append(f'非推荐 colormap: {bad_cmaps}')
        score -= 0.5

    # 检查红绿配色 (V6.2: 从 COLORS.WARM 使用陶土红+鼠尾草绿也算)
    red_patterns = r'#B85042|#EE6677|#CC3311|TERRACOTTA|terracotta|WARM\[0\]'
    green_patterns = r'#7E9B7E|#228833|#117733|SAGE|sage|WARM\[1\]'
    has_red = bool(re.search(red_patterns, all_code))
    has_green = bool(re.search(green_patterns, all_code))
    details['colorblind_safe'] = not (has_red and has_green)
    if has_red and has_green:
        issues.append('⚠️ 代码中同时使用红绿色, 可能色盲不友好')
        score -= 1.0

    # 上限 3.0
    score = max(0, min(3.0, score))

    return {'score': round(score, 1), 'issues': issues, 'details': details}


def check_unicode_boxes(filepath):
    """检查 PNG 中是否有 Unicode 方块渲染缺陷
    
    Unicode 方块在图片中通常表现为纯黑 (0,0,0) 或纯白 (255,255,255)
    的小矩形区域。本函数通过分析像素极值分布来检测。
    
    Args:
        filepath: PNG 文件路径
    
    Returns:
        dict: {'has_boxes': bool, 'score': float, 'issues': [str]}
    """
    try:
        from PIL import Image
        import numpy as np
        img = Image.open(filepath).convert('RGB')
        arr = np.array(img)
        gray = np.mean(arr, axis=2)
        dark_mask = gray < 10
        white_mask = gray > 245
        box_ratio = (dark_mask.sum() + white_mask.sum()) / gray.size
        if box_ratio > 0.05:
            return {
                'has_boxes': True,
                'ratio': round(box_ratio * 100, 1),
                'score': 0,
                'issues': [f'疑似 Unicode 方块 (极端像素 {box_ratio*100:.1f}%)']
            }
        return {
            'has_boxes': False,
            'ratio': round(box_ratio * 100, 1),
            'score': 1.0,
            'issues': []
        }
    except ImportError:
        return {'has_boxes': False, 'ratio': 0, 'score': 1.0, 'issues': ['PIL/numpy 未安装, 跳过']}
    except Exception as e:
        return {'has_boxes': False, 'ratio': 0, 'score': 1.0, 'issues': [f'检测异常: {e}']}


def generate_report(png_files, solve_dir):
    """生成完整审查报告"""
    results = []
    total_score = 0

    for png_path in png_files:
        name = os.path.basename(png_path)
        rel_path = os.path.relpath(png_path, solve_dir)

        dpi_info = check_dpi(png_path)
        size_info = check_file_size(png_path)
        dim_info = check_dimensions(png_path)
        py_info = check_py_source(name, solve_dir)
        unicode_info = check_unicode_boxes(png_path)

        # 综合评分 (各维度加权)
        dim_scores = {
            '标注完整性': round(py_info['score'], 1),
            '配色科学性': round(3.0 - (1.0 if not py_info['details'].get('colorblind_safe', True) else 0) if 'colorblind_safe' in py_info['details'] else 3.0, 1),
            '排版审美':   round((dpi_info['score'] + dim_info['score']) / 2, 1),
            '技术规范':   round(size_info['score'], 1),
        }
        # 配色科学性上限3, 下限0
        dim_scores['配色科学性'] = max(0, min(3, dim_scores['配色科学性']))
        # 排版审美上限2
        dim_scores['排版审美'] = max(0, min(2, dim_scores['排版审美']))
        # 技术规范上限2
        dim_scores['技术规范'] = max(0, min(2, dim_scores['技术规范']))

        overall = round(sum(dim_scores.values()), 1)
        total_score += overall

        all_issues = (dpi_info.get('issues', []) + size_info.get('issues', []) +
                      dim_info.get('issues', []) + py_info.get('issues', []) +
                      unicode_info.get('issues', []))

        grade = 'A' if overall >= 8 else ('B' if overall >= 6 else ('C' if overall >= 4 else 'D'))

        results.append({
            'file': rel_path,
            'name': name,
            'overall': overall,
            'grade': grade,
            'dimensions': dim_scores,
            'dpi': dpi_info.get('dpi_x', 0),
            'size_kb': size_info.get('size_kb', 0),
            'issues': all_issues,
            'details': py_info.get('details', {}),
        })

    avg_score = round(total_score / len(results), 1) if results else 0

    return {
        'results': results,
        'avg_score': avg_score,
        'total_figures': len(results),
        'grade_distribution': {
            'A': sum(1 for r in results if r['grade'] == 'A'),
            'B': sum(1 for r in results if r['grade'] == 'B'),
            'C': sum(1 for r in results if r['grade'] == 'C'),
            'D': sum(1 for r in results if r['grade'] == 'D'),
        },
    }


def render_markdown(report, solve_dir):
    """生成 Markdown 报告"""
    lines = []
    lines.append('# 📊 图表质量审查报告')
    lines.append(f'')
    lines.append(f'**审查时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append(f'**审查目录**: `{solve_dir}`')
    lines.append(f'**图表总数**: {report["total_figures"]}')
    lines.append(f'**平均分**: {report["avg_score"]}/10')
    lines.append(f'')
    lines.append(f'## 等级分布')
    gd = report['grade_distribution']
    lines.append(f'| 等级 | 数量 |')
    lines.append(f'|------|------|')
    for grade in ['A', 'B', 'C', 'D']:
        lines.append(f'| {grade} | {gd[grade]} |')
    lines.append(f'')

    # 判定（附门禁分级标注）
    gate_tier = "[脚本验证]"
    gate_explain = ("DPI/尺寸/文件大小: 确定性检查 | "
                    "源码分析(colormap/标注/配色): 基于正则模式匹配的启发式检查 | "
                    "Unicode方块: 像素分布分析")
    if report['avg_score'] >= 8:
        lines.append(f'✅ **通过** {gate_tier} — 图表质量达标, 可以进入论文写作阶段')
    elif report['avg_score'] >= 6:
        lines.append(f'⚠️ **需改进** {gate_tier} — 图表质量一般, 建议修复后再进入 Phase 3')
    else:
        lines.append(f'❌ **不通过** {gate_tier} — 图表质量不足, 必须修复后重新审查')
    lines.append(f'')
    lines.append(f'> ℹ️ {gate_explain}')

    lines.append(f'')
    lines.append(f'## 逐图详情')
    lines.append(f'')

    for r in report['results']:
        emoji = {'A': '🟢', 'B': '🟡', 'C': '🟠', 'D': '🔴'}.get(r['grade'], '⚪')
        lines.append(f'### {emoji} {r["name"]} — {r["overall"]}/10 ({r["grade"]})')
        lines.append(f'')
        lines.append(f'- **文件**: `{r["file"]}`')
        lines.append(f'- **DPI**: {r["dpi"]:.0f} | **大小**: {r["size_kb"]}KB')
        lines.append(f'')
        lines.append(f'| 维度 | 得分 |')
        lines.append(f'|------|------|')
        for dim, score in r['dimensions'].items():
            lines.append(f'| {dim} | {score} |')
        lines.append(f'')

        if r['issues']:
            lines.append(f'**问题清单**:')
            for issue in r['issues']:
                lines.append(f'- {issue}')
            lines.append(f'')

    # 汇总问题
    all_issues = []
    for r in report['results']:
        all_issues.extend(r['issues'])
    if all_issues:
        unique_issues = list(dict.fromkeys(all_issues))
        lines.append(f'## 🔧 待修复问题汇总 ({len(unique_issues)} 项)')
        for i, issue in enumerate(unique_issues, 1):
            lines.append(f'{i}. {issue}')

    lines.append(f'')
    lines.append(f'---')
    lines.append(f'*报告由 check_figures.py v6.2 自动生成*')

    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print('用法: python 审稿/check_figures.py <求解目录>')
        print('示例: python 审稿/check_figures.py E:/数学建模/测试/求解/')
        sys.exit(1)

    solve_dir = sys.argv[1]
    if not os.path.isdir(solve_dir):
        print(f'❌ 目录不存在: {solve_dir}')
        sys.exit(1)

    # 收集 PNG 文件
    png_files = []
    for root, _, files in os.walk(solve_dir):
        for f in files:
            if f.lower().endswith('.png') and '图片' in root:
                png_files.append(os.path.join(root, f))

    if not png_files:
        print('⚠️ 未找到 PNG 图表文件')
        # 仍然输出空报告
        report = {'results': [], 'avg_score': 0, 'total_figures': 0, 'grade_distribution': {'A':0,'B':0,'C':0,'D':0}}
    else:
        print(f'🔍 扫描到 {len(png_files)} 张图, 正在审查...')
        report = generate_report(png_files, solve_dir)

    # 输出报告
    md = render_markdown(report, solve_dir)
    report_path = os.path.join(solve_dir, '图表质量报告.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(md)

    print(f'📄 报告已保存: {report_path}')
    print(f'📊 平均分: {report["avg_score"]}/10 | A:{report["grade_distribution"]["A"]} B:{report["grade_distribution"]["B"]} C:{report["grade_distribution"]["C"]} D:{report["grade_distribution"]["D"]}')
    print(md[:500])

if __name__ == '__main__':
    main()
