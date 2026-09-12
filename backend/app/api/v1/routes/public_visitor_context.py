"""公开站访客地域上下文 — IP/Accept-Language → 语言 + 旺财/站点 UI 文案。"""

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.db.session import get_db
from app.services.im_locale_service import list_supported_languages
from app.services.media_tenant_traffic_service import get_tenant_by_domain
from app.services.onboarding_im_contacts_service import _contact_from_tenant, _safe_settings
from app.services.site_content_locale_service import localize_site_content_snippet
from app.services.visitor_locale_service import (
    build_visitor_contact_channels,
    resolve_visitor_locale,
    sanitize_contacts_for_country,
    site_ui_strings,
    wangcai_trade_qa_enabled,
    wangcai_ui_strings,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/public"

router = APIRouter(tags=["公开-访客地域"])


@router.get("/tenants/{domain}/visitor-context")
def tenant_visitor_context(
    domain: str,
    request: Request,
    country: str | None = Query(None, min_length=2, max_length=2, description="调试：覆盖国家代码"),
    language: str | None = Query(None, min_length=2, max_length=5, description="调试：覆盖语言"),
    db: Session = Depends(get_db),
):
    """
    根据访客 IP 段（CF-IPCountry / X-Visitor-Country）与 Accept-Language
    返回站点与旺财 UI 文案；Contact 渠道按国家排序。
    """
    tenant = get_tenant_by_domain(db, domain)
    if not tenant:
        return error_response(404, "站点不存在")

    locale = resolve_visitor_locale(
        request,
        country_override=country,
        language_override=language,
    )
    lang = locale["language"]
    cc = locale["country_code"]
    contacts = _contact_from_tenant(tenant)
    channels = build_visitor_contact_channels(contacts, country_code=cc, language=lang)
    public_contacts = sanitize_contacts_for_country(contacts, cc)
    settings = _safe_settings(tenant.settings)
    brand = settings.get("brand") if isinstance(settings.get("brand"), dict) else {}
    site_content = brand.get("site_content") if isinstance(brand.get("site_content"), dict) else {}
    site_overlay = localize_site_content_snippet(site_content, lang)
    payload = success_response(
        data={
            "tenant_domain": tenant.domain,
            **locale,
            "site_ui": site_ui_strings(lang),
            "wangcai_ui": wangcai_ui_strings(lang, cc),
            "contact_channels": channels,
            "contacts": public_contacts,
            "cn_compliant_only": cc == "CN" and lang == "zh",
            "wangcai_trade_qa_enabled": wangcai_trade_qa_enabled(cc),
            "supported_languages": list_supported_languages(),
            "site_content_localized": site_overlay,
        }
    ).model_dump()
    return JSONResponse(
        content=payload,
        headers={
            "Cache-Control": "public, max-age=300, stale-while-revalidate=86400",
        },
    )
