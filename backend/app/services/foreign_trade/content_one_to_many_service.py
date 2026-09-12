"""GW-G-CC-02 — 1 长文 → 多平台变体 + 开发信摘要。"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.content_master import ContentMaster

PLATFORM_RULES: dict[str, dict[str, Any]] = {
    "LinkedIn": {"max_chars": 2800, "prefix": "Professional insight:", "tone": "formal"},
    "百家号": {"max_chars": 2000, "prefix": "", "tone": "article"},
    "抖音": {"max_chars": 500, "prefix": "短视频脚本：", "tone": "short"},
    "小红书": {"max_chars": 900, "prefix": "", "tone": "lifestyle"},
    "Twitter": {"max_chars": 280, "prefix": "", "tone": "punchy"},
    "Facebook": {"max_chars": 1200, "prefix": "", "tone": "social"},
}


def _truncate(text: str, limit: int) -> str:
    """实现 truncate 的功能。
    
    :param text: 参数 text（类型: str）
    :param limit: 参数 limit（类型: int）
    :return: 返回 str 结果
    """
    text = re.sub(r"\s+", " ", (text or "").strip())
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0]
    return cut + "…" if cut else text[:limit]


def _first_paragraph(body: str) -> str:
    """实现 firstparagraph 的功能。
    
    :param body: 参数 body（类型: str）
    :return: 返回 str 结果
    """
    for block in re.split(r"\n\s*\n", body or ""):
        line = block.strip()
        if len(line) > 40:
            return line
    return (body or "").strip()[:400]


def variant_body_for_platform(body: str, platform: str) -> str:
    """实现 variantbodyfor平台 的功能。
    
    :param body: 参数 body（类型: str）
    :param platform: 参数 platform（类型: str）
    :return: 返回 str 结果
    """
    rules = PLATFORM_RULES.get(platform) or {"max_chars": 1500, "prefix": "", "tone": "article"}
    core = _first_paragraph(body) if rules.get("tone") in ("short", "punchy", "lifestyle") else body
    prefix = rules.get("prefix") or ""
    if prefix and not core.startswith(prefix):
        core = f"{prefix}\n\n{core}"
    return _truncate(core, int(rules.get("max_chars") or 1500))


def build_outreach_snippet(title: str, body: str, *, cta_url: str | None = None) -> dict[str, str]:
    """实现 构建outreachsnippet 的功能。
    
    :param title: 参数 title（类型: str）
    :param body: 参数 body（类型: str）
    :param cta_url: 参数 cta_url（类型: str | None）
    :return: 返回 dict[str, str] 结果
    """
    hook = _first_paragraph(body)
    subject = _truncate(re.sub(r"\s+", " ", title or "Partnership inquiry"), 90)
    lines = [
        f"Subject: {subject}",
        "",
        "Hi {{first_name}},",
        "",
        hook,
        "",
        "Would you be open to a 15-minute call to discuss specs and MOQ?",
    ]
    if cta_url:
        lines.extend(["", f"Learn more: {cta_url}"])
    return {
        "subject": subject,
        "body": "\n".join(lines),
        "follow_up_day3": "Following up on specs/MOQ — happy to share catalog PDF.",
        "follow_up_day7": "Checking if timing works for a sample or video factory tour.",
    }


def expand_one_to_many(
    db: Session,
    *,
    master: ContentMaster,
    platforms: list[str],
    include_outreach: bool = True,
) -> dict[str, Any]:
    """从母版生成平台变体草稿（写入 content_masters）。"""
    created: list[dict[str, Any]] = []
    base_title = (master.title or "Untitled").strip()
    base_body = master.body or ""
    for platform in platforms:
        plat = platform.strip()
        if not plat:
            continue
        variant_title = f"[{plat}] {base_title}"[:500]
        exists = (
            db.query(ContentMaster)
            .filter(
                ContentMaster.tenant_id == master.tenant_id,
                ContentMaster.title == variant_title,
                ContentMaster.status.in_(("draft", "ready")),
            )
            .first()
        )
        if exists:
            created.append(
                {
                    "platform": plat,
                    "content_master_id": exists.id,
                    "title": exists.title,
                    "skipped": True,
                    "reason": "already_exists",
                }
            )
            continue

        row = ContentMaster(
            tenant_id=master.tenant_id,
            title=variant_title,
            body=variant_body_for_platform(base_body, plat),
            content_type=master.content_type,
            tenant_canonical_url=master.tenant_canonical_url,
            hub_summary=(master.hub_summary or "")[:500],
            status="draft",
            created_by=master.created_by,
        )
        db.add(row)
        db.flush()
        created.append(
            {
                "platform": plat,
                "content_master_id": row.id,
                "title": row.title,
                "skipped": False,
            }
        )

    outreach = None
    if include_outreach:
        outreach = build_outreach_snippet(
            base_title,
            base_body,
            cta_url=master.tenant_canonical_url,
        )

    db.commit()
    return {
        "source_master_id": master.id,
        "variants": created,
        "outreach": outreach,
        "gw_task": "GW-G-CC-02",
        "write_back": "content_masters",
    }
