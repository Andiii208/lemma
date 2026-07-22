#!/usr/bin/env python3
"""
UltraMath V7.0 — 出版级图表样式模块
=================================
Agent E 导入此模块后无需关心配色/字体/排版细节，
只需调用预设函数即可产出国奖级图表。

设计原则:
  - 数据可视化层 → 科学色板(Paul Tol / cividis), 色盲安全+顶刊标准
  - 论文架构层   → 暖色调(陶土红/鼠尾草绿/金), 仅用于框架图/流程图
  - 所有图共享一套 rcParams, 换题只换数据不换画法

依赖: matplotlib, scienceplots, numpy
可选: LaTeX (MiKTeX/TeXLive) — 若未安装自动回退到 no-latex
"""

import os, sys, warnings
warnings.filterwarnings('ignore')

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.font_manager import FontProperties

__version__ = '6.2.0'

# ═══════════════════════════════════════════════════════════════
# 中文字体自动检测
# ═══════════════════════════════════════════════════════════════

def _find_chinese_font():
    """检测系统中可用的中文字体, 返回 FontProperties 对象
    
    优先选择 Unicode 覆盖全的字体（需支持中文 + 上标/希腊/数学符号）。
    微软雅黑(msyh)和等线(DengXian)对 Unicode 数学符号支持最好。
    """
    candidates = [
        'C:/Windows/Fonts/msyh.ttc',        # 微软雅黑 — Unicode覆盖最全
        'C:/Windows/Fonts/Deng.ttf',        # 等线 — Win10+默认，Unicode好
        'C:/Windows/Fonts/simhei.ttf',      # 黑体
        'C:/Windows/Fonts/simsun.ttc',      # 宋体
        'C:/Windows/Fonts/simkai.ttf',      # 楷体
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/System/Library/Fonts/PingFang.ttc',
    ]
    for path in candidates:
        if os.path.exists(path):
            return FontProperties(fname=path)
    # 兜底
    return FontProperties()

CN_FONT = _find_chinese_font()
_CN_FONT_PATH = CN_FONT.get_file() if CN_FONT.get_file() else None

# ═══════════════════════════════════════════════════════════════
# Unicode→mathtext 自动转换 (修复方框问题)
# Windows 字体普遍不支持 Unicode 上标下标(⁻¹₂₃°等),
# 唯一可靠方案是用 matplotlib mathtext 渲染这些符号。
# ═══════════════════════════════════════════════════════════════

_UNICODE_TO_MATHTEXT = {
    '⁻¹': '^{-1}',   # cm⁻¹ → cm$^{-1}$
    '⁻²': '^{-2}',
    '⁻³': '^{-3}',
    '°':   r'^\circ',  # 10° → 10$^\circ$
    '₁':   '_1',
    '₂':   '_2',
    '₃':   '_3',
    '₄':   '_4',
    '₅':   '_5',
    '₆':   '_6',
    '₇':   '_7',
    '₈':   '_8',
    '₉':   '_9',
    '₀':   '_0',
    '⁰':   '^0',
    '¹':   '^1',
    '²':   '^2',
    '³':   '^3',
    '⁴':   '^4',
    '⁵':   '^5',
    '⁶':   '^6',
    '⁷':   '^7',
    '⁸':   '^8',
    '⁹':   '^9',
    # 希腊字母+下标组合 (Windows字体普遍不支持)
    'θ₁': r'\theta_1',
    'θ₂': r'\theta_2',
    'θ₃': r'\theta_3',
    'α₁': r'\alpha_1',
    'α₂': r'\alpha_2',
    'β₁': r'\beta_1',
    'β₂': r'\beta_2',
    'ε₁': r'\varepsilon_1',
    'ε₂': r'\varepsilon_2',
    'μ₁': r'\mu_1',
    'μ₂': r'\mu_2',
    'σ₁': r'\sigma_1',
    'σ₂': r'\sigma_2',
}

def fix_label(text):
    """将包含 Unicode 上标下标/度数符号的字符串转为 mathtext 格式
    
    示例: '波数 (cm⁻¹)' → '波数 (cm$^{-1}$)'
          'θ₁=10°'     → '$\\theta_1 = 10^\\circ$'
    
    对于不包含任何需要转换的字符的字符串, 原样返回。
    """
    if not isinstance(text, str):
        return text
    
    # 检测是否需要转换
    needs_fix = any(ch in text for ch in _UNICODE_TO_MATHTEXT)
    if not needs_fix:
        return text
    
    # 分段处理: 把每个需要转换的字符替换为 $math$ 块
    result = text
    for uni, math in _UNICODE_TO_MATHTEXT.items():
        result = result.replace(uni, f'${math}$')
    
    # 合并相邻的 $...$ 块 (避免 '$^{-1}$$_{2}$' 这种)
    import re
    result = re.sub(r'\\$\\$', '', result)
    
    return result


def fix_all_labels(fig):
    """递归修复 figure 中所有文本对象的 Unicode 显示问题
    
    自动遍历 figure 中所有 Text 对象（title, axis labels, tick labels,
    legend, annotations等），对包含 Unicode 上标/下标/度数的标签
    应用 fix_label() 转换。
    
    用法::
    
        fig, ax = plt.subplots()
        # ... 绘图代码 ...
        fix_all_labels(fig)
        fig.savefig('output.png', dpi=300)
    
    Args:
        fig: matplotlib Figure 对象
    
    Returns:
        修改后的 Figure 对象
    """
    import matplotlib.text as mtext
    
    for text in fig.findobj(mtext.Text):
        old = text.get_text()
        if old and isinstance(old, str):
            # 检查是否需要修复
            import re
            if any(ord(c) > 127 for c in old):
                new = fix_label(old)
                if new != old:
                    text.set_text(new)
    
    return fig


# ═══════════════════════════════════════════════════════════════
# 色板 ==========================================================
# ═══════════════════════════════════════════════════════════════

class Colors:
    """分层配色方案

    使用规则:
      - 数据可视化(柱状/折线/散点) → BRIGHT / VIBRANT / MUTED
      - 热力图/相关矩阵             → cividis (perceptually uniform)
      - 论文框架图/流程图            → WARM (用户审美偏好)
      - 高亮/标注/推荐点            → HIGHLIGHT
    """

    # ── Paul Tol Bright (色盲安全, 顶刊标配) ──
    BRIGHT = [
        '#4477AA',  # blue
        '#EE6677',  # red (not green-red pairing!)
        '#228833',  # green
        '#CCBB44',  # yellow
        '#66CCEE',  # cyan
        '#AA3377',  # purple
        '#BBBBBB',  # grey
    ]

    # ── Paul Tol Vibrant (更高对比度) ──
    VIBRANT = [
        '#0077BB',  # blue
        '#33BBEE',  # cyan
        '#009988',  # teal
        '#EE7733',  # orange
        '#CC3311',  # red
        '#EE3377',  # magenta
        '#BBBBBB',  # grey
    ]

    # ── Paul Tol Muted (柔和不刺眼, 9色) ──
    MUTED = [
        '#332288',  # indigo
        '#88CCEE',  # cyan
        '#44AA99',  # teal
        '#117733',  # green
        '#999933',  # olive
        '#DDCC77',  # sand
        '#CC6677',  # rose
        '#882255',  # wine
        '#AA4499',  # purple
    ]

    # ── 暖色调 (用户偏好, 仅用于架构/框架图) ──
    TERRACOTTA   = '#B85042'  # 陶土红
    SAGE         = '#7E9B7E'  # 鼠尾草绿
    GOLD         = '#D4A54A'  # 金色
    WARM_ORANGE  = '#E8913A'
    DUSTY_ROSE   = '#C27B7B'
    WARM_GRAY    = '#8B7E74'

    WARM = [TERRACOTTA, SAGE, GOLD, WARM_ORANGE, DUSTY_ROSE, WARM_GRAY]

    # ── 高亮色 ──
    HIGHLIGHT_RED    = '#CC3311'
    HIGHLIGHT_ORANGE = '#EE7733'
    HIGHLIGHT_BLUE   = '#0077BB'

    # ── 推荐 colormap ──
    CMAP_DIVERGING  = 'RdBu_r'     # 发散型(正负区分)
    CMAP_SEQUENTIAL = 'viridis'    # 顺序型
    CMAP_HEATMAP    = 'cividis'    # 热力图(perceptually uniform + 色盲安全)
    CMAP_CORRELATION = 'RdBu_r'    # 相关系数


# 单例
COLORS = Colors()


# ═══════════════════════════════════════════════════════════════
# 全局样式初始化
# ═══════════════════════════════════════════════════════════════

_STYLE_INITIALIZED = False

def setup_style():
    """初始化出版级图表样式 (每个脚本开头调用一次)

    自动检测 LaTeX 是否可用:
      - 有 LaTeX → SciencePlots ['science', 'ieee'] + Computer Modern 字体
      - 无 LaTeX → SciencePlots ['science', 'no-latex', 'ieee'] 回退
    """
    global _STYLE_INITIALIZED
    if _STYLE_INITIALIZED:
        return
    _STYLE_INITIALIZED = True

    # ── SciencePlots ──
    # 默认使用 no-latex (MiKTeX on Windows 首次编译会卡住下载包)
    # 如需 Computer Modern 字体, 设置环境变量 MRITE_USE_LATEX=1
    try:
        import scienceplots
        if os.environ.get('MRITE_USE_LATEX') == '1':
            plt.style.use(['science', 'ieee'])
            print("✅ SciencePlots: science + ieee (Computer Modern, 慢)")
        else:
            plt.style.use(['science', 'no-latex'])  # 不用ieee — 其字体族不支持Unicode符号
            print("✅ SciencePlots: science + no-latex (DejaVu Serif + STIX math)")
    except ImportError:
        print("⚠️  SciencePlots 未安装, 使用 matplotlib 默认 + seaborn")
        try:
            import seaborn as sns
            sns.set_style('whitegrid')
        except ImportError:
            pass

    # ── 全局 rcParams ──
    plt.rcParams.update({
        # 输出
        'figure.dpi':       300,
        'savefig.dpi':      300,
        'savefig.bbox':     'tight',
        'savefig.facecolor': '#FFFCF8',  # 暖白底色

        # ── 字体 (修复方框问题) ──
        # 核心策略: 利用 matplotlib 字体回退链，不依赖 fontproperties。
        # sans-serif 链: MS YaHei(中文+常见符号) → DejaVu Sans(Unicode全覆盖) → STIX math
        # 这样中文走YaHei，数学上标下标(⁻¹₁₂₃)回退到DejaVu，mathtext($...$)用STIX渲染。
        'font.family':       'sans-serif',
        'font.sans-serif':   ['Microsoft YaHei', 'DejaVu Sans', 'SimHei', 'Arial'],
        'font.size':         11,
        'mathtext.fontset':  'dejavusans',    # mathtext 用 DejaVu → 完整符号支持
        'mathtext.default':  'regular',

        'axes.titlesize':   14,
        'axes.labelsize':   11,
        'xtick.labelsize':  9,
        'ytick.labelsize':  9,
        'legend.fontsize':  9,
        'axes.unicode_minus': False,

        # 排版
        'axes.grid':        True,
        'grid.alpha':       0.3,
        'grid.linestyle':   '--',
        'axes.spines.top':    False,
        'axes.spines.right': False,

        # 图例
        'legend.frameon':   True,
        'legend.facecolor': 'white',
        'legend.edgecolor': '#DDDDDD',
        'legend.fancybox':  False,

        # 线条
        'lines.linewidth':  1.5,
        'lines.markersize': 6,
    })

    print(f"🎨 figure_style v{__version__} 就绪 | 中文字体: {os.path.basename(_CN_FONT_PATH) if _CN_FONT_PATH else '后备'}")

# ═══════════════════════════════════════════════════════════════
# 保存
# ═══════════════════════════════════════════════════════════════

def save_figure(fig, rel_path, dpi=300):
    """保存图表, 自动创建目录 + 设置暖白底色

    Args:
        fig: matplotlib Figure
        rel_path: 相对于求解/ 的路径, 如 '问题1/图片/图1_逐年利润.png'
        dpi: 分辨率 (默认 300)
    """
    # 确保目录存在
    full_dir = os.path.dirname(rel_path)
    if full_dir:
        os.makedirs(full_dir, exist_ok=True)

    fig.patch.set_facecolor('#FFFCF8')
    fig.savefig(rel_path, dpi=dpi, bbox_inches='tight', facecolor='#FFFCF8')
    plt.close(fig)
    print(f"  ✅ {rel_path}")


# ═══════════════════════════════════════════════════════════════
# 预设绘图函数
# ═══════════════════════════════════════════════════════════════

def new_figure(figsize=(8, 5), nrows=1, ncols=1):
    """创建新图, 自动设置暖白底色"""
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    fig.patch.set_facecolor('#FFFCF8')

    def _set_bg(ax):
        ax.set_facecolor('#FFFCF8')

    if nrows * ncols > 1:
        for ax in axes.flat:
            _set_bg(ax)
    else:
        _set_bg(axes)
    return fig, axes


def bar_comparison(ax, groups, values_dict, *,
                   colors=None, ylabel='', title='',
                   value_format='{:.1f}', rotation=0):
    """分组柱状对比图

    Args:
        ax: matplotlib Axes
        groups: X轴标签列表, 如 ['2024', '2025', ...]
        values_dict: {系列名: [值列表], ...}
        colors: 颜色列表 (默认 COLORS.BRIGHT)
        ylabel: Y轴标签 (含单位)
        title: 图表标题
        value_format: 数值标签格式
        rotation: X轴标签旋转角度
    """
    if colors is None:
        colors = COLORS.BRIGHT

    x = np.arange(len(groups))
    n_bars = len(values_dict)
    width = 0.8 / n_bars

    for i, (label, values) in enumerate(values_dict.items()):
        offset = (i - (n_bars - 1) / 2) * width
        color = colors[i % len(colors)]
        bars = ax.bar(x + offset, values, width, color=color,
                      alpha=0.85, edgecolor='white', linewidth=0.5, label=label)

        # 数值标签
        for bar in bars:
            h = bar.get_height()
            va = 'bottom' if h >= 0 else 'top'
            ax.text(bar.get_x() + bar.get_width()/2, h,
                    value_format.format(h),
                    ha='center', va=va, fontsize=8, fontweight='bold',
                    color=color)

    ax.set_xticks(x)
    ax.set_xticklabels(groups, rotation=rotation)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', pad=12)
    ax.legend()


def line_comparison(ax, x, values_dict, *,
                    colors=None, xlabel='', ylabel='', title='',
                    markers=True):
    """多系列折线对比图

    Args:
        ax: matplotlib Axes
        x: X轴数据
        values_dict: {系列名: [Y值列表], ...}
        colors: 颜色列表 (默认 COLORS.BRIGHT)
        xlabel, ylabel: 轴标签 (含单位)
        title: 图表标题
        markers: 是否显示数据点标记
    """
    if colors is None:
        colors = COLORS.BRIGHT

    markers_list = ['o', 's', '^', 'D', 'v', 'p', '*']

    for i, (label, y) in enumerate(values_dict.items()):
        color = colors[i % len(colors)]
        marker = markers_list[i % len(markers_list)] if markers else None
        ax.plot(x, y, color=color, linewidth=2, marker=marker,
                markersize=7, label=label, markeredgecolor='white',
                markeredgewidth=0.5)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', pad=12)
    ax.legend()


def heatmap_with_values(ax, matrix, row_labels, col_labels, *,
                        cmap=None, vmin=None, vmax=None, title='',
                        cbar_label='', value_format='{:.2f}',
                        annotate=True, rotation=45):
    """热力图 (自动标注数值)

    Args:
        ax: matplotlib Axes
        matrix: 2D numpy array
        row_labels, col_labels: 行列标签
        cmap: colormap (默认 COLORS.CMAP_HEATMAP / cividis)
        vmin, vmax: colormap 范围 (默认自动)
        title: 图表标题
        cbar_label: 颜色条标签
        value_format: 数值标签格式
        annotate: 是否在每个单元格标注数值 (默认 True)
        rotation: X轴标签旋转角度
    """
    if cmap is None:
        cmap = COLORS.CMAP_HEATMAP

    im = ax.imshow(matrix, cmap=cmap, aspect='auto',
                   vmin=vmin, vmax=vmax)

    n_rows, n_cols = matrix.shape
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(col_labels,
                       rotation=rotation, ha='right', fontsize=9)
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(row_labels, fontsize=9)

    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', pad=12)

    # 颜色条
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    if cbar_label:
        cbar.set_label(cbar_label)

    # 数值标注
    if annotate:
        for i in range(n_rows):
            for j in range(n_cols):
                val = matrix[i, j]
                text_color = 'white' if abs(val) > (vmax or abs(matrix).max()) * 0.5 else 'black'
                ax.text(j, i, value_format.format(val),
                        ha='center', va='center', fontsize=7,
                        color=text_color, fontweight='bold')

    return im


def pareto_front(ax, x, y, *, color=None, xlabel='', ylabel='',
                 title='', highlight=None):
    """Pareto 前沿图 (带推荐点标注)

    Args:
        ax: matplotlib Axes
        x, y: Pareto前沿数据
        color: 线条颜色 (默认 COLORS.BRIGHT[0])
        xlabel, ylabel: 轴标签 (含单位)
        title: 图表标题
        highlight: dict {label: (x, y, color)} 标注推荐方案
    """
    if color is None:
        color = COLORS.BRIGHT[4]  # cyan

    ax.plot(x, y, 'o-', color=color, linewidth=2, markersize=8,
            markerfacecolor='white', markeredgewidth=2)

    # 标注推荐点
    if highlight:
        for label, (hx, hy, hcolor) in highlight.items():
            ax.scatter(hx, hy, marker='s', s=120, color=hcolor,
                      zorder=5, edgecolors='white', linewidth=1.5)
            ax.annotate(label, (hx, hy),
                       textcoords='offset points', xytext=(12, 10),
                       fontsize=10, color=hcolor,
                       fontweight='bold')

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', pad=12)


def sensitivity_plot(ax, x, y_primary, y_secondary=None, *,
                     colors=None, xlabel='', ylabel_primary='',
                     ylabel_secondary='', title=''):
    """敏感性分析双Y轴图

    Args:
        ax: matplotlib Axes (主Y轴)
        x: X轴数据
        y_primary: 主Y轴数据
        y_secondary: 副Y轴数据 (可选)
        colors: [主色, 副色] (默认 COLORS.BRIGHT[0], COLORS.BRIGHT[3])
        xlabel: X轴标签
        ylabel_primary, ylabel_secondary: Y轴标签
        title: 图表标题
    """
    if colors is None:
        colors = [COLORS.BRIGHT[0], COLORS.BRIGHT[3]]

    # 主Y轴
    ax.plot(x, y_primary, 'o-', color=colors[0], linewidth=2,
            markersize=8, markerfacecolor='white', markeredgewidth=2,
            label=ylabel_primary)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel_primary, color=colors[0])

    # 副Y轴
    if y_secondary is not None:
        ax2 = ax.twinx()
        ax2.plot(x, y_secondary, 's--', color=colors[1], linewidth=2,
                 markersize=8, markeredgewidth=1.5,
                 label=ylabel_secondary)
        ax2.set_ylabel(ylabel_secondary, color=colors[1])

    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', pad=12)

    # 合并图例
    lines1, labels1 = ax.get_legend_handles_labels()
    if y_secondary is not None:
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2)
    else:
        ax.legend()


def boxplot_compare(ax, data_list, labels, *,
                    colors=None, ylabel='', title=''):
    """箱线图对比

    Args:
        ax: matplotlib Axes
        data_list: [data1, data2, ...] 各数据集
        labels: 箱线标签
        colors: 颜色列表 (默认 COLORS.MUTED)
        ylabel: Y轴标签 (含单位)
        title: 图表标题
    """
    if colors is None:
        colors = COLORS.MUTED

    bp = ax.boxplot(data_list, labels=labels, patch_artist=True,
                    widths=0.5, medianprops={'color': 'white', 'linewidth': 2})

    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)

    ax.set_xticklabels(labels)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', pad=12)


def scatter_compare(ax, x, y, *, color=None, alpha=0.6, s=30,
                    xlabel='', ylabel='', title='', label=''):
    """散点图

    Args:
        ax: matplotlib Axes
        x, y: 数据
        color: 颜色 (默认 COLORS.BRIGHT[0])
        alpha: 透明度
        s: 点大小
        xlabel, ylabel: 轴标签 (含单位)
        title: 图表标题
        label: 图例标签
    """
    if color is None:
        color = COLORS.BRIGHT[0]

    ax.scatter(x, y, c=color, alpha=alpha, s=s,
               edgecolors='white', linewidth=0.3, label=label or None)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', pad=12)
    if label:
        ax.legend()


# ═══════════════════════════════════════════════════════════════
# 向后兼容 (V6.1 regenerate_figures.py 移植过渡)
# ═══════════════════════════════════════════════════════════════

# 保留旧版色板名映射
WARM_COLORS = {
    'terracotta':  COLORS.TERRACOTTA,
    'sage':        COLORS.SAGE,
    'gold':        COLORS.GOLD,
    'warm_orange': COLORS.WARM_ORANGE,
    'deep_green':  '#5C8A5C',
    'dusty_rose':  COLORS.DUSTY_ROSE,
    'cream':       '#F5E6D3',
    'warm_gray':   COLORS.WARM_GRAY,
}

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='figure_style 图表工具')
    p.add_argument('--self-test', action='store_true', help='模块自检')
    p.add_argument('--figures-only', metavar='SOLVE_DIR',
                   help='只重画 <求解目录> 下的所有图，不重算数据（调用各问题X_求解.py）')
    args = p.parse_args()

    if args.figures_only:
        solve_dir = args.figures_only
        print(f"🎨 --figures-only 模式: {solve_dir}")
        import subprocess, glob
        for py_file in sorted(glob.glob(f'{solve_dir}/问题*_求解.py')):
            print(f"  ▶ 运行 {py_file}")
            subprocess.run(['python', py_file, '--figures-only'],
                          cwd=solve_dir, timeout=600)
        print("✅ 图表重生成完成")
    elif args.self_test:
        setup_style()
        fig, ax = new_figure()
        bar_comparison(ax, groups=['A','B','C'],
                       values_dict={'系列1':[10,20,15], '系列2':[12,18,22]},
                       ylabel='数值（单位）', title='figure_style.py 自检')
        save_figure(fig, '_self_test.png')
        os.remove('_self_test.png')
        print('\n🎉 figure_style.py 模块自检通过')
    else:
        print('用法: python figure_style.py --self-test | --figures-only <求解目录>')
