# LaTeX 数学建模模板与技巧

## 常用包

```latex
\usepackage{amsmath,amssymb}     % 数学符号
\usepackage{graphicx}            % 图片
\usepackage{booktabs}            % 三线表
\usepackage{algorithm,algorithmic} % 伪代码
\usepackage{hyperref}            % 超链接
\usepackage{geometry}            % 页边距
\usepackage{subcaption}          % 子图
```

## 三线表

```latex
\begin{table}[htbp]
\centering
\caption{实验结果}
\begin{tabular}{lccc}
\toprule
方法 & 准确率 & 召回率 & F1 \\
\midrule
方法A & 0.85 & 0.82 & 0.83 \\
\bottomrule
\end{tabular}
\end{table}
```

## 子图

```latex
\begin{figure}[htbp]
\centering
\begin{subfigure}{0.45\textwidth}
  \includegraphics[width=\textwidth]{a.pdf}
  \caption{方案A}
\end{subfigure}
\hfill
\begin{subfigure}{0.45\textwidth}
  \includegraphics[width=\textwidth]{b.pdf}
  \caption{方案B}
\end{subfigure}
\end{figure}
```

## 常见问题
1. 中文支持：ctex 宏包或 XeLaTeX
2. 图片路径：`\graphicspath{{figures/}}`
3. 参考文献：BibTeX 管理
