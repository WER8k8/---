"""A7 扫描器：统计 app/services 根目录 a-m 文件的 docstring 缺失与超长函数。"""
import ast
import io
import json
import os
import sys

BASE = os.path.join("app", "services")


def is_chinese(text):
    """判断字符串是否含中文字符。"""
    return any("\u4e00" <= ch <= "\u9fff" for ch in text or "")


def scan(path):
    """扫描单个文件，返回 (缺docstring函数列表, 超长函数列表, 总函数数)。"""
    with io.open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return None, None, None, "SYNTAX:%s" % exc
    missing = []
    toolong = []
    total = 0
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        total += 1
        doc = ast.get_docstring(node)
        if not doc or not is_chinese(doc):
            missing.append((node.name, node.lineno, bool(doc)))
        end = getattr(node, "end_lineno", node.lineno)
        span = end - node.lineno + 1
        if span > 100:
            toolong.append((node.name, node.lineno, end, span))
    return missing, toolong, total, None


def main():
    """主入口：输出 JSON 汇总。"""
    names = sys.argv[1:]
    if not names:
        names = sorted(
            f for f in os.listdir(BASE)
            if f.endswith(".py") and f[0].lower() in "abcdefghijklm"
        )
    out = {}
    for name in names:
        path = os.path.join(BASE, name)
        missing, toolong, total, err = scan(path)
        if err:
            out[name] = {"error": err}
            continue
        if missing or toolong:
            out[name] = {
                "total": total,
                "missing": missing,
                "toolong": toolong,
            }
    print(json.dumps(out, ensure_ascii=False, indent=1))
    tm = sum(len(v.get("missing", [])) for v in out.values() if "error" not in v)
    tl = sum(len(v.get("toolong", [])) for v in out.values() if "error" not in v)
    print("FILES_WITH_WORK=%d MISSING=%d TOOLONG=%d" % (len(out), tm, tl), file=sys.stderr)


if __name__ == "__main__":
    main()
