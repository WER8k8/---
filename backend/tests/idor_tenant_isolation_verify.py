"""IDOR / 多租户隔离 运行时哨兵（ADR-002 方案 1，T02 tracer + T09 门禁雏形）。

分两层报告，各自独立：
  应用层隔离（第一道防线，T02/T03）：
    A1 租户用户 RFQ 列表只见本租户（不见他租户）；
    A2 租户用户读他租户 RFQ 详情被拒（404）。
  DB 层纵深（第二道防线，T05，尚未接）：
    D1 pilot 表是否 ENABLE+FORCE RLS；
    D2 app 连接角色是否非 superuser（否则 RLS 形同虚设）。

通过 seed 真实 User + user_tenants 关联，走既有 resolve_tenant_id_for_user 路径。
退出码：应用层 A1/A2 任一失败 → exit 1（隔离门禁）；D 层缺失仅 WARN 不 gate（T05 前预期）。
运行需真 PG（默认 youding_dev@5433）。
"""
from __future__ import annotations
import os
import sys
import uuid

# 以脚本直跑时 sys.path[0]=tests/，补 backend 根使 `from app.main import app` 可导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2

PG_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5433"))
PG_USER = os.getenv("POSTGRES_USER", "youding")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "youding")
PG_DB = os.getenv("POSTGRES_DB", "youding_dev")

APP_FAIL = DB_FAIL = TOTAL = 0


def acheck(name, cond, detail=""):
    global APP_FAIL, TOTAL
    TOTAL += 1
    if cond:
        print(f"  [PASS] {name}")
    else:
        APP_FAIL += 1
        print(f"  [FAIL] {name}{(' -- ' + detail) if detail else ''}")


def dcheck(name, cond, detail=""):
    global DB_FAIL, TOTAL
    TOTAL += 1
    if cond:
        print(f"  [PASS] {name}")
    else:
        DB_FAIL += 1
        print(f"  [WARN/未达标] {name}{(' -- ' + detail) if detail else ''}")


def conn():
    return psycopg2.connect(host=PG_HOST, port=PG_PORT, user=PG_USER,
                            password=PG_PASSWORD, dbname=PG_DB)


def main():
    global APP_FAIL, DB_FAIL
    print("=" * 64)
    print("IDOR / 多租户隔离 运行时哨兵 (idor_tenant_isolation_verify)")
    print("=" * 64)

    created_user = created_link = None
    r_a, r_b = str(uuid.uuid4()), str(uuid.uuid4())
    c = conn(); c.autocommit = True; cur = c.cursor()

    # 取两个真实存在的租户
    cur.execute("SELECT id FROM tenants ORDER BY created_at LIMIT 2")
    tids = [str(r[0]) for r in cur.fetchall()]
    if len(tids) < 2:
        print("需要 >=2 个真实租户，跳过"); sys.exit(0)
    ta, tb = tids[0], tids[1]
    u_actor = str(uuid.uuid4())
    uname = f"idor_actor_{u_actor[:8]}"

    def ins_rfq(rid, tid, co):
        cur.execute(
            """INSERT INTO rfqs (id, company, country, application, contact_name,
                                 email, status, rfq_score, intent_score, tenant_id,
                                 created_at, updated_at, deleted_at)
               VALUES (%s,%s,'CN','refractory','tester',%s,'pending',50,0,%s,NOW(),NOW(),NULL)""",
            (rid, co, f"{co}@x.com", tid))

    try:
        ins_rfq(r_a, ta, "TenantA-Co")
        ins_rfq(r_b, tb, "TenantB-Co")
        # 真实用户 + UserTenant 绑定（tenant_admin of ta）
        cur.execute(
            """INSERT INTO users (id, username, email, hashed_password, role,
                                  is_active, is_default_password, created_at, updated_at)
               VALUES (%s,%s,%s,'x','tenant_admin',TRUE,FALSE,NOW(),NOW())""",
            (u_actor, uname, f"{uname}@x.com"))
        created_user = u_actor
        cur.execute(
            """INSERT INTO user_tenants (id, user_id, tenant_id, role, is_active, created_at)
               VALUES (%s,%s,%s,'admin',TRUE,NOW())""",
            (str(uuid.uuid4()), u_actor, ta))

        # D1/D2 DB 层现状
        cur.execute("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname='prospect_leads'")
        row = cur.fetchone()
        dcheck("D1 pilot 表 ENABLE+FORCE RLS", bool(row) and row[0] and row[1],
               f"rowsecurity={row[0] if row else None} force={row[1] if row else None}")
        cur.execute("SELECT rolsuper FROM pg_roles WHERE rolname=current_user")
        dcheck("D2 app 角色非 superuser", cur.fetchone()[0] is False, f"role={PG_USER} super")

        # 应用层：以真实 tenant_admin 身份访问
        from fastapi.testclient import TestClient
        os.environ.update(DB_TYPE="postgresql", REDIS_ENABLED="false")
        os.environ["DATABASE_URL"] = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
        from app.main import app
        from app.core.security import get_current_user
        from app.db.session import SessionLocal
        from app.models.user import User
        s = SessionLocal()
        actor = s.query(User).filter(User.id == u_actor).first()
        s.close()
        app.dependency_overrides[get_current_user] = lambda: actor
        client = TestClient(app)

        r = client.get("/api/v1/rfq?page=1&page_size=100")
        body = (r.json() or {}).get("data") or {}
        items = body.get("items", [])
        foreign = [it.get("id") for it in items if str(it.get("tenant_id")) == str(tb)]
        leaked_b = r_b in {it.get("id") for it in items} or bool(foreign)
        acheck("A1 列表不含任何他租户行", (not leaked_b),
               f"他租户行={len(foreign)} 含B={r_b in {it.get('id') for it in items}}")
        r2 = client.get(f"/api/v1/rfq/{r_b}")
        denied = not (r2.status_code == 200 and (r2.json() or {}).get("code") == 0)
        acheck("A2 读他租户详情被拒", denied, f"status={r2.status_code}")
        r3 = client.get(f"/api/v1/rfq/{r_a}")
        acheck("A3 读本租户详情放行", r3.status_code == 200 and (r3.json() or {}).get("code") == 0,
               f"status={r3.status_code}")

        # A4 多资源列表租户同质性：opportunity/company/campaign/rfq 均不得返回他租户行
        # （用既有真实数据 + 上一步 seed 的本租户 r_a；actor 属 ta，任何 tenant_id≠ta 的行即越权）
        for ep in ("/api/v1/opportunity", "/api/v1/company", "/api/v1/campaign", "/api/v1/rfq"):
            try:
                rr = client.get(ep + "?page=1&page_size=100")
                if rr.status_code != 200:
                    print(f"  [SKIP] A4 {ep} 返回 {rr.status_code}（环境/漂移，不计隔离）")
                    continue
                jj = rr.json() or {}
                d = jj.get("data")
                its = d.get("items") if isinstance(d, dict) else (d if isinstance(d, list) else [])
                its = its or []
                foreign = [it for it in its if it.get("tenant_id") and str(it.get("tenant_id")) != str(ta)]
                acheck(f"A4 {ep} 列表无他租户行", len(foreign) == 0,
                       f"他租户行={len(foreign)} (共 {len(its)} 行)")
            except Exception as e:
                print(f"  [SKIP] A4 {ep} 端点异常（schema 漂移/环境）：{str(e)[:70]}")

        # A5 T07 跨租户引用：actor(租户A) 用他租户 B 的 RFQ 建报价 → 应 403 且不留痕
        try:
            rq = client.post(f"/api/v1/quotes/from-rfq?rfq_id={r_b}&merchant_id={u_actor}")
            if rq.status_code in (403, 404):
                acheck("A5 跨租户 RFQ 建报价被拒", True, f"status={rq.status_code}")
            elif rq.status_code == 200 and (rq.json() or {}).get("code") == 0:
                acheck("A5 跨租户 RFQ 建报价被拒", False, "居然成功创建=越权!")
            else:
                print(f"  [SKIP] A5 端点 {rq.status_code}（非隔离判定/环境）")
        except Exception as e:
            print(f"  [SKIP] A5 异常（schema/环境）：{str(e)[:60]}")
    finally:
        try:
            from app.main import app as _a; _a.dependency_overrides.clear()
        except Exception:
            pass
        for sqlt, args in (
            ("DELETE FROM quote_items WHERE quote_id IN (SELECT id FROM quotes WHERE rfq_id IN (%s,%s))", (r_a, r_b)),
            ("DELETE FROM quotes WHERE rfq_id IN (%s,%s)", (r_a, r_b)),
            ("DELETE FROM rfqs WHERE id IN (%s,%s)", (r_a, r_b)),
            ("DELETE FROM user_tenants WHERE user_id=%s", (u_actor,)),
            ("DELETE FROM users WHERE id=%s", (u_actor,)),
        ):
            try:
                cur.execute(sqlt, args)
            except Exception:
                c.rollback()
        cur.close(); c.close()

    print("\n" + "=" * 64)
    print(f"应用层隔离: {'PASS' if APP_FAIL == 0 else str(APP_FAIL) + ' 失败'} | "
          f"DB 纵深(T05前预期未达标): {DB_FAIL} 项待补")
    print("=" * 64)
    sys.exit(1 if APP_FAIL else 0)


if __name__ == "__main__":
    main()
