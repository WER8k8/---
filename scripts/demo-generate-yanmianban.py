#!/usr/bin/env python3
"""岩棉板生成效果 smoke — 产品候选 / 报价 / Wiki / 语言桥。"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

KEYWORD = "岩棉板"


def _section(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_product_candidate() -> None:
    from app.services.cross_border.industry_belt_product_import_service import list_product_candidates

    data = list_product_candidates(search=KEYWORD, page_size=3)
    items = data.get("items") or []
    _section(f"1. 产业带产品候选「{KEYWORD}」")
    if not items:
        print("未找到候选（检查 survey JSON）")
        return
    for it in items[:2]:
        print(f"- {it.get('name')} | 类目: {it.get('category_name_zh')}")
        print(f"  规格: {', '.join(it.get('specs_common') or [])}")
        print(f"  集群: {it.get('town_cluster')} | 出口: {it.get('export_suitable')}")
        print(f"  证据: {it.get('evidence')}")


def test_export_quote(db, tenant) -> None:
    from app.services.cross_border.export_quote_service import build_export_quote_onepager

    _section("2. 出口报价一页（MOQ 100 m³ · USD 85）")
    data = build_export_quote_onepager(
        db,
        tenant,
        moq="100",
        unit_price=85.0,
        currency="USD",
        notes_zh="岩棉板 A1 防火，厚度 50/75/100mm 可定制。",
    )
    if not data.get("ready"):
        print("未就绪:", data.get("error"), data.get("route_hint"))
        return
    print(data.get("one_pager_zh"))
    pi = data.get("pi") or {}
    lines = pi.get("lines") or pi.get("items") or []
    if lines:
        print("\nPI 首行:", json.dumps(lines[0], ensure_ascii=False)[:300])


def test_wiki_draft() -> None:
    from app.api.v1.routes.building_wiki import _generate_article_for_keyword, create_forum_qa_draft

    _section(f"3. 建材 Wiki 模板「{KEYWORD}」")
    art = _generate_article_for_keyword(KEYWORD, "科普风")
    if art:
        print("标题:", art.get("title"))
        print(art.get("content", "")[:500], "...")
    else:
        sample_q = f"{KEYWORD} A1 防火等级和常用厚度？"
        sample_a = (
            f"{KEYWORD}属于 A1 级不燃材料，常用密度 80–120 kg/m³，"
            "外墙/屋面常用厚度 50、75、100 mm；具体以项目防火设计与当地规范为准。"
        )
        draft = create_forum_qa_draft(sample_q, sample_a)
        print("（无内置模板，用论坛精选草稿示例）")
        print("标题:", draft.get("title") if draft else "—")
        print((draft or {}).get("content", "")[:500], "...")


async def test_forum_bridge(db, tenant) -> None:
    from app.services.cross_border.forum_language_bridge_service import (
        draft_forum_answer_en,
        summarize_forum_question_zh,
    )

    _section("4. 论坛语言桥 · 英问 → 中文摘要")
    en_q = (
        "We need A1 fire rated rock wool board 100mm for facade insulation. "
        "What is your MOQ and FOB Tianjin price?"
    )
    try:
        zh = await summarize_forum_question_zh(
            db,
            tenant,
            question_text=en_q,
            question_title="Rock wool board fire rating",
        )
        print("摘要:", zh.get("summary_zh"))
        print("意向:", zh.get("intent_level"), "| 要点:", zh.get("key_asks"))
        print("模型:", zh.get("model") or "(规则/兜底)")
    except Exception as exc:
        print("LLM 不可用，跳过:", exc)
        return

    _section("5. 论坛语言桥 · 中文要点 → 英文回答")
    boss = "我们是河北大城厂家，A1级岩棉板50-100mm都有，MOQ一般100立方，价格要看密度和包装，可以先报FOB天津参考价。"
    try:
        en = await draft_forum_answer_en(
            db,
            tenant,
            question_title="Rock wool board fire rating",
            question_body=en_q,
            boss_answer_zh=boss,
        )
        print("英文回答:\n", en.get("body_en"))
        print("\n中文回译:", en.get("body_zh_backtranslation"))
    except Exception as exc:
        print("生成失败:", exc)


def _load_dev_env() -> None:
    import os

    env_file = ROOT / "backend" / "config" / "dev" / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if key and key not in os.environ:
            os.environ[key] = val


def main() -> int:
    import os
    from sqlalchemy.exc import OperationalError

    _load_dev_env()
    # 与 start-dev-admin 一致：优先 SQLite 开发库
    backend = ROOT / "backend"
    if not os.environ.get("DATABASE_URL"):
        os.environ["DATABASE_URL"] = f"sqlite:///{(backend / 'youding_dev.db').as_posix()}"
    os.environ.setdefault("ENVIRONMENT", "development")

    from app.db.session import SessionLocal
    from app.models.tenant import Tenant

    test_product_candidate()
    test_wiki_draft()

    db = SessionLocal()
    try:
        tenant = db.query(Tenant).first()
    except OperationalError as exc:
        print("\nWARN: 数据库不可用，跳过报价/语言桥:", exc.__class__.__name__)
        tenant = None
    finally:
        if tenant is None:
            db.close()
            db = None

    if tenant and db:
        try:
            test_export_quote(db, tenant)
            asyncio.run(test_forum_bridge(db, tenant))
        finally:
            db.close()
    else:
        print("\n提示: 文本生成默认走 AI_NVIDIA_API_KEY（NIM）；听写推荐本机 faster-whisper。")

    print("\n完成 — 以上为生成样例，发买家前须人工核对。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
