"""建材术语库片段 — 供 LLM 翻译/回复时引用。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.globalization import GlossaryTerm


def build_glossary_prompt_block(db: Session, *, limit: int = 24) -> str:
    """实现 构建glossarypromptblock 的功能。
    
    :param db: 参数 db（类型: Session）
    :param limit: 参数 limit（类型: int）
    :return: 返回 str 结果
    """
    rows = (
        db.query(GlossaryTerm)
        .filter(GlossaryTerm.is_active, GlossaryTerm.status == "confirmed")
        .order_by(GlossaryTerm.updated_at.desc())
        .limit(limit)
        .all()
    )
    if not rows:
        rows = (
            db.query(GlossaryTerm)
            .filter(GlossaryTerm.is_active)
            .order_by(GlossaryTerm.updated_at.desc())
            .limit(limit)
            .all()
        )
    if not rows:
        return (
            "岩棉=rock wool; 玻璃棉=glass wool; 橡塑=rubber plastic insulation; "
            "挤塑板=XPS board; 酚醛=phenolic foam; MOQ=minimum order quantity; FOB=Free on Board"
        )
    lines = [f"{r.zh}={r.en}" for r in rows if r.zh and r.en]
    return "; ".join(lines[:limit])
