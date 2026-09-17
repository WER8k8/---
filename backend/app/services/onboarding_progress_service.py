# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""开户待办六步 — 真实进度判定（对齐 client-dashboard-bento-spec §3）

七步商业链第 ⑤ 步「询盘 IM」子任务（不新增主步）：
  5a 询盘 IM 入站（企微/抖音 webhook + 官网挂件）
  5b 租户企微销售推送（Corp / Agent / 销售 UserID）
  5c 抖音评论监测 → 自动谈单
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.content import Platform, PlatformAccount, PublishTask
from app.models.inquiry import Inquiry
from app.models.product import Product
from app.models.social_interaction import SocialInteraction
from app.services.media_cuplayer_service import cuplayer_configured
from app.models.tenant import Tenant
from app.models.tenant_wecom_push import TenantWecomPushConfig
from app.services.tenant_wecom_config_service import serialize_for_api

STEP_IDS = ("site", "domain", "product", "publish", "inquiry", "im", "review")

# 对齐七步彩排 step 5 · 询盘 IM
SALES_CHANNEL_SUBSTEPS: tuple[dict[str, Any], ...] = (
    {
        "id": "5a",
        "key": "inquiry_im",
        "title": "客户能联系到你",
        "detail": "把企微、抖音留言接到系统里，别漏消息",
        "route": "/inquiries/im-routing",
        "phase": "接单",
    },
    {
        "id": "5b",
        "key": "wecom_push",
        "title": "销售手机能收到通知",
        "detail": "填你们公司企微和销售是谁，有人问价自动推给他",
        "route": "/inquiries/im-routing#wecom-push",
        "phase": "接单",
    },
    {
        "id": "5c",
        "key": "douyin_worker",
        "title": "抖音评论自动抓",
        "detail": "绑好抖音后，评论问价自动进「自动谈单」",
        "route": "/sales/auto-negotiator",
        "phase": "接单",
    },
)

# 开户清单扩展项（注册时写入 + 进度刷新）
BASE_CHECKLIST_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "key": "email",
        "title": "邮箱验证",
        "detail": "开户验证码已通过",
        "phase": "开张",
    },
    {
        "key": "site",
        "title": "做出公司官网",
        "detail": "填主营产品，点一键开业，系统自动生成网站",
        "route": "/client/onboarding",
        "phase": "开张",
    },
    {
        "key": "ai",
        "title": "智能写文案",
        "detail": "开户已开通，可自动写介绍和引流稿",
        "route": "/client/ai-scenarios",
        "phase": "开张",
    },
    {
        "key": "platforms",
        "title": "绑定抖音等平台",
        "detail": "登录绑定后才能真发视频和文章",
        "route": "/client/distribute",
        "phase": "让人看见",
    },
    {
        "key": "product_images",
        "title": "产品图片空间",
        "detail": "国内七牛 / 海外 R2，平台代开；直接上传白底图",
        "route": "/client/product-images",
        "phase": "开张",
    },
    {
        "key": "storage",
        "title": "视频云存储（酷播）",
        "detail": "发长视频前：酷播官网注册实名 + 设置里填密钥",
        "route": "/client/settings",
        "phase": "让人看见",
    },
    {
        "key": "external_accounts",
        "title": "第三方账号准备",
        "detail": "查看哪些要平台代开、哪些需您注册",
        "route": "/client/onboarding#external-accounts",
        "phase": "让人看见",
    },
    {
        "key": "egress",
        "title": "海外发布网络",
        "detail": "国外平台发布更稳",
        "route": "/client/egress",
        "phase": "让人看见",
    },
)

EXTRA_CHECKLIST_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "key": "domain",
        "title": "绑定自己的网址",
        "detail": "客户打开是你家域名更正规，不会弄可稍后再说",
        "route": "/client/billing",
        "phase": "开张",
        "optional": True,
    },
    {
        "key": "product",
        "title": "上架第一个产品",
        "detail": "放上产品图和介绍，客户才知道你卖啥",
        "route": "/client/products",
        "phase": "让人看见",
    },
    {
        "key": "publish",
        "title": "发出第一条内容",
        "detail": "抖音或公众号发出去，人才看得见你",
        "route": "/client/queues/publish",
        "phase": "让人看见",
    },
)

# 大白话全流程（给向导 / 工作台展示，不含英文术语）
ONBOARDING_ROADMAP_PHASES: tuple[dict[str, Any], ...] = (
    {
        "id": "open",
        "title": "第一步：把店开起来",
        "summary": "填产品，一键生成官网",
        "keys": ("email", "site", "ai", "product_images"),
    },
    {
        "id": "visible",
        "title": "第二步：让人看见你",
        "summary": "绑平台、发视频或文章、产品上架",
        "keys": ("platforms", "publish", "product", "external_accounts", "storage", "egress"),
    },
    {
        "id": "contact",
        "title": "第三步：客户找得到你",
        "summary": "官网留电话微信，渠道留言能进系统",
        "keys": ("inquiry_im",),
    },
    {
        "id": "notify",
        "title": "第四步：销售收得到消息",
        "summary": "企微推送给销售，抖音评论自动抓",
        "keys": ("wecom_push", "douyin_worker"),
    },
    {
        "id": "daily",
        "title": "第五步：天天接单",
        "summary": "看询盘、回客户、继续发内容",
        "keys": ("domain",),
    },
)


def _safe_settings(raw: str | None) -> dict[str, Any]:
    """_safe_settings。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _tenant_has_site(tenant: Tenant | None) -> bool:
    """_tenant_has_site。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if not tenant:
        return False
    settings = _safe_settings(tenant.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    if onboarding.get("site_built"):
        return True
    brand = settings.get("brand") if isinstance(settings.get("brand"), dict) else {}
    site = brand.get("site_content") if isinstance(brand.get("site_content"), dict) else {}
    pages = site.get("pages") if isinstance(site.get("pages"), dict) else {}
    home = pages.get("home") if isinstance(pages.get("home"), dict) else {}
    title = str(home.get("title") or "").strip()
    return len(title) >= 2


def _tenant_has_bound_domain(tenant: Tenant | None) -> bool:
    """_tenant_has_bound_domain。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if not tenant:
        return False
    custom = (tenant.custom_domains or "").strip()
    return bool(custom or tenant.domain)


def _tenant_has_product(db: Session, tenant: Tenant | None) -> bool:
    """_tenant_has_product。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if not tenant:
        return False
    settings = _safe_settings(tenant.settings)
    brand = settings.get("brand") if isinstance(settings.get("brand"), dict) else {}
    categories = brand.get("product_categories") if isinstance(brand, dict) else None
    if isinstance(categories, list) and len(categories) > 0:
        return True
    # 与 client/dashboard 同源：全局活跃产品数（单租户演示仓）
    return db.query(Product).filter(Product.is_active.is_(True)).count() > 0


def _tenant_has_publish(db: Session, tenant: Tenant | None) -> bool:
    """_tenant_has_publish。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if not tenant:
        return False
    tid = str(tenant.id)
    q = (
        db.query(PublishTask.id)
        .join(PlatformAccount, PublishTask.account_id == PlatformAccount.id)
        .filter(PlatformAccount.tenant_id == tid)
    )
    return q.limit(1).count() > 0


def _tenant_has_inquiry(db: Session, tenant: Tenant | None) -> bool:
    """_tenant_has_inquiry。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if not tenant:
        return False
    tid = str(tenant.id)
    return (
        db.query(Inquiry.id)
        .filter(Inquiry.is_active.is_(True), Inquiry.tenant_id == tid)
        .limit(1)
        .count()
        > 0
    )


def _sales_channels_flags(tenant: Tenant | None) -> dict[str, Any]:
    """_sales_channels_flags。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if not tenant:
        return {}
    settings = _safe_settings(tenant.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    sales = onboarding.get("sales_channels") if isinstance(onboarding.get("sales_channels"), dict) else {}
    return sales


def _tenant_inquiry_im_inbound_ready(db: Session, tenant: Tenant | None) -> bool:
    """5a · 询盘 IM 入站（webhook / 挂件 / 已有渠道询盘）。"""
    if not tenant:
        return False
    sales = _sales_channels_flags(tenant)
    if sales.get("inbound_configured") or sales.get("inbound_done"):
        return True
    settings = _safe_settings(tenant.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    media = onboarding.get("media_factory") if isinstance(onboarding.get("media_factory"), dict) else {}
    if media.get("im_connected") or media.get("wecom_bound"):
        return True
    if onboarding.get("im_contacts_done"):
        return True
    channels = settings.get("inquiry_channels") if isinstance(settings.get("inquiry_channels"), dict) else {}
    if channels.get("wecom") or channels.get("douyin") or channels.get("im_widget"):
        return True
    return _tenant_has_inquiry(db, tenant)


def _tenant_wecom_sales_push_ready(db: Session, tenant: Tenant | None) -> bool:
    """5b · 租户企微出站推送（非平台 .env UserID）。"""
    if not tenant:
        return False
    sales = _sales_channels_flags(tenant)
    if sales.get("wecom_push_configured"):
        return True
    row = (
        db.query(TenantWecomPushConfig)
        .filter(TenantWecomPushConfig.tenant_id == str(tenant.id))
        .first()
    )
    if not row:
        return False
    payload = serialize_for_api(row)
    return bool(payload.get("app_ready") or payload.get("webhook_ready"))


def _tenant_douyin_worker_ready(db: Session, tenant: Tenant | None) -> bool:
    """5c · 抖音评论 Worker / 自动谈单链路。"""
    if not tenant:
        return False
    tid = str(tenant.id)
    sales = _sales_channels_flags(tenant)
    if sales.get("douyin_worker_configured"):
        return True
    if (
        db.query(SocialInteraction.id)
        .filter(SocialInteraction.tenant_id == tid)
        .limit(1)
        .count()
        > 0
    ):
        return True
    rows = (
        db.query(PlatformAccount)
        .join(Platform, PlatformAccount.platform_id == Platform.id)
        .filter(PlatformAccount.tenant_id == tid, PlatformAccount.is_active.is_(True))
        .all()
    )
    for acc in rows:
        if acc.login_status != "logged_in":
            continue
        plat = acc.platform
        label = (getattr(plat, "name", "") or "").lower()
        if "douyin" in label or "抖音" in label or "tiktok" in label:
            return True
    return False


def _tenant_has_im(db: Session, tenant: Tenant | None) -> bool:
    """第 6 待办步：企微销售推送（5b）为主；兼容历史 im_connected 标记。"""
    if not tenant:
        return False
    if _tenant_wecom_sales_push_ready(db, tenant):
        return True
    settings = _safe_settings(tenant.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    media = onboarding.get("media_factory") if isinstance(onboarding.get("media_factory"), dict) else {}
    if media.get("im_connected") or media.get("wecom_bound"):
        return True
    channels = settings.get("inquiry_channels") if isinstance(settings.get("inquiry_channels"), dict) else {}
    return bool(channels.get("wecom") or channels.get("im_widget"))


def build_sales_channel_substeps(db: Session, tenant: Tenant | None) -> list[dict[str, Any]]:
    """开户链 / 彩排用：七步⑤ 子任务进度。"""
    evaluators = {
        "inquiry_im": lambda: _tenant_inquiry_im_inbound_ready(db, tenant),
        "wecom_push": lambda: _tenant_wecom_sales_push_ready(db, tenant),
        "douyin_worker": lambda: _tenant_douyin_worker_ready(db, tenant),
    }
    out: list[dict[str, Any]] = []
    for tpl in SALES_CHANNEL_SUBSTEPS:
        key = str(tpl["key"])
        done = evaluators.get(key, lambda: False)()
        out.append(
            {
                **tpl,
                "done": done,
                "framework_step": 5,
                "plain_title": tpl.get("title"),
                "plain_detail": tpl.get("detail"),
            }
        )
    return out


def _checklist_item_status(
    db: Session,
    tenant: Tenant | None,
    key: str,
) -> str:
    """返回 done / partial / pending。"""
    if not tenant:
        return "pending"
    if key == "email":
        return "done"
    if key == "site":
        return "done" if _tenant_has_site(tenant) else "pending"
    if key == "domain":
        return "done" if _tenant_has_bound_domain(tenant) else "pending"
    if key == "product":
        return "done" if _tenant_has_product(db, tenant) else "pending"
    if key == "publish":
        return "done" if _tenant_has_publish(db, tenant) else "pending"
    if key == "platforms":
        tid = str(tenant.id)
        bound = (
            db.query(PlatformAccount.id)
            .filter(
                PlatformAccount.tenant_id == tid,
                PlatformAccount.is_active.is_(True),
                PlatformAccount.login_status == "logged_in",
            )
            .limit(1)
            .count()
            > 0
        )
        return "done" if bound else "pending"
    if key == "product_images":
        return "done"
    if key == "external_accounts":
        settings = _safe_settings(tenant.settings)
        onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
        ext = onboarding.get("external_accounts") if isinstance(onboarding.get("external_accounts"), list) else []
        tenant_owned = [e for e in ext if e.get("owner") == "tenant"]
        if not tenant_owned:
            return "done"
        pending = [e for e in tenant_owned if e.get("status") != "done"]
        if not pending:
            return "done"
        return "partial"
    if key == "storage":
        settings = _safe_settings(tenant.settings)
        onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
        storage = onboarding.get("storage") if isinstance(onboarding.get("storage"), dict) else {}
        if storage.get("configured") or storage.get("writetoken_set") or cuplayer_configured():
            return "done"
        return "partial"
    if key == "egress":
        settings = _safe_settings(tenant.settings)
        onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
        egress = onboarding.get("egress") if isinstance(onboarding.get("egress"), dict) else {}
        assigned = int(egress.get("assigned") or 0)
        return "done" if assigned > 0 else "pending"
    if key == "ai":
        return "done"
    if key == "inquiry_im":
        return "done" if _tenant_inquiry_im_inbound_ready(db, tenant) else "pending"
    if key == "wecom_push":
        return "done" if _tenant_wecom_sales_push_ready(db, tenant) else "pending"
    if key == "douyin_worker":
        return "done" if _tenant_douyin_worker_ready(db, tenant) else "pending"
    return "pending"


def _merge_checklist_template(
    existing: dict[str, dict[str, Any]],
    tpl: dict[str, Any],
    status: str,
) -> None:
    """_merge_checklist_template。

    参数说明：
    :param existing: 参数 existing
    :param tpl: 参数 tpl
    :param status: 参数 status
    :return: 返回处理结果。
    """
    key = str(tpl["key"])
    row = dict(existing.get(key) or {})
    row.update(
        {
            "key": key,
            "title": tpl.get("title") or row.get("title") or key,
            "status": status,
            "detail": tpl.get("detail") or row.get("detail") or "",
            "route": tpl.get("route") or row.get("route"),
            "phase": tpl.get("phase") or row.get("phase"),
        }
    )
    if tpl.get("optional"):
        row["optional"] = True
    if tpl.get("id"):
        row["substep_id"] = tpl["id"]
        row["framework_step"] = 5
    existing[key] = row


def refresh_onboarding_checklist(
    db: Session,
    tenant: Tenant | None,
    checklist: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """刷新开户清单全部环节状态（含 5a/5b/5c 与产品/发布等）。"""
    base = list(checklist or [])
    existing: dict[str, dict[str, Any]] = {
        str(item.get("key")): dict(item) for item in base if item.get("key")
    }
    for tpl in (*BASE_CHECKLIST_TEMPLATES, *EXTRA_CHECKLIST_TEMPLATES):
        key = str(tpl["key"])
        _merge_checklist_template(existing, tpl, _checklist_item_status(db, tenant, key))
    for tpl in SALES_CHANNEL_SUBSTEPS:
        key = str(tpl["key"])
        _merge_checklist_template(existing, tpl, _checklist_item_status(db, tenant, key))
    for key in list(existing.keys()):
        existing[key]["status"] = _checklist_item_status(db, tenant, key)

    preferred_order = [
        "email",
        "site",
        "ai",
        "product_images",
        "product",
        "platforms",
        "publish",
        "external_accounts",
        "storage",
        "egress",
        "domain",
        "inquiry_im",
        "wecom_push",
        "douyin_worker",
    ]
    ordered_keys = [str(i.get("key")) for i in base if i.get("key")]
    for k in preferred_order:
        if k not in ordered_keys and k in existing:
            ordered_keys.append(k)
    for k in existing:
        if k not in ordered_keys:
            ordered_keys.append(k)
    return [existing[k] for k in ordered_keys if k in existing]


def merge_sales_channel_checklist(
    db: Session,
    tenant: Tenant | None,
    checklist: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """兼容旧调用 — 走全量清单刷新。"""
    return refresh_onboarding_checklist(db, tenant, checklist)


def build_onboarding_roadmap(
    db: Session,
    tenant: Tenant | None,
    checklist: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """按阶段分组的大白话开户路线图。"""
    items = {str(i.get("key")): i for i in refresh_onboarding_checklist(db, tenant, checklist)}
    phases: list[dict[str, Any]] = []
    for phase in ONBOARDING_ROADMAP_PHASES:
        keys = phase.get("keys") or ()
        phase_items = [items[k] for k in keys if k in items]
        if not phase_items:
            continue
        done = sum(1 for i in phase_items if i.get("status") == "done")
        phases.append(
            {
                **phase,
                "done": done,
                "total": len(phase_items),
                "completed": done >= len(phase_items),
                "items": phase_items,
            }
        )
    return phases


def _tenant_review_done(tenant: Tenant | None, core_done: int) -> bool:
    """_tenant_review_done。

    参数说明：
    :param tenant: 参数 tenant
    :param core_done: 参数 core_done
    :return: 返回处理结果。
    """
    if not tenant:
        return False
    settings = _safe_settings(tenant.settings)
    if settings.get("onboarding_review_viewed"):
        return True
    # 前五步完成即视为可复盘
    return core_done >= 4


def evaluate_onboarding_step(
    db: Session,
    tenant: Tenant | None,
    step_id: str,
) -> bool:
    """evaluate_onboarding_step。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param step_id: 参数 step_id
    :return: 返回处理结果。
    """
    if step_id == "site":
        return _tenant_has_site(tenant)
    if step_id == "domain":
        return _tenant_has_bound_domain(tenant)
    if step_id == "product":
        return _tenant_has_product(db, tenant)
    if step_id == "publish":
        return _tenant_has_publish(db, tenant)
    if step_id == "inquiry":
        return _tenant_inquiry_im_inbound_ready(db, tenant)
    if step_id == "im":
        return _tenant_has_im(db, tenant)
    if step_id == "review":
        core = sum(
            1
            for sid in ("site", "domain", "product", "publish", "inquiry")
            if evaluate_onboarding_step(db, tenant, sid)
        )
        return _tenant_review_done(tenant, core)
    return False


def build_onboarding_progress(
    db: Session,
    tenant: Tenant | None,
    template: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """build_onboarding_progress。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param template: 参数 template
    :return: 返回处理结果。
    """
    steps: list[dict[str, Any]] = []
    for i, tpl in enumerate(template):
        done = evaluate_onboarding_step(db, tenant, tpl["id"])
        steps.append({**tpl, "order": i, "done": done})
    return steps


def mark_sales_channel_flag(db: Session, tenant_id: str, flag: str) -> None:
    """开户引导 5a/5b/5c 完成标记（写入 tenant.settings.onboarding.sales_channels）。"""
    from datetime import datetime, timezone
    row = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not row:
        return
    settings = _safe_settings(row.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    sales = onboarding.get("sales_channels") if isinstance(onboarding.get("sales_channels"), dict) else {}
    if sales.get(flag):
        return
    sales = {**sales, flag: True, f"{flag}_at": datetime.now(timezone.utc).isoformat()}
    onboarding = {**onboarding, "sales_channels": sales}
    settings = {**settings, "onboarding": onboarding}
    row.settings = json.dumps(settings, ensure_ascii=False)
    db.add(row)
    db.flush()


# SITE-JTBD-01 · 建站四要素检查（定位 / 结构 / 内容 / 转化）
JTBD_SITE_CHECKLIST_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "key": "jtbd_positioning",
        "title": "定位：卖结果不卖陈列",
        "detail": "填写全站主承诺 primary_promise，Hero 写问题→结果，避免「专业制造商」空口号",
        "route": "/client/site-editor-lab",
        "phase": "建站",
        "paradigm": "定位",
    },
    {
        "key": "jtbd_structure",
        "title": "结构：按客户阶段分",
        "detail": "配置 serviceStages（打样→小批→量产）或按任务分的 solutions",
        "route": "/client/site-editor-lab",
        "phase": "建站",
        "paradigm": "结构",
    },
    {
        "key": "jtbd_content",
        "title": "内容：接住搜索意图",
        "detail": "至少 1 条 knowledgeTopics 技术干货，或 2 条以上优势证据",
        "route": "/client/site-editor-lab",
        "phase": "建站",
        "paradigm": "内容",
    },
    {
        "key": "jtbd_conversion",
        "title": "转化：单一主 CTA",
        "detail": "ctaPrimary 与 inquiryHook 全站一致，导到询盘/RFQ",
        "route": "/client/site-editor-lab",
        "phase": "建站",
        "paradigm": "转化",
    },
)

_GENERIC_HERO_MARKERS = ("专业制造商", "专业建材制造商", "professional manufacturer")


def _tenant_site_home(tenant: Tenant | None) -> dict[str, Any]:
    """_tenant_site_home。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if not tenant:
        return {}
    settings = _safe_settings(tenant.settings)
    brand = settings.get("brand") if isinstance(settings.get("brand"), dict) else {}
    site = brand.get("site_content") if isinstance(brand.get("site_content"), dict) else {}
    pages = site.get("pages") if isinstance(site.get("pages"), dict) else {}
    home = pages.get("home") if isinstance(pages.get("home"), dict) else {}
    return home


def _jtbd_site_item_status(tenant: Tenant | None, key: str) -> str:
    """_jtbd_site_item_status。

    参数说明：
    :param tenant: 参数 tenant
    :param key: 参数 key
    :return: 返回处理结果。
    """
    home = _tenant_site_home(tenant)
    if not home:
        return "pending"

    if key == "jtbd_positioning":
        promise = str(home.get("primary_promise") or "").strip()
        if len(promise) >= 12:
            return "done"
        title = str(home.get("title") or "").strip()
        desc = str(home.get("description") or "").strip()
        generic = any(m.lower() in title.lower() for m in _GENERIC_HERO_MARKERS)
        if len(title) >= 10 and len(desc) >= 30 and not generic:
            return "partial"
        return "pending"

    if key == "jtbd_structure":
        stages = home.get("serviceStages")
        solutions = home.get("solutions")
        stage_n = len(stages) if isinstance(stages, list) else 0
        sol_n = len(solutions) if isinstance(solutions, list) else 0
        if stage_n >= 3 or sol_n >= 3:
            return "done"
        if stage_n >= 2 or sol_n >= 2:
            return "partial"
        return "pending"

    if key == "jtbd_content":
        topics = home.get("knowledgeTopics")
        advantages = home.get("advantages")
        topic_n = len(topics) if isinstance(topics, list) else 0
        adv_n = len(advantages) if isinstance(advantages, list) else 0
        if topic_n >= 1 and adv_n >= 1:
            return "done"
        if topic_n >= 1 or adv_n >= 2:
            return "partial"
        return "pending"

    if key == "jtbd_conversion":
        cta = str(home.get("ctaPrimary") or "").strip()
        hook = str(home.get("inquiryHook") or "").strip()
        promise = str(home.get("primary_promise") or "").strip()
        if len(cta) >= 3 and len(hook) >= 12:
            return "done"
        if len(cta) >= 3 and len(promise) >= 12:
            return "partial"
        return "pending"

    return "pending"


def build_jtbd_site_checklist(tenant: Tenant | None) -> list[dict[str, Any]]:
    """SITE-JTBD-01 · 建站四要素（非 mock 分数，读 site_content 真字段）。"""
    items: list[dict[str, Any]] = []
    for tpl in JTBD_SITE_CHECKLIST_TEMPLATES:
        status = _jtbd_site_item_status(tenant, str(tpl["key"]))
        items.append({**tpl, "status": status})
    return items
