# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GoodJob 执行器适配器 · 批次 B 桥的 UJ 侧端口.

设计出处：uj-annex-integration-design §10.5 / §10.19。
插槽原型：EXECUTOR（六插槽契约 app/orchestration/interfaces.py）。

链路：UJ(Hermes 任务包) --HTTP--> GoodJob /api/uj-bridge/task-packages

铁律：
- 五字段任务包（tenant_id / idempotency_key / lease_ttl / checkpoint / budget）
  缺一即拒绝派发——本适配器在发送前校验，GoodJob 侧 zod 再校验一次；
- 幂等：同 idempotency_key 重复提交不产生重复执行（客户端缓存 + 服务端
  去重双保险），客户端缓存仅是网络优化，正确性由服务端保证；
- 失败安全：桥未配置（GOODJOB_BASE_URL 缺失）即禁用，调用方静默跳过，
  绝不阻断询盘主流程；
- 调度主权：GoodJob 侧只吃 UJ 签发的任务包，本适配器不订阅任何
  GoodJob 事件、不给 GoodJob 派活（D3 红线）。

任务内容（task_type + payload）随包同行传输：五字段是调度信封，
信封之外的任务体不进 TaskPackage，避免契约膨胀。
"""

from __future__ import annotations

import json
import os
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.orchestration.interfaces import (
    ExecutionResult,
    ExecutorAdapter,
    SlotArchetype,
    TaskPackage,
)

DEFAULT_TIMEOUT_SECONDS = 10.0
TASK_PATH = "/api/uj-bridge/task-packages"
TASK_TYPE_CUSTOMER_POOL = "customer_pool.sync"
TASK_TYPE_TRADE_DOCUMENT = "trade_document.generate"
TASK_TYPE_STAGE_SYNC = "crm.sync_stage"
_HANDLE_CACHE_LIMIT = 1000


class GoodJobBridgeError(RuntimeError):
    """桥通信失败（网络不可达 / 非 2xx / 响应异常）。"""


class GoodJobBridgeDisabledError(GoodJobBridgeError):
    """桥未配置（缺 GOODJOB_BASE_URL）。"""


class BridgeTransport:
    """HTTP 传输层：默认 urllib 实现，测试注入假传输替身。"""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        self.timeout = timeout

    def request(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
    ) -> tuple[int, bytes]:
        req = Request(url=url, data=body, method=method)
        for key, value in headers.items():
            if value:
                req.add_header(key, value)
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                return resp.status, resp.read()
        except HTTPError as exc:
            return exc.code, exc.read()
        except URLError as exc:
            raise GoodJobBridgeError(f"GoodJob 桥不可达: {exc.reason}") from exc


def _parse_json(status: int, raw: bytes) -> dict[str, Any]:
    try:
        data = json.loads(raw.decode("utf-8"))
        return data if isinstance(data, dict) else {"message": str(data)[:200]}
    except (ValueError, UnicodeDecodeError):
        return {"message": f"HTTP {status} 非 JSON 响应: {raw[:200]!r}"}


class GoodJobExecutor(ExecutorAdapter):
    """批次 B 桥 UJ 侧执行器：submit 派发任务包，poll 查询结果。"""

    archetype = SlotArchetype.EXECUTOR

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        transport: BridgeTransport | None = None,
    ) -> None:
        self.base_url = (base_url or os.environ.get("GOODJOB_BASE_URL", "")).strip().rstrip("/")
        self.token = (token or os.environ.get("GOODJOB_BRIDGE_TOKEN", "")).strip()
        self._transport = transport or BridgeTransport()
        self._handles: dict[str, str] = {}

    @property
    def enabled(self) -> bool:
        return bool(self.base_url)

    @staticmethod
    def _validate_package(package: TaskPackage) -> None:
        if not str(package.tenant_id or "").strip():
            raise ValueError("任务包缺 tenant_id（五字段铁律）")
        if not str(package.idempotency_key or "").strip():
            raise ValueError("任务包缺 idempotency_key（五字段铁律）")
        if int(package.lease_ttl) <= 0:
            raise ValueError("任务包 lease_ttl 必须为正整数（五字段铁律）")
        if not str(package.checkpoint or "").strip():
            raise ValueError("任务包缺 checkpoint（五字段铁律）")

    def _require_enabled(self) -> None:
        if not self.enabled:
            raise GoodJobBridgeDisabledError("GOODJOB_BASE_URL 未配置，GoodJob 桥禁用")

    def _auth_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "X-UJ-Client": "uj-hermes/1.0"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def submit(
        self,
        package: TaskPackage,
        *,
        task_type: str,
        payload: Mapping[str, Any],
    ) -> str:
        """派发任务包至 GoodJob 桥；返回受理句柄（=幂等键）。"""
        self._require_enabled()
        self._validate_package(package)
        cached = self._handles.get(package.idempotency_key)
        if cached is not None:
            return cached
        body = json.dumps(
            {
                "tenant_id": package.tenant_id,
                "idempotency_key": package.idempotency_key,
                "lease_ttl": package.lease_ttl,
                "checkpoint": package.checkpoint,
                "budget": dict(package.budget),
                "task_type": task_type,
                "payload": dict(payload),
            },
            ensure_ascii=False,
        ).encode("utf-8")
        status, raw = self._transport.request(
            "POST", f"{self.base_url}{TASK_PATH}", self._auth_headers(), body
        )
        data = _parse_json(status, raw)
        if status != 200:
            raise GoodJobBridgeError(
                f"GoodJob 桥拒收任务包: HTTP {status} {data.get('message', '')}"
            )
        handle = str((data.get("data") or {}).get("handle") or package.idempotency_key)
        if len(self._handles) >= _HANDLE_CACHE_LIMIT:
            self._handles.pop(next(iter(self._handles)))
        self._handles[package.idempotency_key] = handle
        return handle

    def poll(self, idempotency_key: str) -> ExecutionResult | None:
        """按幂等键查询结果；pending 返回 None，404 返回 None（待重派）。"""
        self._require_enabled()
        status, raw = self._transport.request(
            "GET",
            f"{self.base_url}{TASK_PATH}/{idempotency_key}",
            self._auth_headers(),
            None,
        )
        if status == 404:
            return None
        data = _parse_json(status, raw)
        if status != 200:
            raise GoodJobBridgeError(
                f"GoodJob 桥查询失败: HTTP {status} {data.get('message', '')}"
            )
        task = data.get("data") or {}
        task_status = str(task.get("status") or "")
        if task_status == "done":
            return ExecutionResult(
                ok=True,
                idempotency_key=idempotency_key,
                result_ref=task.get("result_ref"),
            )
        if task_status in ("failed", "lease_expired"):
            return ExecutionResult(
                ok=False,
                idempotency_key=idempotency_key,
                error=str(task.get("error") or task_status),
            )
        return None


def build_goodjob_executor() -> GoodJobExecutor | None:
    """工厂：未配置 GOODJOB_BASE_URL 返回 None（调用方静默跳过）。"""
    executor = GoodJobExecutor()
    return executor if executor.enabled else None
