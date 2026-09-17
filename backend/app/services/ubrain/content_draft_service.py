# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""UBrain-X：将 lead_content_pack 选题写入 ContentMaster 草稿（人审后发布）。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.content_master import ContentMaster


def _draft_body(title: str, category: str) -> str:
    """_draft_body。

    参数说明：
    :param title: 参数 title
    :param category: 参数 category
    :return: 返回处理结果。
    """
    return (
        f"# {title}\n\n"
        f"> 品类：{category} · 由 UBrain-X 获客内容包生成 · **草稿，需人审后发布**\n\n"
        "## 读者常见问题（正文待您补充）\n\n"
        "- 适用场景与规格怎么选\n"
        "- 报价区间受哪些因素影响\n"
        "- 交付周期与验收要点\n\n"
        "## 行动号召（北极星）\n\n"
        "请在**独立域**页面提交询盘表单或拨打页面电话，获取规格与报价。"
        "勿只堆文章不带转化入口。\n"
    )


def write_lead_content_drafts(
    db: Session,
    *,
    tenant_id: str,
    pack: dict[str, Any],
    created_by: str | None = None,
) -> list[dict[str, Any]]:
    """
    把 pack['topics'] 逐条写入 content_masters，status=draft。
    返回已创建记录的简要信息（id/title/status）。
    """
    topics = pack.get("topics") or []
    if not topics or not tenant_id:
        return []

    category = str(pack.get("category") or "建材")
    existing_titles = {
        (row[0] if isinstance(row, tuple) else row)
        for row in db.query(ContentMaster.title)
        .filter(
            ContentMaster.tenant_id == tenant_id,
            ContentMaster.status == "draft",
        )
        .all()
    }
    created: list[dict[str, Any]] = []
    for topic in topics:
        title = str(topic).strip()[:500]
        if not title or title in existing_titles:
            continue
        row = ContentMaster(
            tenant_id=tenant_id,
            title=title,
            body=_draft_body(title, category),
            content_type="article",
            hub_summary=title[:200],
            show_on_hub=False,
            status="draft",
            created_by=created_by,
        )
        db.add(row)
        created.append({"title": title, "status": "draft"})

    if created:
        db.commit()
        # refresh ids after commit
        rows = (
            db.query(ContentMaster)
            .filter(
                ContentMaster.tenant_id == tenant_id,
                ContentMaster.status == "draft",
                ContentMaster.title.in_([c["title"] for c in created]),
            )
            .order_by(ContentMaster.created_at.desc())
            .limit(len(created))
            .all()
        )
        by_title = {r.title: r for r in rows}
        for item in created:
            row = by_title.get(item["title"])
            if row:
                item["id"] = row.id
                item["admin_path"] = "/client/content-masters"

    return created
