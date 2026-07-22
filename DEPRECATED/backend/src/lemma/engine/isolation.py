"""Agent 文件隔离 — 不同 Agent 看到不同的文件集"""
from __future__ import annotations

from pathlib import Path


class FileVisibility:
    """控制 Agent 对工作目录中文件的可见性

    通过文件级别隔离实现真正的独立评审:
    - Critic 看不到原始问题 → 只能评价 Generator 的输出
    - Verifier 看不到推导过程 → 只能用不同方法验证结论
    - Tester 看不到业务上下文 → 纯粹的机械测试
    """

    def __init__(self, work_dir: Path, agent_role: str, isolation_rules: dict[str, list[str]]):
        """
        Args:
            work_dir: 工作目录
            agent_role: 当前角色 ID
            isolation_rules: {role_id: [glob_pattern, ...]} - 每个角色可见的文件模式
        """
        self.work_dir = work_dir
        self.agent_role = agent_role
        self.rules = isolation_rules

    def get_visible_files(self) -> list[Path]:
        """获取当前 Agent 可见的文件列表"""
        allowed = self.rules.get(self.agent_role, ["*"])
        if "*" in allowed:
            return list(self.work_dir.rglob("*"))

        visible: list[Path] = []
        for pattern in allowed:
            visible.extend(self.work_dir.glob(pattern))

        return sorted(set(f for f in visible if f.is_file()))

    def is_visible(self, file_path: str) -> bool:
        """检查指定文件是否对当前 Agent 可见"""
        visible = self.get_visible_files()
        target = self.work_dir / file_path
        return target in visible

    def filter_system_prompt(self, prompt: str) -> str:
        """在 system prompt 中注入可见文件列表"""
        visible = self.get_visible_files()
        max_files = 50
        file_list = "\n".join(
            str(f.relative_to(self.work_dir)) for f in visible[:max_files]
        )
        extra = f"\n\n## 你可访问的文件 ({len(visible)} 个):\n{file_list}"
        if len(visible) > max_files:
            extra += f"\n... 及 {len(visible) - max_files} 个其他文件"
        return prompt + extra
