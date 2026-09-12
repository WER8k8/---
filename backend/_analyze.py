import ast, os, glob

root = "app/api/v1/routes"
files = sorted(glob.glob(os.path.join(root, "[m-z]*.py")))

total_funcs = 0
missing = []
long_funcs = []
parse_err = []
for f in files:
    try:
        src = open(f, encoding="utf-8").read()
    except Exception as e:
        print("READ ERR", f, e); continue
    try:
        tree = ast.parse(src)
    except Exception as e:
        parse_err.append((f, str(e))); continue
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            total_funcs += 1
            has_doc = ast.get_docstring(node)
            end = getattr(node, "end_lineno", node.lineno)
            nlines = end - node.lineno + 1
            if not has_doc:
                missing.append((f, node.name, node.lineno, nlines))
            if nlines > 100:
                long_funcs.append((f, node.name, node.lineno, nlines))

print("FILES:", len(files))
print("TOTAL FUNCS:", total_funcs)
print("MISSING DOCSTR:", len(missing))
print("LONG (>100):", len(long_funcs))
if parse_err:
    print("PARSE ERRORS:", parse_err)
print("---- MISSING (file:line name lines) ----")
for f,name,ln,n in sorted(missing, key=lambda x:(x[0],x[2])):
    print(f"{f}:{ln} {name} ({n} lines)")
print("---- LONG FUNCS ----")
for f,name,ln,n in sorted(long_funcs, key=lambda x:(x[0],x[2])):
    print(f"{f}:{ln} {name} ({n} lines)")
