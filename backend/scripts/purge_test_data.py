"""清除集成测试漏进开发库的自动化测试数据（默认 dry-run）。

背景：tests/integration/test_full_chain_saas_export.py 直连开发库
（app.core.database.SessionLocal），每次运行 commit 两个临时租户
（Tenant A Corp / Tenant B Corp）及其询盘、订单、成员关联。历史上该
fixture 没有 teardown，跑一次漏一批。本模块是该指纹的唯一清理实现，
测试 fixture 的 teardown 也调用它，避免两处各写一遍删除逻辑。

用法：
    python scripts/purge_test_data.py            # 只报告，不删除
    python scripts/purge_test_data.py --apply    # 真正删除

安全护栏：purge_by_tenant_ids() 在删除前逐个校验目标租户名属于
_TEST_TENANT_NAMES、目标用户 hashed_password 等于 _MOCK_PASSWORD_HASH，
任一不匹配即整体拒绝，防止将来把真实客户数据卷进删除范围。
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from sqlalchemy import text

# 自动化测试数据指纹（与 test_full_chain_saas_export.py 保持一致）
TEST_TENANT_NAMES = ("Tenant A Corp", "Tenant B Corp")
MOCK_PASSWORD_HASH = "mock_password_hash"

# 通用 tenant_id 清扫时跳过：tenants 由护栏单独删，user_tenants 需同时按 user_id 清
_SKIP_TENANT_TABLES = {"tenants", "user_tenants"}


def tenant_scoped_tables(conn) -> list[str]:
    """列出 public 下带 tenant_id 列的真实表。"""
    rows = conn.execute(
        text(
            """
            select c.table_name
            from information_schema.columns c
            join information_schema.tables t
              on t.table_schema = c.table_schema and t.table_name = c.table_name
            where c.table_schema = 'public'
              and c.column_name = 'tenant_id'
              and t.table_type = 'BASE TABLE'
            order by c.table_name
            """
        )
    ).fetchall()
    return [r[0] for r in rows if r[0] not in _SKIP_TENANT_TABLES]


def find_auto_test_scopes(conn) -> tuple[list[str], list[str]]:
    """按指纹找出遗留测试租户 id 与测试用户 id。"""
    tenant_ids = [
        str(r[0])
        for r in conn.execute(
            text("select id from tenants where name = any(:names) order by name, id"),
            {"names": list(TEST_TENANT_NAMES)},
        )
    ]
    user_ids = [
        str(r[0])
        for r in conn.execute(
            text("select id from users where hashed_password = :mock_hash order by id"),
            {"mock_hash": MOCK_PASSWORD_HASH},
        )
    ]
    return tenant_ids, user_ids


def _assert_test_scopes(conn, tenant_ids: list[str], user_ids: list[str]) -> None:
    """删除前护栏：目标行必须全部带自动化测试指纹，否则整体拒绝。"""
    if not tenant_ids and not user_ids:
        raise ValueError("purge 拒绝执行：目标集合为空")

    if tenant_ids:
        bad = conn.execute(
            text(
                "select id, name from tenants "
                "where id::text = any(:ids) and name <> all(:names)"
            ),
            {"ids": list(tenant_ids), "names": list(TEST_TENANT_NAMES)},
        ).fetchall()
        if bad:
            raise ValueError(f"purge 拒绝执行：目标租户不全是测试租户 {bad}")
        missing = set(map(str, tenant_ids)) - {
            str(r[0])
            for r in conn.execute(
                text("select id from tenants where id::text = any(:ids)"),
                {"ids": list(tenant_ids)},
            )
        }
        if missing:
            raise ValueError(f"purge 拒绝执行：目标租户不存在 {sorted(missing)}")

    if user_ids:
        bad = conn.execute(
            text(
                "select id, username from users "
                "where id::text = any(:ids) and hashed_password <> :mock_hash"
            ),
            {"ids": list(user_ids), "mock_hash": MOCK_PASSWORD_HASH},
        ).fetchall()
        if bad:
            raise ValueError(f"purge 拒绝执行：目标用户不全是测试用户 {bad}")


def purge_by_tenant_ids(
    conn,
    tenant_ids: list[str],
    user_ids: list[str] | None = None,
) -> dict[str, int]:
    """删除指定测试租户/用户及其全部下游行，返回 {表名: 删除行数}。

    删除顺序按外键依赖倒序：租户作用域子表 -> user_tenants / operation_logs
    -> users -> tenants。逐表 savepoint，单表失败不中断整体，失败记进 errors。
    """
    tenant_ids = [str(t) for t in tenant_ids]
    user_ids = [str(u) for u in (user_ids or [])]
    _assert_test_scopes(conn, tenant_ids, user_ids)

    report: dict[str, int] = {}
    errors: dict[str, str] = {}

    def _delete(sql: str, params: dict, key: str) -> None:
        try:
            with conn.begin_nested():
                result = conn.execute(text(sql), params)
            report[key] = int(result.rowcount or 0)
        except Exception as exc:  # 单表失败不影响其余清理
            errors[key] = f"{type(exc).__name__}: {str(exc)[:160]}"

    # 0. 先清无 tenant_id 或引用 quotes 的订单明细与订单
    _delete(
        """
        delete from order_items where order_id in (
            select id from orders where tenant_id::text = any(:ids)
            or merchant_id::text = any(:uids) or buyer_id::text = any(:uids)
        )
        """,
        {"ids": tenant_ids, "uids": user_ids},
        "order_items",
    )
    _delete(
        """
        delete from orders where tenant_id::text = any(:ids)
        or merchant_id::text = any(:uids) or buyer_id::text = any(:uids)
        """,
        {"ids": tenant_ids, "uids": user_ids},
        "orders",
    )
    _delete(
        """
        delete from quote_items where quote_id in (
            select id from quotes where tenant_id::text = any(:ids)
            or merchant_id::text = any(:uids)
        )
        """,
        {"ids": tenant_ids, "uids": user_ids},
        "quote_items",
    )
    _delete(
        "delete from quotes where tenant_id::text = any(:ids) or merchant_id::text = any(:uids)",
        {"ids": tenant_ids, "uids": user_ids},
        "quotes",
    )

    # 1. 所有带 tenant_id 的子表
    for table in tenant_scoped_tables(conn):
        if table in ("quotes", "quote_items"):
            continue
        _delete(
            f'delete from "{table}" where tenant_id::text = any(:ids)',
            {"ids": tenant_ids},
            table,
        )


    # 2. 成员关联与操作日志（同时按 user_id 兜底）
    _delete(
        "delete from user_tenants where tenant_id::text = any(:tids) or user_id::text = any(:uids)",
        {"tids": tenant_ids, "uids": user_ids},
        "user_tenants",
    )
    _delete(
        "delete from operation_logs where user_id::text = any(:uids)",
        {"uids": user_ids},
        "operation_logs",
    )

    # 3. 主体：先用户后租户
    _delete("delete from users where id::text = any(:ids)", {"ids": user_ids}, "users")
    _delete(
        "delete from tenants where id::text = any(:ids)",
        {"ids": tenant_ids},
        "tenants",
    )

    if errors:
        report["__errors__"] = errors  # type: ignore[assignment]
    return report


def main() -> int:
    from app.core.database import engine

    apply = "--apply" in sys.argv[1:]
    with engine.connect() as conn:
        tenant_ids, user_ids = find_auto_test_scopes(conn)
        print(f"发现自动化测试租户 {len(tenant_ids)} 个、测试用户 {len(user_ids)} 个")
        if not tenant_ids and not user_ids:
            print("库内无自动化测试遗留数据。")
            return 0
        if not apply:
            print("dry-run：未删除任何数据。加 --apply 才执行。")
            return 0
        report = purge_by_tenant_ids(conn, tenant_ids, user_ids)
        conn.commit()

    errors = report.pop("__errors__", {}) or {}
    removed = {k: v for k, v in report.items() if v}
    print(f"已删除 {sum(removed.values())} 行，涉及 {len(removed)} 张表：")
    for table, count in sorted(removed.items(), key=lambda kv: -kv[1]):
        print(f"  {table}: {count}")
    if errors:
        print(f"警告：{len(errors)} 张表清理失败（多为无外键约束或表不存在）：")
        for table, msg in sorted(errors.items()):
            print(f"  {table}: {msg}")
    # 复核：指纹目标应全部归零
    with engine.connect() as conn:
        left_t, left_u = find_auto_test_scopes(conn)
    print(f"复核：剩余测试租户 {len(left_t)} 个、测试用户 {len(left_u)} 个")
    return 1 if (left_t or left_u) else 0


if __name__ == "__main__":
    raise SystemExit(main())
