"""wallet 两表 user_id 维度 RLS 真实 PostgreSQL 隔离验证（轮 25-A 补齐专项）。

用法：python -m tests.wallet_user_rls_verify
前提：真 PG（uj-pg-verify:5432/uj_test），迁移 089_wallet_user_rls 已应用。

覆盖（双用户穿透 0 泄漏）：
1) wallet_accounts / wallet_transactions RLS 启用状态（rowsecurity + force）
2) 4 条策略绑定核验（2 表 × user_isolation + service_bypass）
3) 用户 A 写入本人账户/流水可见
4) 用户 B 读用户 A 数据 0 泄漏（SELECT 穿透拦截）
5) 用户 B 越权 DELETE 用户 A 数据影响 0 行（USING 拦截）
6) 用户 B 伪造 user_id 写入触发 WITH CHECK 拒绝
7) 未设置 app.current_user_id 时 app_user 空门被拦
8) service_role 全量旁路可读写（充值/对账场景）
9) 清理自产测试数据（不残留）
"""

from __future__ import annotations

import datetime
import os
import sys
import uuid

import psycopg2
from psycopg2 import sql

PG_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "test")
PG_DB = os.getenv("POSTGRES_DB", "uj_test")

WALLET_TABLES = ("wallet_accounts", "wallet_transactions")
EXPECTED_POLICIES = {
    "wallet_accounts": {
        "wallet_accounts_user_isolation",
        "wallet_accounts_service_bypass",
    },
    "wallet_transactions": {
        "wallet_transactions_user_isolation",
        "wallet_transactions_service_bypass",
    },
}

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
    print("轮 25-A 补齐: wallet user_id 维度 RLS 真实 PG 验证")
    print("=" * 60)

    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor()

    # ---- 阶段 1: RLS 启用状态 ----
    print("\n[阶段 1: wallet 双表 RLS 启用状态]")
    for tbl in WALLET_TABLES:
        cur.execute(
            "SELECT c.relrowsecurity, c.relforcerowsecurity FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'public' AND c.relname = %s;",
            (tbl,),
        )
        row = cur.fetchone()
        check(f"{tbl} rowsecurity + force 均已启用",
              row is not None and row[0] is True and row[1] is True,
              f"got {row}")

    # ---- 阶段 2: 策略绑定 ----
    print("\n[阶段 2: 4 条策略绑定核验]")
    for tbl, expected in EXPECTED_POLICIES.items():
        cur.execute(
            "SELECT policyname FROM pg_policies "
            "WHERE schemaname = 'public' AND tablename = %s;",
            (tbl,),
        )
        actual = {r[0] for r in cur.fetchall()}
        check(f"{tbl} 策略齐备 {sorted(expected)}", expected <= actual,
              f"actual={sorted(actual)}")

    # ---- 种子：双用户数据（user_id varchar，不依赖 users 表外键） ----
    user_a = f"rls-user-{uuid.uuid4().hex[:12]}"
    user_b = f"rls-user-{uuid.uuid4().hex[:12]}"
    now = datetime.datetime.now(datetime.timezone.utc)
    account_a = str(uuid.uuid4())
    tx_a = str(uuid.uuid4())

    try:
        # ---- 阶段 3: 用户 A 写入与可见 ----
        print("\n[阶段 3: 用户 A 写入本人账户/流水]")
        cur.execute("SET ROLE app_user;")
        cur.execute(f"SET app.current_user_id = '{user_a}';")
        cur.execute(
            "INSERT INTO wallet_accounts (id, user_id, currency, balance) "
            "VALUES (%s, %s, 'CNY', 100);",
            (account_a, user_a),
        )
        cur.execute(
            "INSERT INTO wallet_transactions (id, tx_id, user_id, operation, "
            "amount, currency, balance_after) VALUES (%s, %s, %s, 'recharge', "
            "100, 'CNY', 100);",
            (tx_a, f"tx-{uuid.uuid4().hex[:8]}", user_a),
        )
        cur.execute("SELECT count(*) FROM wallet_accounts WHERE id = %s;", (account_a,))
        check("用户 A 可读本人账户", cur.fetchone()[0] == 1)
        cur.execute("SELECT count(*) FROM wallet_transactions WHERE id = %s;", (tx_a,))
        check("用户 A 可读本人流水", cur.fetchone()[0] == 1)

        # ---- 阶段 4: 用户 B 穿透 0 泄漏 ----
        print("\n[阶段 4: 用户 B 穿透 0 泄漏]")
        cur.execute(f"SET app.current_user_id = '{user_b}';")
        cur.execute("SELECT count(*) FROM wallet_accounts WHERE id = %s;", (account_a,))
        check("用户 B 读用户 A 账户 0 泄漏", cur.fetchone()[0] == 0)
        cur.execute("SELECT count(*) FROM wallet_transactions WHERE id = %s;", (tx_a,))
        check("用户 B 读用户 A 流水 0 泄漏", cur.fetchone()[0] == 0)

        cur.execute("DELETE FROM wallet_accounts WHERE id = %s;", (account_a,))
        check("用户 B 越权删用户 A 账户影响 0 行", cur.rowcount == 0, f"got {cur.rowcount}")
        cur.execute("DELETE FROM wallet_transactions WHERE id = %s;", (tx_a,))
        check("用户 B 越权删用户 A 流水影响 0 行", cur.rowcount == 0, f"got {cur.rowcount}")

        fake_ok = False
        try:
            cur.execute(
                "INSERT INTO wallet_accounts (id, user_id, currency, balance) "
                "VALUES (%s, %s, 'CNY', 1);",
                (str(uuid.uuid4()), user_a),
            )
        except Exception:
            fake_ok = True
        check("用户 B 伪造 user_id 写入触发 WITH CHECK 拒绝", fake_ok)

        # ---- 阶段 5: 空门防线 ----
        print("\n[阶段 5: 未设置 app.current_user_id 空门防线]")
        # user_id 列是 varchar → current_setting 返回空串不抛错，
        # 但空串 ≠ 任何 user_id → 0 行（等效拦截，无泄漏即达标）
        cur.execute("RESET app.current_user_id;")
        cur.execute("SELECT count(*) FROM wallet_accounts;")
        wallet_cnt = cur.fetchone()[0]
        check("未设置 app.current_user_id 时空上下文可见 0 行（无泄漏）",
              wallet_cnt == 0, f"got {wallet_cnt}")
        cur.execute("SELECT count(*) FROM wallet_transactions;")
        tx_cnt = cur.fetchone()[0]
        check("空上下文下流水同样 0 行（无泄漏）", tx_cnt == 0, f"got {tx_cnt}")

        # ---- 阶段 6: service_role 全量旁路 ----
        print("\n[阶段 6: service_role 充值/对账旁路]")
        cur.execute("RESET ROLE;")
        cur.execute("SET ROLE service_role;")
        cur.execute("SELECT count(*) FROM wallet_accounts WHERE id = %s;", (account_a,))
        check("service_role 可读用户 A 账户（旁路）", cur.fetchone()[0] == 1)
        cur.execute(
            "UPDATE wallet_accounts SET balance = balance + 50 WHERE id = %s;",
            (account_a,),
        )
        check("service_role 可改用户 A 账户（充值场景）", cur.rowcount == 1,
              f"got {cur.rowcount}")
    finally:
        cur.execute("RESET ROLE;")
        cur.execute("DELETE FROM wallet_accounts WHERE user_id IN (%s, %s);", (user_a, user_b))
        cur.execute("DELETE FROM wallet_transactions WHERE user_id IN (%s, %s);", (user_a, user_b))
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
