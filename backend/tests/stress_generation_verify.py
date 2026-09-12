"""压测脚本：租户文章生成 + 视频生成 + 智能体编排（真实 LLM 网关）。

用法：python tests/stress_generation_verify.py [BASE_URL] [CONCURRENCY] [ROUNDS]
默认 BASE_URL=http://127.0.0.1:18000，CONCURRENCY=3，ROUNDS=2。

前置：backend/scripts/seed_stress_tenant.py 已执行（tenant_demo/租户绑定存在）。
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:18000"
CONCURRENCY = int(sys.argv[2]) if len(sys.argv) > 2 else 3
ROUNDS = int(sys.argv[3]) if len(sys.argv) > 3 else 2
UA = "YouDingSaaS-Internal/1.0"

PASS = 0
FAIL = 0
RESULTS: list[dict] = []


def http(method: str, path: str, body: dict | None = None, token: str | None = None,
         csrf: str | None = None, cookie: str | None = None, timeout: int = 180):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("User-Agent", UA)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if csrf:
        req.add_header("X-CSRF-Token", csrf)
    if cookie:
        req.add_header("Cookie", cookie)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8", "replace"))
        except Exception:
            return e.code, {}
    except Exception as e:  # noqa: BLE001
        return 0, {"error": str(e)}


def get_csrf() -> str:
    # 任意 GET 会 Set-Cookie csrf_token
    req = urllib.request.Request(BASE + "/api/v1/health")
    req.add_header("User-Agent", UA)
    with urllib.request.urlopen(req, timeout=20) as resp:
        setc = resp.headers.get("Set-Cookie", "")
    for part in setc.split(";"):
        part = part.strip()
        if part.startswith("csrf_token="):
            return part.split("=", 1)[1]
    return ""


def login(username: str, password: str) -> str | None:
    csrf = get_csrf()
    st, body = http("POST", "/api/v1/system/login",
                    {"username": username, "password": password},
                    csrf=csrf, cookie=f"csrf_token={csrf}")
    tok = ((body.get("data") or {}).get("access_token")) if isinstance(body, dict) else None
    print(f"login {username}: HTTP {st} {'OK' if tok else json.dumps(body, ensure_ascii=False)[:120]}")
    return tok


def timed_call(name: str, fn) -> dict:
    t0 = time.perf_counter()
    ok, detail = False, ""
    try:
        st, body = fn()
        code = (body or {}).get("code")
        ok = st == 200 and (code in (0, None, 200))
        detail = json.dumps(body, ensure_ascii=False)[:180] if not ok else \
            json.dumps(body, ensure_ascii=False)[:120]
    except Exception as exc:  # noqa: BLE001
        st, detail = 0, f"EXC {exc}"
    dt = time.perf_counter() - t0
    rec = {"name": name, "ok": ok, "status": st, "sec": round(dt, 2)}
    RESULTS.append(rec)
    print(f"[{'PASS' if ok else 'FAIL'}] {name} HTTP={st} {dt:.1f}s {'' if ok else detail}")
    return rec


def article_job(token: str, i: int):
    def fn():
        return http("POST", "/api/v1/media-factory/ai-write", {
            "prompt": f"面向海外B2B买家的工业级便携式激光清洗机，第{i}篇：写一段150字以内的英文营销文案，突出安全和效率",
            "contentType": "article",
            "scenario": "article",
        }, token=token, timeout=240)
    return fn


def video_job(token: str, i: int):
    def fn():
        return http("POST", "/api/v1/media-factory/article-to-video", {
            "article": f"LaserClean Pro 3000: portable 300W pulsed laser cleaner for rust removal. "
                       f"Test {i}: safe, chemical-free, low operating cost for shipyards and mold shops.",
            "auto_render": False,
        }, token=token, timeout=240)
    return fn


def orchestrate_job(token: str, i: int):
    def fn():
        return http("POST", "/api/v1/public/tenants/stress-a.local/wangcai/ask", {
            "message": f"export feasibility of rock wool insulation board to Germany (stress {i})",
            "product_hint": "rock wool insulation board",
            "language": "en",
        }, token=token, timeout=240)
    return fn


def main() -> int:
    global PASS, FAIL
    print(f"BASE={BASE} CONCURRENCY={CONCURRENCY} ROUNDS={ROUNDS}")
    token = login("tenant_demo", "TenantDemo@2026!")
    if not token:
        print("FATAL: login failed")
        return 1

    jobs = []
    for r in range(ROUNDS):
        for i in range(CONCURRENCY):
            n = r * CONCURRENCY + i + 1
            jobs.append(article_job(token, n))
            jobs.append(video_job(token, n))
            jobs.append(orchestrate_job(token, n))

    print(f"\n--- submitting {len(jobs)} jobs with {CONCURRENCY} workers ---")
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        list(ex.map(timed_call, [f"job{j+1}" for j in range(len(jobs))], jobs))

    PASS = sum(1 for r in RESULTS if r["ok"])
    FAIL = len(RESULTS) - PASS
    secs = sorted(r["sec"] for r in RESULTS)
    p50 = secs[len(secs)//2] if secs else 0
    p95 = secs[int(len(secs)*0.95)] if secs else 0
    print(f"\n===== SUMMARY: {PASS} PASS / {FAIL} FAIL | p50={p50}s p95={p95}s max={secs[-1] if secs else 0}s =====")
    for r in RESULTS:
        if not r["ok"]:
            print(f"  FAIL: {r['name']} HTTP={r['status']} {r['sec']}s")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
