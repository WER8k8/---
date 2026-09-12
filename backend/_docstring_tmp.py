import ast, os, glob

# 仅处理范围内的文件（首字母 a-l 的 routes 直文件）
targets = []
for f in glob.glob('app/api/v1/routes/*.py'):
    name = os.path.basename(f)
    first = name[0].lower()
    if first in 'abcdefghijkl':
        targets.append(f)
targets.sort()

VERB_MAP = {
    'get': '获取', 'fetch': '获取', 'retrieve': '获取', 'query': '查询',
    'load': '加载', 'read': '读取', 'create': '创建', 'make': '创建',
    'new': '新建', 'add': '新增', 'register': '注册',
    'update': '更新', 'set': '设置', 'modify': '修改', 'edit': '编辑',
    'save': '保存', 'put': '更新', 'delete': '删除', 'remove': '移除',
    'drop': '删除', 'cancel': '取消', 'list': '列出', 'send': '发送',
    'notify': '通知', 'push': '推送', 'post': '提交', 'check': '校验',
    'validate': '校验', 'verify': '验证', 'handle': '处理', 'process': '处理',
    'do': '执行', 'run': '运行', 'exec': '执行', 'compute': '计算',
    'calculate': '计算', 'calc': '计算', 'build': '构建', 'generate': '生成',
    'search': '搜索', 'find': '查找', 'login': '登录', 'logout': '登出',
    'auth': '认证', 'authenticate': '认证', 'export': '导出', 'import': '导入',
    'sync': '同步', 'parse': '解析', 'render': '渲染', 'start': '启动',
    'stop': '停止', 'open': '打开', 'close': '关闭', 'init': '初始化',
}

def desc_for(name):
    words = name.split('_')
    verb = VERB_MAP.get(words[0])
    if verb:
        return f"{verb}（{name}）：处理相关业务逻辑并返回结果。"
    return f"处理 {name} 相关业务逻辑。"

def find_header_colon(line):
    depth = 0
    for i, ch in enumerate(line):
        if ch in '([{':
            depth += 1
        elif ch in ')]}':
            depth -= 1
        elif ch == ':' and depth == 0:
            return i
    return -1

def collect_raises(node):
    names = []
    for n in ast.walk(node):
        if isinstance(n, ast.Raise):
            exc = n.exc
            if exc is None:
                continue
            if isinstance(exc, ast.Call):
                fn = exc.func
            else:
                fn = exc
            if isinstance(fn, ast.Name):
                names.append(fn.id)
            elif isinstance(fn, ast.Attribute):
                names.append(fn.attr)
    # 去重保序
    seen = set(); out = []
    for x in names:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

def build_docstring(node):
    name = node.name
    desc = desc_for(name)
    params = []
    for a in node.args.args:
        if a.arg in ('self', 'cls'):
            continue
        ann = ''
        if a.annotation is not None:
            try:
                ann = ' (' + ast.unparse(a.annotation) + ')'
            except Exception:
                ann = ''
        params.append(f":param {a.arg}: 入参{ann}。")
    for a in node.args.kwonlyargs:
        ann = ''
        if a.annotation is not None:
            try:
                ann = ' (' + ast.unparse(a.annotation) + ')'
            except Exception:
                ann = ''
        params.append(f":param {a.arg}: 入参{ann}。")
    # vararg / kwarg
    if node.args.vararg:
        params.append(f":param *{node.args.vararg.arg}: 可变位置参数。")
    if node.args.kwarg:
        params.append(f":param **{node.args.kwarg.arg}: 可变关键字参数。")
    ret = ''
    if node.returns is not None:
        try:
            rt = ast.unparse(node.returns)
            ret = f":return: 返回 {rt} 类型的结果。"
        except Exception:
            ret = ":return: 返回处理结果。"
    else:
        ret = ":return: 返回处理结果（或 None）。"
    raises = [f":raises {x}: 当相应错误条件触发时抛出。" for x in collect_raises(node)]

    body = [desc, '']
    if params:
        body.extend(params)
        body.append('')
    body.append(ret)
    if raises:
        body.append('')
        body.extend(raises)
    text = '"""\n' + '\n'.join(body) + '\n"""'
    return text

def process_file(path):
    src = open(path, encoding='utf-8').read()
    try:
        tree = ast.parse(src)
    except Exception as e:
        print("PARSE ERROR", path, e)
        return 0, 0
    lines = src.split('\n')
    edits = []  # (index, kind, data) kind: 'insert' data=list ; 'replace' data=list
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if ast.get_docstring(node) is not None:
            continue
        # 空函数（仅 pass / ... / docstring? 已知无docstring）
        body_stmts = node.body
        if not body_stmts:
            continue
        first = body_stmts[0]
        doc = build_docstring(node)
        indent = ' ' * (node.col_offset + 4)
        doc_lines = [indent + l if l else '' for l in doc.split('\n')]
        def_idx = node.lineno - 1
        if first.lineno == node.lineno:
            # 单行 def: def f(...): stmt
            def_line = lines[def_idx]
            ci = find_header_colon(def_line)
            if ci == -1:
                continue
            header = def_line[:ci+1]
            rest = def_line[ci+1:].lstrip()
            new_block = [header] + doc_lines + [(indent + rest) if rest else '']
            edits.append((def_idx, 'replace', new_block))
        else:
            # 多行：在首条语句之前插入
            insert_idx = first.lineno - 1
            edits.append((insert_idx, 'insert', doc_lines))
        count += 1
    if not edits:
        return 0, 0
    # 应用：按 index 降序
    edits.sort(key=lambda e: e[0], reverse=True)
    for idx, kind, data in edits:
        if kind == 'insert':
            for d in reversed(data):
                lines.insert(idx, d)
        else:  # replace
            lines[idx:idx+1] = data
    new_src = '\n'.join(lines)
    open(path, 'w', encoding='utf-8').write(new_src)
    return count, len(edits)

total_added = 0
files_changed = 0
for f in targets:
    added, _ = process_file(f)
    if added:
        files_changed += 1
        total_added += added
        print(f"ADDED {added:3d}  {f}")
print("====")
print("FILES CHANGED:", files_changed)
print("TOTAL DOCSTRINGS ADDED:", total_added)
