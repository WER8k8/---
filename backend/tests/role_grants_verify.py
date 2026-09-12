"""生产角色映射 + ALTER DEFAULT PRIVILEGES 真实 PostgreSQL 验证。

用法：python -m tests.role_grants_verify
前提：真 PG（uj-pg-verify:5432/uj_test），role_grants_pilot.sql 已应用。

覆盖：
1) 角色存在性与属性（NOLOGIN / 非 superuser / 无 bypassrls）
2) public schema：PUBLIC 无 CREATE，app_user/service_role 有 USAGE
3) 存量表授权矩阵：app_user = DML 四权 + TRIGGER（无 TRUNCATE）；
   service_role = DML + TRUNCATE；PUBLIC = 0 授权
4) TRUNCATE 实际拒绝（app_user 执行报错）+ service_role 实际可用
5) DDL 拒绝：app_user 建表/删表被拒
6) 新建表默认授权：postgres 建新表 → app_user/service_role 自动带授权
   （ALTER DEFAULT PRIVILEGES 生效实证），验证后清理
7) 默认权限目录：pg_default_acl 对 PUBLIC 的 REVOKE 条目在位
"""

from __future__ import annotations

import os
import sys

import psycopg2

PG_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "test")
PG_DB = os.getenv("POSTGRES_DB", "uj_test")

PASS = 0
FAIL = 0
TOTAL = 0


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


def get_connection():
    return psycopg2.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER,
        password=PG_PASSWORD, dbname=PG_DB,
    )


def main() -> int:
    print("=" * 60)
    print("轮 25-A 收口: 生产角色映射 + 默认权限 真实 PG 验证")
    print("=" * 60)

    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor()

    # ---- 阶段 1: 角色属性 ----
    print("\n[阶段 1: 角色存在性与属性]")
    for role in ("app_user", "service_role"):
        cur.execute(
            "SELECT rolcanlogin, rolsuper, rolbypassrls FROM pg_roles WHERE rolname = %s;",
            (role,),
        )
        row = cur.fetchone()
        check(f"{role} 存在且 NOLOGIN",
              row is not None and row[0] is False, f"got {row}")
        check(f"{role} 非 superuser 且无 bypassrls",
              row is not None and row[1] is False and row[2] is False, f"got {row}")

    # ---- 阶段 2: schema 权限 ----
    print("\n[阶段 2: public schema 权限]")
    # PUBLIC 是伪角色，has_schema_privilege 用 public 关键字表达
    cur.execute(
        "SELECT has_schema_privilege('public', 'public', 'CREATE'), "
        "has_schema_privilege('public', 'public', 'USAGE'), "
        "has_schema_privilege('app_user', 'public', 'USAGE'), "
        "has_schema_privilege('service_role', 'public', 'USAGE');"
    )
    r = cur.fetchone()
    check("PUBLIC 无 public schema CREATE 权", r[0] is False, f"got {r}")
    check("PUBLIC 仍保留 USAGE（连接可用）", r[1] is True)
    check("app_user 有 USAGE", r[2] is True)
    check("service_role 有 USAGE", r[3] is True)

    # ---- 阶段 3: 授权矩阵（information_schema 全表扫） ----
    print("\n[阶段 3: 存量表授权矩阵]")
    cur.execute(
        "SELECT grantee, privilege_type, count(*) FROM information_schema.table_privileges "
        "WHERE table_schema='public' AND grantee IN ('app_user','service_role','PUBLIC') "
        "GROUP BY grantee, privilege_type ORDER BY grantee, privilege_type;"
    )
    matrix = {}
    for grantee, priv, cnt in cur.fetchall():
        matrix.setdefault(grantee, {})[priv] = cnt

    cur.execute(
        "SELECT count(*) FROM pg_tables WHERE schemaname='public';"
    )
    ntables = cur.fetchone()[0]

    au = matrix.get("app_user", {})
    check("app_user: 233 表全部 SELECT/INSERT/UPDATE/DELETE/TRIGGER",
          all(au.get(p) == ntables for p in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRIGGER")),
          f"got {au}")
    check("app_user: 无 TRUNCATE / 无 REFERENCES",
          "TRUNCATE" not in au and "REFERENCES" not in au, f"got {list(au)}")

    sr = matrix.get("service_role", {})
    check("service_role: DML + TRIGGER + TRUNCATE 全表在位",
          all(sr.get(p) == ntables for p in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRIGGER", "TRUNCATE")),
          f"got {sr}")

    check("PUBLIC: 存量表 0 授权", "PUBLIC" not in matrix, f"got {matrix.get('PUBLIC')}")

    # ---- 阶段 4: TRUNCATE 实际行为 ----
    print("\n[阶段 4: TRUNCATE 实际拒绝/放行]")
    cur.execute("SET ROLE app_user;")
    trunc_denied = False
    try:
        cur.execute("TRUNCATE wallet_accounts;")
    except psycopg2.errors.InsufficientPrivilege:
        trunc_denied = True
    finally:
        cur.execute("ROLLBACK")
        cur.execute("RESET ROLE;")
    check("app_user TRUNCATE 被拒 (InsufficientPrivilege)", trunc_denied)

    cur.execute("SET ROLE service_role;")
    trunc_ok = False
    try:
        cur.execute("BEGIN;")
        cur.execute("TRUNCATE wallet_transactions;")
        trunc_ok = True
    finally:
        cur.execute("ROLLBACK")
        cur.execute("RESET ROLE;")
    check("service_role TRUNCATE 可用（对账重载场景）", trunc_ok)

    # ---- 阶段 5: DDL 拒绝 ----
    print("\n[阶段 5: app_user DDL 拒绝]")
    cur.execute("SET ROLE app_user;")
    ddl_denied = False
    try:
        cur.execute("CREATE TABLE _rls_grant_probe (id int);")
    except psycopg2.errors.InsufficientPrivilege:
        ddl_denied = True
    finally:
        cur.execute("RESET ROLE;")
    check("app_user CREATE TABLE 被拒", ddl_denied)

    drop_denied = False
    cur.execute("SET ROLE app_user;")
    try:
        cur.execute("DROP TABLE wallet_accounts;")
    except psycopg2.errors.InsufficientPrivilege:
        drop_denied = True
    finally:
        cur.execute("RESET ROLE;")
    check("app_user DROP TABLE 被拒", drop_denied)

    # ---- 阶段 6: 新建表默认授权 ----
    print("\n[阶段 6: ALTER DEFAULT PRIVILEGES 生效实证]")
    probe = "_default_acl_probe_20260904"
    cur.execute(f"DROP TABLE IF EXISTS {probe};")
    cur.execute(f"CREATE TABLE {probe} (id int);")
    cur.execute(
        "SELECT count(*) FROM information_schema.table_privileges "
        "WHERE table_schema='public' AND table_name=%s "
        "AND grantee='app_user' AND privilege_type IN ('SELECT','INSERT','UPDATE','DELETE');",
        (probe,),
    )
    au_cnt = cur.fetchone()[0]
    check("postgres 新建表自动带 app_user DML 授权", au_cnt == 4, f"got {au_cnt}")
    cur.execute(
        "SELECT count(*) FROM information_schema.table_privileges "
        "WHERE table_schema='public' AND table_name=%s "
        "AND grantee='service_role' AND privilege_type IN ('SELECT','INSERT','UPDATE','DELETE','TRUNCATE');",
        (probe,),
    )
    sr_cnt = cur.fetchone()[0]
    check("postgres 新建表自动带 service_role 全量授权", sr_cnt == 5, f"got {sr_cnt}")
    cur.execute(
        "SELECT count(*) FROM information_schema.table_privileges "
        "WHERE table_schema='public' AND table_name=%s AND grantee='PUBLIC';",
        (probe,),
    )
    pub_cnt = cur.fetchone()[0]
    check("postgres 新建表对 PUBLIC 0 授权", pub_cnt == 0, f"got {pub_cnt}")
    cur.execute(f"DROP TABLE IF EXISTS {probe};")

    # ---- 阶段 7: pg_default_acl 条目 ----
    print("\n[阶段 7: pg_default_acl 目录]")
    cur.execute(
        "SELECT count(*) FROM pg_default_acl "
        "JOIN pg_roles r ON r.oid = defaclrole "
        "WHERE r.rolname='postgres' AND defaclnamespace::regnamespace::text='public' "
        "AND defaclobjtype='r';"
    )
    acl_cnt = cur.fetchone()[0]
    check("pg_default_acl 有 postgres/public/tables 条目", acl_cnt >= 1, f"got {acl_cnt}")

    cur.close()
    conn.close()

    print("\n" + "=" * 60)
    print(f"验证完成: {PASS} PASS / {FAIL} FAIL (共 {TOTAL} 项测试)")
    print("=" * 60)

    if FAIL > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
