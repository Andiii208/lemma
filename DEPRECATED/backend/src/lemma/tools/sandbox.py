"""代码执行沙箱 — AST 级别安全检查（含 dunder 链与动态获取拦截）"""

from __future__ import annotations

import ast

# 禁止的模块（可被 allowlist 覆盖）
BLOCKED_MODULES: set[str] = {
    "subprocess",
    "os",
    "shutil",
    "pathlib",
    "socket",
    "http",
    "urllib",
    "requests",
    "ctypes",
    "importlib",
    "code",
    "codeop",
    "compile",
    "compileall",
    "py_compile",
    "signal",
    "multiprocessing",
    "threading",
    "webbrowser",
    "smtplib",
    "ftplib",
}

# 禁止的内置函数
BLOCKED_BUILTINS: set[str] = {
    "exec",
    "eval",
    "compile",
    "__import__",
}

# 危险 dunder 属性 — 可用于沙箱逃逸（访问 builtins/类元数据/全局变量）
DANGEROUS_DUNDERS: set[str] = {
    "__builtins__",
    "__globals__",
    "__locals__",
    "__subclasses__",
    "__class__",
    "__mro__",
    "__bases__",
    "__code__",
    "__func__",
    "__self__",
}

# getattr 的危险参数（动态获取禁用函数）
DANGEROUS_GETATTR_ARGS: set[str] = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "__builtins__",
    "__globals__",
    "__subclasses__",
}


class SecurityError(Exception):
    """安全策略违规"""

    pass


class SecurityChecker(ast.NodeVisitor):
    """AST 级别的安全检查器"""

    def __init__(self, allowed_modules: set[str] | None = None):
        self.allowed_modules = allowed_modules or set()
        self.errors: list[str] = []

    def check(self, code: str) -> list[str]:
        """检查代码安全性，返回错误列表（空列表表示安全）"""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return [f"Syntax error: {e}"]
        self.visit(tree)
        return self.errors

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            module_name = alias.name.split(".")[0]
            if module_name in BLOCKED_MODULES and module_name not in self.allowed_modules:
                self.errors.append(f"Blocked module: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            module_name = node.module.split(".")[0]
            if module_name in BLOCKED_MODULES and module_name not in self.allowed_modules:
                self.errors.append(f"Blocked module: {node.module}")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """拦截危险 dunder 属性访问（如 obj.__globals__、cls.__subclasses__）"""
        if node.attr in DANGEROUS_DUNDERS:
            self.errors.append(f"Blocked dunder access: {node.attr}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """拦截禁用内置函数 + getattr/hasattr 动态获取"""
        # 拦截直接调用禁用函数：exec(...)、eval(...)
        if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_BUILTINS:
            self.errors.append(f"Blocked builtin: {node.func.id}")

        # 拦截 getattr(x, 'eval') / getattr(x, '__builtins__') 等
        if isinstance(node.func, ast.Name) and node.func.id == "getattr":
            if len(node.args) >= 2:
                arg = node.args[1]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if arg.value in DANGEROUS_GETATTR_ARGS or arg.value in DANGEROUS_DUNDERS:
                        self.errors.append(f"Blocked dynamic getattr: {arg.value}")

        self.generic_visit(node)
