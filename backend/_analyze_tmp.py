import ast, os, glob

targets = []
for f in glob.glob('app/api/v1/routes/*.py'):
    name = os.path.basename(f)
    first = name[0].lower()
    if first in 'abcdefghijkl':
        targets.append(f)
targets.sort()

total_func = 0
no_doc = 0
over100 = 0
files_with_issues = []
for f in targets:
    src = open(f, encoding='utf-8').read()
    try:
        tree = ast.parse(src)
    except Exception as e:
        print("PARSE ERROR", f, e)
        continue
    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    f_no_doc = 0
    f_over = 0
    for fn in funcs:
        total_func += 1
        has_doc = ast.get_docstring(fn) is not None
        if not has_doc:
            no_doc += 1
            f_no_doc += 1
        end = fn.end_lineno
        start = fn.lineno
        if (end - start + 1) > 100:
            over100 += 1
            f_over += 1
    if f_no_doc or f_over:
        files_with_issues.append((f, len(funcs), f_no_doc, f_over))

print("TOTAL FILES:", len(targets))
print("TOTAL FUNCS:", total_func)
print("NO DOC:", no_doc)
print("OVER 100:", over100)
print("---- FILES WITH ISSUES (file, total_funcs, no_doc, over100) ----")
for x in files_with_issues:
    print(x)
