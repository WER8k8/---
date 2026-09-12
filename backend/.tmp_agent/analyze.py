import ast, os

BASE = "app/services"
EXCLUDE_DIRS = {"hermes","ubrain","__pycache__"}
FILES = []
for root, dirs, fnames in os.walk(BASE):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for fn in fnames:
        if fn.endswith(".py"):
            FILES.append(os.path.join(root, fn))

print("TOTAL FILES:", len(FILES))
missing = 0
over100 = 0
file_missing = {}
file_over100 = {}
for fp in FILES:
    try:
        src = open(fp, encoding="utf-8").read()
        tree = ast.parse(src)
    except Exception as e:
        print("PARSE ERROR", fp, e)
        continue
    def visit(node):
        global missing, over100
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                has_doc = ast.get_docstring(child) is not None
                fn_lines = (child.end_lineno - child.lineno + 1) if child.end_lineno else 0
                if not has_doc:
                    missing += 1
                    file_missing.setdefault(fp, []).append((child.name, child.lineno))
                if fn_lines > 100:
                    over100 += 1
                    file_over100.setdefault(fp, []).append((child.name, child.lineno, fn_lines))
                visit(child)
    visit(tree)

print("FUNCS MISSING DOCSTRING:", missing)
print("FUNCS >100 LINES:", over100)
print("FILES WITH MISSING:", len(file_missing))
print("FILES WITH >100:", len(file_over100))
for fp in sorted(file_over100):
    for name,ln,n in file_over100[fp]:
        print(f"  O100 {fp}:{ln} {name} ({n} lines)")
