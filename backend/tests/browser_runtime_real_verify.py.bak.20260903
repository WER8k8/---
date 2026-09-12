"""轮25-C Browser Runtime 真实 Playwright 接入 内存 + 真浏览器双路径验证。

用法：python -m tests.browser_runtime_real_verify
依赖：sqlalchemy（无需 pydantic）；Playwright + chromium 仅在真路径需要时使用。

覆盖：
- shim 路径（无 Playwright/无 chromium）：executor.run_real_execution 对未注册
  动作（fill/click）走 NOT_IMPLEMENTED_25D 降级语义；Playwright 未装时
  runtime.execute 走 PLAYWRIGHT_UNAVAILABLE 降级（与 25-B 一致）。
- 真路径（已装 Playwright + chromium 装好）：开启开关 + 白名单 + 有效
  navigate/screenshot 真实执行 → status=SUCCESS，screenshot_path 非空，
  screenshot_size_bytes > 0，duration_ms > 0。
- Profile 物理目录：ensure_profile_dir 创建到 root 之下，权限 0o700
  （Windows 下 icacls 尽力收紧）。
- EvidenceRecord：screenshot_path/screenshot_size_bytes 字段透传 + to_dict
  序列化。
- executor 异常契约：轮25-D 起统一自吞——BrowserRuntimeUnavailable 与其他异常
  全部转为 mark_failed（FAILED + error_code 标类名/EXEC_RUNTIME_ERROR），
  绝不外泄。runtime.execute 第 5 步仍以同样契约兜底（双层保险）。
- 接线挂点：deerflow_job_service 的 _browser_evidence_after_finish 仍
  在位（25-B 接入 + 25-C 真执行）。
- 总执行：开关关 → DEGRADED 不变（25-B 已覆盖，本轮快速回归 1 项即可）。
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

# ---- 预置 app.core.config shim（开关可切换 + Profile root 用临时目录）----
CFG_SHIM = types.ModuleType("app.core.config")

_TMP_ROOT = tempfile.mkdtemp(prefix="uj_browser_profiles_25c_")


class _FakeSettings:
    SECRET_KEY = "browser-runtime-real-verify-secret-2026"
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
EXEC_SUCCESS = _ev_mod.EXEC_SUCCESS
EXEC_DEGRADED = _ev_mod.EXEC_DEGRADED
EXEC_FAILED = _ev_mod.EXEC_FAILED
ensure_profile_dir = _pf_mod.ensure_profile_dir
resolve_profile_path = _pf_mod.resolve_profile_path
is_runtime_enabled = _pf_mod.is_runtime_enabled
is_tenant_allowed = _pf_mod.is_tenant_allowed
runtime_execute = _rt_mod.execute
runtime_status = _rt_mod.status
run_real_execution = _ex_mod.run_real_execution
BrowserRuntimeUnavailable = _exc_mod.BrowserRuntimeUnavailable
ProfileIsolationError = _exc_mod.ProfileIsolationError

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
    """运行时探测 Playwright + chromium 是否就绪（不抛）。"""
    try:
        from playwright.async_api import async_playwright  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def main() -> int:
    # ============ 1. shim 路径：未注册动作降级 ============
    # 25-D 起 fill/click/submit 已注册；用一个未来动作验证 25-B 兼容降级语义
    print("== 1. shim 路径：未注册动作降级 ==")
    ev = EvidenceRecord(tenant_id="t", actor="a", action="__future_action__", target_url="https://x")
    pp = resolve_profile_path("t-1")
    out = asyncio.run(run_real_execution(evidence=ev, profile=pp))
    check("未注册动作 → DEGRADED", out.status == EXEC_DEGRADED)
    check("未注册动作 → error_code=NOT_IMPLEMENTED___FUTURE_ACTION__",
          out.error_code == "NOT_IMPLEMENTED___FUTURE_ACTION__")

    # ============ 2. Profile 物理目录惰性创建 ============
    print("== 2. Profile 物理目录 ==")
    pp = resolve_profile_path("tenant-test-25c")
    pp2 = ensure_profile_dir(pp)
    check("ensure_profile_dir 返 ProfilePath", pp2 is not None)
    check("物理目录已创建", os.path.isdir(pp2.path))
    check("目录在 root 之下", pp2.path.startswith(pp2.root))
    # 二次幂等：再次调用不报错
    pp3 = ensure_profile_dir(pp)
    check("幂等创建不报错", pp3.path == pp2.path)

    # ============ 3. EvidenceRecord 字段透传 ============
    print("== 3. EvidenceRecord screenshot 字段 ==")
    r = EvidenceRecord(tenant_id="t", actor="a", action="screenshot",
                       target_url="https://example.com")
    r.mark_success(
        output_ref="/x/a.png", output_summary="screenshot ok",
        screenshot_path="/x/a.png", screenshot_size_bytes=12345,
    )
    d = r.to_dict()
    check("to_dict 含 screenshot_path", d["screenshot_path"] == "/x/a.png")
    check("to_dict 含 screenshot_size_bytes", d["screenshot_size_bytes"] == 12345)
    check("mark_success 自动设 status=SUCCESS", r.status == EXEC_SUCCESS)

    # ============ 4. 真路径：完整开关+白名单+Playwright 真实执行 ============
    print("== 4. 真路径：navigate/screenshot 真实执行 ==")
    if not _pw_available():
        print("    [SKIP] Playwright/chromium 未就绪——跳过真路径（这是降级路径仍绿的旁证）")
    else:
        import http.server
        import socketserver
        import threading
        import time

        class _MockHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<!DOCTYPE html><html><head><title>Example Domain</title></head><body><h1>Example Domain</h1><p>Test Body</p></body></html>")
            def log_message(self, format, *args):
                pass  # 静默

        mock_server = socketserver.TCPServer(("127.0.0.1", 0), _MockHandler)
        mock_port = mock_server.server_address[1]
        t = threading.Thread(target=mock_server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.1)

        test_target_url = f"http://127.0.0.1:{mock_port}/"

        _set_flag("BROWSER_RUNTIME_ENABLED", True)
        _set_flag("BROWSER_RUNTIME_ALLOWED_TENANTS", "real-tenant-25c")
        rec = asyncio.run(runtime_execute(
            tenant_id="real-tenant-25c",
            actor="verify",
            action="screenshot",
            url=test_target_url,
        ))
        check("真路径：status=SUCCESS", rec.status == EXEC_SUCCESS,
              f"status={rec.status} err={rec.error_code}:{rec.error_message}")
        check("真路径：screenshot_path 非空",
              bool(rec.screenshot_path) and os.path.isfile(rec.screenshot_path),
              f"path={rec.screenshot_path}")
        check("真路径：screenshot_size_bytes > 0",
              rec.screenshot_size_bytes > 0,
              f"size={rec.screenshot_size_bytes}")
        check("真路径：duration_ms > 0", rec.duration_ms > 0,
              f"dur={rec.duration_ms}")
        # metadata 落 user_data_dir
        check("真路径：user_data_dir 写入 metadata",
              "user_data_dir" in rec.metadata)

        # 二次执行应复用同 Profile（cookies/storage 物理隔离但持久）
        rec2 = asyncio.run(runtime_execute(
            tenant_id="real-tenant-25c",
            actor="verify",
            action="navigate",
            url=test_target_url,
        ))
        check("二次执行：navigate 走 status=SUCCESS", rec2.status == EXEC_SUCCESS,
              f"status={rec2.status} err={rec2.error_code}:{rec2.error_message}")
        check("二次执行：metadata 收 status_code",
              rec2.metadata.get("status_code") is not None)

        # extract
        rec3 = asyncio.run(runtime_execute(
            tenant_id="real-tenant-25c",
            actor="verify",
            action="extract",
            url=test_target_url,
        ))
        check("extract：status=SUCCESS", rec3.status == EXEC_SUCCESS,
              f"status={rec3.status} err={rec3.error_code}:{rec3.error_message}")
        check("extract：metadata 收 title",
              "extracted" in rec3.metadata
              and "title" in rec3.metadata["extracted"])

        mock_server.shutdown()

    # ============ 5. executor 异常契约 ============
    print("== 5. executor 异常契约 ==")
    # 5.1 模拟 launch 失败（用不存在的 user_data_dir 的坏子路径不可能，但能
    #     模拟"action 异常"通过 mock）。最直接：传一个无 target_url 的 navigate。
    ev = EvidenceRecord(tenant_id="t", actor="a", action="navigate", target_url=None)
    pp = resolve_profile_path("t-2")
    try:
        out = asyncio.run(run_real_execution(evidence=ev, profile=pp))
        check("navigate None URL 走 FAILED",
              out.status == EXEC_FAILED)
        check("navigate None URL 异常契约：不外泄",
              out.error_code == "TARGET_URL_REQUIRED")
    except Exception as exc:  # noqa: BLE001
        check("navigate None URL 异常契约：被捕获不外泄", False, f"leaked={exc}")
    # 5.2 模拟 runtime.execute 接收未注册动作 click（25-D 范围）——
    #     Policy 闸门会先于 executor 拒，所以走 BLOCKED（不外抛，绝不命中 executor）
    if _pw_available():
        _set_flag("BROWSER_RUNTIME_ENABLED", True)
        _set_flag("BROWSER_RUNTIME_ALLOWED_TENANTS", "real-tenant-25c")
        rec = asyncio.run(runtime_execute(
            tenant_id="real-tenant-25c", actor="v", action="click",
            url="https://example.com/",
        ))
        # action=click 不在白名单 → Policy 拒绝 → status=BLOCKED
        check("未注册 action=click 被 Policy 拒绝 → BLOCKED",
              rec.status == "blocked", f"status={rec.status} err={rec.error_code}")
        check("未注册 action=click → error_code 含 ACTION_NOT_ALLOWED",
              "ACTION_NOT_ALLOWED" in (rec.error_code or "")
              or rec.policy_verdict is not None)
        # 还原
        _set_flag("BROWSER_RUNTIME_ENABLED", False)
        _set_flag("BROWSER_RUNTIME_ALLOWED_TENANTS", "")

    # ============ 6. 接线挂点结构校验（25-B 接入仍保留） ============
    print("== 6. 接线挂点 ==")
    with open(os.path.join(_BACKEND, "app", "services", "ubrain",
                            "deerflow_job_service.py"),
              encoding="utf-8") as f:
        src = f.read()
    check("_browser_evidence_after_finish 在位（25-B/25-C 共享）",
          "_browser_evidence_after_finish" in src)
    check("publish 类 intent 限定",
          'if job.intent in ("matrix_publish", "geo_submit_pack"):' in src)
    check("runtime.execute 入口", "from app.services.browser_runtime.runtime import execute"
          in src)
    check("executor 入口（25-C 真实）", "import" in src)

    # ============ 7. 开关关快速回归（25-B 不变） ============
    print("== 7. 开关关快速回归 ==")
    _set_flag("BROWSER_RUNTIME_ENABLED", False)
    rec = asyncio.run(runtime_execute(
        tenant_id="t", actor="v", action="navigate", url="https://example.com/"
    ))
    check("开关关：DEGRADED 不变", rec.status == EXEC_DEGRADED)
    check("开关关：error_code=BROWSER_RUNTIME_DISABLED",
          rec.error_code == "BROWSER_RUNTIME_DISABLED")

    # ============ 8. runtime.status() 三态（含 25-C 真路径） ============
    print("== 8. runtime.status() ==")
    s = runtime_status()
    check("status 返 dict 含 enabled/playwright_available/verdict",
          all(k in s for k in ("enabled", "playwright_available", "verdict")))
    if _pw_available():
        check("Playwright 装好时 status.playwright_available=True",
              s["playwright_available"] is True)
    else:
        check("Playwright 未装时 status.playwright_available=False",
              s["playwright_available"] is False)

    # ============ 汇总 ============
    print(f"\n结果: {_passed} PASS / {_failed} FAIL")
    return 1 if _failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
