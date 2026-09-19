# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P1-8 收尾：询盘域名 → 自动建/补公司档案。

为什么必须做：
    P1-8 的 RFM 分层与标签最终要写回 companies。但实测真实库 15 个账号
    **全部 `has_company=false`**（companies 表与询盘域名零匹配）→ 标签落库匹配率 0，
    ABM 账号视图也挂不到公司档案上。P1-8 处于「算得出来、落不下去」的半残状态。

设计红线：
    · **绝不影响询盘创建主流程** —— 本模块用独立 SessionLocal，与请求事务解耦；
      任何异常都被吞掉并记录，询盘该成功还是成功（不能用 savepoint，因为主流程已 commit，
      rollback 反而会丢数据）。
    · **不造脏数据** —— 免费邮箱（gmail/qq/163…）不代表企业账号，不建档案；
      只补空字段，不覆盖人工已填内容。
    · **幂等** —— domain 优先匹配，其次公司名归一化匹配；重复执行不产生重复档案。

挂载点：`api/v1/routes/inquiries.py::create_public_inquiry`（另有批量回填任务）。
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

_SOURCE = "inquiry_autofill"

# 域名 TLD → 国家（外贸 B2B 里 TLD 是最可靠且几乎免费的国家信号，直接供 ICP 国家分层使用）
_TLD_COUNTRY: dict[str, str] = {
    "uk": "United Kingdom", "de": "Germany", "fr": "France", "nl": "Netherlands",
    "es": "Spain", "it": "Italy", "pl": "Poland", "se": "Sweden", "no": "Norway",
    "dk": "Denmark", "fi": "Finland", "be": "Belgium", "ch": "Switzerland",
    "at": "Austria", "pt": "Portugal", "gr": "Greece", "ie": "Ireland",
    "cz": "Czechia", "ro": "Romania", "hu": "Hungary", "tr": "Turkey",
    "br": "Brazil", "mx": "Mexico", "ar": "Argentina", "cl": "Chile",
    "pe": "Peru", "co": "Colombia", "ca": "Canada", "us": "United States",
    "au": "Australia", "nz": "New Zealand", "jp": "Japan", "kr": "South Korea",
    "sg": "Singapore", "my": "Malaysia", "th": "Thailand", "vn": "Vietnam",
    "id": "Indonesia", "ph": "Philippines", "in": "India", "pk": "Pakistan",
    "ae": "United Arab Emirates", "sa": "Saudi Arabia", "qa": "Qatar",
    "kw": "Kuwait", "om": "Oman", "bh": "Bahrain", "eg": "Egypt",
    "za": "South Africa", "ng": "Nigeria", "ke": "Kenya", "ru": "Russia",
    "ua": "Ukraine", "il": "Israel",
}
# 二级域名后缀优先（co.uk 必须整体判断，否则 .uk 匹配不到）
_TLD_TWO_LEVEL = {"co.uk": "United Kingdom", "com.br": "Brazil", "com.au": "Australia",
                  "co.jp": "Japan", "com.mx": "Mexico", "co.za": "South Africa",
                  "com.sg": "Singapore", "co.nz": "New Zealand", "com.tr": "Turkey"}

_GENERIC_TLDS = {"com", "net", "org", "io", "co", "info", "biz", "cn", "xyz", "top"}


def country_from_domain(domain: str) -> str:
    """从域名推断国家；通用 TLD(.com/.net/…) 无法推断时返回空串（不猜）。"""
    d = (domain or "").strip().lower()
    if not d or "." not in d:
        return ""
    parts = d.split(".")
    two = ".".join(parts[-2:])
    if two in _TLD_TWO_LEVEL:
        return _TLD_TWO_LEVEL[two]
    tld = parts[-1]
    if tld in _GENERIC_TLDS:
        return ""
    return _TLD_COUNTRY.get(tld, "")


def _own_session():
    """独立会话（与请求事务解耦，失败不影响主流程）。"""
    try:
        from app.core.database import SessionLocal

        return SessionLocal()
    except Exception:  # noqa: BLE001
        return None


def _find_existing(db, *, domain: str, norm_name: str, tenant_id: str) -> Optional[Any]:
    """按 domain 优先、其次公司名归一化匹配已有档案。"""
    from sqlalchemy import text

    try:
        if domain:
            row = db.execute(
                text(
                    "SELECT id, name, domain, country, tenant_id FROM companies "
                    "WHERE lower(domain) = :d LIMIT 1"
                ),
                {"d": domain},
            ).first()
            if row:
                return row
        if norm_name:
            from app.services.acquisition.rfm_service import _norm_name

            rows = db.execute(
                text(
                    "SELECT id, name, domain, country, tenant_id FROM companies"
                    + (" WHERE tenant_id = :t" if tenant_id else "")
                    + " LIMIT 500"
                ),
                {"t": tenant_id} if tenant_id else {},
            ).fetchall()
            for r in rows:
                if _norm_name(str(r[1] or "")) == norm_name:
                    return r
    except Exception as exc:  # noqa: BLE001
        logger.debug("company lookup miss: %s", exc)
    return None


def resolve_or_create_company(
    *,
    email: str = "",
    company_name: str = "",
    contact_name: str = "",
    country: str = "",
    tenant_id: str = "",
    db: Any = None,
    score: bool = True,
) -> dict[str, Any]:
    """按邮箱域名/公司名建或补公司档案。返回 {action, company_id, ...}。

    action ∈ created | enriched | matched | skipped_free_mail | skipped_no_key | error
    """
    from app.services.acquisition.rfm_service import _norm_name, account_key

    own = db is None
    session = db or _own_session()
    if session is None:
        return {"action": "error", "reason": "db_unavailable"}

    key, kind = account_key(email or "", company_name or "")
    try:
        if kind == "email":
            # 免费邮箱/无企业域名：不代表企业账号，不建档案（避免脏数据）
            return {"action": "skipped_free_mail", "key": key}
        if not key:
            return {"action": "skipped_no_key"}

        domain = key if kind == "domain" else ""
        inferred_country = country or country_from_domain(domain)
        norm_name = _norm_name(company_name) or (key if kind == "name" else "")
        existing = _find_existing(session, domain=domain, norm_name=norm_name, tenant_id=tenant_id)

        from sqlalchemy import text

        if existing:
            cid = str(existing[0])
            fills: list[str] = []
            sets: list[str] = []
            params: dict[str, Any] = {"id": cid}
            # 只补空字段，不覆盖人工填写
            if domain and not existing[2]:
                sets.append("domain = :d")
                params["d"] = domain
                fills.append("domain")
            if inferred_country and not existing[3]:
                sets.append("country = :c")
                params["c"] = inferred_country
                fills.append("country")
            if not tenant_id and existing[4]:
                pass
            if sets:
                session.execute(
                    text(f"UPDATE companies SET {', '.join(sets)} WHERE id = :id"), params
                )
                session.commit()
                return {
                    "action": "enriched",
                    "company_id": cid,
                    "name": str(existing[1] or ""),
                    "filled": fills,
                }
            return {"action": "matched", "company_id": cid, "name": str(existing[1] or "")}

        # 建新档案：名称优先用真实公司名；没有就用**域名全称**（如 "wright-build.co.uk"）。
        # 刻意不取域名首词（"W"、"Ex" 这类看着像真公司名，会污染公司主数据）；
        # 用域名全称一眼可辨是自动建档、待人工补全。
        import uuid as _uuid

        name = (company_name or "").strip() or domain or key
        new_id = str(_uuid.uuid4())
        row = session.execute(
            text(
                """
                INSERT INTO companies
                    (id, name, domain, country, source, tenant_id, icp_score, intent_score,
                     account_score, created_at, updated_at)
                VALUES
                    (:id, :n, :d, :c, :s, :t, 0, 0, 0, now(), now())
                RETURNING id
                """
            ),
            {
                "id": new_id,
                "n": name[:300],
                "d": domain or None,
                "c": inferred_country or None,
                "s": _SOURCE,
                "t": tenant_id or None,
            },
        ).first()
        session.commit()
        cid = str(row[0]) if row else new_id
    except Exception as exc:  # noqa: BLE001
        logger.warning("company autofill 失败: %s", exc)
        try:
            session.rollback()
        except Exception:
            pass
        return {"action": "error", "reason": str(exc)[:200]}
    finally:
        if own:
            try:
                session.close()
            except Exception:
                pass

    # 建档后立即跑 ICP 引擎（P0-7），让新档案即刻可用于优先排序
    if score and cid:
        try:
            from app.core.database import SessionLocal
            from app.models.company import Company
            from app.services.company_scoring_service import score_company

            with SessionLocal() as s2:
                comp = s2.query(Company).filter(Company.id == cid).first()
                if comp is not None:
                    score_company(s2, comp)
                    s2.commit()
        except Exception as exc:  # noqa: BLE001
            logger.debug("新档案评分失败（不影响建档）: %s", exc)

    return {"action": "created", "company_id": cid, "name": name, "domain": domain}


def autofill_from_lead(
    *, email: str = "", contact_name: str = "", company_name: str = "",
    country: str = "", tenant_id: str = "",
) -> dict[str, Any]:
    """询盘入口钩子：安全包装，任何失败都不影响询盘创建。"""
    try:
        return resolve_or_create_company(
            email=email,
            company_name=company_name,
            contact_name=contact_name,
            country=country,
            tenant_id=tenant_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("autofill_from_lead 异常（已吞）: %s", exc)
        return {"action": "error", "reason": str(exc)[:200]}


def backfill_from_inquiries(db: Any, tenant_id: str = "", limit: int = 5000,
                            dry_run: bool = False) -> dict[str, Any]:
    """存量回填：把历史询盘的域名补成公司档案（幂等，可重复跑）。"""
    from sqlalchemy import text

    from app.services.acquisition.rfm_service import account_key

    rows = db.execute(
        text(
            "SELECT email, name, tenant_id FROM inquiries"
            + (" WHERE tenant_id = :t" if tenant_id else "")
            + " LIMIT :lim"
        ),
        ({"t": tenant_id, "lim": limit} if tenant_id else {"lim": limit}),
    ).fetchall()

    summary = {
        "scanned": 0,
        "created": 0,
        "enriched": 0,
        "matched": 0,
        "skipped_free_mail": 0,
        "skipped_no_key": 0,
        "errors": 0,
        "dry_run": dry_run,
        "planned_domains": [],
    }
    seen_domains: set[str] = set()
    for email, name, tid in rows:
        summary["scanned"] += 1
        key, kind = account_key(email or "", "")
        if kind == "email":
            summary["skipped_free_mail"] += 1
            continue
        if not key:
            summary["skipped_no_key"] += 1
            continue
        if key in seen_domains:
            continue
        seen_domains.add(key)
        if dry_run:
            summary["planned_domains"].append(key)
            continue
        r = resolve_or_create_company(
            email=email or "", contact_name=name or "", tenant_id=str(tid or "")
        )
        act = r.get("action", "error")
        if act in ("created", "enriched", "matched"):
            summary[act] += 1
        elif act in ("skipped_free_mail", "skipped_no_key"):
            summary[act] += 1
        else:
            summary["errors"] += 1
    return summary
