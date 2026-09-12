"""一键开业 — Time-to-Value 自动编排（Hermes → 旺财 → 首篇草稿）。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.services.onboarding_chain_service import (
    _primary_product,
    _safe_settings,
    create_first_publish,
    run_wangcai_preview,
    tenant_site_urls,
)
from app.services.onboarding_progress_service import _tenant_has_site
from app.services.tenant_product_context import set_tenant_primary_product
from app.services.trade_intel_data import load_country_index

if TYPE_CHECKING:
    from app.models.user import User


def _utcnow() -> datetime:
    """_utcnow。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc)


def _country_label(code: str | None) -> str:
    """_country_label。

    参数说明：
    :param code: 参数 code
    :return: 返回处理结果。
    """
    code = (code or "").upper()
    if not code:
        return ""
    return load_country_index().get(code, {}).get("name_zh") or code


def _extract_top_market(wangcai: dict[str, Any]) -> dict[str, Any]:
    """_extract_top_market。

    参数说明：
    :param wangcai: 参数 wangcai
    :return: 返回处理结果。
    """
    tool = wangcai.get("tool_result") or {}
    recs = tool.get("recommendations") or []
    top = recs[0] if recs else {}
    code = str(top.get("country_code") or "").upper()
    return {
        "country_code": code,
        "country_label": _country_label(code),
        "growth": top.get("growth"),
        "reason": (top.get("reason") or "")[:120],
        "category": tool.get("category"),
    }


def _build_headline(
    *,
    product: str,
    top_market: dict[str, Any],
    site_built: bool,
    publish_ready: bool,
) -> str:
    """_build_headline。

    参数说明：
    :param product: 参数 product
    :param top_market: 参数 top_market
    :param site_built: 参数 site_built
    :param publish_ready: 参数 publish_ready
    :return: 返回处理结果。
    """
    country = top_market.get("country_label") or top_market.get("country_code") or "海外"
    parts = []
    if site_built:
        parts.append(f"「{product}」官网已生成")
    parts.append(f"首选市场：{country}")
    if publish_ready:
        parts.append("首篇英文引流稿已备好")
    return " · ".join(parts)


def _persist_autopilot(
    db: Session,
    row: Tenant,
    *,
    payload: dict[str, Any],
    mark_wizard_done: bool,
) -> None:
    """_persist_autopilot。

    参数说明：
    :param db: 参数 db
    :param row: 参数 row
    :param payload: 参数 payload
    :param mark_wizard_done: 参数 mark_wizard_done
    :return: 返回处理结果。
    """
    settings = _safe_settings(row.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    onboarding["autopilot"] = payload
    onboarding["autopilot_completed"] = bool(payload.get("ok"))
    if mark_wizard_done and payload.get("ok"):
        onboarding["wizard_completed"] = True
        onboarding["wizard_completed_at"] = _utcnow().isoformat()
        onboarding["wizard_via"] = "autopilot"
    settings["onboarding"] = onboarding
    row.settings = json.dumps(settings, ensure_ascii=False)
    row.updated_at = _utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)


async def run_onboarding_autopilot(
    db: Session,
    tenant: Tenant,
    user: User,
    *,
    product_name: str | None = None,
    product_images: list[str] | None = None,
    skip_hermes: bool = False,
) -> dict[str, Any]:
    """单次调用完成 TTV 三件套；无需客户懂外贸或逐页点菜单。"""
    started = _utcnow()
    tid = str(tenant.id)
    row = db.query(Tenant).filter(Tenant.id == tid).first()
    if not row:
        return {"ok": False, "error": "tenant_not_found"}

    product = (product_name or _primary_product(row)).strip() or "建材产品"
    if product_name:
        set_tenant_primary_product(db, row, product)
        db.commit()
        db.refresh(row)

    steps: list[dict[str, Any]] = []
    ok_all = True
    ok_all, site_built = await _run_autopilot_hermes_step(db, ok_all, product, product_images, row, skip_hermes, steps, tid)
    # ── 1b. 官网 ICP（建站后自动抓取画像写入记忆） ──
    icp_step: dict[str, Any] = {"id": "website_icp", "label": "官网 ICP 画像"}
    if site_built or _tenant_has_site(row):
        try:
            from app.services.foreign_trade.foreign_trade_agent_service import run_website_icp_agent
            icp = run_website_icp_agent(
                db, tid, max_pages=3, persist_memory=True
            )
            icp_step.update(
                {
                    "ok": icp.get("status") != "needs_input",
                    "summary": icp.get("summary"),
                    "skipped": icp.get("status") == "needs_input",
                }
            )
        except Exception as exc:
            icp_step.update({"ok": False, "error": str(exc)[:200]})
    else:
        icp_step.update({"ok": True, "skipped": True})
    steps.append(icp_step)
    ok_all, pub_step, top_market, wc_step = await _run_autopilot_wangcai_publish_steps(db, ok_all, product, row, steps, user)
    duration = (_utcnow() - started).total_seconds()
    urls = tenant_site_urls(row)
    headline = _build_headline(
        product=product,
        top_market=top_market if wc_step.get("ok") else {},
        site_built=site_built or _tenant_has_site(row),
        publish_ready=pub_step.get("ok", False),
    )
    settings = _safe_settings(row.settings)
    prefill = (settings.get("onboarding") or {}).get("first_publish_draft") or {}
    autopilot_payload = {
        "version": 1,
        "ok": ok_all,
        "completed_at": _utcnow().isoformat(),
        "duration_sec": round(duration, 1),
        "headline": headline,
        "product": product,
        "steps": steps,
        "top_market": top_market,
        "site_preview_url": urls["production"],
        "site_preview_dev_url": urls["dev"],
        "publish_prefill": prefill,
    }
    _persist_autopilot(db, row, payload=autopilot_payload, mark_wizard_done=ok_all)
    return {
        **autopilot_payload,
        "chain_step": "done" if ok_all else "hermes",
        "wizard_completed": ok_all,
    }


async def _run_autopilot_hermes_step(db, ok_all, product, product_images, row, skip_hermes, steps, tid):
    """_run_autopilot_hermes_step。

    参数说明：
    :param db: 参数 db
    :param ok_all: 参数 ok_all
    :param product: 参数 product
    :param product_images: 参数 product_images
    :param row: 参数 row
    :param skip_hermes: 参数 skip_hermes
    :param steps: 参数 steps
    :param tid: 参数 tid
    :return: 返回处理结果。
    """
    # ── 1. Hermes 建站 ──
    site_built = _tenant_has_site(row)
    if not skip_hermes and not site_built:

        step: dict[str, Any] = {"id": "hermes", "label": "Hermes 智能建站"}
        try:

            from app.core.deps.tenant_quota import consume_tenant_tokens
            from app.services.hermes.site_build_workflow import run_ai_site_builder_v1
            from app.services.tenant_site_persistence import persist_tenant_site_content
            from app.services.token_service import InsufficientTokenError
            use_ai = True
            try:

                consume_tenant_tokens(db, tid, 50, "onboarding_autopilot_hermes")

            except InsufficientTokenError:

                use_ai = False


            hermes = await run_ai_site_builder_v1(

                db,
                tenant_id=tid,
                product_name=product,
                company_name=row.name or "",
                auto_save=True,
                use_ai=use_ai,
                persist_fn=persist_tenant_site_content,
                product_images=product_images or None,
                skip_i18n_ai=False,

            )
            db.refresh(row)
            home = (

                (hermes.get("site_content") or {})
                .get("pages", {})
                .get("home", {})

            )
            step.update(

                {

                    "ok": True,
                    "source": hermes.get("source"),
                    "home_title": home.get("title"),
                    "detail": home.get("title") or "官网已保存",

                }

            )
            site_built = bool(hermes.get("saved")) or _tenant_has_site(row)

        except Exception as exc:

            step.update({"ok": False, "error": str(exc)[:200]})
            ok_all = False

        steps.append(step)

    else:

        steps.append(

            {

                "id": "hermes",
                "label": "Hermes 智能建站",
                "ok": True,
                "skipped": site_built,

            }

        )

    return (ok_all, site_built)


async def _run_autopilot_wangcai_publish_steps(db, ok_all, product, row, steps, user):
    """_run_autopilot_wangcai_publish_steps。

    参数说明：
    :param db: 参数 db
    :param ok_all: 参数 ok_all
    :param product: 参数 product
    :param row: 参数 row
    :param steps: 参数 steps
    :param user: 参数 user
    :return: 返回处理结果。
    """
    # ── 2. 旺财蓝海（代替客户「懂外贸」） ──
    wc_step: dict[str, Any] = {"id": "wangcai", "label": "旺财 · 蓝海雷达"}
    try:

        wc = run_wangcai_preview(

            db,
            row,
            message=f"{product} 蓝海市场 Top3",

        )
        db.refresh(row)
        top_market = _extract_top_market(wc)
        wc_step.update(

            {

                "ok": True,
                "intent": wc.get("intent"),
                "top_market": top_market,
                "reply_snippet": (wc.get("reply") or "")[:200],
                "detail": f"首选 {top_market.get('country_label') or '—'} · {top_market.get('growth') or ''}",

            }

        )

    except Exception as exc:

        wc_step.update({"ok": False, "error": str(exc)[:200]})
        top_market = {}
        ok_all = False

    steps.append(wc_step)
    # ── 3. 首篇引流稿（注入 Top1 市场） ──
    pub_step: dict[str, Any] = {"id": "publish", "label": "首篇引流稿"}
    try:

        fp = create_first_publish(db, row, user)
        db.refresh(row)
        pub_step.update(

            {

                "ok": True,
                "title": fp.get("title"),
                "preview": fp.get("preview"),
                "already_done": fp.get("already_done"),
                "task_id": fp.get("task_id"),
                "queued": fp.get("queued"),
                "detail": fp.get("title") or "英文引流稿已写入队列",

            }

        )

    except Exception as exc:

        pub_step.update({"ok": False, "error": str(exc)[:200]})
        ok_all = False

    steps.append(pub_step)
    return (ok_all, pub_step, top_market, wc_step)


def get_autopilot_summary(tenant: Tenant) -> dict[str, Any] | None:
    """get_autopilot_summary。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    onboarding = _safe_settings(tenant.settings).get("onboarding") or {}
    if not isinstance(onboarding, dict):
        return None
    auto = onboarding.get("autopilot")
    return auto if isinstance(auto, dict) else None
