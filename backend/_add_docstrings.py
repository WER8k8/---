import ast, os, glob

root = "app/api/v1/routes"
files = sorted(glob.glob(os.path.join(root, "[m-z]*.py")))

# 参数名 -> 中文说明
PARAM_CN = {
    "db": "数据库会话",
    "conn": "数据库连接",
    "current_user": "当前登录用户",
    "user": "用户对象",
    "current_tenant": "当前租户",
    "tenant": "租户对象",
    "tenant_id": "租户ID",
    "user_id": "用户ID",
    "request": "HTTP 请求对象",
    "response": "HTTP 响应对象",
    "payload": "请求体数据",
    "data": "请求数据",
    "body": "请求体",
    "id": "记录ID",
    "id_": "记录ID",
    "pk": "主键ID",
    "token": "令牌",
    "code": "验证码/编码",
    "limit": "返回条数上限",
    "offset": "偏移量",
    "page": "页码",
    "page_size": "每页条数",
    "q": "搜索关键字",
    "query": "查询条件",
    "search": "搜索关键字",
    "filters": "过滤条件",
    "lang": "语言代码",
    "locale": "区域设置",
    "background_tasks": "后台任务",
    "file": "上传文件",
    "files": "上传文件列表",
    "form": "表单数据",
    "kwargs": "附加关键字参数",
    "args": "附加位置参数",
    "settings": "配置对象",
    "config": "配置对象",
    "ctx": "上下文对象",
    "req": "请求对象",
    "res": "响应对象",
    "params": "查询参数",
    "headers": "请求头",
    "name": "名称",
    "email": "邮箱",
    "phone": "电话",
    "status": "状态",
    "enabled": "是否启用",
    "force": "是否强制",
    "dry_run": "是否试运行",
    "scope": "作用域",
    "role": "角色",
    "path": "路径",
    "url": "链接地址",
    "text": "文本内容",
    "content": "内容",
    "title": "标题",
    "description": "描述",
    "category": "分类",
    "tag": "标签",
    "start": "起始时间",
    "end": "结束时间",
    "date": "日期",
    "begin": "开始",
    "size": "大小",
    "type": "类型",
    "kind": "类别",
    "key": "键",
    "value": "值",
    "result": "结果",
    "task_id": "任务ID",
    "job_id": "任务ID",
    "project_id": "项目ID",
    "opportunity_id": "商机ID",
    "lead_id": "线索ID",
    "candidate_id": "候选ID",
    "prospect_id": "潜在客户ID",
    "account_id": "账户ID",
    "customer_id": "客户ID",
    "order_id": "订单ID",
    "invoice_id": "发票ID",
    "payment_id": "支付ID",
    "tenant_domain": "租户域名",
    "domain": "域名",
    "subdomain": "子域名",
    "host": "主机名",
    "ip": "IP地址",
    "worker": "工作进程",
    "redis": "Redis 客户端",
    "cache": "缓存客户端",
    "session": "会话",
}

METHOD_CN = {
    "get": "GET", "post": "POST", "put": "PUT",
    "delete": "DELETE", "patch": "PATCH", "head": "HEAD", "options": "OPTIONS",
}

VERB_CN = {
    "get": "获取", "list": "列出", "create": "创建", "update": "更新",
    "delete": "删除", "remove": "移除", "add": "添加", "set": "设置",
    "save": "保存", "load": "加载", "run": "运行", "start": "启动",
    "stop": "停止", "send": "发送", "fetch": "拉取", "build": "构建",
    "check": "校验", "verify": "验证", "auth": "鉴权", "login": "登录",
    "logout": "登出", "register": "注册", "sync": "同步", "export": "导出",
    "import": "导入", "search": "搜索", "count": "统计", "stats": "统计",
    "approve": "审批", "reject": "拒绝", "mark": "标记", "refresh": "刷新",
    "parse": "解析", "render": "渲染", "inject": "注入", "serialize": "序列化",
    "resolve": "解析", "guard": "校验", "allow": "放行",
}

def cn_param(name):
    if name in PARAM_CN:
        return PARAM_CN[name]
    base = name.rstrip("_")
    return f"参数 {base}"

def summarize(name, method, path):
    base = name.rstrip("_").lstrip("_")
    parts = base.split("_")
    # 取前两个有意义的动词/名词
    if method and path:
        action = VERB_CN.get(parts[0], parts[0]) if parts else name
        return f"处理 {method} {path} 请求，{action}相关资源。"
    # 非路由函数，按名称生成
    words = [VERB_CN.get(p, p) for p in parts[:2]]
    tail = "数据" if any(w in ("获取","列出","创建","更新","删除","搜索","统计","导出") for w in words) else "逻辑"
    return f"执行 {base} 相关{tail}处理。"

def collect_raises(node):
    names = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Raise):
            exc = n.exc
            if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name):
                names.add(exc.func.id)
            elif isinstance(exc, ast.Name):
                names.add(exc.id)
            elif isinstance(exc, ast.Call) and isinstance(exc.func, ast.Attribute):
                names.add(exc.func.attr)
    return sorted(names)

def get_route_info(node):
    for dec in node.decorator_list:
        # 形如 router.get("/path") 或 router.post(...)
        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
            meth = dec.func.attr.lower()
            if meth in METHOD_CN:
                path = ""
                if dec.args and isinstance(dec.args[0], ast.Constant):
                    path = dec.args[0].value
                return METHOD_CN[meth], path
    return None, None

def build_docstring(node):
    method, path = get_route_info(node)
    summary = summarize(node.name, method, path)
    # 参数
    args = []
    a = node.args
    for arg in a.posonlyargs + a.args + a.kwonlyargs:
        args.append(arg.arg)
    if a.vararg:
        args.append(a.vararg.arg)
    if a.kwarg:
        args.append(a.kwarg.arg)
    raises = collect_raises(node)

    indent = " " * (node.col_offset + 4)
    lines = [indent + '"""' + summary]
    if args:
        lines.append(indent)
        for p in args:
            lines.append(f"{indent}:param {p}: {cn_param(p)}")
    lines.append(f"{indent}:return: 返回处理结果。")
    if raises:
        lines.append(f"{indent}:raises: " + ", ".join(raises) + " 等异常在错误时抛出。")
    lines.append(indent + '"""')
    return "\n".join(lines) + "\n"

changed_files = []
total_added = 0
for f in files:
    src = open(f, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except Exception as e:
        print("PARSE ERR", f, e); continue
    funcs = [n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and ast.get_docstring(n) is None]
    if not funcs:
        continue
    # 从后往前插入，避免行偏移
    funcs.sort(key=lambda n: n.lineno, reverse=True)
    lines = src.splitlines(keepends=True)
    offsets = []
    pos = 0
    for ln in lines:
        offsets.append(pos)
        pos += len(ln)
    added = 0
    for n in funcs:
        idx = n.lineno - 1
        # 仅当函数体首语句在 def 之后（多行定义）才插入
        if n.body and getattr(n.body[0], "lineno", n.lineno) <= n.lineno:
            # 单行函数（def 与 body 同行），跳过
            continue
        insert_pos = offsets[idx] + len(lines[idx])
        doc = build_docstring(n)
        src = src[:insert_pos] + doc + src[insert_pos:]
        added += 1
    if added:
        open(f, "w", encoding="utf-8").write(src)
        changed_files.append((f, added))
        total_added += added

print("CHANGED FILES:", len(changed_files))
print("TOTAL ADDED:", total_added)
for f, a in changed_files:
    print(f"  {f}: +{a}")
