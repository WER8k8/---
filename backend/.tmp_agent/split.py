import ast, os

BUILTINS = set(__builtins__) if isinstance(__builtins__, dict) else set(dir(__builtins__))

def collect_names(node):
    loaded=set(); stored=set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            if isinstance(n.ctx, ast.Load):
                loaded.add(n.id)
            else:
                stored.add(n.id)
        elif isinstance(n, (ast.For, ast.AsyncFor)):
            for t in ast.walk(n.target):
                if isinstance(t, ast.Name): stored.add(t.id)
        elif isinstance(n, ast.comprehension):
            for t in ast.walk(n.target):
                if isinstance(t, ast.Name): stored.add(t.id)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            stored.add(n.name)
        elif isinstance(n, (ast.With, ast.AsyncWith)):
            for item in n.items:
                if item.optional_vars:
                    for t in ast.walk(item.optional_vars):
                        if isinstance(t, ast.Name): stored.add(t.id)
        elif isinstance(n, ast.NamedExpr):
            for t in ast.walk(n.target):
                if isinstance(t, ast.Name): stored.add(t.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            stored.add(n.name)
    return loaded, stored

def has_forbidden(node):
    for n in ast.walk(node):
        if isinstance(n, (ast.Return, ast.Break, ast.Continue, ast.Yield, ast.YieldFrom,
                          ast.Global, ast.Nonlocal)):
            return True
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n is not node:
            return True
    return False

def get_module_globals(src):
    tree=ast.parse(src)
    g=set()
    for n in tree.body:
        if isinstance(n, ast.Assign):
            for t in n.targets:
                for nm in ast.walk(t):
                    if isinstance(nm, ast.Name): g.add(nm.id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            g.add(n.target.id)
        elif isinstance(n, ast.Import):
            for a in n.names: g.add(a.asname or a.name.split('.')[0])
        elif isinstance(n, ast.ImportFrom):
            for a in n.names: g.add(a.asname or a.name)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            g.add(n.name)
    return g

def try_extract_seg(func, seg, module_globals, params, is_method):
    if not seg: return False, None
    for s in seg:
        if has_forbidden(s): return False, None
    loaded=set(); stored=set()
    for s in seg:
        l,s_=collect_names(s); loaded|=l; stored|=s_
    inputs = (loaded - stored) - params - module_globals - BUILTINS - ({"self","cls"} if is_method else set())
    seg_end = max(s.end_lineno for s in seg)
    after=set()
    for s in func.body:
        if s.lineno > seg_end:
            l,_=collect_names(s); after|=l
    outputs=[n for n in stored if n in after]
    has_await = any(isinstance(n, ast.Await) for s in seg for n in ast.walk(s))
    return True, {"inputs":sorted(inputs),"outputs":outputs,"has_await":has_await}

def split_once(src, func_name, module_globals):
    lines = src.splitlines()
    tree = ast.parse(src)
    funcs=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==func_name]
    if not funcs: return src, False
    func=funcs[0]
    if (func.end_lineno-func.lineno+1)<=100: return src, False
    is_method = bool(func.args.args) and func.args.args[0].arg in ("self","cls")
    params=set()
    for a in func.args.args: params.add(a.arg)
    if func.args.vararg: params.add(func.args.vararg.arg)
    if func.args.kwarg: params.add(func.args.kwarg.arg)
    for a in func.args.kwonlyargs: params.add(a.arg)
    body=func.body
    # find best segment: prefer longest single eligible statement, else runs
    best=None
    # single statements
    candidates=[]
    for i in range(len(body)):
        ok,_=try_extract_seg(func, body[i:i+1], module_globals, params, is_method)
        if ok: candidates.append((i,i))
    for i in range(len(body)):
        for j in range(i+1,len(body)):
            ok,_=try_extract_seg(func, body[i:j+1], module_globals, params, is_method)
            if ok: candidates.append((i,j))
    if not candidates: return src, False
    # choose the one that reduces most lines: pick largest span
    best=max(candidates, key=lambda c: c[1]-c[0])
    i,j=best
    seg=body[i:j+1]
    ok,info=try_extract_seg(func, seg, module_globals, params, is_method)
    # determine indents
    if is_method:
        DEF_IND="    "; BODY_IND="        "; MAIN_IND="        "
    else:
        DEF_IND=""; BODY_IND="    "; MAIN_IND="    "
    seg_src="\n".join(lines[seg[0].lineno-1:seg[-1].end_lineno])
    seg_lines=seg_src.splitlines()
    nonempty=[l for l in seg_lines if l.strip()]
    minind=min(len(l)-len(l.lstrip()) for l in nonempty) if nonempty else 0
    seg_body="\n".join((l[minind:] if l.strip() else "") for l in seg_lines)
    helper_name="_"+func_name+"_extracted"
    c=1
    while helper_name in module_globals or any(n.name==helper_name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))):
        helper_name="_"+func_name+f"_extracted{c}"; c+=1
    params_str=(", ".join(info['inputs']))
    if is_method:
        full_params=("self"+(", "+params_str if params_str else ""))
    else:
        full_params=params_str
    # build helper source lines
    hdef=DEF_IND+("async def " if info['has_await'] else "def ")+helper_name+"("+full_params+"):\n"
    doc=[]
    doc.append(BODY_IND+'"""提取出的子流程，封装原函数的局部计算逻辑。')
    doc.append("")
    plist=(["self"] if is_method else [])+list(info['inputs'])
    doc.append(BODY_IND+":param "+(", ".join(plist) if plist else "self")+": 输入参数")
    if info['outputs']:
        doc.append(BODY_IND+":return: 返回 "+", ".join(info['outputs'])+" 等计算结果")
    else:
        doc.append(BODY_IND+":return: 无返回（仅副作用）")
    doc.append(BODY_IND+'"""')
    body_code=[]
    for l in seg_body.splitlines():
        if l.strip()=="":
            body_code.append("")
        else:
            body_code.append(BODY_IND+l)
    ret_line=""
    if info['outputs']:
        ret_line=BODY_IND+"return "+(", ".join(info['outputs']) if len(info['outputs'])>1 else info['outputs'][0])
    helper_src=hdef+"\n".join(doc)+"\n"+"\n".join(body_code)
    if ret_line:
        helper_src+="\n"+ret_line
    # call line
    call_out = (", ".join(info['outputs'])+" = ") if info['outputs'] else ""
    call_expr=("self." if is_method else "")+helper_name+"("+params_str+")"
    call_line=MAIN_IND+call_out+(("await " if info['has_await'] else "")+call_expr)
    # replace segment
    start=seg[0].lineno-1
    end=seg[-1].end_lineno
    new_lines=lines[:start]+[call_line]+lines[end:]
    # insert helper before func
    insert_at=func.lineno-1
    helper_block=helper_src.splitlines()
    new_lines=new_lines[:insert_at]+helper_block+[""]+new_lines[insert_at:]
    out="\n".join(new_lines)
    if src.endswith("\n"): out+="\n"
    return out, True

if __name__=="__main__":
    BASE="app/services"
    EXCLUDE={"hermes","ubrain","__pycache__"}
    TARGET=os.environ.get("TARGET","")
    FILES=[]
    for root,dirs,fnames in os.walk(BASE):
        dirs[:]=[d for d in dirs if d not in EXCLUDE]
        for fn in fnames:
            if fn.endswith(".py"):
                full=os.path.join(root,fn)
                if os.path.dirname(full)==BASE: continue
                if TARGET and TARGET not in full: continue
                FILES.append(full)
    changed_files=0
    for fp in FILES:
        src=open(fp,encoding="utf-8").read()
        try: tree=ast.parse(src)
        except Exception as e: print("PARSE ERR",fp,e); continue
        module_globals=get_module_globals(src)
        big=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and (n.end_lineno-n.lineno+1)>100]
        if not big: continue
        orig=src
        did_any=False
        for fn in big:
            for _ in range(20):
                ns,done=split_once(src, fn.name, module_globals)
                if not done: break
                src=ns; did_any=True
        if did_any:
            open(fp,"w",encoding="utf-8").write(src)
            changed_files+=1
            print("SPLIT",fp)
    print("FILES SPLIT:",changed_files)
