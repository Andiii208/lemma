"""文档导出器 — 支持 Markdown、LaTeX、JSON、HTML 格式"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


class DocumentExporter:
    """将会话和产出物导出为多种格式"""

    def __init__(self, work_dir: str):
        self.work_dir = Path(work_dir)
        self.export_dir = self.work_dir / ".ultraagent" / "exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_markdown(self, messages: list, filename: str | None = None) -> str:
        """导出为 Markdown"""
        if filename is None:
            filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        output = self.export_dir / filename
        lines = ["# UltraAgent 会话导出\n"]
        lines.append(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append("---\n")

        for msg in messages:
            role = msg.get("role", "unknown") if isinstance(msg, dict) else getattr(msg, "role", "unknown")
            content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")

            role_labels = {
                "user": "👤 用户",
                "assistant": "🤖 Agent",
                "system": "⚙️ 系统",
                "tool": "🔧 工具",
            }
            label = role_labels.get(role, role)

            lines.append(f"## {label}\n")
            lines.append(content)
            lines.append("\n---\n")

        output.write_text("\n".join(lines), encoding="utf-8")
        return str(output)

    def export_latex(self, content: str, title: str = "UltraAgent 输出", filename: str | None = None) -> str:
        """导出为 LaTeX"""
        if filename is None:
            filename = f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tex"

        output = self.export_dir / filename
        latex = f"""\\documentclass[11pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{amsmath,amssymb,graphicx,hyperref,booktabs}}
\\title{{{title}}}
\\author{{UltraAgent}}
\\date{{\\today}}
\\begin{{document}}
\\maketitle
{content}
\\end{{document}}
"""
        output.write_text(latex, encoding="utf-8")
        return str(output)

    def export_json(self, messages: list, filename: str | None = None) -> str:
        """导出为 JSON"""
        if filename is None:
            filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        output = self.export_dir / filename
        data = []
        for msg in messages:
            if isinstance(msg, dict):
                data.append(msg)
            else:
                data.append({
                    "role": getattr(msg, "role", "unknown"),
                    "content": getattr(msg, "content", ""),
                })

        output.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return str(output)

    def export_html(self, messages: list, title: str = "UltraAgent 会话", filename: str | None = None) -> str:
        """导出为 HTML"""
        if filename is None:
            filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        output = self.export_dir / filename

        body_parts = []
        for msg in messages:
            role = msg.get("role", "unknown") if isinstance(msg, dict) else getattr(msg, "role", "unknown")
            content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")

            role_class = {
                "user": "user-message",
                "assistant": "assistant-message",
                "system": "system-message",
                "tool": "tool-message",
            }.get(role, "other-message")

            body_parts.append(
                f'<div class="message {role_class}">'
                f'<strong>{role}</strong><br>'
                f'<pre>{content}</pre></div>'
            )

        html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
.message {{ padding: 12px; margin: 8px 0; border-radius: 8px; }}
.user-message {{ background: #e3f2fd; }}
.assistant-message {{ background: #f3e5f5; }}
.system-message {{ background: #fff3e0; font-size: 0.9em; }}
.tool-message {{ background: #e8f5e9; font-size: 0.85em; }}
pre {{ white-space: pre-wrap; word-wrap: break-word; }}
</style>
</head>
<body>
<h1>{title}</h1>
<p>导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
{''.join(body_parts)}
</body>
</html>"""

        output.write_text(html, encoding="utf-8")
        return str(output)

    def export_project_summary(self, agent) -> str:
        """导出项目摘要"""
        status = agent.get_status()
        state = status.get("state", {})

        lines = ["# 项目摘要\n"]
        lines.append(f"**领域**: {agent.domain.name}\n")
        lines.append(f"**进度**: {state.get('progress', 0)}%\n")
        lines.append(f"**当前阶段**: {state.get('current_phase_name', '未知')}\n")
        lines.append(f"**消息数**: {status.get('memory_messages', 0)}\n")
        lines.append(f"**Token 数**: {status.get('memory_tokens', 0)}\n")

        context = status.get("context", "")
        if context and "暂无" not in str(context):
            lines.append(f"\n## 已完成工作\n{context}\n")

        return self.export_markdown(
            [{"role": "system", "content": "\n".join(lines)}],
            filename="project_summary.md",
        )
