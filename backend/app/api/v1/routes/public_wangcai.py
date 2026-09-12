"""公开站旺财 — 海关全量数据 + 出口问答（无需登录）。"""



from pydantic import BaseModel, Field



from fastapi import APIRouter, Depends, Query, Request

from sqlalchemy.orm import Session



from app.core.response import error_response, success_response

from app.db.session import get_db

from app.services.media_tenant_traffic_service import get_tenant_by_domain

from app.services.tenant_product_context import resolve_tenant_product_hint

from app.services.wangcai.wangcai_task_service import (
    WangcaiChatTaskError,
    run_wangcai_task,
)

from app.services.visitor_locale_service import resolve_visitor_locale, wangcai_trade_qa_enabled, wangcai_ui_strings

from app.services.wangcai_trade_service import (

    public_customs_payload,

    suggested_prompts,

)




# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/public"

router = APIRouter(tags=["公开-旺财贸易助手"])





class WangcaiAskBody(BaseModel):

    message: str = Field(..., min_length=1, max_length=800)
    product_hint: str | None = Field(None, max_length=200)
    language: str | None = Field(None, max_length=5)
    country_code: str | None = Field(None, max_length=2)





def _locale_from_request(

    request: Request,

    *,

    language: str | None = None,

    country_code: str | None = None,

) -> dict[str, str]:
    """执行 locale_from_request 相关逻辑处理。
    
    :param request: HTTP 请求对象
    :param language: 参数 language
    :param country_code: 参数 country_code
    :return: 返回处理结果。
    """
    return resolve_visitor_locale(

        request,
        country_override=country_code,
        language_override=language,

    )





@router.get("/tenants/{domain}/wangcai/prompts")

def wangcai_prompts(

    domain: str,

    request: Request,

    product_hint: str | None = Query(None, max_length=200),

    language: str | None = Query(None, max_length=5),

    country_code: str | None = Query(None, max_length=2),

    db: Session = Depends(get_db),

):
    """处理 GET /tenants/{domain}/wangcai/prompts 请求，wangcai相关资源。
    
    :param domain: 域名
    :param request: HTTP 请求对象
    :param product_hint: 参数 product_hint
    :param language: 参数 language
    :param country_code: 参数 country_code
    :param db: 数据库会话
    :return: 返回处理结果。
    """
    tenant = get_tenant_by_domain(db, domain)
    if not tenant:

        return error_response(404, "站点不存在")

    hint = (product_hint or "").strip() or resolve_tenant_product_hint(tenant)
    locale = _locale_from_request(request, language=language, country_code=country_code)
    lang = locale["language"]
    cc = locale["country_code"]
    if not wangcai_trade_qa_enabled(cc):
        ui = wangcai_ui_strings(lang, cc)
        return success_response(
            data={
                "tenant_domain": tenant.domain,
                "product_hint": hint,
                "prompts": [],
                "language": lang,
                "country_code": cc,
                "trade_qa_disabled": True,
                "message": ui.get("trade_qa_disabled", ""),
            }
        )

    return success_response(

        data={

            "tenant_domain": tenant.domain,
            "product_hint": hint,
            "prompts": suggested_prompts(hint, language=lang),
            "language": lang,
            "country_code": locale["country_code"],

        }

    )





@router.post("/tenants/{domain}/wangcai/ask")

def wangcai_ask(

    domain: str,

    body: WangcaiAskBody,

    request: Request,

    db: Session = Depends(get_db),

):
    """处理 POST /tenants/{domain}/wangcai/ask 请求，wangcai相关资源。
    
    :param domain: 域名
    :param body: 请求体
    :param request: HTTP 请求对象
    :param db: 数据库会话
    :return: 返回处理结果。
    """
    tenant = get_tenant_by_domain(db, domain)
    if not tenant:

        return error_response(404, "站点不存在")

    hint = (body.product_hint or "").strip() or resolve_tenant_product_hint(tenant)
    locale = _locale_from_request(

        request,
        language=body.language,
        country_code=body.country_code,

    )
    cc = locale["country_code"]
    lang = locale["language"]
    if not wangcai_trade_qa_enabled(cc):
        ui = wangcai_ui_strings(lang, cc)
        return success_response(
            data={
                "intent": "help",
                "reply": ui.get("trade_qa_disabled", "请通过联系渠道咨询。"),
                "prompts": [],
                "disclaimer": "",
                "language": lang,
                "tenant_domain": tenant.domain,
                "product_hint": hint,
                "country_code": cc,
                "trade_qa_disabled": True,
            }
        )

    # H.5：旺财统一走 Hermes 任务面（task_type=wangcai_intent），响应契约不变。
    try:
        _task, data = run_wangcai_task(
            db,
            tenant_id=str(tenant.id),
            message=body.message,
            source="public_site",
            product_hint=hint,
            language=locale["language"],
        )
    except WangcaiChatTaskError as exc:
        return error_response(500, str(exc))
    data["tenant_domain"] = tenant.domain
    data["product_hint"] = hint
    data["country_code"] = locale["country_code"]
    return success_response(data=data)





@router.get("/tenants/{domain}/wangcai/customs")

def wangcai_customs_all(

    domain: str,

    category_key: str | None = Query(None),

    db: Session = Depends(get_db),

):

    """全量海关公开统计（20 品类 × 50 国）；可按 category_key 过滤单品类。"""
    tenant = get_tenant_by_domain(db, domain)
    if not tenant:

        return error_response(404, "站点不存在")

    payload = public_customs_payload(category_key=category_key)
    if category_key and not payload.get("found", True):

        return error_response(404, "品类不存在")

    payload["tenant_domain"] = tenant.domain
    return success_response(data=payload)

