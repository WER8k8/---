import ast
import os
import sys

ROOT = sys.argv[1]
THRESHOLD = int(sys.argv[2]) if len(sys.argv) > 2 else 100

results = []
errors = []

for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git")]
    for fn in sorted(filenames):
        if not fn.endswith(".py"):
            continue
        path = os.path.join(dirpath, fn)
        src = open(path, encoding="utf-8").read()
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            errors.append((path, f"SyntaxError line {e.lineno}: {e.msg}"))
            continue
        lines = src.splitlines()
        stack = []

        def walk(node, prefix):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    length = (child.end_lineno or child.lineno) - child.lineno + 1
                    qual = prefix + child.name
                    if length > THRESHOLD:
                        results.append((path, qual, child.lineno, child.end_lineno, length, "async" if isinstance(child, ast.AsyncFunctionDef) else "def"))
                    walk(child, qual + ".")
                elif isinstance(child, ast.ClassDef):
                    walk(child, prefix + child.name + ".")
                else:
                    walk(child, prefix)

        walk(tree, "")

results.sort(key=lambda r: -r[4])
for r in results:
    print(f"{r[4]:5d}  {r[0]}  ::  {r[1]}  L{r[2]}-{r[3]}  ({r[5]})")
print("---- total long funcs:", len(results))
print("---- syntax errors:", len(errors))
for p, m in errors:
    print("SYNTAXERR", p, m)
