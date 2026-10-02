# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""goodjob_crm 执行器 —— 爱马仕驱动 GoodJob「所有功能」的 D3 双模驱动层（批次 C · 2026-09-20）。

两条驱动路径，按 capability 自动路由（调度主权恒归 Hermes）：

1. 原生直驱（native，无外桥）—— 优丁 CRM 自有真相，写优丁 PG：
   单证（PI/CI/PL）、履约阶段、线索建档、商机阶段。走
   `app.services.goodjob.native_fulfillment`，进程内直驱，无 HTTP。
   能力名：trade.docs / document.generate_pi / crm.sync_stage /
   crm.sync_lead / crm.update_opportunity …

2. D3 全量桥（catalog-driven）—— GoodJob SaaS 全 232 操作 / 45 能力域：
   签名 5 字段任务包 → POST /api/uj-bridge/task-packages → poll 续租约 → 终态。
   GoodJob 只受理不自发（D3 调度主权）。能力名：goodjob_crm.<family>
   （family 来自共享能力目录 gj_capability_catalog.json，由 GoodJob 侧
   agent-api-contracts.ts 自动派生；加功能 = 改目录数据，零改本执行器）。

铁律：需审批的域（whatsapp / commission / trade-documents / system-settings…）
在任务包上带 requires_approval，GoodJob 侧领取执行走审批闸——Hermes 不绕过。
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode
from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

# ── 原生能力集（写优丁 PG，无外桥）────────────────────────────
_CAPS = frozenset({
    "trade.docs",
    "document.generate_pi", "generate_pi", "pi_generator",
    "document.generate_trade_docs", "trade_document.generate",
    "crm.sync_stage", "sync_stage",
    "crm.sync_lead", "sync_lead",
    "crm.update_opportunity", "update_opportunity",
})

_CAP_DEFAULT_DOCTYPE = {
    "trade.docs": "PI",
    "document.generate_pi": "PI",
    "generate_pi": "PI",
    "pi_generator": "PI",
    "document.generate_trade_docs": "CI",
    "trade_document.generate": "CI",
}

# 原生能力声明（保留提交版契约，planner 可见 + 审批标记）
_NATIVE_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    "trade.docs": {
        "desc": "外贸单证（本项目 CRM 原生：PI/CI/PL → 优丁 PG）",
        "input": ["doc_type", "items", "inquiry_id", "order_id"],
        "output": ["doc_type", "doc_no", "document", "invoice_persisted"],
        "cost": {"tokens": 0, "seconds": 3},
        "needs_approval": True,
    },
    "document.generate_pi": {
        "desc": "形式发票 PI（爱马仕直驱原生套打；账户未配置不编造银行号）",
        "input": ["product_name", "quantity", "unit_price", "buyer_name", "order_id"],
        "output": ["pi_number", "doc_no", "document", "bank_configured"],
        "cost": {"tokens": 0, "seconds": 3},
        "needs_approval": True,
    },
    "document.generate_trade_docs": {
        "desc": "发运单证 CI/PL（原生；写 invoices）",
        "input": ["doc_type", "items", "order_id", "bl_number"],
        "output": ["doc_type", "doc_no", "document"],
        "cost": {"tokens": 0, "seconds": 3},
        "needs_approval": True,
    },
    "crm.sync_stage": {
        "desc": "7 步履约阶段推进（orders 状态机 + 管线/触点，无外桥）",
        "input": ["order_id", "stage", "step_number"],
        "output": ["success", "status", "order_number", "pipeline"],
        "cost": {"tokens": 0, "seconds": 2},
        "needs_approval": False,
    },
    "crm.sync_lead": {
        "desc": "线索建档（inquiries + opportunities，本项目 CRM）",
        "input": ["company_name", "contact_name", "email"],
        "output": ["lead_id", "inquiry_id", "success"],
        "cost": {"tokens": 0, "seconds": 2},
        "needs_approval": False,
    },
    "crm.update_opportunity": {
        "desc": "更新商机阶段（opportunities）",
        "input": ["opportunity_id", "status"],
        "output": ["success", "stage"],
        "cost": {"tokens": 0, "seconds": 1},
        "needs_approval": False,
    },
}

# ── D3 全量桥配置（环境变量注入；测试可覆盖）───────────────────
_GOODJOB_BRIDGE_BASE_URL = os.environ.get(
    "GOODJOB_BRIDGE_BASE_URL", "http://127.0.0.1:4188"
)  # GoodJob 默认 PORT=4188（旧 mock 写 5188 是错的）
_GOODJOB_BRIDGE_TOKEN = os.environ.get("UJ_BRIDGE_TOKEN", "")
_BRIDGE_TIMEOUT = float(os.environ.get("GOODJOB_BRIDGE_TIMEOUT", "30"))
_POLL_INTERVAL = float(os.environ.get("GOODJOB_BRIDGE_POLL_INTERVAL", "0.5"))
_MAX_POLLS = int(os.environ.get("GOODJOB_BRIDGE_MAX_POLLS", "40"))


def _catalog_path() -> Path:
    return Path(__file__).resolve().parent / "gj_capability_catalog.json"


def _load_catalog() -> Dict[str, Any]:
    try:
        with _catalog_path().open(encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:  # noqa: BLE001
        logger.warning("GoodJob 能力目录加载失败：%s", exc)
        return {"capabilities": [], "task_types": ["capability.invoke"]}


def _resolve_family(capability: str) -> Optional[str]:
    """goodjob_crm.<family> / goodjob.<family> / <family> → 裸 family 名。"""
    name = (capability or "").lower().strip()
    for prefix in ("goodjob_crm.", "goodjob."):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    return name or None


class GoodJobCrmExecutor(BaseExecutor):
    """爱马仕驱动 GoodJob 全量功能：原生直驱（优丁 PG）+ D3 桥（全 232 操作）。"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        dry_run: bool = False,
    ):
        self.base_url = (base_url or _GOODJOB_BRIDGE_BASE_URL).rstrip("/")
        self.token = token if token is not None else _GOODJOB_BRIDGE_TOKEN
        self.dry_run = dry_run
        self._catalog = _load_catalog()
        self._by_family: Dict[str, Dict[str, Any]] = {
            c["family"]: c for c in self._catalog.get("capabilities", [])
        }

    @classmethod
    def get_executor_name(cls) -> str:
        return "goodjob_crm"

    # ── 能力声明：原生 + 目录，planner 零改动即可见全部功能 ──────
    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = dict(_NATIVE_CAPABILITIES)
        cat = _load_catalog()
        for c in cat.get("capabilities", []):
            fname = c["family"]
            ops = c.get("ops", [])
            out[f"goodjob_crm.{fname}"] = {
                "desc": c.get("desc", ""),
                "family": fname,
                "via": "uj_bridge",
                "risk": c.get("risk", "low"),
                "needs_approval": c.get("needs_approval", False),
                "operations": [f"{o['method']} {o['path']}" for o in ops],
                "input": ["method", "path", "body"],
                "output": ["task_handle", "status", "result_ref"],
                "cost": {"tokens": 50, "seconds": 3},
            }
        return out

    # ── 原生直驱路径（写优丁 PG，无外桥）────────────────────────
    def _run_native(
        self, node: TaskNode, context: ExecutorContext, capability: str
    ) -> ExecutorResult:
        from app.services.goodjob import native_fulfillment as native

        db = context.db
        params: dict[str, Any] = dict(node.input or {})

        if capability in ("crm.sync_stage", "sync_stage"):
            order_id = str(
                params.get("order_id") or params.get("order") or params.get("inquiry_id") or ""
            ).strip()
            stage = str(params.get("stage") or "deposit_received").strip()
            step_number = int(params.get("step_number") or 1)
            out = native.sync_fulfillment_stage(
                tenant_id=context.tenant_id,
                order_id=order_id or None,
                stage=stage,
                step_number=step_number,
                params=params,
                db=db,
            )
            return ExecutorResult(
                node_id=node.id,
                status="succeeded" if out.get("success") else "failed",
                output={**out, "executor": self.get_executor_name(), "capability": capability},
                error=None if out.get("success") else str(out.get("error") or "native_stage_failed"),
            )

        if capability in ("crm.sync_lead", "sync_lead"):
            lead = {
                "company_name": params.get("company_name") or params.get("company"),
                "contact_name": params.get("contact_name") or params.get("name"),
                "email": params.get("email"),
                "phone": params.get("phone"),
                "country": params.get("country"),
                "source": params.get("source") or "hermes_goodjob_crm",
                "inquiry_id": params.get("inquiry_id"),
                "product": params.get("product"),
                "message": params.get("message"),
            }
            out = native.sync_lead(tenant_id=context.tenant_id, lead_data=lead, db=db)
            return ExecutorResult(
                node_id=node.id,
                status="succeeded" if out.get("success") else "failed",
                output={**out, "executor": self.get_executor_name(), "capability": capability},
                error=None if out.get("success") else str(out.get("error") or "native_lead_failed"),
            )

        if capability in ("crm.update_opportunity", "update_opportunity"):
            out = native.update_opportunity(
                opportunity_id=str(params.get("opportunity_id") or params.get("lead_id") or "").strip(),
                status=str(params.get("status") or "").strip(),
                tenant_id=context.tenant_id,
                db=db,
            )
            return ExecutorResult(
                node_id=node.id,
                status="succeeded" if out.get("success") else "failed",
                output={**out, "executor": self.get_executor_name(), "capability": capability},
                error=None if out.get("success") else str(out.get("error") or "native_opp_failed"),
            )

        # 单证族（PI / CI / PL …）
        docs_list = params.get("docs")
        if isinstance(docs_list, list) and len(docs_list) > 1:
            multi_docs = {}
            for dt in docs_list:
                sub_out = native.generate_trade_document(
                    doc_type=str(dt).upper(),
                    tenant_id=context.tenant_id,
                    params=params,
                    db=db,
                    order_id=str(params.get("order_id") or params.get("order") or "").strip() or None,
                    inquiry_id=str(params.get("inquiry_id") or params.get("inquiry") or "").strip() or None,
                )
                multi_docs[str(dt).upper()] = sub_out
            all_ok = all(d.get("success") for d in multi_docs.values())
            return ExecutorResult(
                node_id=node.id,
                status="succeeded" if all_ok else "failed",
                output={
                    "documents": multi_docs,
                    "doc_types": list(multi_docs.keys()),
                    "doc_no": multi_docs.get("CI", {}).get("doc_no") or multi_docs.get("PL", {}).get("doc_no"),
                    "ci_number": multi_docs.get("CI", {}).get("ci_number"),
                    "pl_number": multi_docs.get("PL", {}).get("doc_no"),
                    "executor": self.get_executor_name(),
                    "capability": capability,
                },
                error=None if all_ok else "some_documents_failed",
            )

        doc_type = str(params.get("doc_type") or _CAP_DEFAULT_DOCTYPE.get(capability, "PI")).upper()
        out = native.generate_trade_document(
            doc_type=doc_type,
            tenant_id=context.tenant_id,
            params=params,
            db=db,
            order_id=str(params.get("order_id") or params.get("order") or "").strip() or None,
            inquiry_id=str(params.get("inquiry_id") or params.get("inquiry") or "").strip() or None,
        )
        status = "succeeded" if out.get("success") else "failed"
        if out.get("success") and out.get("bank_configured") is False:
            status = "degraded"
        return ExecutorResult(
            node_id=node.id,
            status=status,
            output={**out, "executor": self.get_executor_name(), "capability": capability},
            error=None if out.get("success") else str(out.get("error") or "native_document_failed"),
        )

    # ── D3 全量桥路径（GoodJob SaaS 表面）────────────────────────
    def _idempotency_key(self, node: TaskNode, context: ExecutorContext, op: str) -> str:
        raw = "|".join([context.tenant_id, context.plan_id or "-", node.id, op or "-"])
        digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
        return f"hermes-gj:{node.id}:{digest}"

    def _build_task_package(
        self, node: TaskNode, context: ExecutorContext, family: str, op: str
    ) -> Dict[str, Any]:
        node_input = dict(node.input or {})
        method = str(node_input.pop("method", "")).strip().upper()
        path = str(node_input.pop("path", "")).strip()
        if not method and not path and op:
            parts = op.split(" ", 1)
            method = parts[0].upper()
            path = parts[1] if len(parts) > 1 else ""
        return {
            "tenant_id": context.tenant_id,
            "idempotency_key": self._idempotency_key(node, context, op),
            "lease_ttl": int(node_input.pop("lease_ttl", 900)),
            "checkpoint": str(node_input.pop("checkpoint", "v1")),
            "budget": {
                "max_retries": int(node_input.pop("max_retries", 2)),
                "hermes_plan_id": context.plan_id,
                "hermes_node_id": node.id,
            },
            "task_type": "capability.invoke",
            "payload": {
                "family": family,
                "method": method,
                "path": path,
                "body": node_input,
            },
        }

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _post_task(self, pkg: Dict[str, Any]):
        import requests

        from urllib.parse import urljoin

        url = urljoin(self.base_url, "/api/uj-bridge/task-packages")
        resp = requests.post(url, json=pkg, headers=self._headers(), timeout=_BRIDGE_TIMEOUT)
        ct = (resp.headers.get("content-type") or "").lower()
        data = resp.json() if "application/json" in ct else resp.text
        return resp.status_code, data

    def _poll_task(self, key: str) -> Dict[str, Any]:
        import requests
        import time

        from urllib.parse import urljoin

        url = urljoin(self.base_url, f"/api/uj-bridge/task-packages/{key}")
        last: Dict[str, Any] = {}
        for _ in range(_MAX_POLLS):
            resp = requests.get(url, headers=self._headers(), timeout=_BRIDGE_TIMEOUT)
            if resp.status_code == 404:
                return {"status": "lease_expired", "error": "task_not_found"}
            resp.raise_for_status()
            last = resp.json().get("data", {})
            if last.get("status") in ("done", "failed", "lease_expired"):
                return last
            time.sleep(_POLL_INTERVAL)
        return last or {"status": "lease_expired", "error": "poll_timeout"}

    def _run_bridge(
        self, node: TaskNode, context: ExecutorContext, family: str
    ) -> ExecutorResult:
        cap = self._by_family.get(family)
        op = (node.input or {}).get("op") or ""
        pkg = self._build_task_package(node, context, family, str(op))

        if self.dry_run:
            payload = pkg["payload"]
            opcheck = f"{payload.get('method', '').upper()} {payload.get('path', '')}".strip()
            if cap and opcheck:
                legal = {f"{o['method']} {o['path']}" for o in cap.get("ops", [])}
                if opcheck not in legal:
                    return ExecutorResult(
                        node_id=node.id,
                        status="failed",
                        error=f"capability_op_not_in_catalog:{family}:{opcheck}",
                        output={"dry_run": True, "family": family},
                    )
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "dry_run": True,
                    "task_handle": pkg["idempotency_key"],
                    "family": family,
                    "operation": opcheck,
                    "requires_approval": bool(cap.get("needs_approval")) if cap else False,
                    "result_ref": f"dryrun:{family}",
                },
            )

        if not self.token:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                error="UJ_BRIDGE_TOKEN_not_configured",
                output={"hint": "set UJ_BRIDGE_TOKEN + GOODJOB_BRIDGE_BASE_URL, or use dry_run for offline"},
            )

        try:
            status_code, data = self._post_task(pkg)
            if status_code == 401:
                return ExecutorResult(node_id=node.id, status="failed", error="bridge_unauthorized", output=data)
            if status_code == 503:
                return ExecutorResult(node_id=node.id, status="failed", error="bridge_unconfigured", output=data)
            if status_code >= 400:
                return ExecutorResult(node_id=node.id, status="failed", error=f"bridge_http_{status_code}", output=data)

            pol = self._poll_task(pkg["idempotency_key"])
            pstatus = pol.get("status")
            if pstatus == "done":
                return ExecutorResult(
                    node_id=node.id,
                    status="succeeded",
                    output={
                        "task_handle": pkg["idempotency_key"],
                        "family": family,
                        "requires_approval": bool(cap.get("needs_approval")) if cap else False,
                        "result_ref": pol.get("result_ref"),
                    },
                )
            # failed / lease_expired → 交回 Hermes 重派（D3 调度主权）
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                error=pol.get("error") or f"bridge_task_{pstatus}",
                output={
                    "task_handle": pkg["idempotency_key"],
                    "family": family,
                    "bridge_status": pstatus,
                    "result_ref": pol.get("result_ref"),
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("GoodJob D3 桥驱动失败: %s", exc)
            return ExecutorResult(node_id=node.id, status="failed", error=f"{type(exc).__name__}: {exc}")

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        """按 capability 自动路由：原生能力→优丁 PG；目录 family→D3 桥。"""
        capability = (node.capability or "").lower().strip()
        for prefix in ("goodjob_crm.", "goodjob."):
            if capability.startswith(prefix):
                capability = capability[len(prefix):]
                break

        # 1) 原生直驱（优丁 PG 自有真相）
        if capability in _CAPS:
            return self._run_native(node, context, capability)

        # 2) D3 全量桥（GoodJob SaaS 能力域）
        family = _resolve_family(node.capability or "")
        if family in self._by_family:
            return self._run_bridge(node, context, family)

        # 3) 未知能力：诚实跳过（不静默假成功）
        return ExecutorResult(
            node_id=node.id,
            status="skipped",
            output={"capability": node.capability, "executor": self.get_executor_name()},
            error=(
                f"goodjob_crm 不支持 capability={node.capability!r}；"
                f"原生={sorted(_CAPS)} | 目录={sorted(self._by_family.keys())}"
            ),
        )

    # ── 供外部调用的原生便捷方法（保留提交版契约）─────────────
    async def sync_lead_to_crm(self, lead_data: dict[str, Any], db: Any = None) -> dict[str, Any]:
        from app.services.goodjob import native_fulfillment as native

        session = db
        close_after = False
        if session is None:
            from app.core.database import SessionLocal

            session = SessionLocal()
            close_after = True
        try:
            return native.sync_lead(tenant_id=lead_data.get("tenant_id"), lead_data=lead_data, db=session)
        finally:
            if close_after:
                session.close()

    async def update_opportunity_status(self, opportunity_id: str, status: str, db: Any = None) -> dict[str, Any]:
        from app.services.goodjob import native_fulfillment as native

        session = db
        close_after = False
        if session is None:
            from app.core.database import SessionLocal

            session = SessionLocal()
            close_after = True
        try:
            return native.update_opportunity(opportunity_id=opportunity_id, status=status, db=session)
        finally:
            if close_after:
                session.close()


# 注册执行器（与旧版同名，__init__.py 的 import 不变）
ExecutorRegistry.register(GoodJobCrmExecutor())
