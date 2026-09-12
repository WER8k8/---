path = 'app/api/v1/routes/client.py'
lines = open(path, encoding='utf-8').read().split('\n')
# replace 1-indexed lines 100..211 inclusive (whole get_client_dashboard func)
start, end = 100, 211
new_block = '''@router.get("/dashboard")
def get_client_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取客户工作台数据"""
    tenant, link, err = _resolve_tenant(db, current_user)
    if err:
        return err

    tid = str(tenant.id)
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    inq_base = apply_real_inquiry_filters(
        db.query(Inquiry).filter(Inquiry.tenant_id == tid)
    )
    today_inquiries = count_real_inquiries(
        db, tenant_id=tid, today_start=today_start
    )
    pending_inquiries = count_real_inquiries(db, tenant_id=tid, status="pending")
    raw_pending = count_raw_inquiries(db, tenant_id=tid, status="pending")
    total_products = db.query(Product).filter(Product.is_active).count()

    recent = inq_base.order_by(Inquiry.created_at.desc()).limit(5).all()

    traffic_7d: dict = {}
    try:
        traffic_board = TrafficAnalyticsService(db).build_board(
            period="7d", tenant_id=tid, scope="tenant"
        )
        traffic_7d = traffic_board.get("summary") or {}
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("获取流量分析数据失败，使用空数据: %s", e)
        traffic_7d = {}

    ai_quota = _resolve_ai_quota(tenant)
    brand = _resolve_brand(tenant)

    publish_in_progress = _count_publish_in_progress(db, tid)
    domain_status = _domain_status(tenant)

    today = build_today_payload(
        db=db,
        tenant=tenant,
        pending_inquiries=pending_inquiries,
        publish_in_progress=publish_in_progress,
    )
    autopilot = get_autopilot_summary(tenant)
    journey_health = today.get("journey_health") or {}

    return success_response(data={
        "tenant_id": str(tenant.id),
        "brand": brand,
        "today_one_thing": today["today_one_thing"],
        "today_queue": today["today_queue"],
        "blue_ocean_hint": today["blue_ocean_hint"],
        "journey_health": journey_health,
        "autopilot": autopilot,
        "autopilot_headline": (autopilot or {}).get("headline"),
        "stats": _build_dashboard_stats(
            traffic_7d, today_inquiries, pending_inquiries, total_products
        ),
        "traffic_7d": traffic_7d,
        "plan_name": ai_quota["plan_name"],
        "plan_expiry": ai_quota["plan_expiry"],
        "tenant_status": tenant.status,
        "ai_quota_used": tenant.ai_quota_used or 0,
        "ai_quota_total": ai_quota["ai_quota_total"],
        "ai_traffic_provider_id": ai_quota["ai_traffic_provider_id"],
        "ai_traffic_provider_label": ai_quota["ai_traffic_provider_label"],
        "site_url": resolve_client_site_url(tenant),
        "publish_in_progress": publish_in_progress,
        "domain_status": domain_status,
        "recent_inquiries": [
            {"id": str(i.id), "name": i.name, "message": i.message,
             "time": i.created_at.strftime("%m-%d %H:%M") if i.created_at else "",
             "status": i.status}
            for i in recent
        ],
        "data_honesty": {
            "excluded_inquiries": max(0, raw_pending - pending_inquiries),
            "raw_pending_inquiries": raw_pending,
            "note": "已排除本地演示/测试询盘，未上线站点不会产生真实询盘。",
        },
    })


def _resolve_ai_quota(tenant: Tenant) -> dict:
    """解析租户的套餐、配额与 AI 流量通道信息。

    :param tenant: 租户对象。
    :return: 包含 plan_name/plan_expiry/ai_quota_total/ai_traffic_provider_id/ai_traffic_provider_label 的字典。
    """
    from app.services.ai_traffic_provider_service import (
        get_tenant_ai_traffic_provider,
        provider_label,
    )
    plan_name = tenant.plan.name if tenant.plan else "免费版"
    trial_end = tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None
    ai_quota_total = tenant.plan.max_ai_quota if tenant.plan else 0
    ai_provider_id = get_tenant_ai_traffic_provider(tenant)
    return {
        "plan_name": plan_name,
        "plan_expiry": trial_end,
        "ai_quota_total": ai_quota_total,
        "ai_traffic_provider_id": ai_provider_id,
        "ai_traffic_provider_label": provider_label(ai_provider_id) if ai_provider_id else None,
    }


def _resolve_brand(tenant: Tenant) -> dict:
    """解析租户品牌配置，缺省回退到租户名称。

    :param tenant: 租户对象。
    :return: 品牌配置字典。
    """
    brand = {"company_name": tenant.name, "slogan": ""}
    if tenant.settings:
        try:
            settings_dict = json.loads(tenant.settings)
            brand_data = settings_dict.get("brand", {})
            if brand_data:
                brand = brand_data
        except (json.JSONDecodeError, TypeError):
            pass
    return brand


def _build_dashboard_stats(
    traffic_7d: dict,
    today_inquiries: int,
    pending_inquiries: int,
    total_products: int,
) -> dict:
    """构建仪表盘统计指标字典。

    :param traffic_7d: 近 7 日流量汇总。
    :param today_inquiries: 今日真实询盘数。
    :param pending_inquiries: 待处理询盘数。
    :param total_products: 上架产品数。
    :return: 统计指标字典。
    """
    return {
        "today_inquiries": today_inquiries,
        "pending_inquiries": pending_inquiries,
        "total_products": total_products,
        "keyword_count": 0,
        "visitors_7d": traffic_7d.get("unique_visitors", 0),
        "page_views_7d": traffic_7d.get("page_views", 0),
        "clicks_7d": traffic_7d.get("total_clicks", 0),
        "inquiries_7d": traffic_7d.get("inquiries", 0),
        "conversion_rate_7d": traffic_7d.get("conversion_rate", 0),
    }'''

new_lines = lines[:start-1] + new_block.split('\n') + lines[end:]
open(path, 'w', encoding='utf-8').write('\n'.join(new_lines))
print("client.py updated; new line count:", len(new_lines))
