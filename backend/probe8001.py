import urllib.request, urllib.error, json
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
BASE = "http://127.0.0.1:8001"

def get(path, method="GET"):
    req = urllib.request.Request(BASE+path, headers={"User-Agent":UA}, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=15)
        return r.status, r.read()[:300].decode("utf-8","ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300].decode("utf-8","ignore")
    except Exception as e:
        return "ERR", str(e)[:150]

# 拓扑 §7 标记的 17 个未挂载(404)模块 + 核心链路
targets = [
    "/api/v1/health",
    "/api/v1/products",       # 旧实例 500
    "/api/v1/orders",         # 拓扑:404
    "/api/v1/seo",            # 拓扑:404
    "/api/v1/leads/summary",  # 拓扑:404
    "/api/v1/n8n",
    "/api/v1/deerflow",
    "/api/v1/sitemap",
    "/api/v1/site_builder",
    "/api/v1/tenants",
    "/api/v1/inquiries",
    "/api/v1/content",
]
print(f"{'状态':>6}  路径")
for p in targets:
    s,b = get(p)
    st = str(s)
    flag = "OK " if s in (200,401,403,422) else ("404未挂载" if s==404 else ("500崩溃" if s==500 else ""))
    print(f"{st:>6}  {p}   {flag}")
    if s not in (200,401,403,404):
        print("        ", b[:180].replace("\n"," "))
