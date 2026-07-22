#!/usr/bin/env python3
"""
UltraMath 代码静态检查脚本 — V9.0

用途: Phase 2 代码生成后的质量控制门禁。
Agent E 提交代码后自动检查三类已知趋势性 bug:
  1. 列表推导式变量名一致性 — body 中用的变量名与 for 子句一致吗？
  2. 跨函数参数传递完整性 — 全局参数在调用链中没漏传？
  3. solve() 配置检查 — 有没有设 timeLimit + gapRel？

使用:
    python scripts/check_code_bugs.py 求解/问题2/q2_cvar.py     # 检查单个文件
    python scripts/check_code_bugs.py --dir 求解/                # 扫描目录下所有 .py
    python scripts/check_code_bugs.py --dir 求解/ --ci           # CI 模式 (exit code only)

返回状态码:
    0 = PASS
    1 = WARN (有建议改进项)
    2 = BLOCK (有必须修复的 bug)
"""

import argparse
import ast
import os
import re
import sys
from pathlib import Path

GLOBAL_PARAM_PATTERNS = [
    r'\bN\b', r'\bM\b', r'\bT\b', r'\bscenarios\b', r'\blambda\b',
    r'\balpha\b', r'\bbeta\b', r'\bgamma\b', r'\bepsilon\b',
    r'\bomega\b', r'\bOmega\b', r'\bseed\b', r'\brandom_state\b',
    r'\btime_limit\b', r'\bgap_rel\b', r'\bnum_scenarios\b',
    r'\bSAMPLE_SIZE\b', r'\bN_SCENARIOS\b', r'\bCLUSTERS\b',
]


def check_listcomp_vars(source_code: str, filename: str) -> list[dict]:
    """Check list comprehension variable name consistency

    CC 已知 bug: 列表推导式中 body 引用了 for 子句未声明的变量名
    例如: [(s - l) for ss in range(N)]  →  s 应为 ss
    """
    results = []
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        results.append({
            "type": "SYNTAX_ERROR",
            "severity": "BLOCK",
            "detail": f"语法错误: {e}",
            "line": e.lineno,
        })
        return results

    class ListCompVisitor(ast.NodeVisitor):
        def __init__(self):
            self.issues = []

        def visit_ListComp(self, node):
            # Collect loop variables from all generators
            loop_vars = set()
            for gen in node.generators:
                for target in ast.walk(gen.target):
                    if isinstance(target, ast.Name):
                        loop_vars.add(target.id)
                    elif isinstance(target, ast.Tuple):
                        for elt in target.elts:
                            if isinstance(elt, ast.Name):
                                loop_vars.add(elt.id)

            # Find all Name references in the body expression
            body_vars = set()
            for n in ast.walk(node.elt):
                if isinstance(n, ast.Name):
                    body_vars.add(n.id)

            # Names used in body but not defined by generators
            undefined = body_vars - loop_vars
            # Filter out builtins, common keywords, etc.
            builtins = {"range", "len", "int", "float", "str", "list", "sum",
                        "min", "max", "abs", "zip", "enumerate", "True", "False", "None",
                        "print", "type", "isinstance", "hasattr", "getattr", "setattr",
                        "sorted", "reversed", "any", "all", "map", "filter",
                        "dict", "set", "tuple", "round", "pow", "sqrt"}
            suspicious = [v for v in undefined if v not in builtins]

            if suspicious:
                loop_vars_str = ", ".join(sorted(loop_vars))
                suspicious_str = ", ".join(suspicious)
                src_snippet = ast.get_source_segment(source_code, node)
                self.issues.append({
                    "type": "LISTCOMP_VAR_MISMATCH",
                    "severity": "BLOCK",
                    "detail": f"列表推导式: body 使用了「{suspicious_str}」但 for 子句变量为「{loop_vars_str}」",
                    "code": (src_snippet[:80] + "..") if src_snippet and len(src_snippet) > 80 else src_snippet,
                    "line": node.lineno,
                })

            self.generic_visit(node)

    visitor = ListCompVisitor()
    visitor.visit(tree)
    results.extend(visitor.issues)
    return results


def check_param_propagation(source_code: str, filename: str) -> list[dict]:
    """Check global parameter propagation across function call chains

    CC 已知 bug: 全局参数（如 N, alpha）在 main→solve→extract 的多层
    调用链中，在某层被遗漏。
    """
    results = []
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return results

    # Build function map
    funcs = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            funcs[node.name] = {
                "params": {arg.arg for arg in node.args.args},
                "calls": set(),
                "lineno": node.lineno,
            }

    # Find call sites
    class CallVisitor(ast.NodeVisitor):
        def visit_Call(self, node):
            if isinstance(node.func, ast.Name) and node.func.id in funcs:
                caller_name = self._current_func if hasattr(self, '_current_func') else None
                if caller_name and caller_name in funcs:
                    funcs[caller_name]["calls"].add(node.func.id)
            self.generic_visit(node)

    # Visit each function
    for func_node in ast.walk(tree):
        if isinstance(func_node, ast.FunctionDef):
            cv = CallVisitor()
            cv._current_func = func_node.name
            cv.visit(func_node)

    # Check parameter propagation across function call chains.
    # Heuristic: find function defs, check if caller's params that look "global"
    # (N, M, alpha, scenarios, etc.) are missing in callee's params.
    # Also check if callee uses global names without receiving them as params.
    func_defs = re.findall(r'def (\w+)\(([^)]*)\)', source_code)
    func_params = {name: [p.strip().split(":")[0].split("=")[0].strip()
                          for p in params.split(",") if p.strip()]
                   for name, params in func_defs}

    # Find common calling patterns
    for caller_name, caller_params in func_params.items():
        caller_body = _get_function_body(source_code, caller_name)
        if not caller_body:
            continue
        for callee_name, callee_params in func_params.items():
            if callee_name == caller_name:
                continue
            if callee_name in caller_body:
                # Caller calls callee. Check if any caller param that looks global
                # is missing in callee
                for p in caller_params:
                    if p in ("self", "cls"):
                        continue
                    if p in ["N", "M", "alpha", "beta", "lambda", "scenarios",
                             "num_scenarios", "seed"] and p not in callee_params:
                        results.append({
                            "type": "PARAM_MISSING",
                            "severity": "WARN",
                            "detail": f"函数 {caller_name} 调用 {callee_name}，但参数「{p}」在 {caller_name} 中有、在 {callee_name} 中未定义（可能遗漏传递）",
                        })

    # Additional check: callee function body uses global names without receiving them
    GLOBAL_NAMES = {"N", "M", "T", "alpha", "beta", "lambda", "scenarios",
                    "num_scenarios", "random_state", "seed", "SAMPLE_SIZE",
                    "N_SCENARIOS", "CLUSTERS"}
    for func_name, params in func_params.items():
        body = _get_function_body(source_code, func_name)
        if not body:
            continue
        for gname in GLOBAL_NAMES:
            if gname in params:
                continue  # already a param
            # Check if body uses this global name (as assignment target or value)
            if re.search(rf'\b{gname}\b', body):
                # Exclude cases where it's defined locally in the body
                if not re.search(rf'\b{gname}\s*=', body):
                    results.append({
                        "type": "GLOBAL_USED",
                        "severity": "WARN",
                        "detail": f"函数 {func_name} 使用了全局变量「{gname}」但未作为参数接收（可能依赖全局状态）",
                    })

    return results


def _get_function_body(source_code: str, func_name: str) -> str:
    """Extract function body text using AST for accuracy."""
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return ""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            # Get source lines for the function body (after the def line)
            start_line = node.lineno  # 1-indexed
            body_start = node.body[0].lineno if node.body else start_line + 1
            lines = source_code.split('\n')
            # Find end of function (next def at same indent or EOF)
            indent = len(lines[body_start - 1]) - len(lines[body_start - 1].lstrip()) if body_start <= len(lines) else 0
            end_line = len(lines)
            for i in range(body_start, len(lines)):
                line = lines[i]
                if line.strip() and not line.startswith(' ' * indent) and not line.startswith('\t'):
                    # Check if this is a new top-level def
                    if re.match(r'^(def |class |@)', line.lstrip()):
                        end_line = i
                        break
            return '\n'.join(lines[body_start - 1:end_line])
    return ""


def check_solve_config(source_code: str, filename: str) -> list[dict]:
    """Check solve() calls for timeLimit and gapRel configuration"""
    results = []

    # Find all model.solve() calls
    solve_calls = re.finditer(
        r'(\w+)\.solve\s*\(([^)]*)\)',
        source_code,
        re.DOTALL
    )

    call_count = 0
    missing_time_limit = 0
    missing_gap = 0

    for m in solve_calls:
        model_name = m.group(1)
        args = m.group(2)
        call_count += 1

        # Check for time_limit / timeLimit / TimeLimit
        if not re.search(r'(?i)time_?limit', args):
            missing_time_limit += 1
        if not re.search(r'(?i)gap_?rel|mip_?gap|opt_?tol', args):
            missing_gap += 1

    if call_count == 0:
        return [{
            "type": "NO_SOLVE_CALLS",
            "severity": "INFO",
            "detail": "未检测到 .solve() 调用（可能未包含求解逻辑）",
        }]

    results.append({
        "type": "SOLVE_COUNT",
        "severity": "INFO",
        "detail": f"检测到 {call_count} 处 .solve() 调用",
    })

    if missing_time_limit > 0:
        results.append({
            "type": "MISSING_TIME_LIMIT",
            "severity": "WARN",
            "detail": f"{missing_time_limit}/{call_count} 处 solve() 缺少 timeLimit 参数",
        })

    if missing_gap > 0:
        results.append({
            "type": "MISSING_GAP",
            "severity": "WARN",
            "detail": f"{missing_gap}/{call_count} 处 solve() 缺少 gapRel/mip_gap 参数",
        })

    if missing_time_limit == 0 and missing_gap == 0:
        results.append({
            "type": "SOLVE_CONFIG_COMPLETE",
            "severity": "PASS",
            "detail": f"所有 {call_count} 处 solve() 均配置了 timeLimit + gapRel",
        })

    return results


def main():
    parser = argparse.ArgumentParser(description="UltraMath 代码静态检查")
    parser.add_argument("files", nargs="*", help="Python 文件路径")
    parser.add_argument("--dir", default=None, help="扫描目录下所有 .py")
    parser.add_argument("--ci", action="store_true", help="CI 模式: 仅输出判定，无表格")
    args = parser.parse_args()

    py_files = []
    if args.files:
        py_files.extend(args.files)
    if args.dir:
        py_files.extend(sorted(Path(args.dir).rglob("*.py")))

    if not py_files:
        print("❌ 未指定 Python 文件。使用 --dir 或直接传入文件名。")
        sys.exit(2)

    all_results = []
    for f in py_files:
        fp = Path(f)
        if not fp.exists():
            print(f"⚠️ 文件不存在: {f}")
            continue

        source = fp.read_text(encoding="utf-8", errors="replace")
        fname = str(fp)

        all_results.extend(check_listcomp_vars(source, fname))
        all_results.extend(check_param_propagation(source, fname))
        all_results.extend(check_solve_config(source, fname))

    # ── Aggregate ──
    blocks = [r for r in all_results if r["severity"] == "BLOCK"]
    warns = [r for r in all_results if r["severity"] == "WARN"]
    passes = [r for r in all_results if r["severity"] == "PASS"]
    infos = [r for r in all_results if r["severity"] == "INFO"]

    # ── Print report ──
    if not args.ci:
        print("=" * 60)
        print("🔍 UltraMath 代码静态检查报告")
        print("=" * 60)

        if blocks:
            print(f"\n❌ BLOCK ({len(blocks)} 项 — 必须修复):")
            for r in blocks:
                line_info = f" 第 {r['line']} 行" if 'line' in r else ""
                print(f"  🔴 {r['detail']} {line_info}")
                if 'code' in r and r['code']:
                    print(f"    代码: {r['code']}")

        if warns:
            print(f"\n⚠️ WARN ({len(warns)} 项 — 建议修复):")
            for r in warns:
                print(f"  ⚠️  {r['detail']}")

        if passes:
            print(f"\n✅ PASS ({len(passes)} 项):")
            for r in passes:
                print(f"  ✅ {r['detail']}")

        if infos:
            print(f"\nℹ️  INFO ({len(infos)} 项):")
            for r in infos:
                print(f"  ℹ️  {r['detail']}")

    # ── Verdict ──
    if blocks:
        verdict = "BLOCK"
    elif warns:
        verdict = "WARN"
    else:
        verdict = "PASS"

    if not args.ci:
        print("\n" + "=" * 60)
        emoji = "✅" if verdict == "PASS" else ("⚠️" if verdict == "WARN" else "🔴")
        # 门禁分级标注：本脚本基于 AST 解析 + 正则匹配，全部为确定性检查
        gate_tier = "[脚本验证]"
        gate_explain = "基于 AST 语法树解析和正则模式匹配，可复现、无LLM参与"
        print(f"判定: {emoji} {verdict}  {gate_tier}")
        print(f"  ℹ️  {gate_explain}")

    if verdict == "BLOCK":
        sys.exit(2)
    elif verdict == "WARN":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
