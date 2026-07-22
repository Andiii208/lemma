"""沙箱安全检查单元测试"""
import pytest
from lemma.tools.sandbox import SecurityChecker, BLOCKED_MODULES


class TestSecurityChecker:
    def test_blocks_subprocess(self):
        checker = SecurityChecker()
        errors = checker.check("import subprocess; subprocess.call(['ls'])")
        assert any("subprocess" in e for e in errors)

    def test_blocks_os(self):
        checker = SecurityChecker()
        errors = checker.check("import os; os.system('rm -rf /')")
        assert any("os" in e for e in errors)

    def test_blocks_socket(self):
        checker = SecurityChecker()
        errors = checker.check("import socket")
        assert any("socket" in e for e in errors)

    def test_blocks_shutil(self):
        checker = SecurityChecker()
        errors = checker.check("import shutil")
        assert any("shutil" in e for e in errors)

    def test_allows_numpy(self):
        checker = SecurityChecker(allowed_modules={"numpy"})
        errors = checker.check("import numpy as np; np.array([1,2,3])")
        assert len(errors) == 0

    def test_allows_scipy(self):
        checker = SecurityChecker(allowed_modules={"scipy"})
        errors = checker.check("from scipy.optimize import minimize")
        assert len(errors) == 0

    def test_blocks_exec(self):
        checker = SecurityChecker()
        errors = checker.check("exec('import os')")
        assert any("exec" in e for e in errors)

    def test_blocks_eval(self):
        checker = SecurityChecker()
        errors = checker.check("eval('1+1')")
        assert any("eval" in e for e in errors)

    def test_blocks_dunder_import(self):
        checker = SecurityChecker()
        errors = checker.check("__import__('os')")
        assert any("__import__" in e for e in errors)

    def test_syntax_error_reported(self):
        checker = SecurityChecker()
        errors = checker.check("def foo(")
        assert len(errors) > 0
        assert "Syntax error" in errors[0]

    def test_clean_code_passes(self):
        checker = SecurityChecker()
        errors = checker.check("x = 1\ny = 2\nprint(x + y)")
        assert len(errors) == 0

    def test_multiple_violations(self):
        checker = SecurityChecker()
        errors = checker.check("import os\nimport subprocess\nexec('test')")
        assert len(errors) >= 3

    def test_allowed_modules_override_blocked(self):
        checker = SecurityChecker(allowed_modules={"os"})
        errors = checker.check("import os")
        assert len(errors) == 0

    def test_nested_import_from(self):
        checker = SecurityChecker()
        errors = checker.check("from os.path import join")
        assert any("os" in e for e in errors)
