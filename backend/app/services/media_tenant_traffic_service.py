"""视频 → 租户官网流量：落地页、UTM、结构化数据、GEO 要点。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.media_factory import MediaRenderTask
from app.models.tenant import Tenant
from app.services.media_cloud_upload_service import playback_url_for_task
from app.services.media_seo_service import build_media_seo_bundle, upsert_media_seo_metadata
from app.services.media_video_edit_service import load_edit_config, save_edit_config

_VIDEO_PATH_PREFIX = "/v/"


def _utcnow() -> datetime:
    """_utcnow。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc)


def _safe_json(raw: str | None) -> dict[str, Any]:
    """_safe_json。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def get_tenant(db: Session, tenant_id: str | None) -> Tenant | None:
    """get_tenant。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    if not tenant_id:
        return None
    return db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.is_active.is_(True)).first()


def get_tenant_by_domain(db: Session, domain: str) -> Tenant | None:
    """get_tenant_by_domain。

    参数说明：
    :param db: 参数 db
    :param domain: 参数 domain
    :return: 返回处理结果。
    """
    from app.repositories.tenant_repository import TenantRepository
    domain = (domain or "").strip().lower()
    if not domain:
        return None
    tenant = TenantRepository(db).get_by_domain(domain)
    if tenant and tenant.is_active:
        return tenant
    return None


def tenant_public_base_url(tenant: Tenant) -> str:
    """租户官网根地址（用于 canonical / 视频落地页）。"""
    cfg = _safe_json(tenant.settings)
    custom = cfg.get("custom_domains") or cfg.get("white_label", {}).get("custom_domains")
    if isinstance(custom, list) and custom:
        host = str(custom[0]).strip().rstrip("/")
        if host.startswith("http"):
            return host
        return f"https://{host}"
    if isinstance(custom, str) and custom.strip():
        c = custom.strip()
        return c if c.startswith("http") else f"https://{c}"

    primary = (settings.SAAS_PRIMARY_DOMAIN or "youding-saas.com").strip()
    slug = (tenant.domain or "").strip()
    if settings.ENVIRONMENT in ("development", "testing", "test"):
        front = (settings.FRONTEND_URL or "http://localhost:3000").rstrip("/")
        return f"{front}/tenant?__tenant={slug}"
    return f"https://{slug}.{primary}"


def tenant_video_landing_url(tenant: Tenant, task_id: str) -> str:
    """tenant_video_landing_url。

    参数说明：
    :param tenant: 参数 tenant
    :param task_id: 参数 task_id
    :return: 返回处理结果。
    """
    base = tenant_public_base_url(tenant).rstrip("/")
    if "__tenant=" in base:
        sep = "&" if "?" in base else "?"
        return f"{base}{sep}video={task_id}"
    prefix = getattr(settings, "MEDIA_TENANT_VIDEO_PATH_PREFIX", _VIDEO_PATH_PREFIX) or _VIDEO_PATH_PREFIX
    return f"{base}{prefix}{task_id}"


def inquiry_cta_url(landing_url: str, task_id: str) -> str:
    """inquiry_cta_url。

    参数说明：
    :param landing_url: 参数 landing_url
    :param task_id: 参数 task_id
    :return: 返回处理结果。
    """
    base = landing_url.split("#")[0]
    params = urlencode(
        {
            "utm_source": "video",
            "utm_medium": "tenant_site",
            "utm_campaign": task_id[:36],
        }
    )
    return f"{base}#contact?{params}"


def build_platform_description(task: MediaRenderTask, tenant: Tenant, bundle: dict[str, Any]) -> str:
    """视频网站描述：摘要 + 回链租户官网（SEO 外链）。"""
    lines = [
        (bundle.get("meta_description") or "").strip(),
        "",
        f"官网了解更多：{bundle.get('tenant_landing_url') or tenant_video_landing_url(tenant, task.id)}",
    ]
    facts = bundle.get("geo_facts") or []
    if facts:
        lines.append("")
        lines.append("【要点】")
        lines.extend(f"· {f}" for f in facts[:5])
    lines.append("")
    lines.append(f"询盘：{bundle.get('inquiry_cta_url') or inquiry_cta_url(tenant_video_landing_url(tenant, task.id), task.id)}")
    return "\n".join(line for line in lines if line is not None).strip()


def publish_video_to_tenant_site(db: Session, task: MediaRenderTask, tenant: Tenant | None = None) -> dict[str, Any]:
    """在租户官网登记视频落地页（SEO metadata + edit_config），不替代酷播/R2。"""
    tenant = tenant or get_tenant(db, task.tenant_id)
    if not tenant:
        return {"published": False, "reason": "no_tenant"}

    if task.status != "done" or task.file_purged:
        return {"published": False, "reason": "task_not_ready"}

    landing = tenant_video_landing_url(tenant, task.id)
    base = tenant_public_base_url(tenant)
    path = f"/v/{task.id}" if "__tenant=" not in base else f"?video={task.id}"
    bundle = build_media_seo_bundle(
        task,
        canonical_path=path,
        site_base_url=base.split("?")[0].rstrip("/") if "__tenant=" in base else base,
    )
    bundle["tenant_landing_url"] = landing
    bundle["inquiry_cta_url"] = inquiry_cta_url(landing, task.id)
    bundle["traffic_goal"] = "tenant_site_inquiry"
    upsert_media_seo_metadata(db, task, bundle)
    cfg = load_edit_config(task)
    cfg["tenant_traffic"] = {
        "landing_url": landing,
        "inquiry_cta_url": bundle["inquiry_cta_url"],
        "published_at": _utcnow().isoformat(),
        "geo_facts": bundle.get("geo_facts") or [],
        "schema_markup_json": bundle.get("schema_markup_json"),
    }
    save_edit_config(db, task, cfg)
    return {"published": True, **bundle}


def list_public_videos_for_tenant(db: Session, tenant: Tenant, limit: int = 50) -> list[dict[str, Any]]:
    """list_public_videos_for_tenant。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    rows = (
        db.query(MediaRenderTask)
        .filter(
            MediaRenderTask.tenant_id == str(tenant.id),
            MediaRenderTask.status == "done",
            MediaRenderTask.file_purged == 0,
        )
        .order_by(MediaRenderTask.finished_at.desc())
        .limit(limit)
        .all()
    )
    out: list[dict[str, Any]] = []
    for task in rows:
        cfg = load_edit_config(task)
        traffic = cfg.get("tenant_traffic") or {}
        if not traffic.get("landing_url"):
            continue
        out.append(public_video_card(task, tenant, traffic))
    return out


def public_video_card(
    task: MediaRenderTask,
    tenant: Tenant,
    traffic: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """public_video_card。

    参数说明：
    :param task: 参数 task
    :param tenant: 参数 tenant
    :param traffic: 参数 traffic
    :return: 返回处理结果。
    """
    traffic = traffic or {}
    play = playback_url_for_task(task) or task.result_url
    return {
        "id": task.id,
        "title": task.title,
        "description": (task.script or "")[:200],
        "playback_url": play,
        "landing_url": traffic.get("landing_url") or tenant_video_landing_url(tenant, task.id),
        "thumbnail": traffic.get("thumbnail"),
        "finished_at": task.finished_at.isoformat() if task.finished_at else None,
        "geo_facts": traffic.get("geo_facts") or [],
    }


def public_video_page_payload(
    db: Session,
    tenant: Tenant,
    task_id: str,
) -> dict[str, Any] | None:
    """public_video_page_payload。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param task_id: 参数 task_id
    :return: 返回处理结果。
    """
    task = (
        db.query(MediaRenderTask)
        .filter(MediaRenderTask.id == task_id, MediaRenderTask.tenant_id == str(tenant.id))
        .first()
    )
    if not task or task.status != "done" or task.file_purged:
        return None

    cfg = load_edit_config(task)
    traffic = cfg.get("tenant_traffic")
    if not traffic:
        publish_video_to_tenant_site(db, task, tenant)
        cfg = load_edit_config(task)
        traffic = cfg.get("tenant_traffic") or {}

    bundle = build_media_seo_bundle(
        task,
        site_base_url=tenant_public_base_url(tenant),
    )
    bundle["tenant_landing_url"] = traffic.get("landing_url") or tenant_video_landing_url(tenant, task.id)
    bundle["inquiry_cta_url"] = traffic.get("inquiry_cta_url") or inquiry_cta_url(
        bundle["tenant_landing_url"], task.id
    )
    return {
        "tenant": {"name": tenant.name, "domain": tenant.domain},
        "video": public_video_card(task, tenant, traffic),
        "seo": bundle,
        "playback_url": playback_url_for_task(task),
    }


def build_videos_sitemap_xml(tenant: Tenant, videos: list[dict[str, Any]]) -> str:
    """build_videos_sitemap_xml。

    参数说明：
    :param tenant: 参数 tenant
    :param videos: 参数 videos
    :return: 返回处理结果。
    """
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">',
    ]
    for v in videos:
        loc = _xml_escape(v.get("landing_url") or "")
        if not loc:
            continue
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        if v.get("playback_url"):
            lines.append("    <video:video>")
            lines.append(f"      <video:content_loc>{_xml_escape(v['playback_url'])}</video:content_loc>")
            lines.append(f"      <video:title>{_xml_escape(v.get('title') or '')}</video:title>")
            desc = _xml_escape((v.get("description") or "")[:2048])
            lines.append(f"      <video:description>{desc}</video:description>")
            lines.append("    </video:video>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines)


def _xml_escape(text: str) -> str:
    """_xml_escape。

    参数说明：
    :param text: 参数 text
    :return: 返回处理结果。
    """
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
