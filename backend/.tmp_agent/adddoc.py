import ast, os

BASE = "app/services"
EXCLUDE_DIRS = {"hermes","ubrain","__pycache__"}

# ---- name -> Chinese description ----
VERB = {
    "get":"获取","retrieve":"获取","fetch":"获取","load":"加载","create":"创建","make":"创建",
    "build":"构建","gen":"生成","generate":"生成","new":"新建","update":"更新","set":"设置",
    "modify":"修改","edit":"编辑","delete":"删除","remove":"移除","clear":"清空","process":"处理",
    "handle":"处理","run":"执行","execute":"执行","exec":"执行","do":"执行","sync":"同步",
    "publish":"发布","check":"检查","validate":"校验","verify":"校验","compute":"计算",
    "calculate":"计算","calc":"计算","parse":"解析","send":"发送","save":"保存","store":"存储",
    "query":"查询","search":"搜索","find":"查找","lookup":"查找","list":"列出","render":"渲染",
    "convert":"转换","transform":"转换","notify":"通知","register":"注册","start":"启动",
    "launch":"启动","stop":"停止","terminate":"终止","init":"初始化","initialize":"初始化",
    "config":"配置","configure":"配置","status":"状态","report":"报告","refresh":"刷新",
    "reload":"重新加载","reset":"重置","apply":"应用","enable":"启用","disable":"禁用",
    "add":"添加","append":"追加","import":"导入","export":"导出","upload":"上传","download":"下载",
    "open":"打开","close":"关闭","send":"发送","receive":"接收","dispatch":"调度","schedule":"调度",
    "scan":"扫描","collect":"收集","merge":"合并","split":"拆分","extract":"提取","format":"格式化",
    "encode":"编码","decode":"解码","compress":"压缩","expand":"展开","ensure":"确保","resolve":"解析",
    "prepare":"准备","clean":"清理","cleanup":"清理","setup":"设置","teardown":"拆除","track":"追踪",
    "monitor":"监控","watch":"监视","probe":"探测","inspect":"检查","analyze":"分析","analysis":"分析",
    "estimate":"估算","predict":"预测","recommend":"推荐","suggest":"建议","match":"匹配",
}
NOUN = {
    "user":"用户","users":"用户","data":"数据","info":"信息","information":"信息","order":"订单",
    "orders":"订单","task":"任务","tasks":"任务","job":"任务","item":"条目","items":"条目",
    "result":"结果","results":"结果","error":"错误","errors":"错误","request":"请求","requests":"请求",
    "response":"响应","token":"令牌","tokens":"令牌","cache":"缓存","file":"文件","files":"文件",
    "image":"图片","images":"图片","video":"视频","videos":"视频","audio":"音频","text":"文本",
    "message":"消息","messages":"消息","event":"事件","events":"事件","config":"配置","service":"服务",
    "services":"服务","account":"账户","accounts":"账户","tenant":"租户","site":"站点","sites":"站点",
    "content":"内容","customer":"客户","customers":"客户","product":"产品","products":"产品",
    "payment":"支付","invoice":"发票","invoices":"发票","report":"报告","status":"状态","state":"状态",
    "profile":"档案","session":"会话","notification":"通知","url":"URL","urls":"URL","email":"邮件",
    "phone":"电话","address":"地址","price":"价格","prices":"价格","score":"评分","rank":"排名",
    "keyword":"关键词","keywords":"关键词","category":"分类","tag":"标签","log":"日志","logs":"日志",
    "metric":"指标","metrics":"指标","node":"节点","graph":"图","tree":"树","list":"列表","map":"映射",
    "dict":"字典","queue":"队列","stack":"栈","pool":"池","client":"客户端","server":"服务端",
    "api":"API","db":"数据库","database":"数据库","sql":"SQL","http":"HTTP","json":"JSON","xml":"XML",
    "html":"HTML","csv":"CSV","pdf":"PDF","id":"ID","ids":"ID","name":"名称","title":"标题",
    "desc":"描述","description":"描述","type":"类型","kind":"种类","mode":"模式","level":"级别",
    "time":"时间","date":"日期","day":"天","month":"月","year":"年","week":"周","count":"数量",
    "total":"总计","sum":"总和","avg":"平均值","max":"最大值","min":"最小值","rate":"比率",
    "ratio":"比率","percent":"百分比","number":"数量","num":"数量","value":"值","values":"值",
    "param":"参数","params":"参数","argument":"参数","arg":"参数","field":"字段","fields":"字段",
    "key":"键","keys":"键","secret":"密钥","password":"密码","passwd":"密码","credential":"凭证",
    "auth":"认证","permission":"权限","role":"角色","group":"组","member":"成员","members":"成员",
    "team":"团队","org":"组织","organization":"组织","company":"公司","agent":"代理","agentic":"代理",
    "model":"模型","models":"模型","provider":"提供商","platform":"平台","platforms":"平台",
    "channel":"渠道","source":"来源","target":"目标","destination":"目标","output":"输出","input":"输入",
    "template":"模板","templates":"模板","config":"配置","setting":"设置","settings":"设置",
    "option":"选项","options":"选项","flag":"标志","flags":"标志","feature":"特性","features":"特性",
    "version":"版本","lang":"语言","language":"语言","locale":"区域","region":"区域","country":"国家",
    "city":"城市","province":"省份","area":"区域","zone":"区域","currency":"货币","money":"金额",
    "amount":"金额","balance":"余额","quota":"配额","limit":"限制","usage":"用量","cost":"成本",
    "price":"价格","fee":"费用","tax":"税","discount":"折扣","coupon":"优惠券","refund":"退款",
    "reward":"奖励","point":"积分","points":"积分","credit":"积分","wallet":"钱包","balance":"余额",
}
def translate_name(name):
    name = name.strip("_")
    if name.startswith("__"):
        name = name.strip("_")
    parts = [p for p in name.split("_") if p]
    out = []
    for p in parts:
        pl = p.lower()
        if pl in VERB:
            out.append(VERB[pl])
        elif pl in NOUN:
            out.append(NOUN[pl])
        else:
            out.append(p)
    # dedupe adjacent duplicates
    res = []
    for w in out:
        if not res or res[-1] != w:
            res.append(w)
    s = "".join(res)
    if not s:
        s = name
    return s

def get_raises(func):
    raises = []
    seen = set()
    for node in ast.walk(func):
        if isinstance(node, ast.Raise):
            exc = node.exc
            nm = None
            if isinstance(exc, ast.Name):
                nm = exc.id
            elif isinstance(exc, ast.Attribute):
                nm = exc.attr
            elif isinstance(exc, ast.Call):
                f = exc.func
                if isinstance(f, ast.Name):
                    nm = f.id
                elif isinstance(f, ast.Attribute):
                    nm = f.attr
            if nm and nm not in seen:
                seen.add(nm)
                raises.append(nm)
    return raises

def args_list(func):
    a = func.args
    res = []
    for arg in getattr(a, "posonlyargs", []) + a.args:
        res.append((arg.arg, arg.annotation))
    if a.vararg:
        res.append((a.vararg.arg, a.vararg.annotation))
    for arg in a.kwonlyargs:
        res.append((arg.arg, arg.annotation))
    if a.kwarg:
        res.append((a.kwarg.arg, a.kwarg.annotation))
    return res

def make_docstring(func):
    desc = translate_name(func.name)
    desc = f"实现 {desc} 的功能。"
    params = args_list(func)
    ret = func.returns
    raises = get_raises(func)
    lines = ['"""' + desc, ""]
    for pname, ann in params:
        if ann is not None:
            try:
                ann_s = ast.unparse(ann)
            except Exception:
                ann_s = "object"
            lines.append(f":param {pname}: 参数 {pname}（类型: {ann_s}）")
        else:
            lines.append(f":param {pname}: 参数 {pname} 的说明")
    if ret is not None:
        try:
            ret_s = ast.unparse(ret)
        except Exception:
            ret_s = "object"
        lines.append(f":return: 返回 {ret_s} 结果")
    else:
        lines.append(":return: 返回处理结果")
    for r in raises:
        lines.append(f":raises {r}: 当操作失败时抛出 {r} 异常")
    lines.append('"""')
    return lines

def process_file(fp):
    src = open(fp, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except Exception as e:
        print("PARSE ERROR", fp, e)
        return 0
    lines = src.splitlines()
    # gather functions needing docstring with insertion info
    todo = []  # (insert_index_0based, block_lines)
    def visit(node):
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if ast.get_docstring(child) is None:
                    doclines = make_docstring(child)
                    if child.body and child.body[0].lineno == child.lineno:
                        # inline body
                        defline = lines[child.lineno-1]
                        # find def terminator ':' at paren depth 0
                        depth = 0
                        idx = None
                        for i,ch in enumerate(defline):
                            if ch in "([{":
                                depth += 1
                            elif ch in ")]}":
                                depth -= 1
                            elif ch == ":" and depth == 0:
                                idx = i
                                break
                        if idx is None:
                            # fallback skip
                            todo.append((None, None))
                            visit(child)
                            continue
                        indent = defline[:len(defline)-len(defline.lstrip())]
                        bodytext = defline[idx+1:].strip()
                        docindent = indent + "    "
                        block = [defline[:idx+1]]
                        block.append(docindent + doclines[0])
                        for dl in doclines[1:]:
                            block.append(docindent + dl)
                        block.append(indent + bodytext)
                        todo.append(("INLINE", child.lineno-1, block))
                    else:
                        insert_idx = child.body[0].lineno - 1
                        indent = lines[insert_idx][:len(lines[insert_idx])-len(lines[insert_idx].lstrip())]
                        block = [indent + dl if dl.startswith('"""') or dl=='' or dl.startswith(':') else indent+dl for dl in doclines]
                        # ensure each line prefixed with indent
                        block = [indent + dl for dl in doclines]
                        todo.append(("NORMAL", insert_idx, block))
                visit(child)
    visit(tree)
    if not todo:
        return 0
    # apply, handle INLINE and NORMAL
    # For INLINE we replace the def line; for NORMAL we insert before index
    # Process in order of descending line to avoid index shifts.
    # Separate inline (replace) vs normal (insert). Do normal first (insert at higher idx),
    # then inline (replace) — but replacement changes one line only, no index shift beyond it.
    normal_ops = [(idx, block) for typ, idx, block in todo if typ == "NORMAL"]
    inline_ops = [(idx, block) for typ, idx, block in todo if typ == "INLINE"]
    # normal: sort descending by index
    normal_ops.sort(key=lambda x: x[0], reverse=True)
    new_lines = lines
    for idx, block in normal_ops:
        new_lines = new_lines[:idx] + block + new_lines[idx:]
    # inline: replace line at idx (1-based stored as child.lineno-1 = idx of def line)
    for idx, block in inline_ops:
        # block[0] is the modified def line (with ':'), then docstring lines, then body
        new_lines = new_lines[:idx] + block + new_lines[idx+1:]
    out = "\n".join(new_lines)
    if src.endswith("\n"):
        out += "\n"
    open(fp, "w", encoding="utf-8").write(out)
    return len(todo)

# gather files
FILES = []
for root, dirs, fnames in os.walk(BASE):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for fn in fnames:
        if fn.endswith(".py"):
            full = os.path.join(root, fn)
            # only subdirectory files
            if os.path.dirname(full) != BASE:
                FILES.append(full)

total = 0
changed = 0
for fp in FILES:
    n = process_file(fp)
    if n:
        changed += 1
        total += n
print(f"FILES PROCESSED: {len(FILES)}")
print(f"FILES CHANGED: {changed}")
print(f"DOCSTRINGS ADDED: {total}")
