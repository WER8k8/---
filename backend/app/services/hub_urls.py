"""总站枢纽 URL 构建"""

from app.core.config import settings
from app.models.content_master import ContentMaster
from app.models.tenant import Tenant


def tenant_hub_slug(tenant: Tenant) -> str:
    """tenant_hub_slug。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    return (tenant.domain or "").strip().lower()


def build_hub_page_url(tenant: Tenant, content_id: str) -> str:
    """build_hub_page_url。

    参数说明：
    :param tenant: 参数 tenant
    :param content_id: 参数 content_id
    :return: 返回处理结果。
    """
    base = settings.SITE_URL.rstrip("/")
    slug = tenant_hub_slug(tenant)
    return f"{base}/industry/{slug}/{content_id}"


def build_dual_links(
    tenant: Tenant,
    master: ContentMaster,
    platform_code: str = "",
) -> tuple[str | None, str | None]:
    """主链租户域，次链枢纽页（仅站外发布文案用）。"""
    primary = master.tenant_canonical_url
    if not primary:
        return None, None
    secondary = None
    if master.show_on_hub:
        secondary = build_hub_page_url(tenant, master.id)
        if platform_code:
            sep = "&" if "?" in secondary else "?"
            secondary = f"{secondary}{sep}utm_source={platform_code}&utm_campaign={master.id}"
    sep_p = "&" if "?" in primary else "?"
    primary = f"{primary}{sep_p}utm_source={platform_code}&utm_campaign={master.id}" if platform_code else primary
    return primary, secondary
