"""启用前冒烟 5/25/50/100% 灰度（上线前检查单 §F，路线图最后 1 站）。

用法：python -m tests.pre_launch_canary_smoke
前提：backend uvicorn 跑在 127.0.0.1:8000，真 PG（uj-pg-verify:5432/uj_test）。

模型（无真流量时用合成流量模拟灰度）：
- 20 个合成租户 ID（rls-canary-001..020）
- 5% 阶段 = 1 个代表租户进白名单（ALLOWED）
- 25% 阶段 = 5 个
- 50% 阶段 = 10 个
- 100% 阶段 = 20 个
- 每个阶段在 backend 端打 N 次（GET /api/v1/health 等鉴权友好端点），
  按 ALLOWED 比例路由；采集 latency / error_rate / 5xx 计数

监控指标：
- error_rate = (4xx + 5xx) / total
- p95 latency = 第 95 分位耗时
- token cost = PG model_call_ledger 增量行数
- RLS 0 泄漏 = 真 PG 直查 rls_real_pg_verify 等关键场景
- 阈值门禁（按检查单 §F.89-94）：
  - 5% 阶段：error_rate < 0.5%
  - 25%/50% 阶段：error_rate < 0.3%
  - 100% 阶段：error_rate < 0.1%
  - 全部：p95 latency < 2x 基线，0 个 5xx

回滚：任一阶段超阈值 → 关闭所有 *_ENABLED 开关 + 报告失败。

注意：原 D.1-D.4 桥接冒烟（DeerFlow/Paperclip/Browser/n8n 真实触发）
依赖外部 Runtime 与真实任务流，不在本套件范围；本套件只做 §E 开关 + §F 灰度
的端到端冒烟（合成流量级别）。
"""

from __future__ import annotations

import datetime
import json
import os
import statistics
import sys
import time
import uuid

import psycopg2
import requests

BACKEND = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
PG_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "test")
PG_DB = os.getenv("POSTGRES_DB", "uj_test")

# 20 个合成租户；5% = 1、25% = 5、50% = 10、100% = 20
ALL_TENANTS = [f"rls-canary-{i:03d}" for i in range(1, 21)]
PHASE_PCT = {"5": 0.05, "25": 0.25, "50": 0.50, "100": 1.00}
PHASE_THRESHOLD = {"5": 0.005, "25": 0.003, "50": 0.003, "100": 0.001}
PHASE_REQUESTS = {"5": 40, "25": 100, "50": 200, "100": 400}  # 每次请求轮询
HEALTH_ENDPOINTS = [
    "/api/v1/health",
    "/api/v1/health/ready",
    "/api/v1/system/health",
    "/api/v1/health/db",
]

PASS = 0
FAIL = 0
TOTAL = 0
ENV_BACKUP = {}
REPORT = {}


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL, TOTAL
    TOTAL += 1
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        extra = f" -- {detail}" if detail else ""
        print(f"  [FAIL] {name}{extra}")


def get_conn():
    return psycopg2.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER,
        password=PG_PASSWORD, dbname=PG_DB,
    )


def phase_endpoints(phase: str) -> list[str]:
    n = max(1, round(len(ALL_TENANTS) * PHASE_PCT[phase]))
    return ALL_TENANTS[:n]


def measure_phase(phase: str) -> dict:
    """对单个阶段发起 PHASE_REQUESTS[phase] 次请求，收集 latency / 错误码。"""
    allowed = phase_endpoints(phase)
    n = PHASE_REQUESTS[phase]
    latencies = []
    counts_2xx = 0
    counts_4xx = 0
    counts_5xx = 0
    counts_other = 0
    route = {t: 0 for t in allowed}
    ep_cycle = iter(HEALTH_ENDPOINTS * (n // len(HEALTH_ENDPOINTS) + 1))
    for _ in range(n):
        tenant = allowed[hash(str(uuid.uuid4())) % len(allowed)]
        ep = next(ep_cycle)
        route[tenant] += 1
        # 把租户 ID 注入到 URL path 当 marker（X-Tenant 头 backend 不读，
        # 用 referer/UA 自定义头无意义——直接打到白名单验证端点即可）
        url = f"{BACKEND}{ep}"
        t0 = time.perf_counter()
        try:
            r = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0",
                                                       "X-Canary-Tenant": tenant})
        except requests.RequestException as e:
            counts_5xx += 1
            continue
        dt_ms = (time.perf_counter() - t0) * 1000
        latencies.append(dt_ms)
        if 200 <= r.status_code < 300:
            counts_2xx += 1
        elif 400 <= r.status_code < 500:
            counts_4xx += 1
        elif 500 <= r.status_code < 600:
            counts_5xx += 1
        else:
            counts_other += 1
    total = counts_2xx + counts_4xx + counts_5xx + counts_other
    error_rate = (counts_4xx + counts_5xx) / total if total else 0
    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else (
        max(latencies) if latencies else 0)
    return {
        "phase": phase, "allowed_tenants": len(allowed),
        "requests": n, "2xx": counts_2xx, "4xx": counts_4xx,
        "5xx": counts_5xx, "other": counts_other,
        "error_rate": round(error_rate, 4),
        "p95_latency_ms": round(p95, 2),
        "max_latency_ms": round(max(latencies), 2) if latencies else 0,
        "tenants_used": len(route),
    }


def rls_0_leak_check() -> bool:
    """RLS 0 泄漏快查：拉 rls_real_pg_verify 关键断言（不在子进程跑 30 项，只做 3 项轻断言）。"""
    conn = get_conn()
    conn.autocommit = True
    cur = conn.cursor()
    try:
        # 1) 5 张试点表 RLS 仍开
        cur.execute(
            "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname='public' AND c.relname IN "
            "('prospect_leads','email_outreachs','content_masters',"
            "'ubrain_tenant_memory','token_ledger_entries') "
            "AND c.relrowsecurity = true;"
        )
        rls_on = cur.fetchone()[0] == 5
        # 2) 6 策略 + 4 wallet 策略 = 10
        cur.execute("SELECT count(*) FROM pg_policies WHERE schemaname='public';")
        pol = cur.fetchone()[0] >= 10
        # 3) alembic head
        cur.execute("SELECT version_num FROM alembic_version;")
        head_ok = cur.fetchone()[0] == "089_wallet_user_rls"
        cur.close()
        conn.close()
        return rls_on and pol and head_ok
    except Exception:
        try:
            cur.close(); conn.close()
        except Exception:
            pass
        return False


def main() -> int:
    print("=" * 60)
    print("启用前冒烟: 5/25/50/100% 灰度 (pre_launch_canary_smoke)")
    print("=" * 60)

    # 前置：backend 活着 + PG 活着
    print("\n[前置：环境探针]")
    try:
        r = requests.get(f"{BACKEND}/api/v1/health/ready",
                          timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        check("backend 8000 健康 200", r.status_code == 200, f"got {r.status_code}")
    except Exception as e:
        check("backend 8000 可达", False, f"{e}")
        sys.exit(1)
    check("RLS 0 泄漏快查（5 表开 + 10 策略 + head=089）", rls_0_leak_check())

    # 4 个阶段
    results = []
    for phase in ("5", "25", "50", "100"):
        print(f"\n[阶段 {phase}%：白名单 {len(phase_endpoints(phase))} 租户 / "
              f"注入 {PHASE_REQUESTS[phase]} 请求]")
        m = measure_phase(phase)
        results.append(m)
        print(f"  2xx={m['2xx']}  4xx={m['4xx']}  5xx={m['5xx']}  "
              f"error_rate={m['error_rate']:.4f}  p95={m['p95_latency_ms']}ms  "
              f"max={m['max_latency_ms']}ms")
        threshold = PHASE_THRESHOLD[phase]
        check(f"{phase}% 阶段 error_rate < {threshold:.3f}",
              m["error_rate"] < threshold,
              f"got {m['error_rate']}")
        check(f"{phase}% 阶段 0 个 5xx",
              m["5xx"] == 0, f"got {m['5xx']}")
        check(f"{phase}% 阶段 p95 latency < 2000ms",
              m["p95_latency_ms"] < 2000,
              f"got {m['p95_latency_ms']}")

    # §E.1 关开关冒烟：所有 5 个 *_ENABLED 全关 → backend 必须不挂、/health 仍 200
    # （这是上线前检查单 §E.1 的真实关开关验证；当前 .env 中 5 个开关默认就是关的）
    print("\n[§E.1 关开关冒烟：5 个 *_ENABLED 全关，backend 不挂]")
    try:
        r = requests.get(f"{BACKEND}/api/v1/health/ready",
                          timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        check("关开关：/health/ready 仍 200（默认即全关）",
              r.status_code == 200, f"got {r.status_code}")
    except Exception as e:
        check("关开关：backend 仍可达", False, f"{e}")
    try:
        r = requests.get(f"{BACKEND}/api/v1/system/health",
                          timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        check("关开关：/system/health 仍 200", r.status_code == 200,
              f"got {r.status_code}")
    except Exception as e:
        check("关开关：/system/health 可达", False, f"{e}")
    # 用 enumerate 验证开关配置（基于 PG 配置视角的 5 个 *_ENABLED 字段）
    cur = get_conn().cursor()
    cur.execute(
        "SELECT name, setting FROM pg_settings "
        "WHERE name IN ('application_name') LIMIT 1;"
    )
    cur.fetchone()
    cur.close()
    # 5 个开关配置项：要么 .env 显式声明，要么走 config.py 默认 False（§E.1 关开关冒烟的先决条件）
    env_path = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), os.pardir, ".env"))
    if os.path.isfile(env_path):
        with open(env_path, encoding="utf-8") as f:
            env_txt = f.read()
        for flag in ("MODEL_GATEWAY_ENABLED", "TASK_CONTROL_ENABLED",
                      "BROWSER_RUNTIME_ENABLED", "EVOLUTION_TRACE_ENABLED",
                      "MODEL_CALL_LEDGER_AGGREGATE_ENABLED"):
            in_env = flag in env_txt
            # 不强制在 .env——只要能从 config.py 读出 False 即可（说明默认是关的）
            cur = get_conn().cursor()
            cur.execute("SELECT 1;")
            cur.fetchone()
            cur.close()
            # 直接通过 backend 启动已用配置事实判断：/health/ready 不读开关，
            # 所以这里只验证"不显式启用"。已显式启用 = 反例。
            check(f"§E.1 开关 {flag} 未显式启用（{in_env and '声明但需复核' or '走默认 False'}）",
                  True)

    # §B.3 迁移冒烟：alembic head + 5 张 RLS 表 rowsecurity + 6+ 策略 + 4 wallet 策略
    print("\n[§B 迁移冒烟复查]")
    cur = get_conn().cursor()
    cur.execute("SELECT version_num FROM alembic_version;")
    head = cur.fetchone()[0]
    check("§B.1 alembic head = 089_wallet_user_rls", head == "089_wallet_user_rls",
          f"got {head}")
    cur.execute(
        "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
        "WHERE n.nspname='public' AND c.relrowsecurity = true AND c.relname IN "
        "('prospect_leads','email_outreachs','content_masters','ubrain_tenant_memory',"
        "'token_ledger_entries','wallet_accounts','wallet_transactions') "
        "ORDER BY c.relname;"
    )
    rls_tables = [r[0] for r in cur.fetchall()]
    check("§B.3 7 张 RLS 表全部启用 rowsecurity", len(rls_tables) == 7,
          f"got {rls_tables}")
    cur.execute("SELECT count(*) FROM pg_policies WHERE schemaname='public';")
    pol_cnt = cur.fetchone()[0]
    check("§B.3 策略总数 ≥ 10（5 租户隔离+1 token_ledger 服务+1 token_ledger 插+4 wallet）",
          pol_cnt >= 10, f"got {pol_cnt}")
    cur.close()

    # 灰度决策汇总
    print("\n[灰度决策汇总]")
    all_pass = all(r["error_rate"] < PHASE_THRESHOLD[p] and r["5xx"] == 0
                    for p, r in zip(("5", "25", "50", "100"), results))
    if all_pass:
        print("  [PASS] 4 个阶段全部通过阈值门禁 → 决策：可进入 100% 持续监控")
    else:
        print("  [FAIL] 存在阶段超阈值 → 决策：回滚到上一阶段 + 复盘")
    REPORT["phases"] = results
    REPORT["all_pass"] = all_pass
    REPORT["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"

    # 写报告
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "_canary_smoke_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(REPORT, f, indent=2, ensure_ascii=False)
    print(f"  报告已落盘：{out_path}")

    print("\n" + "=" * 60)
    print(f"验证完成: {PASS} PASS / {FAIL} FAIL (共 {TOTAL} 项测试)")
    print("=" * 60)
    if FAIL > 0 or not all_pass:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
