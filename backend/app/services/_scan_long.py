import ast
import os
import sys

TARGET = os.path.dirname(os.path.abspath(__file__))


def scan_one(path):
    try:
        src = open(path, "r", encoding="utf-8").read()
        tree = ast.parse(src)
    except SyntaxError as exc:
        return [("__SYNTAX_ERROR__", str(exc), 0)]
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            n = node.end_lineno - node.lineno + 1
            if n > 100:
                out.append((node.name, node.lineno, n))
    return out


def main():
    rows = []
    for name in sorted(os.listdir(TARGET)):
        if not name.endswith(".py"):
            continue
        p = os.path.join(TARGET, name)
        if not os.path.isfile(p):
            continue
        for r in scan_one(p):
            rows.append((name, r[0], r[1], r[2]))
    rows.sort(key=lambda x: -x[3])
    for f, fn, ln, n in rows:
        print(f"{f}::{fn} line={ln} len={n}")
    print("TOTAL", len(rows))


main()
