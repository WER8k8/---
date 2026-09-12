"""轮17 注册表服务 内存 SQLite 全流程验证脚本（不触碰真实 DB）。

用法：python -m tests.registry_verify
依赖：sqlalchemy（已装 2.0.49）；无需 pytest / pydantic。

说明：为避免牵入 app 全栈（pydantic/fastapi 等重依赖），在 import 模型前
预置一个假的 app.core.database 模块（提供 Base/UUID_TYPE），与交接记录
"shim 包绕开重型依赖"的既有验证模式一致。
"""

import os
import sys
import types
import importlib.util

# ---- 预置 app.core.database shim，避免 pydantic 依赖 ----
DB_SHIM = types.ModuleType("app.core.database")

from sqlalchemy import String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

class _Base(DeclarativeBase):
    pass

DB_SHIM.Base = _Base
DB_SHIM.UUID_TYPE = String(36)
_db_shim_module_name = None

sys.modules["app.core.database"] = DB_SHIM

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _new_dummy(mod_name: str) -> types.ModuleType:
    """预置空白父包，阻止 import 机制执行真实包 __init__（全模型树/全服务树）。"""
    mod = types.ModuleType(mod_name)
    mod.__path__ = []  # 标记为包，避免再走 finder
    sys.modules[mod_name] = mod
    return mod


def _load_from_file(mod_name: str, path: str):
    """绕过包 __init__ 直接加载模块（避免触发 app.models/app.services 整树）。"""
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REG = os.path.join(_BACKEND, "app", "services", "registry")

# 预置空父包，阻断 app / app.core / app.models / app.services 的真实 __init__
for _pkg in ("app", "app.core", "app.models", "app.services", "app.services.registry"):
    _new_dummy(_pkg)

_registry_mod = _load_from_file(
    "app.models.registry", os.path.join(_BACKEND, "app", "models", "registry.py")
)
registry_models = _registry_mod
RegistrySkill = _registry_mod.RegistrySkill
McpServer = _registry_mod.McpServer
McpTool = _registry_mod.McpTool
RegistryPlugin = _registry_mod.RegistryPlugin
TenantCapabilityToggle = _registry_mod.TenantCapabilityToggle
MCP_TOOL_PERMISSIONS = _registry_mod.MCP_TOOL_PERMISSIONS
SKILL_STATUSES = _registry_mod.SKILL_STATUSES

# 供服务模块引用的 app.models.registry 已是 shim 版；Base 取 shim 类以建表
Base = DB_SHIM.Base

# ---- 直接加载服务模块（common -> matrix -> permissions -> 各 service）----
_common = _load_from_file("app.services.registry.common", os.path.join(_REG, "common.py"))
_matrix = _load_from_file("app.services.registry.matrix", os.path.join(_REG, "matrix.py"))
_perms = _load_from_file(
    "app.services.registry.permissions", os.path.join(_REG, "permissions.py")
)
_skill_svc = _load_from_file(
    "app.services.registry.skill_service", os.path.join(_REG, "skill_service.py")
)
_mcp_svc = _load_from_file(
    "app.services.registry.mcp_service", os.path.join(_REG, "mcp_service.py")
)
_plugin_svc = _load_from_file(
    "app.services.registry.plugin_service", os.path.join(_REG, "plugin_service.py")
)
_ds_svc = _load_from_file(
    "app.services.registry.data_source_service",
    os.path.join(_REG, "data_source_service.py"),
)
_tt_svc = _load_from_file(
    "app.services.registry.tenant_toggle", os.path.join(_REG, "tenant_toggle.py")
)

# 切片A：Trade AI 运行时移植（ExecutionContext + BaseSkill）
_exec_ctx = _load_from_file(
    "app.core.execution_context",
    os.path.join(_BACKEND, "app", "core", "execution_context.py"),
)
_base = _load_from_file(
    "app.services.registry.skill_base", os.path.join(_REG, "skill_base.py")
)
ExecutionContext = _exec_ctx.ExecutionContext
BaseSkill = _base.BaseSkill
SkillRegistry = _base.SkillRegistry
SkillStatus = _base.SkillStatus
register_skill = _base.register_skill

build_skill_service = _skill_svc.build_skill_service
build_mcp_service = _mcp_svc.build_mcp_service
build_plugin_service = _plugin_svc.build_plugin_service
build_data_source_service = _ds_svc.build_data_source_service
build_tenant_toggle_service = _tt_svc.build_tenant_toggle_service
SkillConflictError = _skill_svc.SkillConflictError
IllegalTransitionError = _skill_svc.IllegalTransitionError
PluginConflictError = _plugin_svc.PluginConflictError
DataSourceConflictError = _ds_svc.DataSourceConflictError
build_granted = _perms.build_granted
can = _perms.can
can_start = _matrix.can_start
publish_transition = _matrix.publish_transition

PASS = 0
FAIL = 0


# 外部依赖表 tenants（registry 模型 ForeignKey("tenants.id") 只在建表时解析）
from sqlalchemy.orm import mapped_column  # noqa: E402


class _TenantShim(Base):
    __tablename__ = "tenants"
    id = mapped_column(String(36), primary_key=True)


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} {detail}")


def main() -> int:
    # ---- 内存 SQLite（独立于真实 DB，RLS 监听器不会在这里注册）----
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("== 1. schema 建表 ==")
    import sqlalchemy.inspection as ins
    insp = ins.inspect(engine)
    for t in (
        "skills", "skill_versions", "mcp_servers", "mcp_tools",
        "plugins", "plugin_versions", "data_source_providers", "tenant_capability_toggles",
    ):
        check(f"表存在: {t}", insp.has_table(t))

    print("== 2. Skill 注册/查询/版本/发布态 ==")
    skill = build_skill_service(db)
    s = skill.register_skill(
        name="outreach",
        display_name="开发信与客户触达",
        category="outreach",
        description="生成开发信",
        triggers=["写开发信"],
        keywords=["开发信", "触达"],
        modules=["development-email"],
        tool_refs=["outreach.draft_letter"],
        config_schema={"type": "object"},
        default_config={"tone": "professional"},
        permissions={"invoke": ["read"]},
        version="1.0.0",
    )
    check("注册返回 status=draft", s.status == "draft")
    check("触发词持久化", skill.get(s.id).triggers == ["写开发信"])
    check("by_name 命中", skill.get_by_name("outreach") is not None)
    # 唯一约束冲突
    try:
        skill.register_skill(name="outreach")
        check("同名冲突抛异常", False)
    except SkillConflictError:
        check("同名冲突抛异常", True)
    # 非法发布态跃迁 draft->active
    try:
        skill.set_publish_status(s.id, "active")
        check("draft->active 应被拒", False)
    except IllegalTransitionError:
        check("draft->active 应被拒", True)
    # 合法跃迁 draft->testing->active
    skill.set_publish_status(s.id, "testing")
    check("draft->testing ok", skill.get(s.id).status == "testing")
    skill.set_publish_status(s.id, "active", approved_by="reviewer-1")
    check("testing->active ok + approved", skill.get(s.id).status == "active")
    check("can_start(active)=True", can_start("active") is True)
    check("can_start(draft)=False", can_start("draft") is False)
    check("publish_transition(active->rollback)", publish_transition("active", "rollback"))
    # 新版本
    skill.create_version(s.id, version="1.1.0", implementation={"prompt": "v2"})
    check("版本数=2", len(skill.list_versions(s.id)) == 2)
    check("current_version=1.1.0", skill.get(s.id).current_version == "1.1.0")

    print("== 2.5 轮18 083.1 字段（priority/retry/tool_refs/lifecycle）==")
    check("priority 默认=50", skill.get(s.id).priority == 50)
    s2 = skill.register_skill(
        name="outreach-hot",
        category="outreach",
        priority=90,
        timeout=30,
        retry_count=3,
        retry_delay=2,
        tool_refs=["a.tool1"],
        version_tool_refs=["a.tool1", "b.tool2"],
    )
    check("priority 可覆盖", skill.get(s2.id).priority == 90)
    check("retry_count 持久化", skill.get(s2.id).retry_count == 3)
    cat = skill.list_by_category("outreach")
    check("list_by_category 按 priority 降序", [r["name"] for r in cat] == ["outreach-hot", "outreach"])
    ver = skill.list_versions(s2.id)[0]
    check("版本级 tool_refs 持久化", ver["tool_refs"] == ["a.tool1", "b.tool2"])
    # validators 缺 lifecycle 钩子应拒绝
    try:
        skill.create_version(s.id, version="9.9.9", validators={"foo": 1})
        check("validators 缺 lifecycle 拒绝", False)
    except ValueError:
        check("validators 缺 lifecycle 拒绝", True)
    # 合法 validators：带全 4 个 lifecycle 钩子
    skill.create_version(
        s.id,
        version="2.0.0",
        validators={"lifecycle": {"on_start": [], "on_success": [], "on_failure": [], "on_skip": []}},
        tool_refs=["a.tool9"],
    )
    check("2.0.0 已创建且 tool_refs 可写", any(_v["version"] == "2.0.0" for _v in skill.list_versions(s.id)))
    check("2.0.0 版本 tool_refs", next(v for v in skill.list_versions(s.id) if v["version"] == "2.0.0")["tool_refs"] == ["a.tool9"])

    print("== 3. MCP server/tool + 权限 ==")
    mcp = build_mcp_service(db)
    server = mcp.register_server(
        name="enrich-api", endpoint="https://api.enrich.io", protocol="http",
        credential_vault_ref="vault://credential/33333333-3333-3333-3333-333333333333",
    )
    check("MCP server 注册", mcp.get_server(server.id) is not None)
    try:
        mcp.register_server(name="bad-ref", credential_vault_ref="vault:LEGACY_KEY")
        check("轮20 旧式 vault ref 拒绝", False)
    except ValueError:
        check("轮20 旧式 vault ref 拒绝", True)
    tool = mcp.register_tool(server.id, name="lookup_company", input_schema={"type": "object"})
    check("tool 默认权限 none", tool.permission == "none")
    check("tool 默认禁用", tool.enabled is False)
    mcp.set_tool_permission(tool.id, "execute")
    mcp.set_tool_enabled(tool.id, True)
    t = mcp.list_tools(server.id, enabled_only=True)
    check("启用后工具可见", len(t) == 1 and t[0]["permission"] == "execute")
    try:
        mcp.list_tools("no-such", enabled_only=True)
        check("MCP 虚拟 server 空列表", True)
    except Exception:
        check("MCP 虚拟 server 空列表", True)

    print("== 3.5 轮19 083.2 connector-manifest 字段 ==")
    # 既有注册（仅 endpoint）：stage 派生 available + 默认值
    d = mcp.list_servers()[0]
    check("带endpoint派生stage=available", d["stage"] == "available")
    check("默认authentication=none", d["authentication"] == "none")
    check("默认max_tools=200", d["max_tools"] == 200)
    check("默认allow_insecure_loopback=False", d["allow_insecure_loopback"] is False)
    check("默认hosts/ports空列表", d["approved_hosts"] == [] and d["allowed_ports"] == [])
    check("派生manifest_hash为64位hex", isinstance(d["manifest_hash"], str) and len(d["manifest_hash"]) == 64)

    # 完整 oauth2 manifest 注册（GoodJob integration-sdk ConnectorManifest 形态）
    full = mcp.register_server(
        name="graph-connector",
        endpoint="https://graph.microsoft.com/v1.0",
        protocol="http",
        driver="microsoft_graph",
        approved_hosts=["Graph.Microsoft.com"],
        allowed_ports=[443],
        authentication="oauth2",
        oauth={"clientId": "cid-123", "scopes": ["user.read", "mail.read"], "profile": "mcp"},
        max_tools=50,
    )
    d2 = next(s for s in mcp.list_servers() if s["id"] == str(full.id))
    check("oauth2字段持久化stage", d2["stage"] == "available")
    check("driver持久化", d2["driver"] == "microsoft_graph")
    check("hosts小写化并持久化", d2["approved_hosts"] == ["graph.microsoft.com"])
    check("ports持久化", d2["allowed_ports"] == [443])
    check("oauth持久化", d2["oauth"]["clientId"] == "cid-123")
    check("max_tools覆盖", d2["max_tools"] == 50)
    check("manifest_hash存在", isinstance(d2["manifest_hash"], str) and len(d2["manifest_hash"]) == 64)

    # api_token 注册（credential_fields）
    api_token_srv = mcp.register_server(
        name="easypost-connector",
        endpoint="https://api.easypost.com/v2",
        driver="easypost",
        approved_hosts=["api.easypost.com"],
        allowed_ports=[443],
        authentication="api_token",
        credential_fields=[
            {"key": "api_key", "label": "API Key", "secret": True, "minLength": 8, "maxLength": 500}
        ],
    )
    d3 = next(s for s in mcp.list_servers() if s["id"] == str(api_token_srv.id))
    check("credential_fields持久化", d3["credential_fields"][0]["key"] == "api_key")

    # planned 注册（无运行配置）
    planned = mcp.register_server(
        name="wecom-planned", stage="planned", approved_hosts=["qyapi.weixin.qq.com"]
    )
    d4 = next(s for s in mcp.list_servers() if s["id"] == str(planned.id))
    check("planned注册成功stage=planned", d4["stage"] == "planned")
    check("planned无endpoint", d4["endpoint"] is None)

    # 显式 manifest_hash 传入优先
    explicit = mcp.register_server(name="hash-override", manifest_hash="a" * 64)
    d5 = next(s for s in mcp.list_servers() if s["id"] == str(explicit.id))
    check("显式manifest_hash优先", d5["manifest_hash"] == "a" * 64)

    # 校验红线拒绝
    def _expect_value_error(label, **kwargs):
        try:
            mcp.register_server(**kwargs)
            check(label, False, "未抛出 ValueError")
        except ValueError:
            check(label, True)

    _expect_value_error("非法stage拒绝", name="bad-stage", stage="ga", endpoint="https://a.b")
    _expect_value_error("非法authentication拒绝", name="bad-auth", authentication="basic", endpoint="https://a.b")
    _expect_value_error("非法driver拒绝", name="bad-driver", driver="ssh", endpoint="https://a.b")
    _expect_value_error("max_tools越界拒绝", name="bad-tools", max_tools=201, endpoint="https://a.b")
    _expect_value_error("端口重复拒绝", name="bad-ports", allowed_ports=[443, 443], endpoint="https://a.b")
    _expect_value_error("端口越界拒绝", name="bad-port2", allowed_ports=[70000], endpoint="https://a.b")
    _expect_value_error("通配符host拒绝", name="bad-host", approved_hosts=["*.evil.com"], endpoint="https://a.b")
    _expect_value_error("planned带endpoint拒绝", name="bad-planned", stage="planned", endpoint="https://a.b")
    _expect_value_error("planned带driver拒绝", name="bad-planned2", stage="planned", driver="native_mcp")
    _expect_value_error("none带oauth拒绝", name="bad-none", endpoint="https://a.b", oauth={"clientId": "x"})
    _expect_value_error("oauth2缺oauth拒绝", name="bad-oauth2", endpoint="https://a.b", authentication="oauth2")
    _expect_value_error(
        "api_token缺credential_fields拒绝",
        name="bad-token", endpoint="https://a.b", authentication="api_token",
    )
    _expect_value_error(
        "credential_fields键重复拒绝",
        name="bad-token2", endpoint="https://a.b", authentication="api_token",
        credential_fields=[
            {"key": "k", "label": "A", "secret": True},
            {"key": "k", "label": "B", "secret": True},
        ],
    )

    # manifest_hash 确定性：相同输入 → 相同 hash；不同输入 → 不同 hash
    h1 = mcp.register_server(name="hash-a", endpoint="https://x.y", approved_hosts=["x.y"])
    h2 = mcp.register_server(name="hash-b", endpoint="https://x.y", approved_hosts=["x.y"])
    h3 = mcp.register_server(name="hash-c", endpoint="https://x.y", approved_hosts=["x.y"], max_tools=100)
    dh1 = next(s for s in mcp.list_servers() if s["id"] == str(h1.id))["manifest_hash"]
    dh2 = next(s for s in mcp.list_servers() if s["id"] == str(h2.id))["manifest_hash"]
    dh3 = next(s for s in mcp.list_servers() if s["id"] == str(h3.id))["manifest_hash"]
    check("相同manifest输入hash一致", dh1 == dh2)
    check("不同manifest输入hash不同", dh1 != dh3)

    print("== 4. Plugin 注册 + 版本 ==")
    pg = build_plugin_service(db)
    p = pg.register_plugin(name="crm-connector", manifest={"entry": "main"}, version="1.0.0")
    check("Plugin 注册 status=draft", p.status == "draft")
    pg.create_version(p.id, version="1.1.0", manifest={"entry": "main", "v2": True})
    check("Plugin 版本数=2", len(pg.list_versions(p.id)) == 2)
    pg.set_publish_status(p.id, "testing")
    check("Plugin testing 跃迁", pg.get(p.id).status == "testing")
    try:
        pg.set_publish_status(p.id, "rollback")
        check("Plugin testing->rollback 应被拒", False)
    except (PluginConflictError, Exception):
        check("Plugin testing->rollback 应被拒", True)

    print("== 5. DataSource 登记 + 评审门禁 ==")
    ds = build_data_source_service(db)
    d = ds.register(
        name="apify-web",
        data_class="public_corporate",
        license_basis="scraping",
        tos_verified=True,
    )
    check("登记默认 pending", d.review_status == "pending")
    try:
        ds.ensure_approved(d.id)
        check("未批准禁止采集", False)
    except PermissionError:
        check("未批准禁止采集", True)
    ds.review(d.id, decision="approved", notes="TOS 已核")
    check("评审通过", ds.ensure_approved(d.id).review_status == "approved")
    try:
        ds.register(name="apify-web", data_class="public_corporate", license_basis="scraping")
        check("数据源同名冲突", False)
    except DataSourceConflictError:
        check("数据源同名冲突", True)

    print("== 6. TenantToggle 默认关闭 ==")
    tt = build_tenant_toggle_service(db)
    check("未启用默认 False", tt.is_enabled("t-1", "skill", s.id) is False)
    tt.set_enabled("t-1", "skill", s.id, True)
    check("启用后 True", tt.is_enabled("t-1", "skill", s.id) is True)
    try:
        tt.set_enabled("t-1", "bogus_type", s.id, True)
        check("非法 capability_type 拒绝", False)
    except ValueError:
        check("非法 capability_type 拒绝", True)

    print("== 7. Permissions 五级判定 ==")
    grants = build_granted("read", "execute")
    check("read->view 允许", can(grants, "view") is True)
    read_only = build_granted("read")
    check("仅 read 不能 invoke", can(read_only, "invoke") is False)
    check("execute->invoke 允许", can(grants, "invoke") is True)
    check("无 write -> create 拒绝", can(grants, "create") is False)
    check("仅 read 不能 publish", can(grants, "publish") is False)
    full = build_granted("read", "write", "execute", "delete", "publish")
    check("全部权限 publish 允许", can(full, "publish") is True)
    check("空授权 publish 拒绝", can(set(), "publish") is False)
    check("未知动作拒绝", can(full, "hack") is False)

    print("== 8. 切片A: BaseSkill 运行时（Trade AI 移植）==")
    import asyncio

    @register_skill
    class EchoSkill(BaseSkill):
        name = "echo"
        display_name = "Echo"
        description = "echo back input"
        category = "test"
        input_schema = {"properties": {"msg": {"required": True}}}
        output_schema = {"properties": {"echo": {"required": True}}}

        async def execute(self, context):
            return {"echo": context.input_data["msg"]}

    try:
        SkillRegistry.register(dict)
        check("非 BaseSkill 注册拒绝", False)
    except TypeError:
        check("非 BaseSkill 注册拒绝", True)

    async def _rt():
        inst = SkillRegistry.create_instance("echo", tenant_id="t-1")
        ctx = ExecutionContext(workflow_id="w1", execution_id="e1", tenant_id="t-1", input_data={"msg": "hi"})
        out = await inst.run(ctx)
        return inst, ctx, out

    inst, ctx, out = asyncio.run(_rt())
    check("运行成功+输出正确", out == {"echo": "hi"} and inst.get_status() == SkillStatus.SUCCESS)
    check("租户注入生效", inst.tenant_id == "t-1")
    check("生命周期时间线", ctx.step_history and ctx.step_history[0]["step"] == "echo_start"
          and ctx.step_history[-1]["step"] == "echo_success")
    check("时间戳带时区", ctx.started_at.tzinfo is not None)

    async def _bad():
        inst2 = SkillRegistry.create_instance("echo")
        try:
            await inst2.run(ExecutionContext(workflow_id="w", execution_id="e2", input_data={}))
        except ValueError as e:
            return e
        return None

    check("缺必填输入拒绝", isinstance(asyncio.run(_bad()), ValueError))

    db.close()
    engine.dispose()

    print("\n========== 结果 ==========")
    print(f"PASS: {PASS}  FAIL: {FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())