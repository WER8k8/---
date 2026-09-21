# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P1-8 RFM 分层 + 标签体系 + ABM 账号聚合。

背景（真实取证）：
    · `inquiries` 有 email/product/created_at/priority_score，但**没有 company_id**，
      询盘与 companies 之间没有外键——所以账号聚合只能靠「邮箱域名 / 公司名归一」锚定。
    · `companies` 有 domain + icp/intent/account_score，但**没有标签列**（P1-8 需补）。
    · 成交金额在跟单卡 payload 里（OpsCard.won_amount），按 inquiry_id 关联回账号。

三块能力：
    ① RFM 分层：按账号聚合 R(最近询盘)/F(询盘频次)/M(成交额)，各打 1-5 分 → 客户分层
    ② 标签体系：规则化生成账号标签（高价值/高频询盘/沉睡待唤醒/高ICP…），可落库到
       companies.tags 供筛选运营
    ③ ABM 账号聚合：把一个买家在多个联系人/多条询盘/多张跟单卡上的动作汇总成一个账号视图

注意：本项目 datetime 列普遍 naive（见 2026-09-19 记忆的时区教训），
      所有时间差必须先经 _aware() 规整，否则 aware-naive 相减直接 TypeError。
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Optional

# 免费邮箱：不能作为「企业账号」锚点，此时退回按买家名归并
_FREE_MAIL = {
    "gmail.com", "yahoo.com", "yahoo.co.jp", "hotmail.com", "outlook.com", "live.com",
    "aol.com", "icloud.com", "protonmail.com", "mail.com", "gmx.com", "qq.com",
    "163.com", "126.com", "sina.com", "foxmail.com", "yandex.com", "web.de",
}

# 客户分层（中文，运营可直接用）
SEGMENTS = {
    "champion": "冠军客户",
    "loyal": "忠诚客户",
    "potential": "潜力客户",
    "new": "新客户",
    "at_risk": "流失风险",
    "hibernating": "沉睡客户",
    "regular": "一般客户",
}


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    """naive → UTC aware（项目 datetime 列普遍 naive，差运算前必须规整）。"""
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _norm_name(name: str) -> str:
    """公司名归一：小写、去常见后缀与标点。"""
    s = (name or "").strip().lower()
    s = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", s)
    s = re.sub(
        r"\b(co\.?|ltd\.?|limited|llc|inc\.?|corp\.?|jsc|jsc\.|plc|gmbh|s\.?a\.?|bv|pty)\b",
        "",
        s,
    )
    return re.sub(r"\s+", " ", s).strip()


def account_key(email: str = "", company_name: str = "") -> tuple[str, str]:
    """确定账号锚点。返回 (key, kind)。kind ∈ domain|name|email。"""
    email = (email or "").strip().lower()
    if "@" in email:
        domain = email.split("@", 1)[1]
        if domain and domain not in _FREE_MAIL:
            return domain, "domain"
    if company_name and _norm_name(company_name):
        return _norm_name(company_name), "name"
    return email, "email"


def _rfm_score(values: list[float], v: float, reverse: bool = False) -> int:
    """五等分打分（1-5）。

    reverse=True 用于**逆向指标**（R：距今天数越小越好）——此时值越小得分越高。
    两个易错点（实测踩出）：
      ① 逆向指标若沿用正向公式，会把「今天刚联系过」判成 1 分 → 客户被误分层为流失风险；
      ② 样本无区分度（如全部 won_amount=0）时，分位恒为 1.0 会让所有人拿满分 5，
         语义荒谬（零成交≠最高价值）。此时返回中性分 3。
    """
    if not values or v is None:
        return 1
    if len(set(values)) <= 1:
        return 3  # 无区分度 → 中性分，不假装满分
    s = sorted(values)
    n = len(s)
    rank = sum(1 for x in s if x <= v) / n  # ∈ (0, 1]
    if reverse:
        return max(1, min(5, 5 - int(rank * 4.999)))
    return max(1, min(5, int(rank * 4.999) + 1))


def classify(r: int, f: int, m: int) -> str:
    """RFM 分层（规则简化版，便于运营理解）。"""
    if r >= 4 and f >= 4 and m >= 4:
        return "champion"
    if r >= 3 and f >= 3:
        return "loyal"
    if r >= 4 and f <= 2:
        return "new"
    if r >= 3 and f <= 2 and m >= 3:
        return "potential"
    if r <= 2 and f >= 3:
        return "at_risk"
    if r <= 2 and f <= 2:
        return "hibernating"
    return "regular"


def _collect(db, tenant_id: str = ""):
    """拉取询盘 + 跟单卡（一次查询，内存聚合，避免 N+1）。"""
    from sqlalchemy import text

    where = "WHERE i.is_active IS NOT FALSE" + (" AND i.tenant_id = :t" if tenant_id else "")
    try:
        rows = db.execute(
            text(
                f"""
                SELECT i.id, i.name, i.email, i.product, i.status, i.created_at,
                       i.tenant_id, i.assigned_to, i.priority_score, i.attribution_channel
                FROM inquiries i {where}
                """
            ),
            {"t": tenant_id} if tenant_id else {},
        ).fetchall()
    except Exception:  # noqa: BLE001 — is_active 可能不存在，退回简单查询
        rows = db.execute(
            text(
                f"""
                SELECT i.id, i.name, i.email, i.product, i.status, i.created_at,
                       i.tenant_id, i.assigned_to, i.priority_score, i.attribution_channel
                FROM inquiries i {"WHERE i.tenant_id = :t" if tenant_id else ""}
                """
            ),
            {"t": tenant_id} if tenant_id else {},
        ).fetchall()

    cards: dict[str, dict] = {}
    try:
        for iid, tid, payload in db.execute(
            text("SELECT inquiry_id, tenant_id, payload FROM acquisition_ops_cards")
        ).fetchall():
            data = payload
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except (json.JSONDecodeError, TypeError):
                    continue
            if isinstance(data, dict):
                cards[str(iid)] = data
    except Exception:  # noqa: BLE001 — 表不存在则无成交数据
        pass

    companies: list[tuple] = []
    try:
        companies = db.execute(
            text(
                "SELECT name, domain, icp_score, intent_score, account_score, country, tenant_id "
                "FROM companies" + (" WHERE tenant_id = :t" if tenant_id else "")
            ),
            {"t": tenant_id} if tenant_id else {},
        ).fetchall()
    except Exception:  # noqa: BLE001
        pass

    return rows, cards, companies


def build_accounts(db, tenant_id: str = "") -> list[dict[str, Any]]:
    """ABM 账号聚合 + RFM 打分 + 标签（核心产出）。"""
    rows, cards, companies = _collect(db, tenant_id)
    now = datetime.now(timezone.utc)

    comp_by_domain = {
        str(c[1]).strip().lower(): c for c in companies if c[1] and str(c[1]).strip()
    }
    comp_by_name = {_norm_name(str(c[0])): c for c in companies if c[0]}

    acc: dict[str, dict[str, Any]] = {}
    for (iid, name, email, product, status, created_at, tid, assigned_to, prio, channel) in rows:
        key, kind = account_key(email or "", name or "")
        if not key:
            continue
        a = acc.setdefault(
            key,
            {
                "account_key": key,
                "key_kind": kind,
                "buyers": set(),
                "emails": set(),
                "inquiry_ids": [],
                "products": set(),
                "statuses": {},
                "owners": set(),
                "channels": {},
                "first_at": None,
                "last_at": None,
                "won_amount": 0.0,
                "cards": 0,
                "tenant_ids": set(),
                "max_priority": 0,
            },
        )
        a["buyers"].add((name or "").strip())
        if email:
            a["emails"].add(str(email).strip().lower())
        a["inquiry_ids"].append(str(iid))
        if product:
            a["products"].add(str(product).strip().lower())
        st = (status or "pending").lower()
        a["statuses"][st] = a["statuses"].get(st, 0) + 1
        if assigned_to:
            a["owners"].add(str(assigned_to))
        if channel:
            a["channels"][channel] = a["channels"].get(channel, 0) + 1
        if tid:
            a["tenant_ids"].add(str(tid))
        if prio:
            a["max_priority"] = max(a["max_priority"], int(prio or 0))
        ca = _aware(created_at)
        if ca:
            if a["first_at"] is None or ca < a["first_at"]:
                a["first_at"] = ca
            if a["last_at"] is None or ca > a["last_at"]:
                a["last_at"] = ca
        c = cards.get(str(iid))
        if c:
            a["cards"] += 1
            try:
                a["won_amount"] += float(c.get("won_amount") or 0)
            except (TypeError, ValueError):
                pass

    # 打分（以账号为单位）
    recency_days = [max((now - a["last_at"]).days, 0) for a in acc.values() if a["last_at"]]
    freqs = [len(a["inquiry_ids"]) for a in acc.values()]
    moneys = [a["won_amount"] for a in acc.values()]

    out: list[dict[str, Any]] = []
    for key, a in acc.items():
        days = max((now - a["last_at"]).days, 0) if a["last_at"] else 9999
        freq = len(a["inquiry_ids"])
        money = round(a["won_amount"], 2)
        # R：距今天数越小越好 → 用「新鲜度」参与分位（reverse=True 时按天数排名翻转）
        r = _rfm_score(recency_days or [days], days, reverse=True)
        f = _rfm_score(freqs or [freq], freq)
        m = _rfm_score(moneys or [money], money)
        seg = classify(r, f, m)

        comp = comp_by_domain.get(key) if a["key_kind"] == "domain" else None
        if comp is None:
            for nm in a["buyers"]:
                if _norm_name(nm) in comp_by_name:
                    comp = comp_by_name[_norm_name(nm)]
                    break
        icp = int(comp[2] or 0) if comp else 0
        intent = int(comp[3] or 0) if comp else 0
        acct_score = int(comp[4] or 0) if comp else 0

        rec = {
            "account_key": key,
            "key_kind": a["key_kind"],
            "company_name": (comp[0] if comp else (sorted(a["buyers"])[0] if a["buyers"] else key)),
            "country": (comp[5] if comp else ""),
            "has_company_record": bool(comp),
            "icp_score": icp,
            "intent_score": intent,
            "account_score": acct_score,
            "contacts_count": len(a["emails"]),
            "inquiries_count": freq,
            "cards_count": a["cards"],
            "products_count": len(a["products"]),
            "top_products": sorted(a["products"])[:5],
            "statuses": a["statuses"],
            "owners": sorted(a["owners"]),
            "channels": a["channels"],
            "first_at": a["first_at"].isoformat() if a["first_at"] else "",
            "last_at": a["last_at"].isoformat() if a["last_at"] else "",
            "recency_days": days if days != 9999 else None,
            "won_amount": money,
            "max_priority": a["max_priority"],
            "rfm": {"r": r, "f": f, "m": m, "code": f"{r}{f}{m}"},
            "segment": seg,
            "segment_label": SEGMENTS.get(seg, seg),
        }
        rec["tags"] = generate_tags(rec)
        out.append(rec)

    out.sort(key=lambda x: (-x["won_amount"], -x["inquiries_count"], x["recency_days"] or 10**6))
    return out


def generate_tags(rec: dict[str, Any]) -> list[str]:
    """规则标签（运营可直接用来圈人）。"""
    tags: list[str] = []
    r, f, m = rec["rfm"]["r"], rec["rfm"]["f"], rec["rfm"]["m"]
    if m >= 4 or rec["won_amount"] >= 10000:
        tags.append("高价值账号")
    if f >= 4 or rec["inquiries_count"] >= 5:
        tags.append("高频询盘")
    if rec["products_count"] >= 3:
        tags.append("多品类意向")
    if rec["icp_score"] >= 70:
        tags.append("高ICP匹配")
    if rec["intent_score"] >= 70:
        tags.append("高购买意向")
    if rec["won_amount"] > 0:
        tags.append("已成交客户")
    if r <= 2 and rec["inquiries_count"] >= 2:
        tags.append("沉睡待唤醒")
    if rec["segment"] == "at_risk":
        tags.append("流失风险")
    if not rec["has_company_record"]:
        tags.append("待建公司档案")
    if rec["contacts_count"] >= 2:
        tags.append("多联系人")
    return tags


def persist_account_tags(db, tenant_id: str = "", accounts: Optional[list] = None) -> dict[str, Any]:
    """把 RFM 分层与标签写回 companies（P1-8 标签落库，供运营按标签筛人）。

    只在能匹配到真实公司档案时写（domain 优先、其次归一化公司名）；
    询盘里凭空冒出的邮箱域名不硬造公司档案 —— 留给「待建公司档案」标签提示人工补全。
    """
    from sqlalchemy import text

    accounts = accounts if accounts is not None else build_accounts(db, tenant_id)
    comps = db.execute(
        text(
            "SELECT id, name, domain FROM companies"
            + (" WHERE tenant_id = :t" if tenant_id else "")
        ),
        {"t": tenant_id} if tenant_id else {},
    ).fetchall()
    by_domain = {str(c[2]).strip().lower(): str(c[0]) for c in comps if c[2] and str(c[2]).strip()}
    by_name = {_norm_name(str(c[1])): str(c[0]) for c in comps if c[1]}

    now = datetime.now(timezone.utc)
    updated = 0
    for a in accounts:
        cid = None
        if a["key_kind"] == "domain":
            cid = by_domain.get(a["account_key"])
        if cid is None:
            cid = by_name.get(_norm_name(a["company_name"]))
        if cid is None:
            continue
        db.execute(
            text(
                """
                UPDATE companies
                SET tags = :tags, rfm_segment = :seg, rfm_code = :code, rfm_updated_at = :ts
                WHERE id = :id
                """
            ),
            {
                "tags": json.dumps(a["tags"], ensure_ascii=False),
                "seg": a["segment"],
                "code": a["rfm"]["code"],
                "ts": now,
                "id": cid,
            },
        )
        updated += 1
    db.commit()
    seg_count: dict[str, int] = {}
    for a in accounts:
        seg_count[a["segment"]] = seg_count.get(a["segment"], 0) + 1
    return {
        "updated": updated,
        "total_accounts": len(accounts),
        "skipped_no_company": len(accounts) - updated,
        "segments": seg_count,
    }


def rfm_summary(accounts: list[dict[str, Any]]) -> dict[str, Any]:
    """分层汇总 + 分位统计（给运营看的一页）。"""
    by_seg: dict[str, int] = {}
    tag_count: dict[str, int] = {}
    for a in accounts:
        by_seg[a["segment"]] = by_seg.get(a["segment"], 0) + 1
        for t in a["tags"]:
            tag_count[t] = tag_count.get(t, 0) + 1
    total_won = round(sum(a["won_amount"] for a in accounts), 2)
    return {
        "total_accounts": len(accounts),
        "segments": {k: {"count": v, "label": SEGMENTS.get(k, k)} for k, v in by_seg.items()},
        "tags": dict(sorted(tag_count.items(), key=lambda x: -x[1])),
        "won_amount_total": total_won,
        "top_accounts": [
            {
                "account_key": a["account_key"],
                "company_name": a["company_name"],
                "segment_label": a["segment_label"],
                "rfm_code": a["rfm"]["code"],
                "won_amount": a["won_amount"],
                "inquiries_count": a["inquiries_count"],
                "tags": a["tags"],
            }
            for a in accounts[:10]
        ],
    }
