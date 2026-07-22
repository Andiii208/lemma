"""沙箱逃逸测试 — 验证 AST 黑名单能拦截常见绕过手法"""

import pytest
from lemma.tools.sandbox import SecurityChecker


class TestSandboxEscape:
    """当前黑名单可被以下手法绕过，测试应 FAIL（红）直到修复"""

    def test_blocks_getattr_builtins_eval(self):
        """getattr(__builtins__, 'eval') 应被拦截"""
        code = "f = getattr(__builtins__, 'eval'); f('1+1')"
        errors = SecurityChecker().check(code)
        assert any(
            "builtins" in e.lower() or "getattr" in e.lower() or "eval" in e.lower()
            for e in errors
        ), f"沙箱被绕过! errors={errors}"

    def test_blocks_dunder_class_mro(self):
        """().__class__.__bases__[0].__subclasses__() 应被拦截"""
        code = "().__class__.__bases__[0].__subclasses__()"
        errors = SecurityChecker().check(code)
        assert len(errors) > 0, f"通过 mro 链访问子类未被拦截! errors={errors}"

    def test_blocks_dunder_globals(self):
        """访问 __globals__ 应被拦截"""
        code = "def f(): pass\nf.__globals__['__builtins__']"
        errors = SecurityChecker().check(code)
        assert any("globals" in e.lower() or "dunder" in e.lower() for e in errors), \
            f"__globals__ 访问未被拦截! errors={errors}"

    def test_blocks_dunder_subclasses(self):
        """访问 __subclasses__ 应被拦截"""
        code = "str.__subclasses__()"
        errors = SecurityChecker().check(code)
        assert len(errors) > 0, f"__subclasses__ 未被拦截! errors={errors}"

    def test_blocks_dunder_mro(self):
        """访问 __mro__ 应被拦截"""
        code = "x = str.__mro__"
        errors = SecurityChecker().check(code)
        assert any("mro" in e.lower() or "dunder" in e.lower() for e in errors), \
            f"__mro__ 未被拦截! errors={errors}"

    def test_allows_normal_code(self):
        """普通科学计算代码不应被误拦"""
        code = """
import numpy as np
x = np.array([1, 2, 3])
print(x.mean())
"""
        errors = SecurityChecker(allowed_modules={"numpy"}).check(code)
        assert len(errors) == 0, f"正常代码被误拦: {errors}"
