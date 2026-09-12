import ast, os
scope_dirs = ["app/core", "app/tasks", "app/geo_engine"]
scope_files = ["app/main.py", "app/__init__.py"]
def iter_py(p):
    if os.path.isfile(p):
        yield p; return
    for dp,_,fs in os.walk(p):
        for f in fs:
            if f.endswith(".py"):
                yield os.path.join(dp,f)
files=[]
for d in scope_dirs:
    files += list(iter_py(d))
files += scope_files
for f in sorted(set(files)):
    try:
        src=open(f,encoding="utf-8").read()
    except Exception as e:
        print("ERR",f,e); continue
    try:
        tree=ast.parse(src)
    except Exception as e:
        print("PARSEERR",f,e); continue
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            end=getattr(node,"end_lineno",None)
            if end is None: continue
            length=end-node.lineno+1
            if length>100:
                print(f"{f}:{node.name}:{length} lines (def@{node.lineno})")
