import ast, sys, json

BACKEND = "C:/Users/Administrator.WIN-36O2UQRI3U1/Desktop/上线网站开发完成/上线网站.worktrees/agents-install-vscode-cline-deploy-strix/backend"

def find_function(tree, name, lineno):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name and node.lineno == lineno:
                return node
    return None

def get_indent(line):
    return len(line) - len(line.lstrip(' '))

def refactor(file_rel, func_name, func_lineno, start, end, helper_name,
             params=None, returns=None, is_method=None, is_async=None,
             return_call=False, preview=False):
    path = BACKEND + "/" + file_rel if not file_rel.startswith("/") else file_rel
    src = open(path, encoding="utf-8").read()
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)
    fn = find_function(tree, func_name, func_lineno)
    if fn is None:
        print("ERROR: function not found", file_rel, func_name, func_lineno)
        return False
    is_method_auto = any(isinstance(a, ast.arg) and a.arg in ('self','cls') for a in fn.args.args)
    if is_method is None:
        is_method = is_method_auto
    is_async_auto = isinstance(fn, ast.AsyncFunctionDef)
    if is_async is None:
        is_async = is_async_auto

    block = lines[start-1:end]
    min_indent = min(get_indent(l) for l in block if l.strip())
    def_line = lines[fn.lineno-1]
    fn_indent = get_indent(def_line)
    fn_indent_str = " " * fn_indent
    body_indent = " " * (fn_indent + 4)
    dedented = []
    for l in block:
        if l.strip() == "":
            dedented.append("")
        else:
            stripped = l[min_indent:] if len(l) >= min_indent else l.lstrip(' ')
            dedented.append(body_indent + stripped)
    helper_body = "\n".join(dedented)
    if helper_body and not helper_body.endswith("\n"):
        helper_body += "\n"

    builtins_set = set(__builtins__ if isinstance(__builtins__, dict) else dir(__builtins__))

    def gather_nodes(node, collected, in_nested=False):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            in_nested = True
        if isinstance(node, ast.Name) and not in_nested:
            collected.append((node.id, type(node.ctx)))
        for child in ast.iter_child_nodes(node):
            gather_nodes(child, collected, in_nested)

    block_nodes = [n for n in fn.body if hasattr(n,'lineno') and start <= n.lineno <= end]
    seen = {}
    def add_target_names(target):
        if isinstance(target, ast.Name):
            seen.setdefault(target.id, 'store')
        elif isinstance(target, (ast.Tuple, ast.List)):
            for e in target.elts:
                add_target_names(e)
        elif isinstance(target, ast.Starred):
            add_target_names(target.value)
    for n in block_nodes:
        for sub in ast.walk(n):
            if isinstance(sub, ast.ExceptHandler) and sub.name:
                seen.setdefault(sub.name, 'store')
            elif isinstance(sub, ast.comprehension):
                add_target_names(sub.target)
            elif isinstance(sub, (ast.For, ast.AsyncFor)):
                add_target_names(sub.target)
            elif isinstance(sub, ast.withitem) and sub.optional_vars is not None:
                add_target_names(sub.optional_vars)
    assigns = set()
    for n in block_nodes:
        collected = []
        gather_nodes(n, collected)
        for nm, ctx in collected:
            if nm not in seen:
                seen[nm] = 'store' if ctx is ast.Store else 'load'
            if ctx is ast.Store:
                assigns.add(nm)

    mod_globals = set(['self','cls','True','False','None'])
    for top in ast.walk(tree):
        if isinstance(top, ast.Import):
            for a in top.names:
                mod_globals.add((a.asname or a.name).split('.')[0])
        elif isinstance(top, ast.ImportFrom):
            for a in top.names:
                mod_globals.add(a.asname or a.name)
        elif isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and top is not fn:
            mod_globals.add(top.name)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                for sub in ast.walk(t):
                    if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                        mod_globals.add(sub.id)

    inputs = sorted(nm for nm, c in seen.items() if c == 'load' and nm not in builtins_set and nm not in mod_globals)

    block_text = "".join(block)
    has_await = ("await " in block_text) or ("await(" in block_text)

    if params is None:
        params = inputs
    if returns is None:
        post_reads = set()
        for n in fn.body:
            if hasattr(n,'lineno') and n.lineno > end:
                collected = []
                gather_nodes(n, collected)
                for nm, ctx in collected:
                    if ctx is ast.Load:
                        post_reads.add(nm)
        outputs = sorted(assigns & post_reads)
        returns = outputs

    pre_defined = set(a.arg for a in fn.args.args) | set(a.arg for a in fn.args.posonlyargs) | set(a.arg for a in fn.args.kwonlyargs)
    for n in fn.body:
        if hasattr(n,'lineno') and n.lineno < start:
            collected=[]
            gather_nodes(n, collected)
            for nm, ctx in collected:
                if ctx is ast.Store:
                    pre_defined.add(nm)
    extra = [r for r in returns if r in pre_defined and r not in builtins_set and r not in mod_globals]
    params = sorted(set(params) | set(extra))

    all_params = (['self'] if is_method else []) + list(params)
    seenp=set(); all_params=[p for p in all_params if not (p in seenp or seenp.add(p))]
    sig_params = ", ".join(all_params)
    call_args = ", ".join(all_params)

    async_kw = "async " if (is_async or has_await) else ""
    return_str = ""
    if returns:
        if len(returns) == 1:
            return_str = f"\n{body_indent}return {returns[0]}"
            assign_lhs = returns[0]
        else:
            return_str = f"\n{body_indent}return ({', '.join(returns)})"
            assign_lhs = ", ".join(returns)
    else:
        assign_lhs = None

    helper = f"\n\n{fn_indent_str}{async_kw}def {helper_name}({sig_params}):\n{helper_body}{return_str}\n"

    # ---- static verification of helper body ----
    import textwrap
    helper_ast = ast.parse(textwrap.dedent(helper))
    hfunc = [n for n in ast.walk(helper_ast) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))][0]
    h_assigns = set(); h_reads = set()
    def hgather(node, in_nested=False):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.Lambda,ast.ClassDef)):
            in_nested=True
        if isinstance(node, ast.Name) and not in_nested:
            if isinstance(node.ctx, ast.Store): h_assigns.add(node.id)
            elif isinstance(node.ctx, ast.Load): h_reads.add(node.id)
        for c in ast.iter_child_nodes(node):
            hgather(c, in_nested)
    hgather(hfunc)
    covered = set(all_params) | h_assigns | builtins_set | mod_globals
    missing = sorted(h_reads - covered)
    if missing:
        print("  *** WARNING missing inputs in helper:", missing)
    else:
        print("  OK: helper body references all covered.")

    call_indent = " " * min_indent
    await_kw = ('await ' if (is_async or has_await) else '')
    if return_call:
        call_line = f"{call_indent}return {await_kw}{helper_name}({call_args})\n"
    elif assign_lhs:
        call_line = f"{call_indent}{assign_lhs} = {await_kw}{helper_name}({call_args})\n"
    else:
        call_line = f"{call_indent}{await_kw}{helper_name}({call_args})\n"

    # warn about control-flow exits that would change semantics
    exits = {'return': 0, 'break': 0, 'continue': 0, 'raise': 0}
    def walk_exit(node, nested=False):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            nested = True
        for c in ast.iter_child_nodes(node):
            if isinstance(c, ast.Return) and not nested:
                exits['return'] += 1
            if isinstance(c, (ast.Break, ast.Continue)) and not nested:
                exits['break'] += 1
            if isinstance(c, ast.Raise) and not nested:
                exits['raise'] += 1
            walk_exit(c, nested)
    for n in block_nodes:
        walk_exit(n)
    if exits['break'] or exits['continue'] or exits['raise']:
        print("  *** WARNING block contains break/continue/raise - semantics may change")
    if exits['return'] and not return_call:
        print("  *** WARNING block contains return but return_call=False - semantics may change")

    new_lines = lines[:start-1] + [call_line] + lines[end:]
    new_text = "".join(new_lines)
    # re-parse to locate function end in the modified file, then insert helper
    new_tree = ast.parse(new_text)
    new_fn = find_function(new_tree, func_name, func_lineno)
    if new_fn is None:
        print("ERROR: function not found after modification")
        return False
    new_end = new_fn.end_lineno  # 1-indexed last line of function
    lines2 = new_text.splitlines(keepends=True)
    lines2 = lines2[:new_end] + [helper] + lines2[new_end:]
    out = "".join(lines2)

    print(f"### {file_rel} :: {func_name}  [{start}-{end}]")
    print(f"  is_method={is_method} is_async={is_async} has_await={has_await}")
    print(f"  params={params}")
    print(f"  returns={returns}")
    print("----- HELPER -----")
    print(helper)
    print("----- CALL -----")
    print(call_line)
    print("-----------------")

    if not preview:
        open(path, "w", encoding="utf-8").write(out)
        print("WRITTEN.")
    return True

if __name__ == "__main__":
    spec_path = sys.argv[1]
    specs = json.load(open(spec_path, encoding="utf-8"))
    # apply bottom-up so earlier (lower-line) edits don't shift later ranges
    specs.sort(key=lambda s: s.get('start', 0), reverse=True)
    for s in specs:
        s.setdefault('return_call', False)
        refactor(**s)
