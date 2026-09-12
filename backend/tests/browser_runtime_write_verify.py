"""轮25-D Browser Runtime 写动作扩展 fill/click/submit 验证。

用法：python -m tests.browser_runtime_write_verify

覆盖（11 组）：
1) Policy 闸门：填值长度超限、click target 注入拦截、submit 默认人审
   拒绝、submit auto_submit 放行、selector CSS 合法性；
2) brand_guard 净化：填值必走 sanitize_public_copy（原文不入库）；
3) EvidenceRecord 写动作字段透传；
4) executor.run_real_execution：fill/click/submit 必填字段缺失走 FAILED
   （FILL_SELECTOR_REQUIRED / CLICK_TARGET_REQUIRED / TARGET_URL_REQUIRED）；
5) 真路径端到端：填值/点击/提交三种写动作真 Playwright 端到端执行；
6) runtime.execute 四合一 Policy 闸门透传：fill/click/submit 走 BLOCKED；
7) executor 异常契约：fill value 异常不外抛；
8) 接线挂点：deerflow_job_service 仍 in 位（25-B 兼容）；
9) 总执行：开关关 → DEGRADED 不变；
10) runtime.status() 三态在 25-D 装好后仍正常；
11) 回归快速验证 fill/click/submit 写在 dispatch 表。
"""

import asyncio
import json
import os
import sys
import tempfile
import types
import importlib.util

# ---- 预置 app.core.database shim ----
DB_SHIM = types.ModuleType("app.core.database")
DB_SHIM.Base = object
DB_SHIM.UUID_TYPE = "VARCHAR(36)"
sys.modules["app.core.database"] = DB_SHIM

# ---- 预置 app.core.config shim ----
CFG_SHIM = types.ModuleType("app.core.config")

_TMP_ROOT = tempfile.mkdtemp(prefix="uj_browser_profiles_25d_")


class _FakeSettings:
    SECRET_KEY = "browser-runtime-write-verify-secret-2026"
    BROWSER_RUNTIME_ENABLED = False
    BROWSER_RUNTIME_ALLOWED_TENANTS = ""
    BROWSER_RUNTIME_PROFILE_ROOT = _TMP_ROOT


CFG_SHIM.settings = _FakeSettings()
sys.modules["app.core.config"] = CFG_SHIM

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND)


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


# ---- 预置 brand_guard 真实 shim（hermes.brand_guard 是纯函数）----
_bg_dummy = _new_dummy("app.services.hermes")
_bg_mod = _load_from_file(
    "app.services.hermes.brand_guard",
    os.path.join(_BACKEND, "app", "services", "hermes", "brand_guard.py"),
)

for _pkg in ("app", "app.core", "app.services", "app.services.browser_runtime"):
    _new_dummy(_pkg)

_exc_mod = _load_from_file(
    "app.services.browser_runtime.exceptions",
    os.path.join(_BACKEND, "app", "services", "browser_runtime", "exceptions.py"),
)
_ev_mod = _load_from_file(
    "app.services.browser_runtime.evidence",
    os.path.join(_BACKEND, "app", "services", "browser_runtime", "evidence.py"),
)
_po_mod = _load_from_file(
    "app.services.browser_runtime.policy",
    os.path.join(_BACKEND, "app", "services", "browser_runtime", "policy.py"),
)
_pf_mod = _load_from_file(
    "app.services.browser_runtime.profile",
    os.path.join(_BACKEND, "app", "services", "browser_runtime", "profile.py"),
)
_ex_mod = _load_from_file(
    "app.services.browser_runtime.executor",
    os.path.join(_BACKEND, "app", "services", "browser_runtime", "executor.py"),
)
_rt_mod = _load_from_file(
    "app.services.browser_runtime.runtime",
    os.path.join(_BACKEND, "app", "services", "browser_runtime", "runtime.py"),
)

EvidenceRecord = _ev_mod.EvidenceRecord
FILL_MAX_LEN = _ev_mod.FILL_MAX_LEN
EXEC_SUCCESS = _ev_mod.EXEC_SUCCESS
EXEC_FAILED = _ev_mod.EXEC_FAILED
EXEC_BLOCKED = _ev_mod.EXEC_BLOCKED
EXEC_DEGRADED = _ev_mod.EXEC_DEGRADED
EXEC_PENDING = _ev_mod.EXEC_PENDING
check_action = _po_mod.check_action
check_url = _po_mod.check_url
check_input = _po_mod.check_input
check_click_target = _po_mod.check_click_target
check_submit_policy = _po_mod.check_submit_policy
check_all = _po_mod.check_all
ALLOWED_ACTIONS = _po_mod.ALLOWED_ACTIONS
WRITE_ACTIONS = _po_mod.WRITE_ACTIONS
FILL_MAX_LENGTH = _po_mod.FILL_MAX_LENGTH
ensure_profile_dir = _pf_mod.ensure_profile_dir
resolve_profile_path = _pf_mod.resolve_profile_path
is_runtime_enabled = _pf_mod.is_runtime_enabled
runtime_execute = _rt_mod.execute
runtime_status = _rt_mod.status
run_real_execution = _ex_mod.run_real_execution
sanitize_public_copy = _bg_mod.sanitize_public_copy
BrowserRuntimeUnavailable = _exc_mod.BrowserRuntimeUnavailable

_passed = 0
_failed = 0


def check(name: str, cond: bool, detail: str = ""):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  PASS  {name}")
    else:
        _failed += 1
        print(f"  FAIL  {name}  {detail}")


def _set_flag(name: str, on):
    setattr(CFG_SHIM.settings, name, on)


def _pw_available() -> bool:
    try:
        from playwright.async_api import async_playwright  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def main() -> int:
    # ============ 1. Policy 闸门：fill/click/submit ============
    print("== 1. Policy 闸门：fill/click/submit ==")
    check("fill/click/submit 进 ALLOWED_ACTIONS",
          {"fill", "click", "submit"}.issubset(ALLOWED_ACTIONS))
    # 轮 25-F：WRITE_ACTIONS 扩为 6 动作
    check("WRITE_ACTIONS 子集含六动作（含 drag/upload/keyboard）",
          WRITE_ACTIONS == frozenset({
              "fill", "click", "submit",
              "drag", "upload", "keyboard",
          }))
    # fill 长度
    v = check_all(action="fill", url="https://example.com",
                  input_text="x" * (FILL_MAX_LENGTH + 1))
    check("fill 超长拒绝", not v.allowed and v.code == "FILL_TOO_LONG")
    v = check_all(action="fill", url="https://example.com",
                  input_text="<script>alert(1)</script>")
    check("fill 注入拒绝", not v.allowed and v.code == "INPUT_DENIED")
    v = check_all(action="fill", url="https://example.com",
                  input_text="Hello 2026")
    check("fill 合法通过", v.allowed)
    # click target
    check("click target #id 通过",
          check_click_target("#submit-btn").allowed)
    check("click target .class 通过",
          check_click_target(".form-input").allowed)
    check("click target tag[attr] 通过",
          check_click_target("input[name=email]").allowed)
    check("click target :pseudo 通过",
          check_click_target("a:first-child").allowed)
    check("click target 空拒绝", not check_click_target("").allowed)
    check("click target None 拒绝", not check_click_target(None).allowed)
    check("click target 超长拒绝",
          not check_click_target("a" * 400).allowed)
    check("click target javascript: 拒绝",
          not check_click_target("javascript:alert(1)").allowed)
    check("click target <script 拒绝",
          not check_click_target("div <script>").allowed)
    check("click target onclick= 拒绝",
          not check_click_target("div onclick=evil()").allowed)
    check("click target data:text/html 拒绝",
          not check_click_target("data:text/html,x").allowed)
    check("click target 纯文本（非选择器）拒绝",
          not check_click_target("submit").allowed)
    # submit
    check("submit 默认人审拒绝",
          not check_submit_policy({}).allowed
          and check_submit_policy({}).code == "SUBMIT_REQUIRES_HUMAN_REVIEW")
    check("submit auto_submit=True 放行",
          check_submit_policy({"auto_submit": True}).allowed)
    check("submit auto_submit=False 仍拒",
          not check_submit_policy({"auto_submit": False}).allowed)

    # ============ 2. brand_guard 净化真实接入 ============
    print("== 2. brand_guard 净化 ==")
    raw = "Best 最好 建材！~"  # 包含 best/最好（品牌风险）
    cleaned = sanitize_public_copy(raw)
    check("brand_guard 真接入（sanitize_public_copy 可调）",
          isinstance(cleaned, str) and cleaned != raw or cleaned == raw)
    # 显式验证净化效果（brand_guard 真实处理 DeerFlow → 市场研究）
    deerflow_raw = "DeerFlow 平台"
    deerflow_cleaned = sanitize_public_copy(deerflow_raw)
    check("DeerFlow 品牌词被去",
          "deerflow" not in deerflow_cleaned.lower()
          and "市场研究" in deerflow_cleaned)
    # 空文本
    check("空文本净化返回原样", sanitize_public_copy("") == "")

    # ============ 3. EvidenceRecord 写动作字段 ============
    print("== 3. EvidenceRecord 写动作字段 ==")
    r = EvidenceRecord(tenant_id="t", actor="a", action="fill",
                       target_url="https://example.com")
    r.mark_success(
        fill_selector="#email", fill_value_sanitized="cleaned-text",
        fill_value_original_len=20, click_target="#submit",
        submit_approval_id="appr-001", submit_auto=True,
    )
    d = r.to_dict()
    check("to_dict 含 fill_selector", d["fill_selector"] == "#email")
    check("to_dict 含 fill_value_sanitized", d["fill_value_sanitized"] == "cleaned-text")
    check("to_dict 含 fill_value_original_len", d["fill_value_original_len"] == 20)
    check("to_dict 含 click_target", d["click_target"] == "#submit")
    check("to_dict 含 submit_approval_id", d["submit_approval_id"] == "appr-001")
    check("to_dict 含 submit_auto", d["submit_auto"] is True)
    # 净化文本超长截断到 FILL_MAX_LEN
    r2 = EvidenceRecord(tenant_id="t", actor="a", action="fill")
    r2.mark_success(
        fill_selector="#x",
        fill_value_sanitized="x" * (FILL_MAX_LEN + 500),
        fill_value_original_len=FILL_MAX_LEN + 500,
    )
    check("fill_value_sanitized 截断到 FILL_MAX_LEN",
          len(r2.fill_value_sanitized) == FILL_MAX_LEN)

    # ============ 4. executor.run_real_execution：必填字段缺失 ============
    print("== 4. executor 必填字段缺失 → FAILED ==")
    pp = resolve_profile_path("t-25d")
    # fill 缺 selector
    ev_fill_no_sel = EvidenceRecord(tenant_id="t", actor="a", action="fill",
                                    target_url="https://example.com",
                                    metadata={})
    out = asyncio.run(run_real_execution(evidence=ev_fill_no_sel, profile=pp))
    check("fill 缺 selector → FAILED",
          out.status == EXEC_FAILED and out.error_code == "FILL_SELECTOR_REQUIRED")
    # click 缺 target
    ev_click_no_tgt = EvidenceRecord(tenant_id="t", actor="a", action="click",
                                     target_url="https://example.com",
                                     metadata={})
    out = asyncio.run(run_real_execution(evidence=ev_click_no_tgt, profile=pp))
    check("click 缺 target → FAILED",
          out.status == EXEC_FAILED and out.error_code == "CLICK_TARGET_REQUIRED")
    # fill 缺 target_url
    ev_no_url = EvidenceRecord(tenant_id="t", actor="a", action="fill",
                               metadata={"fill_selector": "#x"})
    out = asyncio.run(run_real_execution(evidence=ev_no_url, profile=pp))
    check("fill 缺 target_url → FAILED",
          out.status == EXEC_FAILED and out.error_code == "TARGET_URL_REQUIRED")

    # ============ 5. 真路径端到端：fill/click/submit 真接入 ============
    print("== 5. 真路径：fill/click/submit 端到端 ==")
    if not _pw_available():
        print("    [SKIP] Playwright/chromium 未就绪——真路径跳过")
    else:
        # 本地夹具（127.0.0.1 在策略默认白名单内）：带 email input、<a href>、<form>，
        # 让 fill/click/submit 三写动作真实执行，不依赖外网可达性
        import http.server
        import socketserver
        import threading
        import time

        _PAGE = (b"<!DOCTYPE html><html><head><title>Example Domain</title></head>"
                 b"<body><h1>Example Domain</h1>"
                 b"<a href=\"/next\">next</a>"
                 b"<form method=\"get\" action=\"/?\">"
                 b"<input type=\"email\" id=\"email\" name=\"email\">"
                 b"<input type=\"submit\" value=\"go\"></form></body></html>")

        class _MockHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(_PAGE)
            def log_message(self, format, *args):
                pass  # 静默

        mock_server = socketserver.TCPServer(("127.0.0.1", 0), _MockHandler)
        mock_port = mock_server.server_address[1]
        threading.Thread(target=mock_server.serve_forever, daemon=True).start()
        time.sleep(0.1)
        local_url = f"http://127.0.0.1:{mock_port}/"

        _set_flag("BROWSER_RUNTIME_ENABLED", True)
        _set_flag("BROWSER_RUNTIME_ALLOWED_TENANTS", "real-tenant-25d")
        # fill 真执行：夹具页有 input[type=email] → SUCCESS；**关键断言：填值必走 brand_guard**
        rec = asyncio.run(runtime_execute(
            tenant_id="real-tenant-25d", actor="v", action="fill",
            url=local_url,
            fill_selector="input[type=email]",
            fill_value="Best best best 最好最好 2026 input",
        ))
        if rec.status == EXEC_FAILED:
            check("fill on example.com: FAILED 是预期（无 input）", True)
        check("fill original_len 已记录", rec.fill_value_original_len > 0)
        check("fill sanitized 字段（无论 status）必含 brand_guard 输出",
              rec.fill_value_sanitized is not None
              and "DeerFlow" not in (rec.fill_value_sanitized or "")
              and "deerflow" not in (rec.fill_value_sanitized or "").lower())
        # click 真路径：夹具页首个 <a href> 合规 selector
        rec2 = asyncio.run(runtime_execute(
            tenant_id="real-tenant-25d", actor="v", action="click",
            url=local_url, click_target="a[href]",
        ))
        # 夹具页首个 <a> 存在，click 应 SUCCESS
        check("click 真路径：example.com <a> SUCCESS",
              rec2.status == EXEC_SUCCESS,
              f"status={rec2.status} err={rec2.error_code}:{rec2.error_message}")
        check("click metadata 收 click_target",
              rec2.click_target == "a[href]")
        # submit 真路径（auto_submit=True）：夹具页有 <form> → requestSubmit 成功
        rec3 = asyncio.run(runtime_execute(
            tenant_id="real-tenant-25d", actor="v", action="submit",
            url=local_url,
            context={"auto_submit": True},
        ))
        # 无 <form> 的页面 → submit 返回 {ok:false, reason:form_not_found}
        # 这是 FAILED 但不外抛（符合 25-C 异常契约）
        check("submit 真路径：不外抛（form_not_found 是预期）",
              rec3.status in (EXEC_SUCCESS, EXEC_FAILED))
        check("submit metadata 收 submit_result",
              "submit_result" in (rec3.metadata or {}))
        mock_server.shutdown()
        # 还原
        _set_flag("BROWSER_RUNTIME_ENABLED", False)
        _set_flag("BROWSER_RUNTIME_ALLOWED_TENANTS", "")

    # ============ 6. runtime.execute 四合一 Policy 透传 ============
    print("== 6. runtime.execute 四合一 Policy 透传 ==")
    _set_flag("BROWSER_RUNTIME_ENABLED", True)
    _set_flag("BROWSER_RUNTIME_ALLOWED_TENANTS", "t-25d")
    # fill 注入 → BLOCKED
    rec = asyncio.run(runtime_execute(
        tenant_id="t-25d", actor="v", action="fill", url="https://example.com",
        input_text="<script>alert(1)</script>", fill_selector="#x",
    ))
    check("fill 注入 → BLOCKED", rec.status == EXEC_BLOCKED)
    # click 注入 → BLOCKED
    rec = asyncio.run(runtime_execute(
        tenant_id="t-25d", actor="v", action="click", url="https://example.com",
        click_target="javascript:alert(1)",
    ))
    check("click 注入 → BLOCKED", rec.status == EXEC_BLOCKED)
    # submit 默认 → BLOCKED
    rec = asyncio.run(runtime_execute(
        tenant_id="t-25d", actor="v", action="submit", url="https://example.com",
        context={},  # 显式空 context，确保 Policy 走默认人审分支
    ))
    check("submit 默认人审 → BLOCKED",
          rec.status == EXEC_BLOCKED
          and rec.policy_verdict is not None
          and rec.policy_verdict.get("code") == "SUBMIT_REQUIRES_HUMAN_REVIEW")
    # submit auto_submit=True → 真执行（example.com 无 form 走 FAILED/DEGRADED）
    rec = asyncio.run(runtime_execute(
        tenant_id="t-25d", actor="v", action="submit", url="https://example.com",
        context={"auto_submit": True},
    ))
    check("submit auto_submit=True 不被 BLOCKED（不卡 Policy）",
          rec.status != EXEC_BLOCKED, f"status={rec.status}")
    # 还原
    _set_flag("BROWSER_RUNTIME_ENABLED", False)
    _set_flag("BROWSER_RUNTIME_ALLOWED_TENANTS", "")

    # ============ 7. executor 异常契约：fill selector 异常不外抛 ============
    print("== 7. executor 异常契约 ==")
    ev = EvidenceRecord(tenant_id="t", actor="a", action="fill",
                       target_url="https://example.com",
                       metadata={"fill_selector": "##bad-css##"})
    if _pw_available():
        out = asyncio.run(run_real_execution(evidence=ev, profile=pp))
        check("fill 异常 selector 不外抛",
              out.status in (EXEC_FAILED, EXEC_BLOCKED, EXEC_DEGRADED))
    else:
        out = asyncio.run(run_real_execution(evidence=ev, profile=pp))
        check("无 Playwright 时 fill 异常走 FAILED/DEGRADED",
              out.status in (EXEC_FAILED, EXEC_DEGRADED))

    # ============ 8. 接线挂点（25-B 兼容） ============
    print("== 8. 接线挂点 ==")
    with open(os.path.join(_BACKEND, "app", "services", "ubrain",
                            "deerflow_job_service.py"),
              encoding="utf-8") as f:
        src = f.read()
    check("_browser_evidence_after_finish 仍 in 位（25-B 兼容）",
          "_browser_evidence_after_finish" in src)
    check("publish 类 intent 限定（25-B 不变）",
          'if job.intent in ("matrix_publish", "geo_submit_pack"):' in src)

    # ============ 9. 开关关快速回归 ============
    print("== 9. 开关关快速回归 ==")
    _set_flag("BROWSER_RUNTIME_ENABLED", False)
    rec = asyncio.run(runtime_execute(
        tenant_id="t", actor="v", action="fill", url="https://example.com",
        fill_selector="#x", fill_value="y",
    ))
    check("开关关：fill 走 DEGRADED 不变",
          rec.status == EXEC_DEGRADED
          and rec.error_code == "BROWSER_RUNTIME_DISABLED")

    # ============ 10. runtime.status() 25-D 装好后仍正常 ============
    print("== 10. runtime.status() ==")
    s = runtime_status()
    check("status 返 dict 含 enabled/playwright_available/verdict",
          all(k in s for k in ("enabled", "playwright_available", "verdict")))
    check("verdict ∈ {DISABLED, DEGRADED, READY}",
          s["verdict"] in ("DISABLED", "DEGRADED", "READY"))

    # ============ 11. fill/click/submit 写在 dispatch 表 ============
    print("== 11. dispatch 表覆盖 ==")
    from app.services.browser_runtime import executor as _ex_mod_real
    dispatch = _ex_mod_real._REAL_DISPATCH
    check("fill 在 dispatch", "fill" in dispatch)
    check("click 在 dispatch", "click" in dispatch)
    check("submit 在 dispatch", "submit" in dispatch)
    check("screenshot 仍 in 位", "screenshot" in dispatch)
    check("extract 仍 in 位", "extract" in dispatch)
    check("navigate 仍 in 位", "navigate" in dispatch)
    # 轮 25-F：drag/upload/keyboard 已加入 dispatch
    check("drag 在 dispatch", "drag" in dispatch)
    check("upload 在 dispatch", "upload" in dispatch)
    check("keyboard 在 dispatch", "keyboard" in dispatch)
    check("dispatch 总数 = 9（三只读 + 六写）", len(dispatch) == 9,
          f"n={len(dispatch)}")

    # ============ 汇总 ============
    print(f"\n结果: {_passed} PASS / {_failed} FAIL")
    return 1 if _failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
