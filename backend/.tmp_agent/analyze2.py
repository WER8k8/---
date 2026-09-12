import ast, os
BASE="app/services"
EXCLUDE={"hermes","ubrain","__pycache__"}
FILES=[]
for root,dirs,fnames in os.walk(BASE):
    dirs[:]=[d for d in dirs if d not in EXCLUDE]
    for fn in fnames:
        if fn.endswith(".py"):
            full=os.path.join(root,fn)
            if os.path.dirname(full)==BASE: continue
            FILES.append(full)
missing=0; over100=0
miss_files=set(); over_files={}
for fp in FILES:
    try:
        src=open(fp,encoding="utf-8").read(); tree=ast.parse(src)
    except Exception as e:
        print("ERR",fp,e); continue
    def visit(n):
        global missing,over100
        for c in n.body:
            if isinstance(c,(ast.FunctionDef,ast.AsyncFunctionDef)):
                if ast.get_docstring(c) is None:
                    missing+=1; miss_files.add(fp)
                nl=(c.end_lineno-c.lineno+1) if c.end_lineno else 0
                if nl>100:
                    over100+=1
                    over_files.setdefault(fp,[]).append((c.name,c.lineno,nl))
                visit(c)
    visit(tree)
print("SUBDIR FUNCS MISSING DOCSTRING:",missing,"in",len(miss_files),"files")
print("SUBDIR FUNCS >100 LINES:",over100)
for fp in sorted(over_files):
    for nm,ln,nl in over_files[fp]:
        print(f"  O100 {fp}:{ln} {nm} ({nl})")
