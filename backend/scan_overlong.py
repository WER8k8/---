import ast, os

root = "app/services/ubrain"
results = []
for dirpath, _, files in os.walk(root):
    for f in files:
        if not f.endswith(".py"):
            continue
        path = os.path.join(dirpath, f)
        try:
            src = open(path, encoding="utf-8").read()
            tree = ast.parse(src)
        except Exception as e:
            print("PARSE ERROR", path, e)
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.lineno and node.end_lineno:
                    cnt = node.end_lineno - node.lineno + 1
                    if cnt > 100:
                        results.append((path, node.name, node.lineno, node.end_lineno, cnt, isinstance(node, ast.AsyncFunctionDef)))

results.sort(key=lambda r: -r[4])
for path, name, ln, eln, cnt, isasync in results:
    print(f"{cnt:4d} lines  {path}  {name} (def@{ln}-{eln}) {'async' if isasync else ''}")
print("\nTOTAL overlong:", len(results))
