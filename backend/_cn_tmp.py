import ast, os, glob, re

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

def collect_raises(node):
    names = []
    for n in ast.walk(node):
        if isinstance(n, ast.Raise):
            exc = n.exc
            if exc is None:
                continue
            fn = exc.func if isinstance(exc, ast.Call) else exc
            if isinstance(fn, ast.Name):
                names.append(fn.id)
            elif isinstance(fn, ast.Attribute):
                names.append(fn.attr)
    seen=set(); out=[]
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
            try: ann = ' (' + ast.unparse(a.annotation) + ')'
            except Exception: ann = ''
        params.append(f":param {a.arg}: 入参{ann}。")
    for a in node.args.kwonlyargs:
        ann = ''
        if a.annotation is not None:
            try: ann = ' (' + ast.unparse(a.annotation) + ')'
            except Exception: ann = ''
        params.append(f":param {a.arg}: 入参{ann}。")
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
        body.extend(params); body.append('')
    body.append(ret)
    if raises:
        body.append(''); body.extend(raises)
    return '"""\n' + '\n'.join(body) + '\n"""'

targets = [
    ('app/api/v1/routes/attribution.py', 'get_attribution_report'),
    ('app/api/v1/routes/attribution.py', 'handle_email_reply'),
    ('app/api/v1/routes/auth.py', '_check_email_code_rate'),
    ('app/api/v1/routes/auth.py', '_token_json_response'),
    ('app/api/v1/routes/case_studies.py', '_safe_case_image_dict'),
    ('app/api/v1/routes/case_studies.py', '_safe_case_study_dict'),
]

def find_func(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None

for f, name in targets:
    src = open(f, encoding='utf-8').read()
    tree = ast.parse(src)
    node = find_func(tree, name)
    if node is None:
        print("NOT FOUND", f, name); continue
    # locate docstring expr
    if not (node.body and isinstance(node.body[0], ast.Expr)
            and isinstance(getattr(node.body[0], 'value', None), ast.Constant)
            and isinstance(node.body[0].value.value, str)):
        print("NO DOC NODE", f, name); continue
    doc_node = node.body[0]
    indent = ' ' * doc_node.col_offset
    raw = build_docstring(node)
    indented = '\n'.join((indent + l) if l else l for l in raw.split('\n'))
    lines = src.split('\n')
    a = doc_node.lineno - 1
    b = doc_node.end_lineno - 1
    new_lines = lines[:a] + indented.split('\n') + lines[b+1:]
    open(f, 'w', encoding='utf-8').write('\n'.join(new_lines))
    print("CONVERTED", f, name)
