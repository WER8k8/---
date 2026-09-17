"""批次 B 隔离冒烟测试（垫片模式）：UJ 侧 GoodJob 桥全链验证。

用法：python -m tests.goodjob_bridge_verify
依赖：仅标准库（executor/interfaces/桥服务均为 stdlib-only，无需 SQLAlchemy）。

覆盖（设计文档 uj-annex-integration-design §10.5 / §10.19）：
1. 五字段任务包铁律（缺一拒发，两侧一致）
2. submit 的 HTTP 信封形状（URL/认证头/五字段+task_type+payload 同行传输）
3. 幂等：同幂等键客户端缓存（网络优化层），重复提交不再发 HTTP
4. poll：done/failed/lease_expired/pending/404/异常 六态
5. 桥禁用（GOODJOB_BASE_URL 缺失）：enabled=False、工厂返回 None、静默跳过
6. customer_pool 投影：tenant_id 红线、载荷形状、确定性幂等键
7. trade-document 桥：白名单/上限/内容哈希幂等键、submit+poll
8. 两侧契约一致性：task_type 与 DOC_TYPES 与 GoodJob TS 侧逐一比对
"""

from __future__ import annotations

import json
import os
import sys
import types
import importlib.util
from typing import Any, Mapping

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


for _pkg in ("app", "app.orchestration", "app.orchestration.executors",
             "app.services", "app.services.goodjob"):
    _new_dummy(_pkg)

_ORCH = os.path.join(_BACKEND, "app", "orchestration")
interfaces = _load_from_file("app.orchestration.interfaces", os.path.join(_ORCH, "interfaces.py"))
executor_mod = _load_from_file(
    "app.orchestration.executors.goodjob_executor",
    os.path.join(_ORCH, "executors", "goodjob_executor.py"),
)
_GJ = os.path.join(_BACKEND, "app", "services", "goodjob")
projection_mod = _load_from_file(
    "app.services.goodjob.customer_pool_projection",
    os.path.join(_GJ, "customer_pool_projection.py"),
)
doc_bridge_mod = _load_from_file(
    "app.services.goodjob.trade_document_bridge",
    os.path.join(_GJ, "trade_document_bridge.py"),
)

TaskPackage = interfaces.TaskPackage
GoodJobExecutor = executor_mod.GoodJobExecutor
BridgeTransport = executor_mod.BridgeTransport
GoodJobBridgeError = executor_mod.GoodJobBridgeError
GoodJobBridgeDisabledError = executor_mod.GoodJobBridgeDisabledError
build_goodjob_executor = executor_mod.build_goodjob_executor

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} {detail}")


class FakeTransport(BridgeTransport):
    """假传输：记录请求，按脚本回放响应。"""

    def __init__(self, script: list[tuple[int, dict[str, Any]]] | None = None):
        super().__init__()
        self.calls: list[dict[str, Any]] = []
        self.script = list(script or [])
        self.fail_with: Exception | None = None

    def request(self, method, url, headers, body):
        self.calls.append(
            {"method": method, "url": url, "headers": dict(headers),
             "body": json.loads(body.decode("utf-8")) if body else None}
        )
        if self.fail_with is not None:
            raise self.fail_with
        if self.script:
            status, payload = self.script.pop(0)
            return status, json.dumps(payload).encode("utf-8")
        return 200, json.dumps({"data": {"handle": "auto"}}).encode("utf-8")


def _package(**overrides: Any) -> TaskPackage:
    fields: dict[str, Any] = {
        "tenant_id": "tenant-001",
        "idempotency_key": "gj-pool:i1:pending:2026-09-02T00:00:00Z",
        "lease_ttl": 900,
        "checkpoint": "v1",
        "budget": {"max_retries": 2},
    }
    fields.update(overrides)
    return TaskPackage(**fields)


def main() -> int:
    global PASS, FAIL
    print("== 1. 五字段铁律（缺一拒发）==")
    ex = GoodJobExecutor(base_url="http://127.0.0.1:4188", token="tok123")
    for field, value in (
        ("tenant_id", " "), ("idempotency_key", ""), ("lease_ttl", 0), ("checkpoint", None),
    ):
        try:
            ex.submit(_package(**{field: value}), task_type="customer_pool.sync", payload={})
            check(f"缺 {field} 拒发", False)
        except ValueError:
            check(f"缺 {field} 拒发", True)
        except Exception as exc:  # noqa: BLE001
            check(f"缺 {field} 拒发", False, f"异常类型 {type(exc).__name__}")

    print("== 2. submit HTTP 信封形状 ==")
    ft = FakeTransport(script=[(200, {"data": {"handle": "h-1", "duplicate": False}})])
    ex2 = GoodJobExecutor(base_url="http://127.0.0.1:4188/", token="tok123", transport=ft)
    pkg = _package()
    handle = ex2.submit(pkg, task_type="customer_pool.sync", payload={"master": "uj"})
    check("受理句柄透传", handle == "h-1", handle)
    call = ft.calls[0]
    check("POST 至桥端点", call["method"] == "POST" and call["url"] == "http://127.0.0.1:4188/api/uj-bridge/task-packages", call["url"])
    check("Bearer 认证头", call["headers"].get("Authorization") == "Bearer tok123")
    body = call["body"]
    for field in ("tenant_id", "idempotency_key", "lease_ttl", "checkpoint", "budget"):
        check(f"信封含 {field}", field in body)
    check("task_type 随包同行", body.get("task_type") == "customer_pool.sync")
    check("payload 随包同行", body.get("payload") == {"master": "uj"})

    print("== 3. 幂等客户端缓存 ==")
    handle_again = ex2.submit(pkg, task_type="customer_pool.sync", payload={"master": "uj"})
    check("同键重复提交不再发 HTTP", len(ft.calls) == 1, f"实际 {len(ft.calls)} 次")
    check("重复提交返回缓存句柄", handle_again == "h-1")

    print("== 4. poll 六态 ==")
    states = [
        (200, {"data": {"status": "done", "result_ref": "projection:t1:i1"}}, "done→ok=True"),
        (200, {"data": {"status": "failed", "error": "boom"}}, "failed→ok=False"),
        (200, {"data": {"status": "lease_expired"}}, "lease_expired→ok=False"),
        (200, {"data": {"status": "pending"}}, "pending→None"),
        (404, {"message": "not found"}, "404→None"),
    ]
    for status, payload, label in states:
        ft3 = FakeTransport(script=[(status, payload)])
        ex3 = GoodJobExecutor(base_url="http://x", transport=ft3)
        result = ex3.poll("k")
        if label.startswith("done"):
            check(label, result is not None and result.ok and result.result_ref == "projection:t1:i1")
        elif label.startswith(("failed", "lease")):
            check(label, result is not None and not result.ok)
        else:
            check(label, result is None)
    ft_err = FakeTransport()
    ft_err.fail_with = GoodJobBridgeError("不可达")
    ex_err = GoodJobExecutor(base_url="http://x", transport=ft_err)
    try:
        ex_err.poll("k")
        check("桥异常抛出", False)
    except GoodJobBridgeError:
        check("桥异常抛出", True)

    print("== 5. 桥禁用（未配置 GOODJOB_BASE_URL）==")
    os.environ.pop("GOODJOB_BASE_URL", None)
    check("工厂返回 None", build_goodjob_executor() is None)
    ex_off = GoodJobExecutor(base_url="", transport=FakeTransport())
    check("enabled=False", not ex_off.enabled)
    try:
        ex_off.submit(_package(), task_type="customer_pool.sync", payload={})
        check("禁用态 submit 拒绝", False)
    except GoodJobBridgeDisabledError:
        check("禁用态 submit 拒绝", True)

    print("== 6. customer_pool 投影 ==")
    class Row:
        id = "i1"
        tenant_id = "tenant-001"
        name = "Alice"
        email = "alice@example.com"
        phone = "+86"
        product = "棉柔巾"
        message = "Need price" * 100
        status = "pending"
        source_channel = "seo"
        attribution_channel = "google"
        updated_at = None
        created_at = "2026-09-02T00:00:00Z"
    row = Row()
    no_tenant = Row()
    no_tenant.tenant_id = ""
    try:
        projection_mod.build_projection(no_tenant)
        check("缺 tenant_id 拒投影", False)
    except ValueError:
        check("缺 tenant_id 拒投影", True)
    proj = projection_mod.build_projection(row)
    check("master=uj", proj["master"] == "uj")
    check("source_of_truth=inquiries", proj["source_of_truth"] == "inquiries")
    check("投影含 entity.inquiry_id", proj["entity"]["inquiry_id"] == "i1")
    check("客户字段齐全", all(k in proj["customer"] for k in ("name", "email", "status", "source_channel")))
    check("留言截断 200 字", len(proj["customer"]["message_excerpt"]) <= 200)
    check("幂等键确定性", projection_mod.projection_idempotency_key(row) == projection_mod.projection_idempotency_key(row))
    row.status = "converted"
    check("状态变更换新键", projection_mod.projection_idempotency_key(row) != projection_mod.projection_idempotency_key(Row()))
    ft4 = FakeTransport(script=[(200, {"data": {"handle": "h-pool"}})])
    ex4 = GoodJobExecutor(base_url="http://x", transport=ft4)
    check("sync 推送返回句柄", projection_mod.sync_inquiry_to_pool(ex4, row) == "h-pool")
    check("sync 信封 task_type 正确", ft4.calls[0]["body"]["task_type"] == "customer_pool.sync")
    check("禁用态 sync 静默 None", projection_mod.sync_inquiry_to_pool(ex_off, row) is None)

    print("== 7. trade-document 桥 ==")
    ft5 = FakeTransport(script=[(200, {"data": {"handle": "h-doc"}})])
    ex5 = GoodJobExecutor(base_url="http://x", transport=ft5)
    items = [{"description": "棉柔巾", "quantity": 1000, "unit_price": 0.35}]
    check("合法派单返回句柄",
          doc_bridge_mod.submit_document_task(
              ex5, tenant_id="t1", inquiry_id="i1", doc_type="QUOTATION", items=items) == "h-doc")
    body5 = ft5.calls[0]["body"]
    check("单证信封 task_type 正确", body5["task_type"] == "trade_document.generate")
    check("载荷含 inquiry_id/doc_type/items", body5["payload"]["inquiry_id"] == "i1" and body5["payload"]["doc_type"] == "QUOTATION")
    for label, kwargs in (
        ("非法 doc_type 拒单", {"doc_type": "INVOICE_FAKENEW", "tenant_id": "t1", "inquiry_id": "i1", "items": []}),
        ("缺 tenant_id 拒单", {"doc_type": "CI", "tenant_id": " ", "inquiry_id": "i1", "items": []}),
        ("缺 inquiry_id 拒单", {"doc_type": "CI", "tenant_id": "t1", "inquiry_id": "", "items": []}),
        ("条目超上限拒单", {"doc_type": "CI", "tenant_id": "t1", "inquiry_id": "i1", "items": [{}]*201}),
    ):
        try:
            doc_bridge_mod.submit_document_task(ex5, **kwargs)
            check(label, False)
        except ValueError:
            check(label, True)
    key_a = doc_bridge_mod.document_idempotency_key("t1", "i1", "CI", items, {})
    key_b = doc_bridge_mod.document_idempotency_key("t1", "i1", "CI", items, {})
    key_c = doc_bridge_mod.document_idempotency_key("t1", "i1", "CI", items + [{"x": 1}], {})
    check("同内容同幂等键", key_a == key_b)
    check("内容变更换键", key_a != key_c)
    ft6 = FakeTransport(script=[(200, {"data": {"status": "done", "result_ref": "doc:d1"}})])
    ex6 = GoodJobExecutor(base_url="http://x", transport=ft6)
    result = doc_bridge_mod.poll_document_task(ex6, "gj-doc:t1:i1:CI:abc")
    check("poll 单证结果", result is not None and result.ok and result.result_ref == "doc:d1")
    check("禁用态派单静默 None",
          doc_bridge_mod.submit_document_task(ex_off, tenant_id="t1", inquiry_id="i1", doc_type="CI", items=[]) is None)

    print("== 8. 两侧契约一致性（UJ py <-> GoodJob ts）==")
    ts_candidates = [
        os.path.normpath(os.path.join(_BACKEND, "..", "..", "..", "_external", "goodjob-crm",
                                      "backend", "src", "integrations", "uj-bridge-routes.ts")),
        os.path.normpath(os.path.join(_BACKEND, "..", "_external", "goodjob-crm",
                                      "backend", "src", "integrations", "uj-bridge-routes.ts")),
    ]
    ts_path = next((p for p in ts_candidates if os.path.exists(p)), "")
    if ts_path:
        ts_src = open(ts_path, encoding="utf-8").read()
        check("task_type customer_pool.sync 一致",
              'TASK_TYPE_CUSTOMER_POOL = "customer_pool.sync"' in ts_src)
        check("task_type trade_document.generate 一致",
              'TASK_TYPE_TRADE_DOCUMENT = "trade_document.generate"' in ts_src)
        ts_docs = set()
        for line in ts_src.splitlines():
            line = line.strip().strip(",")
            if line.startswith('"') and line.endswith('"') and line.strip('"') in {
                "PI", "CI", "PL", "CONTRACT", "QUOTATION", "CUSTOMS", "COO", "SHIPPING"}:
                ts_docs.add(line.strip('"'))
        check("DOC_TYPES 八类逐一一致", ts_docs == set(doc_bridge_mod.DOC_TYPES), f"ts={sorted(ts_docs)}")
    else:
        check("GoodJob TS 源码可达", False, ts_path)

    print(f"\n结果: {PASS} 通过 / {FAIL} 失败")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
