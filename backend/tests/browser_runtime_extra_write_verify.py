"""轮 25-F 写动作扩展（drag/upload/keyboard）验证（不触碰真实 Playwright）。

用法：python tests/browser_runtime_extra_write_verify.py

覆盖：
1) Policy 闸门：drag 起点/终点 selector 校验（含 click 复用）
2) Policy 闸门：upload 路径白名单 + 扩展名校验 + 数量上限
3) Policy 闸门：keyboard 文本长度 + 按键白名单
4) Evidence 字段：drag_from/to / upload_file_paths / keyboard_text/keys
5) 调度表 _REAL_DISPATCH：3 动作均在位
"""
import asyncio
import importlib.util
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
    SECRET_KEY = "browser-runtime-25f-verify-secret-2026"
    BROWSER_RUNTIME_ENABLED = True
    BROWSER_RUNTIME_ALLOWED_TENANTS = "t-25f-1"
    BROWSER_RUNTIME_PROFILE_ROOT = os.path.join(
        os.environ.get("TEMP", "C:\\Windows\\Temp"),
        "uj_browser_profiles_25f_verify",
    )


CFG_SHIM.settings = _FakeSettings()
sys.modules["app.core.config"] = CFG_SHIM

# ---- 预置 app.services / app.services.browser_runtime 空包（防 import 链触发外贸易）----
# 关键：module 路径含点时 Python 会自动 import 父包；这里用 shim 占位避免触发
# app.services/__init__.py 的 foreign_trade 链（Python 3.10 datetime.UTC 兼容 bug）。
APP_SERVICES = types.ModuleType("app.services")
APP_SERVICES.__path__ = []  # 标记为包
sys.modules["app.services"] = APP_SERVICES
APP_BR = types.ModuleType("app.services.browser_runtime")
APP_BR.__path__ = [os.path.join(_BACKEND, "app", "services", "browser_runtime")]
sys.modules["app.services.browser_runtime"] = APP_BR


# ---- 直接 importlib 加载 evidence / exceptions / policy / executor ----
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
_executor = _load(
    "app.services.browser_runtime.executor",
    os.path.join(_BROWSER_RUNTIME, "executor.py"),
)

# ---- 准备样本 EvidenceRecord ----
EvidenceRecord = _evidence.EvidenceRecord


# ---- 用例计数器 ----
_results: list[tuple[str, bool, str]] = []


def _check(name: str, cond: bool, detail: str = ""):
    status = "PASS" if cond else "FAIL"
    _results.append((name, cond, detail))
    flag = "✔" if cond else "✘"
    extra = f"  {detail}" if detail and not cond else ""
    print(f"  {flag}  {status}  {name}{extra}")


# ============================================================
# 1) Policy 白名单 + WRITE_ACTIONS
# ============================================================
print("== 1. 25-F 三动作白名单 ==")


def test_action_whitelist_25f():
    _check("drag 在 ALLOWED_ACTIONS", "drag" in _policy.ALLOWED_ACTIONS)
    _check("upload 在 ALLOWED_ACTIONS", "upload" in _policy.ALLOWED_ACTIONS)
    _check("keyboard 在 ALLOWED_ACTIONS", "keyboard" in _policy.ALLOWED_ACTIONS)
    _check("drag 在 WRITE_ACTIONS", "drag" in _policy.WRITE_ACTIONS)
    _check("upload 在 WRITE_ACTIONS", "upload" in _policy.WRITE_ACTIONS)
    _check("keyboard 在 WRITE_ACTIONS", "keyboard" in _policy.WRITE_ACTIONS)


test_action_whitelist_25f()


# ============================================================
# 2) drag 起点/终点 selector 校验
# ============================================================
print("== 2. drag selector 校验 ==")


def test_drag_selectors_required():
    v = _policy.check_all(
        action="drag", url="https://example.com", context={}
    )
    _check("drag 缺 selectors → 拒绝",
           not v.allowed and v.code == "DRAG_SELECTORS_MISSING",
           f"code={v.code!r}")


def test_drag_selectors_valid():
    v = _policy.check_all(
        action="drag",
        url="https://example.com",
        context={"drag_from_selector": "#item-1", "drag_to_selector": "#bin-1"},
    )
    _check("drag 合规 selectors → 允许",
           v.allowed and v.code == "OK",
           f"code={v.code!r}")


def test_drag_from_invalid_selector():
    v = _policy.check_all(
        action="drag",
        url="https://example.com",
        context={"drag_from_selector": "javascript:alert(1)", "drag_to_selector": "#bin-1"},
    )
    _check("drag from 含 JS 协议 → 拒绝",
           not v.allowed and v.code == "CLICK_TARGET_DENIED",
           f"code={v.code!r}")


test_drag_selectors_required()
test_drag_selectors_valid()
test_drag_from_invalid_selector()


# ============================================================
# 3) upload 路径白名单 + 扩展名校验
# ============================================================
print("== 3. upload 路径/扩展名校验 ==")


def test_upload_no_paths():
    v = _policy.check_all(
        action="upload", url="https://example.com", context={}
    )
    _check("upload 缺 paths → 拒绝",
           not v.allowed and v.code == "UPLOAD_PATHS_MISSING",
           f"code={v.code!r}")


def test_upload_too_many():
    v = _policy.check_all(
        action="upload",
        url="https://example.com",
        context={"upload_file_paths": [f"C:\\Windows\\Temp\\f{i}.txt" for i in range(10)]},
    )
    _check("upload > 5 文件 → 拒绝",
           not v.allowed and v.code == "UPLOAD_TOO_MANY",
           f"code={v.code!r}")


def test_upload_path_not_allowed():
    v = _policy.check_all(
        action="upload",
        url="https://example.com",
        context={"upload_file_paths": ["D:\\secrets\\leak.exe"]},
    )
    _check("upload 路径不在白名单 → 拒绝",
           not v.allowed and v.code == "UPLOAD_PATH_NOT_ALLOWED",
           f"code={v.code!r}")


def test_upload_ext_denied():
    v = _policy.check_all(
        action="upload",
        url="https://example.com",
        context={"upload_file_paths": ["C:\\Windows\\Temp\\virus.bat"]},
    )
    _check("upload 扩展名不在白名单 → 拒绝",
           not v.allowed and v.code == "UPLOAD_EXT_DENIED",
           f"code={v.code!r}")


def test_upload_valid():
    v = _policy.check_all(
        action="upload",
        url="https://example.com",
        context={"upload_file_paths": [
            "C:\\Windows\\Temp\\doc.pdf",
            "C:\\Windows\\Temp\\pic.png",
        ]},
    )
    _check("upload 合规 → 允许",
           v.allowed and v.code == "OK",
           f"code={v.code!r}")


test_upload_no_paths()
test_upload_too_many()
test_upload_path_not_allowed()
test_upload_ext_denied()
test_upload_valid()


# ============================================================
# 4) keyboard 文本长度 + 按键白名单
# ============================================================
print("== 4. keyboard 文本/按键校验 ==")


def test_keyboard_empty():
    v = _policy.check_all(
        action="keyboard", url="https://example.com", context={}
    )
    _check("keyboard 全空 → 拒绝",
           not v.allowed and v.code == "KEYBOARD_EMPTY",
           f"code={v.code!r}")


def test_keyboard_text_too_long():
    v = _policy.check_all(
        action="keyboard",
        url="https://example.com",
        context={"keyboard_text": "x" * 3000},
    )
    _check("keyboard 文本超 2000 → 拒绝",
           not v.allowed and v.code == "KEYBOARD_TEXT_TOO_LONG",
           f"code={v.code!r}")


def test_keyboard_disallowed_key():
    v = _policy.check_all(
        action="keyboard",
        url="https://example.com",
        context={"keyboard_keys": ["F1", "F13"]},  # F13 不在白名单
    )
    _check("keyboard 非法键 F13 → 拒绝",
           not v.allowed and v.code == "KEYBOARD_KEY_DENIED",
           f"code={v.code!r}")


def test_keyboard_valid():
    v = _policy.check_all(
        action="keyboard",
        url="https://example.com",
        context={"keyboard_text": "hello", "keyboard_keys": ["Tab", "Enter", "F1"]},
    )
    _check("keyboard 合规 → 允许",
           v.allowed and v.code == "OK",
           f"code={v.code!r}")


test_keyboard_empty()
test_keyboard_text_too_long()
test_keyboard_disallowed_key()
test_keyboard_valid()


# ============================================================
# 5) Evidence 字段
# ============================================================
print("== 5. Evidence 字段 ==")


def test_evidence_25f_fields():
    rec = EvidenceRecord(
        tenant_id="t-25f-1", actor="verify", action="drag"
    )
    _check("EvidenceRecord.drag_from_selector 字段在位",
           hasattr(rec, "drag_from_selector"))
    _check("EvidenceRecord.drag_to_selector 字段在位",
           hasattr(rec, "drag_to_selector"))
    _check("EvidenceRecord.upload_file_paths 字段在位",
           hasattr(rec, "upload_file_paths"))
    _check("EvidenceRecord.upload_count 字段在位",
           hasattr(rec, "upload_count"))
    _check("EvidenceRecord.keyboard_text 字段在位",
           hasattr(rec, "keyboard_text"))
    _check("EvidenceRecord.keyboard_keys 字段在位",
           hasattr(rec, "keyboard_keys"))


test_evidence_25f_fields()


# ============================================================
# 6) _REAL_DISPATCH 注册
# ============================================================
print("== 6. dispatch 表 ==")


def test_dispatch_25f():
    d = _executor._REAL_DISPATCH
    _check("drag 在 dispatch", "drag" in d)
    _check("upload 在 dispatch", "upload" in d)
    _check("keyboard 在 dispatch", "keyboard" in d)
    _check("dispatch 总数 = 9（3 只读 + 6 写）", len(d) == 9,
           f"n={len(d)}")


test_dispatch_25f()


# ============================================================
# 7) handler 签名
# ============================================================
print("== 7. handler 签名 ==")


def test_handler_signatures():
    import inspect
    for name in ("_real_execute_drag", "_real_execute_upload", "_real_execute_keyboard"):
        fn = getattr(_executor, name)
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        _check(f"{name} 接受 evidence/profile 关键字",
               "evidence" in params and "profile" in params,
               f"params={params}")


test_handler_signatures()


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
