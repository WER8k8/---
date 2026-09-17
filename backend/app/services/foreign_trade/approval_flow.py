# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""多级审批流 -- sales_rep -> sales_manager -> director，支持超阈值逐级上报。"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    ESCALATED = "escalated"


class ApprovalLevel(str, Enum):
    SALES_REP = "sales_rep"
    SALES_MANAGER = "sales_manager"
    DIRECTOR = "director"


@dataclass
class ApprovalRecord:
    actor_role: str
    actor_id: str
    action: str
    timestamp: datetime
    notes: Optional[str] = None


@dataclass
class ApprovalRequest:
    negotiation_id: str
    tenant_id: Optional[str]
    round_no: int
    requested_discount: float
    concession_price: float
    base_price: float
    requester_id: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    current_level: ApprovalLevel = ApprovalLevel.SALES_REP
    history: List[ApprovalRecord] = field(default_factory=list)
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    decision_at: Optional[datetime] = None
    decision_by: Optional[str] = None
    decision_notes: Optional[str] = None
    timeout_warned: bool = False


class ApprovalFlow:
    TIMEOUT_HOURS: Dict[ApprovalLevel, int] = {
        ApprovalLevel.SALES_REP: 24,
        ApprovalLevel.SALES_MANAGER: 48,
        ApprovalLevel.DIRECTOR: 72,
    }
    ESCALATION_THRESHOLDS: Dict[ApprovalLevel, float] = {
        ApprovalLevel.SALES_REP: 5.0,
        ApprovalLevel.SALES_MANAGER: 10.0,
    }
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pending: Dict[str, Dict[str, ApprovalRequest]] = {}

    def submit_for_approval(self, *, negotiation_id: str, tenant_id: str, round_no: int, requested_discount: float, concession_price: float, base_price: float, requester_id: str, extra_threshold: Optional[float] = None) -> ApprovalRequest:
        if requested_discount >= self.ESCALATION_THRESHOLDS[ApprovalLevel.SALES_MANAGER]:
            level = ApprovalLevel.DIRECTOR
        elif requested_discount >= self.ESCALATION_THRESHOLDS[ApprovalLevel.SALES_REP]:
            level = ApprovalLevel.SALES_MANAGER
        else:
            level = ApprovalLevel.SALES_REP
        req = ApprovalRequest(negotiation_id=negotiation_id, tenant_id=tenant_id, round_no=round_no, requested_discount=requested_discount, concession_price=concession_price, base_price=base_price, requester_id=requester_id, current_level=level)
        with self._lock:
            tid_map = self._pending.setdefault(tenant_id, {})
            tid_map[negotiation_id] = req
        logger.info("[Approval] submit negotiation=%s level=%s discount=%.1f%%", negotiation_id, level.value, requested_discount)
        return req

    def approve(self, *, negotiation_id: str, tenant_id: str, approver_id: str, approver_role: str, notes: Optional[str] = None) -> ApprovalRequest:
        with self._lock:
            req = self._get(tenant_id, negotiation_id)
            if req is None:
                raise ValueError(f"未找到待审批记录: negotiation={negotiation_id}")
            if req.status != ApprovalStatus.PENDING:
                raise ValueError(f"审批状态已非 pending: {req.status.value}")
            record = ApprovalRecord(actor_role=approver_role, actor_id=approver_id, action="approve", timestamp=datetime.now(timezone.utc), notes=notes)
            req.history.append(record)
            req.status = ApprovalStatus.APPROVED
            req.decision_at = record.timestamp
            req.decision_by = approver_id
            req.decision_notes = notes
        logger.info("[Approval] approved negotiation=%s by=%s", negotiation_id, approver_id)
        return req

    def reject(self, *, negotiation_id: str, tenant_id: str, rejecter_id: str, rejecter_role: str, notes: Optional[str] = None) -> ApprovalRequest:
        with self._lock:
            req = self._get(tenant_id, negotiation_id)
            if req is None:
                raise ValueError(f"未找到待审批记录: negotiation={negotiation_id}")
            if req.status != ApprovalStatus.PENDING:
                raise ValueError(f"审批状态已非 pending: {req.status.value}")
            record = ApprovalRecord(actor_role=rejecter_role, actor_id=rejecter_id, action="reject", timestamp=datetime.now(timezone.utc), notes=notes)
            req.history.append(record)
            req.status = ApprovalStatus.REJECTED
            req.decision_at = record.timestamp
            req.decision_by = rejecter_id
            req.decision_notes = notes
        logger.info("[Approval] rejected negotiation=%s by=%s", negotiation_id, rejecter_id)
        return req

    def pending(self, *, negotiation_id: str, tenant_id: str) -> Optional[ApprovalRequest]:
        with self._lock:
            return self._get(tenant_id, negotiation_id)

    def check_timeouts(self) -> List[ApprovalRequest]:
        now = datetime.now(timezone.utc)
        timed_out: List[ApprovalRequest] = []
        with self._lock:
            for tid, negotiations in self._pending.items():
                for neg_id, req in list(negotiations.items()):
                    if req.status != ApprovalStatus.PENDING:
                        continue
                    timeout_hours = self.TIMEOUT_HOURS.get(req.current_level, 24)
                    elapsed = (now - req.submitted_at).total_seconds() / 3600.0
                    if elapsed >= timeout_hours and not req.timeout_warned:
                        req.status = ApprovalStatus.TIMEOUT
                        req.timeout_warned = True
                        timed_out.append(req)
        return timed_out

    def warn_upcoming(self, *, threshold_hours: float = 4.0) -> List[ApprovalRequest]:
        now = datetime.now(timezone.utc)
        upcoming: List[ApprovalRequest] = []
        with self._lock:
            for tid, negotiations in self._pending.items():
                for neg_id, req in negotiations.items():
                    if req.status != ApprovalStatus.PENDING:
                        continue
                    timeout_hours = self.TIMEOUT_HOURS.get(req.current_level, 24)
                    elapsed = (now - req.submitted_at).total_seconds() / 3600.0
                    remaining = timeout_hours - elapsed
                    if 0 < remaining <= threshold_hours:
                        upcoming.append(req)
        return upcoming

    def _get(self, tenant_id: str, negotiation_id: str) -> Optional[ApprovalRequest]:
        return self._pending.get(tenant_id, {}).get(negotiation_id)

    def clear(self, *, tenant_id: str, negotiation_id: str) -> bool:
        with self._lock:
            tid_map = self._pending.get(tenant_id)
            if tid_map and negotiation_id in tid_map:
                del tid_map[negotiation_id]
                return True
        return False



ApprovalAuditHook = Callable[[ApprovalRecord, ApprovalRequest], None]
_audit_hooks: List[ApprovalAuditHook] = []


def register_audit_hook(hook: ApprovalAuditHook) -> None:
    _audit_hooks.append(hook)


def fire_audit_event(record: ApprovalRecord, req: ApprovalRequest) -> None:
    for hook in _audit_hooks:
        try:
            hook(record, req)
        except Exception as exc:
            logger.warning("[Approval] audit hook error: %s", exc)


_default_flow: Optional[ApprovalFlow] = None
_flow_lock = threading.Lock()


def get_approval_flow() -> ApprovalFlow:
    global _default_flow
    with _flow_lock:
        if _default_flow is None:
            _default_flow = ApprovalFlow()
        return _default_flow
