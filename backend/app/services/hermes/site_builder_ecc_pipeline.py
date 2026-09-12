"""Hermes 建站 ECC 专家流水线 — 美工/文案/视觉营销/美学 UI，非裸 LLM。"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.services.hermes.site_design_guard import apply_design_guard, load_design_manifest
from app.services.hermes.site_cta_audit import audit_site_western_cta
from app.services.site_ai_service import generate_site_content
from app.services.site_product_assets import apply_customer_product_images

logger = logging.getLogger(__name__)

_PIPELINE_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "hermes_site_builder_pipeline.json"
)

DEFAULT_CTA_PRIMARY = "Request Quotation"
DEFAULT_CTA_SECONDARY = "WhatsApp Us"
DEFAULT_INQUIRY_HOOK = (
    "Share your project specs, quantity and destination port — "
    "our export team replies within 24 hours with datasheet and sample options."
)
DEFAULT_INQUIRY_PROMPT = "Free sample & technical datasheet available for qualified projects."


@lru_cache(maxsize=1)
def load_site_builder_pipeline() -> dict[str, Any]:
    """load_site_builder_pipeline。
    :return: 返回处理结果。
    """
    with open(_PIPELINE_PATH, encoding="utf-8") as f:
        return json.load(f)


def compile_expert_brief(manifest: dict[str, Any] | None = None) -> str:
    """合并 manifest 设计技能 + pipeline 专家阶段，注入 LLM prompt。"""
    pipe = load_site_builder_pipeline()
    manifest = manifest or load_design_manifest()
    lines = ["【Hermes ECC 建站专家编排 — 必须遵守】"]
    for stage in pipe.get("stages") or []:
        if not isinstance(stage, dict):
            continue
        title = stage.get("title") or stage.get("id")
        experts = ", ".join(stage.get("experts") or [])
        skills = stage.get("ecc_skills") or []
        lines.append(f"▸ {title}（专家：{experts}）")
        for sid in skills:
            for skill in manifest.get("design_skills") or []:
                if isinstance(skill, dict) and skill.get("id") == sid:
                    for rule in skill.get("rules") or []:
                        lines.append(f"  · {rule}")
    lessons = pipe.get("reference_lessons") or {}
    if lessons:
        lines.append("【对标站教训】")
        for site, lesson in lessons.items():
            lines.append(f"  · {site}：{lesson}")
    return "\n".join(lines)


def _stage_record(stage_id: str, experts: list[str], skills: list[str], note: str) -> dict[str, Any]:
    """_stage_record。

    参数说明：
    :param stage_id: 参数 stage_id
    :param experts: 参数 experts
    :param skills: 参数 skills
    :param note: 参数 note
    :return: 返回处理结果。
    """
    return {
        "stage": stage_id,
        "experts": experts,
        "ecc_skills": skills,
        "note": note,
    }


def apply_copy_expert_pass(site_content: dict[str, Any], product_name: str) -> dict[str, Any]:
    """文案专家：tagline/描述克制、B2B 制造商语气。"""
    out = json.loads(json.dumps(site_content, ensure_ascii=False))
    brand = out.setdefault("brand", {})
    if not str(brand.get("tagline") or "").strip():
        short = (product_name or "Insulation")[:24]
        brand["tagline"] = f"{short} Insulation Manufacturer in China · OEM/ODM"

    pages = out.setdefault("pages", {})
    home = pages.setdefault("home", {})
    desc = str(home.get("description") or "")
    if len(desc) > 420:
        home["description"] = desc[:417].rsplit(" ", 1)[0] + "…"

    products = pages.setdefault("products", {})
    if not str(products.get("description") or "").strip():
        products["description"] = (
            f"Hot {product_name} series for distributors and EPC contractors — inquiry welcome."
        )
    return out


def apply_visual_marketing_pass(site_content: dict[str, Any]) -> dict[str, Any]:
    """
    视觉营销专家：西方采购商询盘欲望（对标 vortex 教训 — 大图不够，要 CTA+承诺）。
    """
    out = json.loads(json.dumps(site_content, ensure_ascii=False))
    pages = out.setdefault("pages", {})
    home = pages.setdefault("home", {})
    contact = pages.setdefault("contact", {})
    whatsapp = str(contact.get("whatsapp") or "").strip()
    home.setdefault("ctaPrimary", DEFAULT_CTA_PRIMARY)
    home.setdefault(
        "ctaSecondary",
        DEFAULT_CTA_SECONDARY if whatsapp else "Contact Us",
    )
    home.setdefault("inquiryHook", DEFAULT_INQUIRY_HOOK)
    contact.setdefault("inquiryPrompt", DEFAULT_INQUIRY_PROMPT)
    if whatsapp and "WhatsApp" not in home.get("ctaSecondary", ""):
        home["ctaSecondary"] = DEFAULT_CTA_SECONDARY

    return out


def apply_ui_aesthetic_pass(site_content: dict[str, Any]) -> dict[str, Any]:
    """
    美学/UI 专家：反 cellularglass 拥挤排版 — 留白、密度、节标题清晰。
    """
    out = json.loads(json.dumps(site_content, ensure_ascii=False))
    meta = out.setdefault("meta", {})
    meta["layout_density"] = "balanced"
    meta["anti_patterns"] = ["cellularglass-clutter", "hero-only-no-cta"]
    pages = out.setdefault("pages", {})
    home = pages.setdefault("home", {})
    for key in ("title", "sectionTitle", "applicationsTitle"):
        val = str(home.get(key) or "")
        if val:
            home[key] = " ".join(val.split())[:120]

    return out


def collect_pipeline_experts() -> list[dict[str, str]]:
    """collect_pipeline_experts。
    :return: 返回处理结果。
    """
    pipe = load_site_builder_pipeline()
    seen: set[str] = set()
    rows: list[dict[str, str]] = []
    for stage in pipe.get("stages") or []:
        if not isinstance(stage, dict):
            continue
        for eid in stage.get("experts") or []:
            if eid not in seen:
                seen.add(eid)
                rows.append({"id": eid, "stage": str(stage.get("id") or "")})
    return rows


def _apply_expert_passes(
    site_content: dict[str, Any],
    *,
    product_name: str,
    product_images: list[Any] | None,
    trace: list[dict[str, Any]],
) -> dict[str, Any]:
    """依次执行文案/视觉营销/美学 UI/设计门禁/L-Pro 填槽等专家后处理。"""
    site_content = apply_copy_expert_pass(site_content, product_name)
    trace.append(
        _stage_record(
            "structure_copy",
            ["copywriter"],
            ["brand-copy-plain"],
            "文案专家后处理",
        ),
    )
    site_content = apply_visual_marketing_pass(site_content)
    trace.append(
        _stage_record(
            "visual_marketing",
            ["visual-marketing", "ux-architect", "ad-creative-strategist"],
            ["western-inquiry-conversion", "sme-acceptable-bar"],
            "CTA 与询盘钩子已注入",
        ),
    )
    site_content = apply_ui_aesthetic_pass(site_content)
    trace.append(
        _stage_record(
            "ui_aesthetic",
            ["ui-designer", "brand-guardian"],
            ["ui-design-handoff", "anti-clutter-layout"],
            "美学密度与反拥挤排版",
        ),
    )
    site_content = apply_design_guard(site_content)
    site_content = apply_customer_product_images(site_content, product_images)
    trace.append(
        _stage_record(
            "guard_assets",
            ["qa-reviewer"],
            ["customer-product-assets", "ui-design-handoff"],
            "设计门禁 + 客户产品图挂接",
        ),
    )
    from app.services.site_l_pro_service import apply_l_pro_site_pass
    site_content = apply_l_pro_site_pass(site_content, product_name=product_name)
    from app.services.jtbd_site_service import apply_jtbd_site_pass
    site_content = apply_jtbd_site_pass(site_content)
    trace.append(
        _stage_record(
            "l_pro_slots",
            ["ui-designer", "product-manager"],
            ["premium-b2b-v1", "site-editor-schema"],
            f"L-Pro 填槽 templateId={site_content.get('templateId')}",
        ),
    )
    return site_content


def _finalize_pipeline_meta(
    site_content: dict[str, Any],
    *,
    trace: list[dict[str, Any]],
) -> dict[str, Any]:
    """写入流水线元信息（版本/专家/trace/CTA 审计/发布门禁）并返回 meta。"""
    meta = site_content.setdefault("meta", {})
    meta["ecc_pipeline_version"] = load_site_builder_pipeline().get("pipeline_version")
    meta["ecc_experts_applied"] = [e["id"] for e in collect_pipeline_experts()]
    meta["pipeline_trace"] = trace
    meta["cta_audit"] = audit_site_western_cta(site_content)
    from app.services.site_l_pro_service import validate_l_pro_publish_gate
    meta["l_pro_publish_gate"] = validate_l_pro_publish_gate(site_content)
    return meta


async def run_ecc_site_builder_pipeline(
    db: Session | None,
    *,
    product_name: str,
    company_name: str = "",
    tenant_id: str | None = None,
    use_ai: bool = True,
    product_images: list[Any] | None = None,
    skip_i18n_ai: bool = False,
) -> dict[str, Any]:
    """
    Hermes 驱动 ECC 建站全流程。
    返回 site_content, source, pipeline_trace, ecc_experts_applied。
    """
    manifest = load_design_manifest()
    expert_brief = compile_expert_brief(manifest)
    trace: list[dict[str, Any]] = []
    trace.append(
        _stage_record(
            "brief",
            ["pm-orchestrator", "workflow-architect"],
            ["site-editor-schema", "b2b-industrial-layout"],
            "专家简报已编译",
        ),
    )
    gen = await generate_site_content(
        db,
        product_name=product_name,
        company_name=company_name,
        tenant_id=tenant_id,
        use_ai=use_ai,
        design_manifest={**manifest, "_ecc_expert_brief": expert_brief},
        product_images=product_images,
        skip_i18n_ai=skip_i18n_ai,
    )
    site_content = gen["site_content"]
    source = gen.get("source") or "template"
    trace.append(
        _stage_record(
            "structure_copy",
            ["copywriter", "insulation-material-product-manager", "technical-writer"],
            ["brand-copy-plain", "industry-giant-narrative"],
            f"内容生成 source={source}",
        ),
    )
    site_content = _apply_expert_passes(
        site_content,
        product_name=product_name,
        product_images=product_images,
        trace=trace,
    )
    meta = _finalize_pipeline_meta(site_content, trace=trace)
    cta_audit = meta["cta_audit"]
    return {
        "site_content": site_content,
        "source": source,
        "pipeline_trace": trace,
        "ecc_experts_applied": meta["ecc_experts_applied"],
        "expert_brief_chars": len(expert_brief),
        "cta_audit": cta_audit,
        "l_pro_publish_gate": meta.get("l_pro_publish_gate"),
    }
