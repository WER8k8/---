# -*- coding: utf-8 -*-
"""端到端闭环验证 v2：用真实挂载路径验证 鉴权 -> RBAC -> 业务数据 -> 写入回读"""
import warnings, json
warnings.filterwarnings("ignore")
import urllib.request, urllib.error

BASE = "http://127.0.0.1:8899"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"
# 本机直连：绕过环境里的 HTTP 代理（否则 127.0.0.1 会被代理拦成 502）
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))

from app.core.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
row = db.execute(text("SELECT id, username, role FROM users WHERE username='admin'")).fetchone()
db.close()
uid, uname, role = str(row[0]), row[1], row[2]

from app.core.security import create_access_token
token = create_access_token({"sub": uid, "username": uname, "role": role})
print("[AUTH] token 铸造 OK (user=%s role=%s)" % (uname, role))

def call(path, method="GET", body=None):
    hdr = {"User-Agent": UA, "Content-Type": "application/json",
           "Authorization": f"Bearer {token}"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=hdr, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=30)
        return r.status, r.read()[:180].decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:180].decode("utf-8", "ignore")
    except Exception as e:
        return "ERR", str(e)[:150]

print("\n=== 未鉴权对照（应 401/403）===")
req = urllib.request.Request(BASE + "/api/v1/products", headers={"User-Agent": UA})
try:
    urllib.request.urlopen(req, timeout=20)
    print("  /api/v1/products -> 200（未鉴权放行，鉴权缺失）")
except urllib.error.HTTPError as e:
    print(f"  /api/v1/products -> {e.code}（鉴权拦截生效）")

print("\n=== 带 token 的真实业务端点 ===")
targets = [
    "/api/v1/health",
    "/api/v1/products",
    "/api/v1/tenants",
    "/api/v1/permissions",
    "/api/v1/lead-generation/capabilities",
    "/api/v1/lead-enrichment/status",
    "/api/v1/ops/deerflow-schedule/status",
    "/api/v1/hub/sitemap.xml",
    "/api/v1/cross-border/export-quote",
]
for p in targets:
    s, b = call(p)
    flag = "OK " if s == 200 else ("404未挂载" if s == 404 else "异常")
    print(f"  [{flag}] {p} -> {s} :: {b[:90]}")

print("\n=== 写入回读（数据流转闭环）===")
s, b = call("/api/v1/products", "POST", {
    "name": "闭环验证产品", "slug": "closed-loop-check",
    "description": "端到端闭环写入测试", "status": "draft",
})
print(f"  POST /api/v1/products -> {s} :: {b[:150]}")
s, b = call("/api/v1/products?page=1&page_size=3")
print(f"  GET  /api/v1/products -> {s} :: {b[:120]}")
