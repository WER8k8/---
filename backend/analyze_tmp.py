import ast, os

base = "app/services"
files = sorted([f for f in os.listdir(base)
               if f.endswith('.py') and not f.endswith('.bak')
               and f[0] in 'nopqrstuvwxyz'])

total_funcs = 0
no_doc = 0
over100 = 0
report = []
for f in files:
    path = os.path.join(base, f)
    src = open(path, encoding='utf-8').read()
    try:
        tree = ast.parse(src)
    except Exception as e:
        report.append((f, 'PARSE_ERROR', str(e)))
        continue

    def walk(node):
        for n in ast.iter_child_nodes(node):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield n
            else:
                yield from walk(n)

    fns = list(walk(tree))
    f_no = 0
    f_over = 0
    for fn in fns:
        total_funcs += 1
        has_doc = (fn.body and isinstance(fn.body[0], ast.Expr)
                   and isinstance(fn.body[0].value, ast.Constant)
                   and isinstance(fn.body[0].value.value, str))
        end = getattr(fn, 'end_lineno', None) or fn.lineno
        length = end - fn.lineno + 1
        if not has_doc:
            f_no += 1
            no_doc += 1
        if length > 100:
            f_over += 1
            over100 += 1
    report.append((f, len(fns), f_no, f_over))

print(f"FILES={len(files)} TOTAL_FUNCS={total_funcs} NO_DOC={no_doc} OVER100={over100}")
print("-" * 80)
for item in report:
    if isinstance(item[1], str):
        print(f"PARSE ERROR {item[0]}: {item[2]}")
        continue
    f, nf, nd, ov = item
    if nd > 0 or ov > 0:
        print(f"{f:45s} funcs={nf:3d} no_doc={nd:3d} over100={ov:3d}")
