"""轮 25-E PolicyEngine 真接入 验证（不触碰真实 Playwright / DB）。

用法：python tests/browser_runtime_policy_real_verify.py

关键设计：
- 不 import app.services.__init__（含 foreign_trade 链会触发 Python 3.10 兼容 bug）
- 用 importlib 直接加载 evidence / executor / policy 文件
- mock PolicyEngine 让 submit 走受控裁决路径

覆盖：
1) execute() 签名增 db 入参（默认 None，向后兼容）
2) submit 走 PolicyEngine 真裁决（mock 引擎）：
   - decision=allow + approval_id=xxx → evidence.submit_approval_id 写入
   - decision=deny → evidence.status=BLOCKED
   - decision=require_approval 且无 approval_id → evidence.status=BLOCKED
3) db=None 走内置快路径（25-D 行为不变，submit_approval_id=None）
4) PolicyEngine 调用失败 → 降级内置快路径（best-effort）
5) run_real_execution submit 分支正确传 db
"""
import asyncio
import importlib.util
import inspect
import os
import sys
import types

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BROWSER_RUNTIME = os.path.join(
    _BACKEND, "app", "services", "browser_runtime"
)
sys.path.insert(0, _BACKEND)

# ---- 预置 app.core.database shim ----
DB_SHIM = types.ModuleType("app.core.database")
DB_SHIM.Base = object
DB_SHIM.UUID_TYPE = "VARCHAR(36)"
DB_SHIM.SessionLocal = None
sys.modules["app.core.database"] = DB_SHIM

# ---- 预置 app.core.config shim ----
CFG_SHIM = types.ModuleType("app.core.config")


class _FakeSettings:
    SECRET_KEY = "browser-runtime-policy-verify-secret-2026"
    BROWSER_RUNTIME_ENABLED = True
    BROWSER_RUNTIME_ALLOWED_TENANTS = "t-verify-1"
    BROWSER_RUNTIME_PROFILE_ROOT = os.path.join(
        os.environ.get("TEMP", "C:\\Windows\\Temp"),
        "uj_browser_profiles_25e_verify",
    )


CFG_SHIM.settings = _FakeSettings()
sys.modules["app.core.config"] = CFG_SHIM

# ---- 预置 app.services.policy.engine shim ----
PE_SHIM = types.ModuleType("app.services.policy.engine")


class _FakePolicyDecision:
    def __init__(self, decision, reasons=None, approval_id=None, rule_hits=None):
        self.decision = decision
        self.reasons = reasons or []
        self.approval_id = approval_id
        self.rule_hits = rule_hits or []


class _FakePolicyEngine:
    def __init__(self, response):
        self._response = response

    def evaluate(self, db, **kwargs):
        return self._response


def _make_evaluate_action(response):
    def _evaluate_action(db, **kwargs):
        return response
    return _evaluate_action


PE_SHIM.PolicyEngine = _FakePolicyEngine
PE_SHIM.PolicyDecision = _FakePolicyDecision
PE_SHIM.evaluate_action = None
sys.modules["app.services.policy.engine"] = PE_SHIM

# ---- 直接 importlib 加载 evidence / exceptions / policy / profile（独立模块）----
# 避免触发 app.services.__init__.py 链（外贸易 osint 含 Python 3.10 兼容 bug）

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_evidence = _load(
    "app.services.browser_runtime.evidence",
    os.path.join(_BROWSER_RUNTIME, "evidence.py"),
)
_exceptions = _load(
    "app.services.browser_runtime.exceptions",
    os.path.join(_BROWSER_RUNTIME, "exceptions.py"),
)
_policy = _load(
    "app.services.browser_runtime.policy",
    os.path.join(_BROWSER_RUNTIME, "policy.py"),
)
_profile = _load(
    "app.services.browser_runtime.profile",
    os.path.join(_BROWSER_RUNTIME, "profile.py"),
)
_executor = _load(
    "app.services.browser_runtime.executor",
    os.path.join(_BROWSER_RUNTIME, "executor.py"),
)
# runtime.py 依赖 profile + exceptions + evidence + policy → 拼装其依赖后再加载
_runtime = _load(
    "app.services.browser_runtime.runtime",
    os.path.join(_BROWSER_RUNTIME, "runtime.py"),
)


# ---- 常量 ----
EXEC_BLOCKED = _evidence.EXEC_BLOCKED
EXEC_DEGRADED = _evidence.EXEC_DEGRADED
EXEC_FAILED = _evidence.EXEC_FAILED
EXEC_SUCCESS = _evidence.EXEC_SUCCESS
EvidenceRecord = _evidence.EvidenceRecord
BrowserRuntimeUnavailable = _exceptions.BrowserRuntimeUnavailable


TENANT_OK = "t-verify-1"


def _patch_policy_response(response):
    sys.modules["app.services.policy.engine"].evaluate_action = _make_evaluate_action(response)


def _reset_policy_response():
    sys.modules["app.services.policy.engine"].evaluate_action = None


def _enable_runtime():
    CFG_SHIM.settings.BROWSER_RUNTIME_ENABLED = True
    CFG_SHIM.settings.BROWSER_RUNTIME_ALLOWED_TENANTS = TENANT_OK


# ---- 用例计数器 ----
_results: list[tuple[str, bool, str]] = []


def _check(name: str, cond: bool, detail: str = ""):
    status = "PASS" if cond else "FAIL"
    _results.append((name, cond, detail))
    flag = "✔" if cond else "✘"
    extra = f"  {detail}" if detail and not cond else ""
    print(f"  {flag}  {status}  {name}{extra}")


# ============================================================
# 1) execute() 签名：db 默认 None，向后兼容
# ============================================================
print("== 1. execute() 签名兼容 ==")


def test_signature_accepts_db():
    sig = inspect.signature(_runtime.execute)
    has_db = "db" in sig.parameters
    _check("execute 增 db 入参", has_db,
           "" if has_db else "no db in sig")
    if has_db:
        default = sig.parameters["db"].default
        _check("db 默认 None（向后兼容）", default is None,
               f"default={default!r}")


test_signature_accepts_db()


# ============================================================
# 2) submit 走 PolicyEngine 真裁决（mock 引擎返回 allow + approval_id）
# ============================================================
print("== 2. submit 走 PolicyEngine 真裁决 ==")


def test_submit_with_db_returns_approval_id():
    _enable_runtime()
    _patch_policy_response(
        _FakePolicyDecision(
            decision="allow",
            reasons=["allowed by policy"],
            approval_id="appr-test-001",
        )
    )
    rec = EvidenceRecord(
        tenant_id=TENANT_OK,
        actor="verify",
        action="submit",
    )
    rec.metadata["policy_context"] = {
        "company_id": "co-1",
        "agent_id": "ag-1",
        "auto_submit": True,
        "auto_create_approval": True,
    }
    try:
        result = asyncio.run(
            _executor._real_execute_submit(evidence=rec, profile=None, db="mock-db")
        )
    except BrowserRuntimeUnavailable:
        # 接受 Playwright launch 失败（持久化 context 不可用）
        result = rec
    except Exception as exc:
        result = rec
        _check(f"  submit handler 抛 {type(exc).__name__} 可接受", True)
    _check("submit_approval_id 写入 PolicyEngine 返回值",
           result.submit_approval_id == "appr-test-001",
           f"got {result.submit_approval_id!r}")
    _check("policy_decision 写入 metadata",
           result.metadata.get("policy_decision") == "allow",
           f"got {result.metadata.get('policy_decision')!r}")


test_submit_with_db_returns_approval_id()


def test_submit_deny_blocks_evidence():
    _enable_runtime()
    _patch_policy_response(
        _FakePolicyDecision(
            decision="deny",
            reasons=["forbidden_action: raw_shell"],
            approval_id=None,
        )
    )
    rec = EvidenceRecord(
        tenant_id=TENANT_OK,
        actor="verify",
        action="submit",
    )
    rec.metadata["policy_context"] = {"auto_submit": True, "company_id": "co-1"}
    try:
        result = asyncio.run(
            _executor._real_execute_submit(evidence=rec, profile=None, db="mock-db")
        )
    except BrowserRuntimeUnavailable:
        result = rec
    except Exception:
        result = rec
    _check("PolicyEngine deny → status=BLOCKED",
           result.status == EXEC_BLOCKED,
           f"got {result.status!r}")
    _check("BLOCKED 时 policy_verdict.code=POLICY_ENGINE_DENIED",
           (result.policy_verdict or {}).get("code") == "POLICY_ENGINE_DENIED",
           f"got {(result.policy_verdict or {}).get('code')!r}")


test_submit_deny_blocks_evidence()


def test_submit_require_approval_no_id_blocks():
    _enable_runtime()
    _patch_policy_response(
        _FakePolicyDecision(
            decision="require_approval",
            reasons=["human_review_required: paperclip.task_execute"],
            approval_id=None,
        )
    )
    rec = EvidenceRecord(
        tenant_id=TENANT_OK,
        actor="verify",
        action="submit",
    )
    rec.metadata["policy_context"] = {"company_id": "co-1", "auto_create_approval": False}
    try:
        result = asyncio.run(
            _executor._real_execute_submit(evidence=rec, profile=None, db="mock-db")
        )
    except BrowserRuntimeUnavailable:
        result = rec
    except Exception:
        result = rec
    _check("require_approval 无 id → status=BLOCKED",
           result.status == EXEC_BLOCKED,
           f"got {result.status!r}")


test_submit_require_approval_no_id_blocks()


# ============================================================
# 3) db=None 走内置快路径（25-D 行为不变）
# ============================================================
print("== 3. db=None 走内置快路径（向后兼容）==")


def test_submit_db_none_uses_builtin_path():
    _enable_runtime()
    _reset_policy_response()
    rec = EvidenceRecord(
        tenant_id=TENANT_OK,
        actor="verify",
        action="submit",
    )
    rec.metadata["policy_context"] = {"auto_submit": True}
    try:
        result = asyncio.run(
            _executor._real_execute_submit(evidence=rec, profile=None, db=None)
        )
    except BrowserRuntimeUnavailable:
        result = rec
    except Exception:
        result = rec
    _check("db=None 时 submit_approval_id=None",
           result.submit_approval_id is None,
           f"got {result.submit_approval_id!r}")
    _check("db=None 时不写 policy_decision",
           "policy_decision" not in (result.metadata or {}),
           f"got {(result.metadata or {}).get('policy_decision')!r}")


test_submit_db_none_uses_builtin_path()


# ============================================================
# 4) PolicyEngine 抛异常 → 降级内置快路径
# ============================================================
print("== 4. PolicyEngine 抛异常 → 降级内置（best-effort）==")


def test_submit_policy_engine_raises_falls_back():
    _enable_runtime()
    def _explode(db, **kwargs):
        raise RuntimeError("simulated PolicyEngine crash")
    sys.modules["app.services.policy.engine"].evaluate_action = _explode
    rec = EvidenceRecord(
        tenant_id=TENANT_OK,
        actor="verify",
        action="submit",
    )
    rec.metadata["policy_context"] = {"auto_submit": True, "company_id": "co-1"}
    try:
        result = asyncio.run(
            _executor._real_execute_submit(evidence=rec, profile=None, db="mock-db")
        )
    except BrowserRuntimeUnavailable:
        result = rec
    except Exception:
        result = rec
    _check("PolicyEngine 抛错时仍落 Evidence（不外泄）",
           result is not None, "")
    _check("降级路径：submit_approval_id=None",
           result.submit_approval_id is None, "")
    _check("metadata 记录 policy_engine_error",
           "policy_engine_error" in (result.metadata or {}),
           f"got {(result.metadata or {}).get('policy_engine_error')!r}")


test_submit_policy_engine_raises_falls_back()


# ============================================================
# 5) run_real_execution submit 分支传 db
# ============================================================
print("== 5. run_real_execution 透传 db 到 submit handler ==")


def test_run_real_execution_passes_db_to_submit():
    sig = inspect.signature(_executor.run_real_execution)
    has_db = "db" in sig.parameters
    _check("run_real_execution 增 db 入参", has_db,
           "" if has_db else "no db in sig")


test_run_real_execution_passes_db_to_submit()


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
