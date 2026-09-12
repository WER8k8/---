import ast, os
BASE="app/services"
EXCLUDE={"hermes","ubrain","__pycache__"}
cnt=0
examples=[]
for root,dirs,fnames in os.walk(BASE):
    dirs[:]=[d for d in dirs if d not in EXCLUDE]
    for fn in fnames:
        if fn.endswith(".py"):
            full=os.path.join(root,fn)
            if os.path.dirname(full)==BASE: continue
            try:
                tree=ast.parse(open(full,encoding="utf-8").read())
            except: continue
            def visit(n):
                global cnt
                for c in n.body:
                    if isinstance(c,(ast.FunctionDef,ast.AsyncFunctionDef)):
                        if ast.get_docstring(c) is None and c.body and c.body[0].lineno==c.lineno:
                            cnt+=1
                            if len(examples)<15: examples.append(f"{full}:{c.lineno} {c.name}")
                        visit(c)
            visit(tree)
print("inline-missing-docstring functions:",cnt)
for e in examples: print("  ",e)
