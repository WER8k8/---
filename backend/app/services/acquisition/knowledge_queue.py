# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P3-8 阅读知识队列 — 认证/诈骗/合规必读（业务员能勾）。

原则：
    · 知识条目静态种子 + 完成状态
    · 未读优先展示；不假装自动学会
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class KnowledgeItem:
    id: str
    title: str
    category: str
    plain: str
    why: str
    source_hint: str = ""
    done: bool = False
    done_at: str = ""
    done_by: str = ""


_SEED: list[dict[str, Any]] = [
    {
        "id": "know-cert-official",
        "title": "认证官方清单怎么查",
        "category": "认证合规",
        "plain": "SASO/CE/ISO 等以官方或认可机构名单为准，不轻信「包过」中介。",
        "why": "无证宣称有证 = 红线，会丢单甚至违法",
        "source_hint": "目的国海关/标准机构官网；工厂证书扫描件核对编号",
    },
    {
        "id": "know-scam-cases",
        "title": "外贸诈骗常见套路",
        "category": "风险",
        "plain": "假水单、假汇款通知、换收款账号、超大单压价催发货、冒充老客户。",
        "why": "定金未到账勿排产；改账户必须二次核实",
        "source_hint": "公司内部案例库 + 银行回单真伪",
    },
    {
        "id": "know-whatsapp-policy",
        "title": "WhatsApp / 社媒触达政策",
        "category": "渠道",
        "plain": "禁止群发骚扰；先背调再私信；退订/拉黑立即停止；养号勿自动化违规。",
        "why": "封号 = 渠道黑洞，获客链路中断",
        "source_hint": "WA Business 政策；平台条款",
    },
    {
        "id": "know-gdpr",
        "title": "GDPR / 隐私与退订",
        "category": "合规",
        "plain": "欧盟线索：合法依据、可退订、名单抑制；邮件需有退订路径。",
        "why": "违规罚款高；退订后系统必须抑制",
        "source_hint": "GDPR 简明指南；系统抑制名单",
    },
    {
        "id": "know-cbam",
        "title": "CBAM 碳边境（欧盟建材相关）",
        "category": "合规",
        "plain": "部分建材出口欧盟可能涉及碳数据申报；报价前了解客户是否要求碳足迹。",
        "why": "客户要碳数据时临时找会丢单",
        "source_hint": "欧盟 CBAM 官方说明；品类是否覆盖",
    },
    {
        "id": "know-incoterms",
        "title": "Incoterms / 报价术语",
        "category": "报价",
        "plain": "CIF/FOB/DDP 责任与费用分界写进报价与 PI，避免口头默认。",
        "why": "术语误解 = 运费纠纷与亏损",
        "source_hint": "Incoterms 2020 简表",
    },
    {
        "id": "know-payment-risk",
        "title": "付款风险与定金习惯",
        "category": "收款",
        "plain": "新客提高定金；高风险地区更谨慎；全款需核验实力；到账再排产。",
        "why": "资损主因之一",
        "source_hint": "系统 Playbook + 付款风险闸",
    },
    {
        "id": "know-identity-consistent",
        "title": "身份一致红线",
        "category": "获客",
        "plain": "同一买家全渠道同一称呼/公司/人设；禁止开发信里编造背调事实。",
        "why": "身份漂移 = 信任崩塌",
        "source_hint": "Buyer Master 身份锁",
    },
    {
        "id": "know-india-playbook",
        "title": "印度新客付款习惯",
        "category": "国别",
        "plain": "首款常谈全款或高比例定金；议价频繁勿首轮过早让价。",
        "why": "赊销风险高，回款难",
        "source_hint": "Playbook IN×new",
    },
    {
        "id": "know-saudi-playbook",
        "title": "沙特/中东工程单要点",
        "category": "国别",
        "plain": "认证与交期敏感；斋月影响工期；30/70 付款常见，交期写工作日。",
        "why": "漏认证/交期会直接丢标",
        "source_hint": "Playbook SA×project",
    },
    {
        "id": "know-scam-fake-watermark",
        "title": "假水单/假汇款套路",
        "category": "风险",
        "plain": "PS 过的银行水单可伪造；以银行入账为准，不以截图为准。",
        "why": "未到账就排产 = 直接资损",
        "source_hint": "公司内部风控",
    },
    {
        "id": "know-sample-fee",
        "title": "样品费与运费归属",
        "category": "样品",
        "plain": "寄样前书面确认：样品费、运费谁出、是否大货抵扣。",
        "why": "样品黑洞会吃掉利润与时间",
        "source_hint": "跟单卡样品状态机",
    },
    {
        "id": "know-quote-validity",
        "title": "报价有效期与汇率",
        "category": "报价",
        "plain": "报价必写有效期；汇率波动大时锁汇或调价条款。",
        "why": "过期报价被强执行 = 亏损",
        "source_hint": "报价有效期闸 P3-2",
    },
    {
        "id": "know-tender-docs",
        "title": "招投标资质包清单",
        "category": "大单",
        "plain": "营业执照、体系认证、检测报告、业绩案例、收款账户、工厂视频。",
        "why": "缺一项可能废标",
        "source_hint": "TenderEngine checklist",
    },
    {
        "id": "know-africa-payment",
        "title": "非洲/高风险地收款",
        "category": "国别",
        "plain": "提高定金；核实付款账户；小单可拼柜但收款安全优先。",
        "why": "付款欺诈高发",
        "source_hint": "Playbook AF×new",
    },
    {
        "id": "know-sanctions-screen",
        "title": "制裁名单筛查习惯",
        "category": "合规",
        "plain": "大单/新市场先筛名单；系统未接真源时结果不可当合规证明。",
        "why": "触碰制裁 = 法律与收款双风险",
        "source_hint": "sanctions_source / risk-rescan",
    },
    {
        "id": "know-identity-lock-buyer",
        "title": "Buyer Master 身份锁",
        "category": "获客",
        "plain": "姓名/性别全渠道锁定；改身份需人工合并，禁止同邮箱多人设。",
        "why": "身份乱了 CRM 与信任都崩",
        "source_hint": "Buyer Master Store",
    },
]


class KnowledgeQueueStore:
    def __init__(self, seed: bool = True) -> None:
        self._items: dict[str, KnowledgeItem] = {}
        if seed:
            for s in _SEED:
                self._items[s["id"]] = KnowledgeItem(**s)

    def list(self, *, tenant_id: str = "", category: str = "", only_pending: bool = False) -> list[dict[str, Any]]:
        out = []
        for it in self._items.values():
            if category and it.category != category:
                continue
            if only_pending and it.done:
                continue
            out.append(it.__dict__)
        out.sort(key=lambda x: (x.get("done", False), x.get("category") or "", x.get("id") or ""))
        return out

    def mark_done(self, item_id: str, *, by: str = "sales") -> dict[str, Any]:
        it = self._items.get(item_id)
        if it is None:
            return {"ok": False, "code": "not_found", "message": f"无此知识条目 {item_id}"}
        if it.done:
            return {"ok": True, "code": "already_done", "message": f"「{it.title}」已读过", "item": it.__dict__}
        it.done = True
        it.done_at = _now()
        it.done_by = by
        return {"ok": True, "code": "done", "message": f"已标记读完：{it.title}", "item": it.__dict__}

    def mark_pending(self, item_id: str) -> dict[str, Any]:
        it = self._items.get(item_id)
        if it is None:
            return {"ok": False, "code": "not_found", "message": f"无此知识条目 {item_id}"}
        it.done = False
        it.done_at = ""
        it.done_by = ""
        return {"ok": True, "code": "reset", "message": f"已重置为待读：{it.title}", "item": it.__dict__}

    def report(self, *, tenant_id: str = "") -> dict[str, Any]:
        items = self.list(tenant_id=tenant_id)
        done_n = sum(1 for i in items if i.get("done"))
        total = len(items)
        pending = [i for i in items if not i.get("done")]
        cats: dict[str, int] = {}
        for i in items:
            cats[i.get("category") or "其他"] = cats.get(i.get("category") or "其他", 0) + 1
        next_id = pending[0] if pending else None
        plain = (
            f"合规/知识待读 {len(pending)}/{total}。"
            + (f"下一题：{next_id['title']}" if next_id else "全部已读完，继续保持。")
        )
        return {
            "tenant_id": tenant_id,
            "total": total,
            "done_count": done_n,
            "pending_count": len(pending),
            "categories": cats,
            "next_item": next_id,
            "items": items,
            "plain_summary": plain,
            "hint": "知识队列不会自动替你合规，但能保证该读的不漏；读完在作战台勾选。",
        }


knowledge_queue_store = KnowledgeQueueStore()
