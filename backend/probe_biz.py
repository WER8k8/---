import urllib.request
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
def get(path):
    req = urllib.request.Request("http://127.0.0.1:8000"+path, headers={"User-Agent":UA})
    try:
        r = urllib.request.urlopen(req, timeout=8)
        return r.status, r.read()[:400].decode("utf-8","ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:400].decode("utf-8","ignore")
    except Exception as e:
        return "ERR", str(e)[:200]

# 业务端点探针（不依赖登录：看是否 404 vs 401/200/422）
for p in ["/api/v1/products", "/api/v1/auth/login", "/api/v1/tenants", "/api/v1/health", "/api/v1/orders", "/api/v1/leads/summary", "/api/v1/seo", "/docs"]:
    s,b = get(p)
    print(f"{s}  {p}")
    if s not in (200,403):
        print("     ", b[:200].replace("\n"," "))
