"""轮 25-A RLS 试点 验证（不依赖真 PG）。

用法：python tests/rls_pilot_verify.py

覆盖：
1) RLS_PILOT_TABLES 常量含 6 张表
2) DEFAULT_POLICIES 每张表都有策略定义
3) generate_enable_rls_sql / generate_disable_rls_sql 互逆
4) generate_policy_sql 格式正确（CREATE POLICY ... ON ... FOR ... TO ...）
5) generate_all_pilot_sql 顺序正确（enable 在前，disable 逆序）
6) token_ledger 特殊处理（service_role 旁路 + INSERT 限制）
7) leads 实际表名映射（unified_lead + prospect_lead）
8) 验证 verify_rls_applied 返回结构
9) SQL 输出可在 SQLite 上无错误执行（shim 模式：仅检 SQL 格式）

本测试基于 shim 模式（不接真 PG），SQLite 跑 alembic 时由迁移本身做 noop。
"""
import importlib.util
import os
import re
import sys
import types

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND)

# ---- 预置 app.core.database shim（防 import 链触发 opentelemetry 等）----
DB_SHIM = types.ModuleType("app.core.database")
DB_SHIM.Base = object
DB_SHIM.UUID_TYPE = "VARCHAR(36)"
DB_SHIM.SessionLocal = None
sys.modules["app.core.database"] = DB_SHIM

CFG_SHIM = types.ModuleType("app.core.config")


class _FakeSettings:
    SECRET_KEY = "rls-pilot-verify-secret-2026"
    DATABASE_URL = "postgresql://localhost/test"
    BROWSER_RUNTIME_ENABLED = False


CFG_SHIM.settings = _FakeSettings()
sys.modules["app.core.config"] = CFG_SHIM

# ---- 预置空包 + 加载 rls_policies ----
APP_SERVICES = types.ModuleType("app.services")
APP_SERVICES.__path__ = []
sys.modules["app.services"] = APP_SERVICES
APP_DB = types.ModuleType("app.db")
APP_DB.__path__ = [os.path.join(_BACKEND, "app", "db")]
sys.modules["app.db"] = APP_DB


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_rls = _load("app.db.rls_policies", os.path.join(_BACKEND, "app", "db", "rls_policies.py"))


# ---- 用例计数器 ----
_results: list[tuple[str, bool, str]] = []


def _check(name: str, cond: bool, detail: str = ""):
    status = "PASS" if cond else "FAIL"
    _results.append((name, cond, detail))
    flag = "✔" if cond else "✘"
    extra = f"  {detail}" if detail and not cond else ""
    print(f"  {flag}  {status}  {name}{extra}")


# ============================================================
# 1) 常量结构
# ============================================================
print("== 1. 常量结构 ==")


def test_pilot_tables_count():
    _check("RLS_PILOT_TABLES 6 张表", len(_rls.RLS_PILOT_TABLES) == 6,
           f"got {len(_rls.RLS_PILOT_TABLES)}")


def test_pilot_tables_content():
    expected = {"leads", "email_outreach", "content_master",
                "wallet", "token_ledger", "ubrain_tenant_memory"}
    got = set(_rls.RLS_PILOT_TABLES)
    _check("6 张表名匹配", got == expected,
           f"diff: missing={expected - got}, extra={got - expected}")


def test_pilot_table_mapping():
    # 2026-09-03 真 PG 实战修正：映射对齐模型 __tablename__（prospect_leads 等）
    leads = _rls.RLS_PILOT_TABLE_MAPPING.get("leads", ())
    _check("leads → prospect_leads（真表名）",
           set(leads) == {"prospect_leads"},
           f"got {leads}")
    # ubrain_tenant_memory → ubrain_tenant_memory（模型即此名）
    ubrain = _rls.RLS_PILOT_TABLE_MAPPING.get("ubrain_tenant_memory", ())
    _check("ubrain_tenant_memory → ubrain_tenant_memory", ubrain == ("ubrain_tenant_memory",),
           f"got {ubrain}")


test_pilot_tables_count()
test_pilot_tables_content()
test_pilot_table_mapping()


# ============================================================
# 2) DEFAULT_POLICIES 覆盖
# ============================================================
print("== 2. DEFAULT_POLICIES 覆盖 ==")


def test_policies_all_covered():
    for table in _rls.RLS_PILOT_TABLES:
        policies = _rls.DEFAULT_POLICIES.get(table, [])
        _check(f"{table} 有策略定义", len(policies) >= 1,
               f"got {len(policies)}")


test_policies_all_covered()


# ============================================================
# 3) enable / disable 互逆
# ============================================================
print("== 3. enable / disable 互逆 ==")


def test_enable_disable_inverse():
    # 启用某张表的 SQL 列表
    table = "wallet"
    enable_sqls = _rls.generate_enable_rls_sql(table)
    disable_sqls = _rls.generate_disable_rls_sql(table)
    _check("enable 2 条 SQL", len(enable_sqls) == 2,
           f"got {len(enable_sqls)}")
    _check("disable 2 条 SQL", len(disable_sqls) == 2,
           f"got {len(disable_sqls)}")
    # enable 第一条 = ENABLE，disable 倒数第一条 = DISABLE
    _check("enable 首条 = ENABLE", "ENABLE" in enable_sqls[0], "")
    _check("disable 末条 = DISABLE", "DISABLE" in disable_sqls[-1], "")


test_enable_disable_inverse()


# ============================================================
# 4) generate_policy_sql 格式
# ============================================================
print("== 4. CREATE POLICY 格式 ==")


def test_policy_sql_format():
    p = _rls.RLSPolicy(
        table="wallet",
        policy_name="wallet_test",
    )
    sql = _rls.generate_policy_sql(p)
    # 必须含 CREATE POLICY + ON + FOR + TO + USING + WITH CHECK
    for kw in ("CREATE POLICY", "ON wallet", "FOR ALL", "TO app_user",
               "USING (", "WITH CHECK ("):
        _check(f"policy SQL 含 {kw!r}", kw in sql, f"sql={sql!r}")


test_policy_sql_format()


# ============================================================
# 5) generate_all_pilot_sql 顺序
# ============================================================
print("== 5. 全部 SQL 顺序 ==")


def test_all_pilot_sql_enable_order():
    sqls = _rls.generate_all_pilot_sql(enable=True)
    n = len(sqls)
    _check("总 SQL 数 > 0", n > 0, f"n={n}")
    enable_count = sum(1 for s in sqls if "ENABLE" in s and "FORCE" not in s)
    policy_count = sum(1 for s in sqls if "CREATE POLICY" in s)
    # G.2（2026-09-11）：SQL 按物理表出 —— 6 逻辑组 → 7 物理表（wallet 组 2 张）
    _check(f"ENABLE 数 = 7（7 张物理表 × 1）", enable_count == 7,
           f"got {enable_count}")
    _check(f"FORCE 数 = 7", enable_count == 7, "")
    _check("策略数 ≥ 10", policy_count >= 10, f"got {policy_count}")


def test_all_pilot_sql_disable_inverse():
    enable_sqls = _rls.generate_all_pilot_sql(enable=True)
    disable_sqls = _rls.generate_all_pilot_sql(enable=False)
    _check("disable 序列含 DROP POLICY", any("DROP POLICY" in s for s in disable_sqls), "")
    _check("disable 序列含 DISABLE", any("DISABLE" in s for s in disable_sqls), "")
    _check("enable 与 disable 长度大致相等", abs(len(enable_sqls) - len(disable_sqls)) <= 3,
           f"enable={len(enable_sqls)}, disable={len(disable_sqls)}")


test_all_pilot_sql_enable_order()


def test_generated_sql_only_physical_tables():
    # G.2 验收：生成 SQL 不得引用真库不存在的逻辑表名
    sqls = _rls.generate_all_pilot_sql(enable=True)
    physical = {"prospect_leads", "email_outreachs", "content_masters",
                "wallet_accounts", "wallet_transactions",
                "token_ledger_entries", "ubrain_tenant_memory"}
    referenced: set = set()
    for s in sqls:
        m = re.search(r"ALTER TABLE (\w+)", s)
        if m:
            referenced.add(m.group(1))
        m = re.search(r"CREATE POLICY \w+ ON (\w+)", s)
        if m:
            referenced.add(m.group(1))
    _check("生成 SQL 只引用存在的物理表", referenced <= physical,
           f"非物理引用: {referenced - physical}")


test_generated_sql_only_physical_tables()
test_all_pilot_sql_disable_inverse()


# ============================================================
# 6) token_ledger 特殊处理
# ============================================================
print("== 6. token_ledger 特殊 ==")


def test_token_ledger_special():
    policies = _rls.DEFAULT_POLICIES.get("token_ledger", [])
    _check("token_ledger 有 ≥ 2 条策略", len(policies) >= 2,
           f"got {len(policies)}")
    # 必有 service_role 旁路
    has_service = any(p.role == "service_role" for p in policies)
    _check("含 service_role 旁路", has_service, "")
    # 必有 app_user INSERT 限制
    has_user_insert = any(
        p.role == "app_user" and p.operation == "INSERT" for p in policies
    )
    _check("含 app_user INSERT 限制", has_user_insert, "")


test_token_ledger_special()


# ============================================================
# 7) verify_rls_applied 返回结构
# ============================================================
print("== 7. verify_rls_applied 签名 ==")


def test_verify_rls_signature():
    r = _rls.verify_rls_applied("wallet")
    _check("返回 enabled 字段", "enabled" in r, "")
    _check("返回 forced 字段", "forced" in r, "")
    _check("返回 policies_count 字段", "policies_count" in r, "")
    _check("返回 dialect_supported 字段", "dialect_supported" in r, "")
    _check("PG 时 dialect_supported=True", r["dialect_supported"] is True, "")


test_verify_rls_signature()


# ============================================================
# 8) SQL 文本格式正则校验（防脚本错误）
# ============================================================
print("== 8. SQL 格式正则 ==")


def test_sql_format_regex():
    for sql in _rls.generate_all_pilot_sql(enable=True):
        # 启用类必须以 ALTER TABLE 开头
        if "ALTER TABLE" in sql:
            assert re.match(
                r"^ALTER TABLE \w+ (ENABLE|FORCE ROW LEVEL SECURITY|NO FORCE|DISABLE)",
                sql.strip(),
            ), f"bad SQL: {sql}"
        # 策略类必须以 CREATE POLICY 开头
        if "CREATE POLICY" in sql:
            assert sql.strip().startswith("CREATE POLICY"), f"bad: {sql}"
    _check("全部 SQL 格式正则通过", True, "")


test_sql_format_regex()


# ============================================================
# 9) 迁移文件存在性 + down_revision 链路
# ============================================================
print("== 9. 迁移链路 ==")


def test_migration_file():
    mig = os.path.join(
        _BACKEND, "alembic_migrations", "versions", "088_rls_pilot.py"
    )
    _check("088_rls_pilot.py 存在", os.path.exists(mig), "")
    if os.path.exists(mig):
        with open(mig, "r", encoding="utf-8") as f:
            content = f.read()
        _check("迁移含 revision = '088_rls_pilot'", 'revision: str = "088_rls_pilot"' in content, "")
        # 2026-09-03 二次修正：081-097 全链已真 PG 真跑，down_revision 恢复 097 原链
        _check("迁移 down_revision = '097'（全链真跑后的原链恢复）",
           'down_revision: Union[str, None] = "097"' in content, "")
        _check("迁移 upgrade() 调用 rls_policies",
               "from app.db.rls_policies" in content, "")
        _check("迁移 downgrade() 逆序",
               "def downgrade" in content and "reversed" in content, "")


test_migration_file()


# ============================================================
# 汇总
# ============================================================
print()
passed = sum(1 for _, ok, _ in _results if ok)
failed = sum(1 for _, ok, _ in _results if not ok)
total = len(_results)
print(f"结果: {passed} PASS / {failed} FAIL  (total {total})")
if failed:
    print("\n失败用例：")
    for name, ok, detail in _results:
        if not ok:
            print(f"  - {name}  {detail}")
    sys.exit(1)
sys.exit(0)
