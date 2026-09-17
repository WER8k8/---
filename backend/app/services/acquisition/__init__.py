# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客服务层 · Buyer Master 身份锁 + 跟单卡 + Playbook。

对齐细胞总谱：
    ACQ-E-01 BuyerMaster（身份锁）
    ACQ-E-06 OpsCard（跟单作战卡）
    ACQ-E-08 TradePlaybook（国别/类型作战包）

原则：
    · 身份一致：同 buyer_id 全渠道同一人设，禁止漂移
    · 跟单卡：谁在跟 / 发什么货 / 物流 / 联系 / 交代 / 付款
    · Playbook：国别×类型提醒（如印度新客首款偏全款）
    · 诚实：缺字段返回 None/空，不编造
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════
# ACQ-E-01 Buyer Master（身份锁）
# ═══════════════════════════════════════════════════════════

@dataclass
class BuyerMaster:
    """联系人主档 — 全渠道唯一身份。"""

    buyer_id: str = field(default_factory=lambda: str(uuid4()))
    tenant_id: str = ""
    # 公司
    company_name: str = ""
    company_domain: str = ""
    company_country: str = ""
    company_city: str = ""
    # 联系人（锁定展示）
    contact_name: str = ""
    contact_gender: str = "unknown"  # unknown/male/female/other
    contact_title: str = ""
    email: str = ""
    phone_e164: str = ""
    whatsapp_id: str = ""
    linkedin_url: str = ""
    # 分类
    buyer_type: str = "unknown"  # importer/distributor/contractor/epc/retailer/project_owner/unknown
    industry: str = ""
    languages: list[str] = field(default_factory=list)
    # 身份锁
    persona_locked: bool = True
    # 来源与风险
    source: str = ""
    risk_flags: list[str] = field(default_factory=list)
    owner_user_id: str = ""
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def display_identity(self) -> str:
        """对外展示用的身份串 — 全渠道必须一致。"""
        gender_map = {"male": "男", "female": "女", "other": "其他", "unknown": ""}
        g = gender_map.get(self.contact_gender, "")
        title = f" {self.contact_title}" if self.contact_title else ""
        company = f" @ {self.company_name}" if self.company_name else ""
        return f"{self.contact_name}{title}{company}".strip()


class BuyerMasterStore:
    """Buyer Master 内存存储（生产替换为 DB 模型）。

    规则：
        · tenant_id + email 唯一
        · persona_locked=True 时禁止改姓名/性别
        · 冲突时告警并保留旧档
    """

    def __init__(self) -> None:
        self._by_id: dict[str, BuyerMaster] = {}
        self._by_email: dict[tuple[str, str], str] = {}  # (tenant_id, email) -> buyer_id
        self.conflict_alerts: list[dict[str, Any]] = []

    def upsert(self, buyer: BuyerMaster) -> tuple[BuyerMaster, bool, list[str]]:
        """返回 (buyer, is_new, alerts)。"""
        alerts: list[str] = []
        key = (buyer.tenant_id, (buyer.email or "").lower())
        if key[1]:
            existing_id = self._by_email.get(key)
            if existing_id and existing_id != buyer.buyer_id:
                # 身份冲突告警
                existing = self._by_id.get(existing_id)
                alert = {
                    "type": "identity_conflict",
                    "existing_id": existing_id,
                    "incoming_id": buyer.buyer_id,
                    "email": buyer.email,
                    "at": _now_iso(),
                }
                self.conflict_alerts.append(alert)
                alerts.append(
                    f"邮箱 {buyer.email} 已关联 buyer_id={existing_id}，"
                    f"请人工合并（禁止同一邮箱多人设）"
                )
                # persona_locked：保留旧档，不覆盖姓名/性别
                if existing and existing.persona_locked:
                    if existing.contact_name and buyer.contact_name and existing.contact_name != buyer.contact_name:
                        alerts.append(
                            f"身份锁拒绝改名：{existing.contact_name} ≠ {buyer.contact_name}"
                        )
                        buyer.contact_name = existing.contact_name
                    if existing.contact_gender != buyer.contact_gender and existing.contact_gender != "unknown":
                        buyer.contact_gender = existing.contact_gender
                        alerts.append("身份锁拒绝改性别")
                buyer.buyer_id = existing_id
                existing = existing or buyer
                existing.updated_at = _now_iso()
                self._by_id[existing_id] = existing
                self._by_email[key] = existing_id
                return existing, False, alerts
            if key[1]:
                self._by_email[key] = buyer.buyer_id
        is_new = buyer.buyer_id not in self._by_id
        buyer.updated_at = _now_iso()
        self._by_id[buyer.buyer_id] = buyer
        return buyer, is_new, alerts

    def get(self, buyer_id: str) -> Optional[BuyerMaster]:
        return self._by_id.get(buyer_id)

    def get_by_email(self, tenant_id: str, email: str) -> Optional[BuyerMaster]:
        bid = self._by_email.get((tenant_id, (email or "").lower()))
        return self._by_id.get(bid) if bid else None

    def list_by_tenant(self, tenant_id: str) -> list[BuyerMaster]:
        return [b for b in self._by_id.values() if b.tenant_id == tenant_id]


# ═══════════════════════════════════════════════════════════
# ACQ-E-06 Ops Card（跟单作战卡）
# ═══════════════════════════════════════════════════════════

@dataclass
class OpsCardNote:
    author: str = ""
    body: str = ""
    at: str = field(default_factory=_now_iso)
    pinned: bool = False


@dataclass
class OpsCardSkuLine:
    name: str = ""
    spec: str = ""
    qty: float = 0.0
    unit: str = ""
    price: float = 0.0
    currency: str = "USD"


@dataclass
class OpsCardLogistics:
    forwarder: str = ""
    carrier: str = ""
    bl_no: str = ""
    container_no: str = ""
    etd: str = ""
    eta: str = ""
    milestone: str = ""


@dataclass
class OpsCardPayment:
    pi_no: str = ""
    deposit_amount: float = 0.0
    deposit_due: str = ""
    deposit_paid_at: str = ""
    balance_amount: float = 0.0
    balance_status: str = ""  # pending/paid/overdue
    voucher_url: str = ""
    overdue_days: int = 0


@dataclass
class OpsCard:
    """客户跟单作战卡 — 租户每天要看的一页。"""

    card_id: str = field(default_factory=lambda: str(uuid4()))
    inquiry_id: str = ""
    buyer_id: str = ""
    tenant_id: str = ""
    stage: str = "new"
    # 人
    owner_user_id: str = ""
    collaborators: list[str] = field(default_factory=list)
    handoff_history: list[dict[str, Any]] = field(default_factory=list)
    # 货
    sku_lines: list[OpsCardSkuLine] = field(default_factory=list)
    container_hint: str = ""
    # 物流
    logistics: OpsCardLogistics = field(default_factory=OpsCardLogistics)
    # 联系
    last_touch_at: str = ""
    last_channel: str = ""
    last_summary: str = ""
    next_action: str = ""
    next_action_at: str = ""
    # 交代
    notes: list[OpsCardNote] = field(default_factory=list)
    # 收款
    payment: OpsCardPayment = field(default_factory=OpsCardPayment)
    # 买家快照
    buyer_display: str = ""
    buyer_grade: str = ""
    buyer_grade_reason: str = ""
    playbook_tips: list[str] = field(default_factory=list)
    # 流失
    loss_reasons: list[str] = field(default_factory=list)
    loss_note: str = ""
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d

    def summary_lines(self) -> dict[str, str]:
        """傻子都行：六组一句话。"""
        last = self.last_touch_at or "未联系"
        return {
            "负责人": self.owner_user_id or "未分配",
            "货": self._sku_text() or "未填货物",
            "物流": self._logistics_text() or "未发货",
            "联系": f"{last} · {self.last_summary or self.next_action or '无记录'}",
            "交代": self.notes[0].body if self.notes else "无",
            "付款": self._payment_text() or "未收款",
        }

    def _sku_text(self) -> str:
        if not self.sku_lines:
            return ""
        s = self.sku_lines[0]
        more = f" 等{len(self.sku_lines)}项" if len(self.sku_lines) > 1 else ""
        return f"{s.name} {s.spec} {s.qty}{s.unit}{more}"

    def _logistics_text(self) -> str:
        lg = self.logistics
        if not lg.bl_no and not lg.container_no:
            return ""
        return f"{lg.carrier or lg.forwarder} {lg.bl_no or lg.container_no} {lg.milestone}".strip()

    def _payment_text(self) -> str:
        p = self.payment
        if not p.pi_no and p.deposit_amount == 0 and p.balance_amount == 0:
            return ""
        dep = "已收" if p.deposit_paid_at else ("待收" if p.deposit_amount else "-")
        bal = p.balance_status or "pending"
        return f"PI={p.pi_no or '-'} 定金{dep} 尾款{bal}"


class OpsCardStore:
    """跟单卡内存存储（生产替换为 DB）。"""

    def __init__(self) -> None:
        self._by_inquiry: dict[str, OpsCard] = {}
        self._by_id: dict[str, OpsCard] = {}

    def materialize(
        self,
        *,
        tenant_id: str,
        inquiry_id: str,
        buyer_id: str = "",
        owner_user_id: str = "",
        buyer: Optional[BuyerMaster] = None,
        grade: str = "",
        grade_reason: str = "",
        playbook_tips: Optional[list[str]] = None,
        stage: str = "new",
    ) -> OpsCard:
        card = self._by_inquiry.get(inquiry_id)
        if card is None:
            card = OpsCard(inquiry_id=inquiry_id, tenant_id=tenant_id)
        card.buyer_id = buyer_id or card.buyer_id
        card.owner_user_id = owner_user_id or card.owner_user_id
        card.stage = stage or card.stage
        if buyer:
            card.buyer_display = buyer.display_identity()
        if grade:
            card.buyer_grade = grade
        if grade_reason:
            card.buyer_grade_reason = grade_reason
        if playbook_tips is not None:
            card.playbook_tips = list(playbook_tips)
        card.updated_at = _now_iso()
        self._by_inquiry[inquiry_id] = card
        self._by_id[card.card_id] = card
        return card

    def get(self, card_id: str) -> Optional[OpsCard]:
        return self._by_id.get(card_id)

    def get_by_inquiry(self, inquiry_id: str) -> Optional[OpsCard]:
        return self._by_inquiry.get(inquiry_id)

    def update(self, card: OpsCard) -> OpsCard:
        card.updated_at = _now_iso()
        self._by_id[card.card_id] = card
        if card.inquiry_id:
            self._by_inquiry[card.inquiry_id] = card
        return card

    def add_note(self, inquiry_id: str, author: str, body: str, pinned: bool = False) -> OpsCard:
        card = self._by_inquiry.get(inquiry_id)
        if card is None:
            card = OpsCard(inquiry_id=inquiry_id)
        card.notes.append(OpsCardNote(author=author, body=body, pinned=pinned))
        if pinned and len(card.notes) > 1:
            card.notes.sort(key=lambda n: (not n.pinned, n.at))
        return self.update(card)

    def set_owner(self, inquiry_id: str, owner_user_id: str, note: str = "") -> OpsCard:
        card = self._by_inquiry.get(inquiry_id)
        if card is None:
            card = OpsCard(inquiry_id=inquiry_id)
        if card.owner_user_id and card.owner_user_id != owner_user_id:
            card.handoff_history.append({
                "from": card.owner_user_id,
                "to": owner_user_id,
                "at": _now_iso(),
                "note": note,
            })
        card.owner_user_id = owner_user_id
        return self.update(card)

    def record_touch(
        self,
        inquiry_id: str,
        *,
        channel: str,
        summary: str,
        next_action: str = "",
        next_action_at: str = "",
        direction: str = "outbound",
    ) -> OpsCard:
        card = self._by_inquiry.get(inquiry_id)
        if card is None:
            card = OpsCard(inquiry_id=inquiry_id)
        card.last_touch_at = _now_iso()
        card.last_channel = channel
        card.last_summary = summary
        if next_action:
            card.next_action = next_action
        if next_action_at:
            card.next_action_at = next_action_at
        return self.update(card)

    def record_loss(self, inquiry_id: str, reasons: list[str], note: str = "") -> OpsCard:
        card = self._by_inquiry.get(inquiry_id)
        if card is None:
            card = OpsCard(inquiry_id=inquiry_id)
        card.loss_reasons = reasons
        card.loss_note = note
        card.stage = "lost"
        return self.update(card)

    def update_payment(self, inquiry_id: str, **kwargs: Any) -> OpsCard:
        card = self._by_inquiry.get(inquiry_id)
        if card is None:
            card = OpsCard(inquiry_id=inquiry_id)
        p = card.payment
        for k, v in kwargs.items():
            if hasattr(p, k):
                setattr(p, k, v)
        return self.update(card)

    def update_logistics(self, inquiry_id: str, **kwargs: Any) -> OpsCard:
        card = self._by_inquiry.get(inquiry_id)
        if card is None:
            card = OpsCard(inquiry_id=inquiry_id)
        lg = card.logistics
        for k, v in kwargs.items():
            if hasattr(lg, k):
                setattr(lg, k, v)
        return self.update(card)


# ═══════════════════════════════════════════════════════════
# ACQ-E-08 TradePlaybook（国别 × 类型 × 阶段）
# ═══════════════════════════════════════════════════════════

@dataclass
class PlaybookEntry:
    playbook_id: str = field(default_factory=lambda: str(uuid4()))
    country: str = ""
    buyer_type: str = ""
    stage: str = ""  # empty = all
    tips: list[str] = field(default_factory=list)
    payment_bias: str = ""
    warnings: list[str] = field(default_factory=list)
    talk_tracks: list[str] = field(default_factory=list)
    enabled: bool = True
    source: str = "seed"


# 内置种子 Playbook（对齐第二大脑 08/18；行业常识，需经验校准）
_SEED_PLAYBOOKS: list[dict[str, Any]] = [
    {
        "country": "IN",
        "buyer_type": "new",
        "payment_bias": "lean_full_prepay_or_high_deposit",
        "tips": [
            "印度新客首款常谈全款或高比例定金；先验付款能力再深谈定制。",
            "议价频繁属常见，勿首轮过早让价。",
            "确认公司实体与采购决策人后再投入深度报价。",
        ],
        "warnings": ["谨防过度赊销；定金到账再排产。"],
        "talk_tracks": [
            "首回必问：数量 / 目的港 / 认证 / 付款方式与时间。",
        ],
    },
    {
        "country": "SA",
        "buyer_type": "project",
        "payment_bias": "deposit_30_70_common",
        "tips": [
            "中东工程单：认证与交期敏感；准备 SASO/项目案例。",
            "验厂与关系建立重要，可主动提供工厂视频。",
            "付款 30/70 常见，交期写清工作日与排产前提。",
        ],
        "warnings": ["斋月与高温季影响工地进度，报价有效期要明确。"],
        "talk_tracks": ["强调认证与交期可靠性，而非只报最低价。"],
    },
    {
        "country": "EU",
        "buyer_type": "professional",
        "payment_bias": "formal_terms",
        "tips": [
            "欧美专业买家重认证、合规与交期可靠性。",
            "邮件规范、规格数据齐全；避免夸张营销话术。",
        ],
        "warnings": ["注意 GDPR 与退订要求。"],
        "talk_tracks": ["提供规格表 + 认证 + 质保条款摘要。"],
    },
    {
        "country": "AF",
        "buyer_type": "new",
        "payment_bias": "higher_deposit_required",
        "tips": [
            "部分非洲/高风险地付款风险较高，提高定金比例。",
            "小批量可谈拼柜，但收款安全优先。",
        ],
        "warnings": ["谨慎赊销；核实付款账户。"],
        "talk_tracks": ["付款方案前置，再谈定制规格。"],
    },
]


class PlaybookStore:
    def __init__(self, seed: bool = True) -> None:
        self._items: list[PlaybookEntry] = []
        if seed:
            self.load_seeds()

    def load_seeds(self) -> None:
        for s in _SEED_PLAYBOOKS:
            self._items.append(PlaybookEntry(**s))

    def add(self, entry: PlaybookEntry) -> PlaybookEntry:
        self._items.append(entry)
        return entry

    def match(
        self,
        country: str = "",
        buyer_type: str = "",
        stage: str = "",
    ) -> list[PlaybookEntry]:
        """返回匹配的 Playbook（空 country/type 可放宽）。"""
        country = (country or "").upper()[:2]
        buyer_type = (buyer_type or "").lower()
        out = []
        for p in self._items:
            if not p.enabled:
                continue
            if p.country and country and p.country != country:
                continue
            if p.buyer_type and buyer_type:
                # new 匹配 new/unknown
                if p.buyer_type == "new" and buyer_type not in ("new", "unknown", ""):
                    continue
                if p.buyer_type not in ("new", "") and p.buyer_type != buyer_type:
                    continue
            if p.stage and stage and p.stage != stage:
                continue
            out.append(p)
        return out

    def tips_for(self, country: str, buyer_type: str = "new") -> list[str]:
        """作战提示：先按 国家×类型 精确；无命中则放宽到该国任意类型。"""
        tips: list[str] = []
        matched = self.match(country=country, buyer_type=buyer_type)
        if not matched and country:
            matched = self.match(country=country, buyer_type="")
        for p in matched:
            tips.extend(p.tips)
            tips.extend(p.warnings)
        return tips

    def all(self) -> list[PlaybookEntry]:
        return list(self._items)


# ── 全局单例（生产可替换为 DI）───────────────────────────────
buyer_store = BuyerMasterStore()
ops_card_store = OpsCardStore()
playbook_store = PlaybookStore()


def score_grade(score: int) -> tuple[str, str]:
    """0-100 → (A/B/C/D, 大白话理由)。"""
    if score >= 80:
        return "A", "需求清楚、身份可信，建议深跟"
    if score >= 60:
        return "B", "较有意向，标准跟进并补齐资格四问"
    if score >= 40:
        return "C", "信息不足或匹配一般，保持低成本触达"
    return "D", "风险或低意向，不投入深度报价"
