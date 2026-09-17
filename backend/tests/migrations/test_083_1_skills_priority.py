"""轮18/轮19 §A.2 迁移测试：083_1/083_2 补字段 + 迁移链线性。

不需要真实 DB / pydantic / alembic：以「正则解析迁移文件 revision/down_revision
常量」断言版本图无分支、双向往返描述存在；模型列由 registry_verify 隔离 SQLite 覆盖。
"""

import os
import re

_BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_VERSIONS = os.path.join(_BACKEND, "alembic_migrations", "versions")

_REV_RE = re.compile(r"^revision[^'\"]*['\"]([^'\"]+)['\"]", re.MULTILINE)
_DOWN_RE = re.compile(r"^down_revision[^'\"]*['\"]([^'\"]+)['\"]", re.MULTILINE)
# 本测试只关注注册表→Pipeline 子链；全目录含合法 merge 迁移(元组 down_revision)，
# 不在本次无分支断言范围内。
_CHAIN = {"082", "083", "083_1", "083_2", "087", "090", "091", "094", "095", "096", "097"}


def _load_rev(path: str):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    rev = _REV_RE.search(src).group(1)
    down_m = _DOWN_RE.search(src)
    down = down_m.group(1) if down_m else None
    return rev, down


def _iter_revs():
    for name in sorted(os.listdir(_VERSIONS)):
        if name.startswith("__") or not name.endswith(".py"):
            continue
        path = os.path.join(_VERSIONS, name)
        rev, down = _load_rev(path)
        if rev in _CHAIN:
            yield name, rev, down


def test_083_1_depends_on_083():
    revisions = dict((rev, down) for _, rev, down in _iter_revs())
    assert revisions.get("083_1") == "083", "083_1 必须直接接在 083 之后"
    assert revisions.get("083_2") == "083_1", "083_2 必须直接接在 083_1 之后"
    assert revisions.get("087") == "083_2", "087 必须直接接在 083_2 之后"
    assert revisions.get("090") == "087", "090 必须改指针到 087，保持线性链"


def test_chain_is_linear():
    """无分支判定：任何两个迁移不得共用同一前驱（down_revision 值唯一）。"""
    revisions = dict((rev, down) for _, rev, down in _iter_revs())
    downs = [d for d in revisions.values() if d is not None]
    assert len(downs) == len(set(downs)), f"迁移图存在分支: {downs}"
    assert revisions["083_1"] == "083", "083_1 -> 083"
    assert revisions["083_2"] == "083_1", "083_2 -> 083_1"
    assert revisions["087"] == "083_2", "087 -> 083_2"
    assert revisions["090"] == "087", "090 已被重指 -> 087"
    assert revisions["095"] == "094", "095 -> 094"
    assert revisions["096"] == "095", "096 -> 095"
    assert revisions.get("097") == "096", "依赖链 head=097（计量埋点）"


def test_087_defines_tables():
    """轮20：087 迁移应声明 credentials/credential_grants 双表与 PG CHECK 哨兵。"""
    path = os.path.join(_VERSIONS, "087_credential_vault.py")
    with open(path, encoding="utf-8") as f:
        src = f.read()
    for token in (
        "credentials",
        "credential_grants",
        "aad_fingerprint",
        "crypto_backend",
        "ck_credentials_status",
        "ck_credentials_crypto_backend",
        "ck_credential_grants_status",
        "ix_credentials_tenant_id",
        "ix_credential_grants_credential_id",
    ):
        assert token in src, f"087 迁移缺少哨兵: {token}"


def test_083_1_defines_columns():
    """迁移文件应声明补列与约束（文本哨兵，配合 registry_verify 行为断言）。"""
    path = os.path.join(_VERSIONS, "083_1_skills_priority.py")
    with open(path, encoding="utf-8") as f:
        src = f.read()
    for token in ("priority", "timeout", "retry_count", "retry_delay",
                  "tool_refs_json", "ck_skill_versions_tool_refs_array",
                  "ck_skill_versions_validators_lifecycle"):
        assert token in src, f"083_1 迁移缺少哨兵: {token}"


def test_083_2_defines_columns():
    """轮19：083_2 迁移应声明十字段与 PG 侧 STRICT CHECK 哨兵。"""
    path = os.path.join(_VERSIONS, "083_2_mcp_connector_fields.py")
    with open(path, encoding="utf-8") as f:
        src = f.read()
    for token in (
        "stage", "driver", "approved_hosts_json", "allowed_ports_json",
        "allow_insecure_loopback", "authentication", "oauth_json",
        "credential_fields_json", "max_tools", "manifest_hash",
        "ck_mcp_servers_stage", "ck_mcp_servers_authentication",
        "ck_mcp_servers_max_tools", "ck_mcp_servers_hosts_array",
        "ck_mcp_servers_ports_array",
    ):
        assert token in src, f"083_2 迁移缺少哨兵: {token}"
    assert src.count("sa.Column(") == 10, "083_2 应恰好补 10 列"


def test_096_defines_tables():
    """轮21：096 迁移应声明 task_traces/skill_performance/agent_scorecards 与 stage 补列。"""
    path = os.path.join(_VERSIONS, "096_traces_evolution.py")
    with open(path, encoding="utf-8") as f:
        src = f.read()
    for token in (
        "task_traces", "skill_performance", "agent_scorecards",
        "evolution_experiences", "stage", "prompt_ref", "artifacts",
        "validation_results", "uq_skill_performance_window", "uq_agent_scorecard_key",
    ):
        assert token in src, f"096 迁移缺少哨兵: {token}"
    assert src.count("op.create_table(") == 3, "096 应恰好创建 3 张表"


def test_097_defines_tables():
    """轮22：097 迁移应声明 meter_events（append-only）与 7 类动作/对账哨兵。"""
    path = os.path.join(_VERSIONS, "097_meter_events.py")
    with open(path, encoding="utf-8") as f:
        src = f.read()
    for token in (
        "meter_events", "event_key", "aggregated_at", "occurred_at",
        "ai_generation", "content_publish", "lead_generated", "rfq_created",
        "api_call", "export", "video_job", "uq_meter_events_event_key",
        "ck_meter_events_type",
    ):
        assert token in src, f"097 迁移缺少哨兵: {token}"
    assert src.count("op.create_table(") == 1, "097 应恰好创建 1 张表"


if __name__ == "__main__":
    test_083_1_depends_on_083()
    test_chain_is_linear()
    test_083_1_defines_columns()
    test_083_2_defines_columns()
    test_087_defines_tables()
    test_096_defines_tables()
    test_097_defines_tables()
    print("migration chain tests: ALL PASS")
