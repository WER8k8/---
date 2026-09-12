import ast, os, py_compile, sys
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
err=0
for fp in FILES:
    try:
        py_compile.compile(fp, doraise=True, quiet=2)
    except py_compile.PyCompileError as e:
        err+=1
        print("COMPILE ERROR:",fp)
        print(str(e)[:300])
print("COMPILE ERRORS:",err,"of",len(FILES),"files")
