"""轮20 Vault + Policy Engine 内存 SQLite 全流程验证脚本（不触碰真实 DB）。

用法：python -m tests.vault_policy_verify
依赖：sqlalchemy + cryptography（已装）；无需 pytest / pydantic / gmssl。

说明：沿用 registry_verify 的 shim 模式——预置假的 app.core.database /
app.core.config，绕开重型依赖，直接从文件加载被测模块。
"""

import os
import sys
import types
import importlib.util

# ---- 预置 app.core.database shim ----
DB_SHIM = types.ModuleType("app.core.database")

from sqlalchemy import String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class _Base(DeclarativeBase):
    pass


DB_SHIM.Base = _Base
DB_SHIM.UUID_TYPE = String(36)
sys.modules["app.core.database"] = DB_SHIM

# ---- 预置 app.core.config shim（vault crypto 的 SECRET_KEY 来源）----
CFG_SHIM = types.ModuleType("app.core.config")


class _FakeSettings:
    SECRET_KEY = "vault-policy-verify-secret-key-2026"
    MODEL_GATEWAY_ENABLED = False


CFG_SHIM.settings = _FakeSettings()
sys.modules["app.core.config"] = CFG_SHIM

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _new_dummy(mod_name: str) -> types.ModuleType:
    mod = types.ModuleType(mod_name)
    mod.__path__ = []
    sys.modules[mod_name] = mod
    return mod


def _load_from_file(mod_name: str, path: str):
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODELS = os.path.join(_BACKEND, "app", "models")

for _pkg in (
    "app",
    "app.core",
    "app.models",
    "app.services",
    "app.services.vault",
    "app.services.policy",
    "app.services.paperclip",
    "app.services.registry",
):
    _new_dummy(_pkg)

_vault_models = _load_from_file(
    "app.models.vault", os.path.join(_MODELS, "vault.py")
)
_gm_crypto = _load_from_file(
    "app.core.gm_crypto", os.path.join(_BACKEND, "app", "core", "gm_crypto.py")
)
_paperclip_models = _load_from_file(
    "app.models.paperclip", os.path.join(_MODELS, "paperclip.py")
)
_registry_models = _load_from_file(
    "app.models.registry", os.path.join(_MODELS, "registry.py")
)

_crypto = _load_from_file(
    "app.services.vault.crypto",
    os.path.join(_BACKEND, "app", "services", "vault", "crypto.py"),
)
_cred_svc = _load_from_file(
    "app.services.vault.credential_service",
    os.path.join(_BACKEND, "app", "services", "vault", "credential_service.py"),
)
_policy = _load_from_file(
    "app.services.policy.engine",
    os.path.join(_BACKEND, "app", "services", "policy", "engine.py"),
)
_budget_guard = _load_from_file(
    "app.services.paperclip.budget_guard",
    os.path.join(_BACKEND, "app", "services", "paperclip", "budget_guard.py"),
)
_approval_gate = _load_from_file(
    "app.services.paperclip.approval_gate",
    os.path.join(_BACKEND, "app", "services", "paperclip", "approval_gate.py"),
)
_orchestrator = _load_from_file(
    "app.services.paperclip.orchestrator",
    os.path.join(_BACKEND, "app", "services", "paperclip", "orchestrator.py"),
)

VaultCredential = _vault_models.VaultCredential
CredentialGrant = _vault_models.CredentialGrant
PaperclipCompany = _paperclip_models.PaperclipCompany
PaperclipAgent = _paperclip_models.PaperclipAgent
PaperclipApproval = _paperclip_models.PaperclipApproval
DataSourceProvider = _registry_models.DataSourceProvider

CredentialVaultService = _cred_svc.CredentialVaultService
VaultError = _cred_svc.VaultError
CredentialNotFoundError = _cred_svc.CredentialNotFoundError
CredentialRevokedError = _cred_svc.CredentialRevokedError
GrantDeniedError = _cred_svc.GrantDeniedError
make_vault_ref = _cred_svc.make_vault_ref
parse_vault_ref = _cred_svc.parse_vault_ref

AadMismatchError = _crypto.AadMismatchError
VaultCryptoError = _crypto.VaultCryptoError
aad_fingerprint = _crypto.aad_fingerprint

PolicyEngine = _policy.PolicyEngine
evaluate_action = _policy.evaluate_action

Base = DB_SHIM.Base

PASS = 0
FAIL = 0

from sqlalchemy.orm import mapped_column  # noqa: E402


class TenantShim(Base):
    """外部依赖表 tenants（vault/paperclip/registry 模型 ForeignKey 解析用）。"""

    __tablename__ = "tenants"
    id = mapped_column(String(36), primary_key=True)


class UserShim(Base):
    """外部依赖表 users（paperclip_approvals.reviewer_id FK 解析用）。"""

    __tablename__ = "users"
    id = mapped_column(String(36), primary_key=True)


class DeerflowJobShim(Base):
    """外部依赖表 deerflow_jobs（paperclip_tasks.deerflow_job_id FK 解析用）。"""

    __tablename__ = "deerflow_jobs"
    id = mapped_column(String(36), primary_key=True)


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} {detail}")


def expect_raise(label: str, exc_type, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc_type:
        check(label, True)
    except Exception as e:  # noqa: BLE001
        check(label, False, f"抛出 {type(e).__name__}: {e}")
    else:
        check(label, False, "未抛异常")


def main() -> int:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    tenant_a = "11111111-1111-1111-1111-111111111111"
    tenant_b = "22222222-2222-2222-2222-222222222222"

    print("== 1. crypto 层 ==")
    s = _crypto.aad_string(tenant_a, "agent", "ag1", "email", "conn1", "api_key")
    check("aad_string 六段拼接", s.count(_crypto.AAD_SEP) == 5)
    fp1 = aad_fingerprint(tenant_a, "agent", "ag1", "email", "conn1", "api_key")
    fp2 = aad_fingerprint(tenant_a, "agent", "ag1", "email", "conn1", "api_key")
    check("指纹稳定", fp1 == fp2 and len(fp1) == 64)
    check(
        "指纹对租户敏感",
        aad_fingerprint(tenant_b, "agent", "ag1", "email", "conn1", "api_key") != fp1,
    )
    check(
        "指纹对工件敏感",
        aad_fingerprint(tenant_a, "agent", "ag1", "email", "conn1", "password") != fp1,
    )
    ct = _crypto.encrypt_with_aad("secret-value", s, "aes_gcm")
    check("aes_gcm 加密往返", _crypto.decrypt_with_aad(ct, s, "aes_gcm") == "secret-value")
    expect_raise(
        "aes_gcm 错 AAD → AadMismatchError",
        AadMismatchError,
        _crypto.decrypt_with_aad,
        ct,
        _crypto.aad_string(tenant_b, "agent", "ag1", "email", "conn1", "api_key"),
        "aes_gcm",
    )
    expect_raise(
        "未知后端拒绝",
        VaultCryptoError,
        _crypto.encrypt_with_aad,
        "x",
        s,
        "des",
    )
    try:
        import gmssl  # noqa: F401
        has_gmssl = True
    except ImportError:
        has_gmssl = False
    if not has_gmssl:
        expect_raise(
            "sm4 未装 gmssl 显式请求 → 报错（可启动不崩）",
            Exception,
            _crypto.encrypt_with_aad,
            "x",
            s,
            "sm4",
        )
        print("  （gmssl 未安装，sm4 后端仅验证降级报错；生产按 VAULT_CRYPTO_BACKEND 切换）")

    print("== 2. vault 服务：存/取/AAD 绑定 ==")
    vault = CredentialVaultService(db)
    cred = vault.store_credential(
        secret="sk-live-abcdef",
        tenant_id=tenant_a,
        owner_type="agent",
        owner_id="ag-001",
        connection_type="email",
        connection_id="conn-77",
        artifact_type="api_key",
        name="mailgun-key",
    )
    check("store 落行 status=active", cred.status == "active")
    check("store 后端=aes_gcm", cred.crypto_backend == "aes_gcm")
    check("密文非明文", "sk-live-abcdef" not in cred.ciphertext)
    ref = make_vault_ref(str(cred.id))
    check("vault_ref 格式", ref.startswith("vault://credential/") and str(cred.id) in ref)
    check("parse_vault_ref 往返", parse_vault_ref(ref) == str(cred.id))
    expect_raise("坏 ref 格式拒绝", VaultError, parse_vault_ref, "plaintext-secret")

    ctx = dict(
        tenant_id=tenant_a,
        owner_type="agent",
        owner_id="ag-001",
        connection_type="email",
        connection_id="conn-77",
        artifact_type="api_key",
    )
    check(
        "正确上下文解密",
        vault.resolve_credential(ref, **ctx) == "sk-live-abcdef",
    )
    check("last_used_at 回写", cred.last_used_at is not None)

    bad_tenant = dict(ctx, tenant_id=tenant_b)
    expect_raise("错租户拒绝", AadMismatchError, vault.resolve_credential, ref, **bad_tenant)
    bad_owner = dict(ctx, owner_id="ag-999")
    expect_raise("错属主拒绝", AadMismatchError, vault.resolve_credential, ref, **bad_owner)
    bad_conn = dict(ctx, connection_id="conn-88")
    expect_raise("错连接拒绝", AadMismatchError, vault.resolve_credential, ref, **bad_conn)
    bad_artifact = dict(ctx, artifact_type="password")
    expect_raise("错工件拒绝", AadMismatchError, vault.resolve_credential, ref, **bad_artifact)
    check("裸 ID 也可解析", vault.resolve_credential(str(cred.id), **ctx) == "sk-live-abcdef")

    expect_raise(
        "非法 owner_type",
        VaultError,
        vault.store_credential,
        secret="x",
        tenant_id=tenant_a,
        owner_type="hacker",
        owner_id="a",
        connection_type="email",
        artifact_type="api_key",
        name="n",
    )
    expect_raise(
        "非法 connection_type",
        VaultError,
        vault.store_credential,
        secret="x",
        tenant_id=tenant_a,
        owner_type="agent",
        owner_id="a",
        connection_type="telepathy",
        artifact_type="api_key",
        name="n",
    )

    print("== 3. vault 服务：授权关系 ==")
    grant = vault.grant_access(ref, grantee_type="skill", grantee_id="skill-x", granted_by="u1")
    check("grant 落行 active", grant.status == "active")
    check(
        "被授权 grantee 可读",
        vault.resolve_credential(ref, **ctx, grantee_type="skill", grantee_id="skill-x")
        == "sk-live-abcdef",
    )
    expect_raise(
        "未授权 grantee 拒绝",
        GrantDeniedError,
        vault.resolve_credential,
        ref,
        **dict(ctx, grantee_type="agent", grantee_id="ag-777"),
    )
    from datetime import datetime, timedelta, timezone as _tz

    expired_grant = vault.grant_access(
        ref,
        grantee_type="service",
        grantee_id="svc-old",
        expires_at=datetime.now(_tz.utc) - timedelta(hours=1),
    )
    expect_raise(
        "过期 grant 无效",
        GrantDeniedError,
        vault.resolve_credential,
        ref,
        **dict(ctx, grantee_type="service", grantee_id="svc-old"),
    )
    vault.revoke_grant(str(grant.id))
    expect_raise(
        "revoke 后拒绝",
        GrantDeniedError,
        vault.resolve_credential,
        ref,
        **dict(ctx, grantee_type="skill", grantee_id="skill-x"),
    )

    print("== 4. vault 服务：轮换/吊销/过期 ==")
    new_cred = vault.rotate_credential(ref, new_secret="sk-live-newkey")
    check("旧凭证 status=rotated", cred.status == "rotated")
    check("新凭证解密新值", vault.resolve_credential(make_vault_ref(str(new_cred.id)), **ctx) == "sk-live-newkey")
    check("新凭证 rotated_from 指向旧", str(new_cred.rotated_from_id) == str(cred.id))
    expect_raise("轮换后旧凭证不可用", CredentialRevokedError, vault.resolve_credential, ref, **ctx)

    rot_grant = vault.grant_access(
        make_vault_ref(str(new_cred.id)), grantee_type="skill", grantee_id="skill-y"
    )
    rot2 = vault.rotate_credential(make_vault_ref(str(new_cred.id)), new_secret="sk-live-3rd")
    check(
        "轮换平移授权",
        vault.resolve_credential(
            make_vault_ref(str(rot2.id)), **ctx, grantee_type="skill", grantee_id="skill-y"
        )
        == "sk-live-3rd",
    )

    vault.revoke_credential(make_vault_ref(str(rot2.id)))
    check("吊销 status=revoked", rot2.status == "revoked")
    expect_raise(
        "吊销后不可解析",
        CredentialRevokedError,
        vault.resolve_credential,
        make_vault_ref(str(rot2.id)),
        **ctx,
    )

    exp_cred = vault.store_credential(
        secret="short-lived",
        tenant_id=tenant_a,
        owner_type="agent",
        owner_id="ag-002",
        connection_type="api",
        connection_id="",
        artifact_type="api_token",
        name="tmp",
        expires_at=datetime.now(_tz.utc) - timedelta(minutes=1),
    )
    expect_raise(
        "过期凭证拒绝",
        CredentialRevokedError,
        vault.resolve_credential,
        make_vault_ref(str(exp_cred.id)),
        tenant_id=tenant_a,
        owner_type="agent",
        owner_id="ag-002",
        connection_type="api",
        connection_id="",
        artifact_type="api_token",
    )
    expect_raise(
        "不存在凭证",
        CredentialNotFoundError,
        vault.resolve_credential,
        "vault://credential/00000000-0000-0000-0000-000000000000",
        **dict(ctx, owner_id="ag-002"),
    )

    print("== 5. Policy Engine 四维裁决 ==")
    engine = PolicyEngine()

    d = engine.evaluate(db, action="raw_shell")
    check("Hermes 禁用动作 deny", d.decision == "deny" and "forbidden" in d.reasons[0])

    d = engine.evaluate(db, action="email.send_campaign", context={"local_hour": 23})
    check("营销动作×安静时段 deny", d.decision == "deny" and "quiet_hours" in d.reasons[0])
    d = engine.evaluate(db, action="email.send_campaign", context={"local_hour": 10})
    check("营销动作×白天 allow", d.decision == "allow")
    d = engine.evaluate(
        db, action="whatsapp.send_marketing", context={"local_hour": 3}
    )
    check("跨午夜窗口(凌晨3点) deny", d.decision == "deny")
    d = engine.evaluate(
        db, action="email.send_campaign", context={"local_hour": 23, "skip_quiet_hours": True}
    )
    check("skip_quiet_hours 豁免", d.decision == "allow")
    d = engine.evaluate(db, action="report.generate")
    check("普通动作 allow", d.decision == "allow")

    # 配额维度（budget_guard）
    company = PaperclipCompany(tenant_id=tenant_a, name="co", mission="")
    db.add(company)
    db.commit()
    db.refresh(company)
    agent_ok = PaperclipAgent(
        company_id=company.id, name="a-ok", monthly_budget_credits=100.0, used_credits=10.0
    )
    agent_alert = PaperclipAgent(
        company_id=company.id, name="a-warn", monthly_budget_credits=100.0, used_credits=85.0
    )
    agent_dead = PaperclipAgent(
        company_id=company.id, name="a-dead", monthly_budget_credits=100.0, used_credits=100.0
    )
    for a in (agent_ok, agent_alert, agent_dead):
        db.add(a)
    db.commit()
    db.refresh(agent_ok)
    db.refresh(agent_alert)
    db.refresh(agent_dead)

    d = engine.evaluate(db, action="paperclip.task_execute", agent_id=str(agent_ok.id))
    check("预算充足 → require_approval（人审优先于无配额问题）", d.decision == "require_approval")
    d = engine.evaluate(db, action="report.generate", agent_id=str(agent_alert.id))
    check("预算 85% → warn", d.decision == "warn" and any("budget_alert" in r for r in d.reasons))
    d = engine.evaluate(db, action="report.generate", agent_id=str(agent_dead.id))
    check("预算耗尽 → deny", d.decision == "deny" and any("budget" in r for r in d.reasons))

    # 人审维度
    d = engine.evaluate(
        db,
        action="paperclip.hire_agent",
        company_id=str(company.id),
        context={
            "approval_action_type": "hire_agent",
            "payload": {"name": "T"},
            "agent_id": None,
        },
    )
    check("hire → require_approval", d.decision == "require_approval")
    check("审批单已建", d.approval_id is not None)
    approval_row = (
        db.query(PaperclipApproval).filter(PaperclipApproval.id == d.approval_id).first()
    )
    check(
        "审批单 action_type=hire_agent",
        approval_row is not None and approval_row.action_type == "hire_agent",
    )
    d = engine.evaluate(
        db, action="paperclip.fire_agent", company_id=str(company.id), auto_create_approval=False
    )
    check("auto_create_approval=False → 无审批单", d.decision == "require_approval" and d.approval_id is None)

    # 合规维度：数据源评审门
    d = engine.evaluate(db, action="datasource.enable", context={})
    check("数据源启用无 provider → deny", d.decision == "deny")
    prov_pending = DataSourceProvider(
        name="p-pending", data_class="public_corporate",
        license_basis="official_api", tos_verified=True, review_status="pending",
    )
    prov_ok = DataSourceProvider(
        name="p-ok", data_class="public_corporate",
        license_basis="official_api", tos_verified=True, review_status="approved",
    )
    db.add_all([prov_pending, prov_ok])
    db.commit()
    db.refresh(prov_pending)
    db.refresh(prov_ok)
    d = engine.evaluate(
        db, action="datasource.enable", context={"data_provider_id": str(prov_pending.id)}
    )
    check("评审 pending → deny", d.decision == "deny" and "not_approved" in d.reasons[0])
    d = engine.evaluate(
        db,
        action="datasource.enable",
        company_id=str(company.id),
        context={"data_provider_id": str(prov_ok.id)},
    )
    check("评审 approved → require_approval", d.decision == "require_approval")

    print("== 6. orchestrator 接线（行为兼容）==")
    result = _orchestrator.hire_agent(
        db, company_id=str(company.id), name="R2D2", title="droid", budget=500.0
    )
    check(
        "hire 经 policy 返回 pending_approval",
        result.get("status") == "pending_approval" and result.get("approval_id"),
    )
    wired = (
        db.query(PaperclipApproval)
        .filter(
            PaperclipApproval.id == result["approval_id"],
            PaperclipApproval.action_type == "hire_agent",
        )
        .first()
    )
    check("接线后审批单 action_type 兼容", wired is not None)
    import json as _json

    wired_payload = _json.loads(wired.action_payload_json or "{}")
    check(
        "接线后 payload 含 budget",
        wired_payload.get("monthly_budget_credits") == 500.0,
    )

    # 审批通过 → 自动创建 Agent（approval_gate 既有链路不回归）
    before = db.query(PaperclipAgent).count()
    _approval_gate.approve(db, wired.id, reviewer_id="u-reviewer")
    check("审批通过自动建 Agent", db.query(PaperclipAgent).count() == before + 1)
    new_agent = (
        db.query(PaperclipApproval)
        .filter(PaperclipApproval.id == wired.id)
        .first()
    )
    check("审批单状态 approved", new_agent.status == "approved")

    hire_result_agent = (
        db.query(PaperclipAgent).filter(PaperclipAgent.name == "R2D2").first()
    )
    check("Agent 名字来自 payload", hire_result_agent is not None)

    fire_result = _orchestrator.fire_agent(db, str(hire_result_agent.id))
    check(
        "fire 经 policy 返回 pending_approval",
        fire_result.get("status") == "pending_approval" and fire_result.get("approval_id"),
    )
    fire_approval = (
        db.query(PaperclipApproval)
        .filter(PaperclipApproval.id == fire_result["approval_id"])
        .first()
    )
    check("fire 审批 action_type=fire_agent", fire_approval.action_type == "fire_agent")

    print("== 7. mcp_service vault_ref 红线 ==")
    _common_mod = _load_from_file(
        "app.services.registry.common",
        os.path.join(_BACKEND, "app", "services", "registry", "common.py"),
    )
    _mcp_svc = _load_from_file(
        "app.services.registry.mcp_service",
        os.path.join(_BACKEND, "app", "services", "registry", "mcp_service.py"),
    )
    build_mcp_service = _mcp_svc.build_mcp_service
    mcp = build_mcp_service(db)
    expect_raise(
        "明文密钥 vault_ref 拒绝",
        ValueError,
        mcp.register_server,
        name="bad-secret",
        credential_vault_ref="sk-plaintext-nope",
    )
    ok_server = mcp.register_server(
        name="vault-ok", credential_vault_ref=f"vault://credential/{cred.id}"
    )
    check("合法 vault_ref 可注册", ok_server.name == "vault-ok")

    print()
    print(f"vault_policy_verify: {PASS} PASS / {FAIL} FAIL")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
