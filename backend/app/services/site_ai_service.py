"""租户官网 AI 一键建站：根据产品名生成 site_content 结构。"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.services.ai_invocation_service import invoke_llm
from app.services.site_content_array_i18n import default_product_items_en

logger = logging.getLogger(__name__)

_SITE_JSON_EXAMPLE = """{
  "brand": {"name": "品牌名", "tagline": "一句标语"},
  "footer": {"text": ""},
  "theme": {"headerBg": "#1e293b", "heroBg": "#f8fafc", "footerBg": "#1e293b"},
  "pages": {
    "home": {
      "title": "产品英文名 + 制造商",
      "description": "公司成立年份、工厂面积、出口经验一段介绍",
      "seoDescription": "搜索简介",
      "seoKeywords": "关键词1,关键词2",
      "heroImage": "",
      "sectionTitle": "为什么选择我们",
      "features": ["优势标题1", "优势标题2", "优势标题3", "优势标题4"],
      "categories": [
        {"name": "产品分类1", "description": "一句话说明用途"},
        {"name": "产品分类2", "description": "一句话说明用途"}
      ],
      "applications": [
        {"title": "Roof Insulation", "description": "适用说明"},
        {"title": "External Wall", "description": "适用说明"}
      ],
      "applicationsTitle": "What Are You Insulating?",
      "solutions": [
        {"segment": "Building", "title": "Building & Construction", "description": "墙体屋面保温系统"},
        {"segment": "Industrial", "title": "Industrial", "description": "工业设备与管道保温"},
        {"segment": "HVAC", "title": "HVAC", "description": "暖通空调风管与设备"},
        {"segment": "Marine", "title": "Marine & Offshore", "description": "船用防火保温"}
      ],
      "advantages": [
        {"title": "品质可控", "description": "源头工厂质检"},
        {"title": "定制生产", "description": "OEM/ODM"},
        {"title": "安装便捷", "description": "施工友好"},
        {"title": "全球出口", "description": "多国标认证"}
      ],
      "establishedYear": "2005",
      "trustBadges": ["15+ Years Experience", "OEM/ODM", "ISO Quality", "Global Export"],
      "stats": [
        {"value": "50,000+", "label": "Tons Annual Capacity"},
        {"value": "40+", "label": "Countries Served"},
        {"value": "1,000+", "label": "Customers Worldwide"},
        {"value": "100+", "label": "Product SKUs"}
      ],
      "phone": "", "email": "", "address": ""
    },
    "products": {
      "title": "产品中心",
      "description": "主营系列产品介绍",
      "seoDescription": "",
      "seoKeywords": "",
      "heroImage": "",
      "products": ["产品A", "产品B", "产品C"],
      "productItems": [
        {"name": "产品A", "summary": "规格与应用一句说明", "image": ""},
        {"name": "产品B", "summary": "规格与应用一句说明", "image": ""}
      ]
    },
    "about": {
      "title": "关于我们",
      "aboutText": "公司历史、工厂、研发与出口能力（参考 cattuong/luyang 关于页）",
      "mission": "Bring customers reliable insulation and building material solutions with verified factory quality.",
      "vision": "Become a trusted export partner for distributors and project contractors worldwide.",
      "capacitySummary": "Modern production lines, bulk warehousing, and export logistics for container shipments.",
      "milestones": [
        {"year": "2005", "title": "Established", "description": "Founded as a manufacturing and trading company"},
        {"year": "2012", "title": "Factory Expansion", "description": "Added automated lines and QC laboratory"},
        {"year": "2018", "title": "Global Export", "description": "Regular shipments to Middle East, Europe and Southeast Asia"},
        {"year": "2024", "title": "OEM/ODM Hub", "description": "Full custom branding and packaging for overseas buyers"}
      ]
    },
    "contact": {
      "title": "联系我们",
      "phone": "<租户真实电话，未知留空>",
      "email": "<租户真实邮箱，未知留空>",
      "whatsapp": "<租户真实 WhatsApp，未知留空>",
      "wechat": "<租户真实微信号，未知留空>",
      "address": "<租户真实地址，未知留空>",
      "factoryAddress": "<工厂地址，未知留空>"
    }
  }
}"""

# 对标站结构参考（Hermes 建站 prompt 用，不对客户展示 URL）
_REFERENCE_SITE_PATTERNS = (
    "ydalison.com（L-Pro 信任）：About/Since/工厂叙事、行业应用、中英文、专业配图、多线路 Contact",
    "t-global.com（L-Pro 产品中心）：多级 Products、筛选列表、SKU 规格表、Downloads、询盘对比钩子",
    "shenzhou.cc：多产品线矩阵+项目分类+新闻（本地巨头）",
    "cnabm.com：四领域解决方案+四数字 stats（樱花岩棉）",
    "rockwool.com/asia：What are you insulating? 按系统部位分应用",
    "insulation-manufacturer.com：个人站合格线，图普通清晰度即可",
    "cellularglass.cn：反模式 — 拥挤堆叠无留白，禁止对标",
)


def _default_categories(name: str, short: str) -> list[dict[str, str]]:
    """_default_categories。

    参数说明：
    :param name: 参数 name
    :param short: 参数 short
    :return: 返回处理结果。
    """
    return [
        {"name": f"{short} Board / Slab", "description": f"Rigid {name} boards for walls, roofs and facades"},
        {"name": f"{short} Blanket / Roll", "description": f"Flexible {name} rolls for pipes, ducts and equipment"},
        {"name": f"{short} Pipe / Tube", "description": f"Pre-formed {name} pipe sections for HVAC and industrial lines"},
        {"name": "OEM / Custom", "description": "Custom density, facing and packaging for export brands"},
    ]


def _default_applications(name: str) -> list[dict[str, str]]:
    """_default_applications。

    参数说明：
    :param name: 参数 name
    :return: 返回处理结果。
    """
    return [
        {
            "title": "Roof Systems",
            "description": f"{name} roof systems improve thermal performance and reduce energy loss for commercial and industrial buildings.",
        },
        {
            "title": "External Wall Systems",
            "description": f"Facade and cavity wall solutions with {name} for fire-safe, energy-efficient envelopes.",
        },
        {
            "title": "HVAC & Ductwork",
            "description": "Duct, pipe and equipment solutions to cut heat gain and noise in central HVAC systems.",
        },
        {
            "title": "Industrial Equipment",
            "description": f"High-temperature {name} for furnaces, boilers, tanks and process pipelines.",
        },
        {
            "title": "Fire Protection",
            "description": "Non-combustible layers to improve fire resistance ratings in public buildings.",
        },
        {
            "title": "Acoustic Control",
            "description": "Sound absorption and vibration control between floors, rooms and mechanical zones.",
        },
    ]


def _default_solutions(name: str) -> list[dict[str, str]]:
    """_default_solutions。

    参数说明：
    :param name: 参数 name
    :return: 返回处理结果。
    """
    return [
        {
            "segment": "Building",
            "title": "Building & Construction",
            "description": f"Integrated {name} systems for walls, roofs and facades in commercial projects.",
        },
        {
            "segment": "Industrial",
            "title": "Industrial Projects",
            "description": "Reliable thermal solutions for plants, pipelines and high-temperature equipment.",
        },
        {
            "segment": "HVAC",
            "title": "HVAC Systems",
            "description": "Duct, air-handling and chiller insulation for efficient climate control.",
        },
        {
            "segment": "Marine",
            "title": "Marine & Offshore",
            "description": "Fire-safe insulation solutions for marine compartments and offshore modules.",
        },
    ]


def _default_advantages(short: str) -> list[dict[str, str]]:
    """_default_advantages。

    参数说明：
    :param short: 参数 short
    :return: 返回处理结果。
    """
    return [
        {"title": "Quality Control", "description": f"In-house production with traceable {short} batches"},
        {"title": "Custom Manufacturing", "description": "OEM/ODM support with drawing-based sampling"},
        {"title": "Easy Installation", "description": "Standard specs to shorten on-site construction time"},
        {"title": "Global Export", "description": "Export documentation and multi-container shipping experience"},
    ]


def _default_stats(name: str) -> list[dict[str, str]]:
    """_default_stats。

    参数说明：
    :param name: 参数 name
    :return: 返回处理结果。
    """
    return [
        {"value": "20+", "label": "Years of Experience"},
        {"value": "500+", "label": "Projects Supplied"},
        {"value": "30+", "label": "Patents & Standards"},
        {"value": "40+", "label": "Export Countries"},
    ]


def _default_trust_badges() -> list[str]:
    """_default_trust_badges。
    :return: 返回处理结果。
    """
    return [
        "15+ Years Experience",
        "OEM/ODM Available",
        "Factory Direct Supply",
        "Global Export Support",
    ]


def _default_milestones(brand: str) -> list[dict[str, str]]:
    """_default_milestones。

    参数说明：
    :param brand: 参数 brand
    :return: 返回处理结果。
    """
    return [
        {"year": "2005", "title": "Established", "description": f"{brand} founded with focus on export manufacturing"},
        {"year": "2012", "title": "Capacity Upgrade", "description": "Expanded production lines and quality lab"},
        {"year": "2018", "title": "Global Markets", "description": "Regular export to Europe, Middle East and ASEAN"},
        {"year": "2024", "title": "Custom Solutions", "description": "OEM/ODM branding and project-based supply"},
    ]


def build_template_site_content(
    product_name: str,
    company_name: str = "",
    contact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """无 AI 密钥时的确定性模板，保证可用。

    :param contact: 租户真实联系方式（phone/email/whatsapp/wechat/address/factory_address）。
                    缺省即留空，**绝不填假号码/假邮箱**（此前硬编码 0086-571-8888-0000 /
                    sales@example.com，会直接出现在生成的官网上）。
    """
    contact = contact or {}
    name = (product_name or "产品").strip()
    brand = (company_name or f"{name}专业供应").strip()
    short = name[:20]
    advantages = _default_advantages(short)
    categories = _default_categories(name, short)
    applications = _default_applications(name)
    solutions = _default_solutions(name)
    default_cat = categories[0]["name"] if categories else short
    product_items = default_product_items_en(name, short, default_cat)
    return _finalize_site_content(
        {
        "templateTier": "L-Pro",
        "templateId": "premium-b2b-v1",
        "visualEditor": {"templateId": "premium-b2b-v1", "html": "", "css": ""},
        "brand": {
            "name": brand,
            "tagline": f"{short} Manufacturer in China · OEM/ODM Export",
        },
        "footer": {"text": ""},
        "theme": {
            "headerBg": "#1e3a5f",
            "heroBg": "#f8fafc",
            "footerBg": "#1e3a5f",
        },
        "pages": {
            "home": {
                "title": f"{short} Manufacturer, Supplier & Factory",
                "description": (
                    f"{brand} specializes in {name} R&D, manufacturing and export. "
                    f"Modern production facilities; products shipped to Europe, the Middle East "
                    f"and Southeast Asia; OEM/ODM and sample orders supported."
                ),
                "seoDescription": f"{brand} — {name} manufacturer and exporter from China",
                "seoKeywords": f"{short},{name},manufacturer,supplier,factory,export",
                "heroImage": "",
                "sectionTitle": "Why Choose Us",
                "features": [a["title"] for a in advantages],
                "categories": categories,
                "applications": applications,
                "applicationsTitle": "Application Scenarios",
                "solutions": solutions,
                "advantages": advantages,
                "establishedYear": "2005",
                "trustBadges": _default_trust_badges(),
                "stats": _default_stats(name),
                "phone": "",
                "email": "",
                "address": "",
            },
            "products": {
                "title": "Products",
                "description": f"Hot {name} series for distributors and EPC contractors — board, roll and pipe formats",
                "seoDescription": f"{brand} {name} product list",
                "seoKeywords": f"{short},products,catalog,wholesale",
                "heroImage": "",
                "products": [p["name"] for p in product_items],
                "productItems": product_items,
            },
            "about": {
                "title": "About Us",
                "description": "",
                "seoDescription": f"About {brand}",
                "seoKeywords": f"{brand},about,factory",
                "heroImage": "",
                "aboutText": (
                    f"{brand} is a professional manufacturer of {name} based in China. "
                    f"We integrate R&D, production, quality control and export services. "
                    f"Our factory is equipped for bulk orders and customized solutions. "
                    f"Welcome distributors and project buyers worldwide to contact us for quotation and samples."
                ),
                "mission": (
                    f"Deliver reliable {name} solutions with consistent factory quality, "
                    f"transparent communication and on-time export delivery for every partner."
                ),
                "vision": (
                    f"Build {brand} into a trusted global supplier recognized for technical support, "
                    f"sustainable manufacturing and long-term cooperation with distributors and EPC contractors."
                ),
                "capacitySummary": (
                    f"{brand} operates modern production lines with bulk warehousing and container-ready packaging. "
                    f"We support mixed-SKU orders, project quotations and third-party inspection before shipment."
                ),
                "milestones": _default_milestones(brand),
            },
            "contact": {
                "title": "Contact Us",
                "description": "Get quotation and sample support",
                "seoDescription": f"Contact {brand}",
                "seoKeywords": f"{brand},contact,whatsapp",
                "heroImage": "",
                # 联系方式一律取真实入参；未提供则留空，**不填假号码/假邮箱**
                "phone": str(contact.get("phone") or ""),
                "email": str(contact.get("email") or ""),
                "whatsapp": str(contact.get("whatsapp") or ""),
                "wechat": str(contact.get("wechat") or ""),
                "address": str(contact.get("address") or ""),
                "factoryAddress": str(contact.get("factory_address") or ""),
            },
            "downloads": {
                "title": "Download Center",
                "description": "Brochures, datasheets and certificates",
                "items": [
                    {"title": f"{brand} Company Profile", "url": "", "type": "brochure"},
                    {"title": "Product Catalog PDF", "url": "", "type": "catalog"},
                ],
            },
        },
    },
        product_name=name,
        company_name=brand,
    )


def _finalize_site_content(
    content: dict[str, Any],
    *,
    product_name: str,
    company_name: str,
) -> dict[str, Any]:
    """_finalize_site_content。

    参数说明：
    :param content: 参数 content
    :param product_name: 参数 product_name
    :param company_name: 参数 company_name
    :return: 返回处理结果。
    """
    from app.services.site_content_i18n_service import ensure_site_content_i18n
    finalized, _ = ensure_site_content_i18n(
        content,
        product_name=product_name,
        company_name=company_name,
    )
    return finalized


def _extract_json_object(text: str) -> dict[str, Any] | None:
    """_extract_json_object。

    参数说明：
    :param text: 参数 text
    :return: 返回处理结果。
    """
    raw = (text or "").strip()
    if not raw:
        return None
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.IGNORECASE)
    if fence:
        raw = fence.group(1).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _merge_with_template(ai_data: dict[str, Any], product_name: str, company_name: str) -> dict[str, Any]:
    """AI 输出缺字段时用模板补齐。"""
    base = build_template_site_content(product_name, company_name)
    for key in ("brand", "footer", "theme"):
        if isinstance(ai_data.get(key), dict):
            base[key] = {**base.get(key, {}), **ai_data[key]}
    pages = ai_data.get("pages")
    if isinstance(pages, dict):
        for page_key, page_val in pages.items():
            if page_key in base["pages"] and isinstance(page_val, dict):
                base["pages"][page_key] = {**base["pages"][page_key], **page_val}
    return _finalize_site_content(base, product_name=product_name, company_name=company_name)


def _build_llm_prompt(
    product_name: str,
    company_name: str,
    design_manifest: dict[str, Any] | None = None,
    *,
    product_image_count: int = 0,
) -> str:
    """_build_llm_prompt。

    参数说明：
    :param product_name: 参数 product_name
    :param company_name: 参数 company_name
    :param design_manifest: 参数 design_manifest
    :param product_image_count: 参数 product_image_count
    :return: 返回处理结果。
    """
    ctx = f"产品名称：{product_name}"
    if company_name:
        ctx += f"\n公司名称参考：{company_name}"
    if product_image_count > 0:
        ctx += (
            f"\n客户已上传 {product_image_count} 张产品照片（白底产品图），"
            f"请生成恰好 {product_image_count} 个 productItems，名称与规格说明对应真实品类；"
            "所有 image/heroImage 字段留空，由系统挂接客户照片"
        )
    else:
        ctx += (
            "\n客户不会自行制作网站图片，只会提供产品名称；"
            "heroImage 与各 productItems.image 一律留空字符串，站点可无图正常运行"
        )

    skill_block = ""
    ecc_brief = (design_manifest or {}).get("_ecc_expert_brief")
    if ecc_brief:
        skill_block = f"\n{ecc_brief}\n"
    elif design_manifest:
        lines = []
        refs = design_manifest.get("reference_site_patterns") or _REFERENCE_SITE_PATTERNS
        lines.append("【对标 B2B 外贸站结构】")
        for r in refs:
            lines.append(f"  · {r}")
        for skill in design_manifest.get("design_skills") or []:
            if not isinstance(skill, dict):
                continue
            title = skill.get("title") or skill.get("id")
            rules = skill.get("rules") or []
            lines.append(f"- {title}:")
            for r in rules:
                lines.append(f"  · {r}")
        if lines:
            skill_block = "\n【设计技能约束 — 必须遵守】\n" + "\n".join(lines) + "\n"

    theme = (design_manifest or {}).get("default_theme") or {}
    theme_hint = ""
    if theme:
        theme_hint = (
            f"theme 颜色必须使用：headerBg={theme.get('headerBg')}, "
            f"heroBg={theme.get('heroBg')}, footerBg={theme.get('footerBg')}\n"
        )

    return (
        "你是 B2B 外贸官网文案与结构专家（Hermes 建站 Agent）。根据以下产品名，生成一套中文企业官网内容。\n"
        f"{ctx}\n"
        f"{skill_block}"
        "要求：\n"
        "1. 只输出一个 JSON 对象，不要 markdown 说明\n"
        "2. 语气专业、面向海外采购商，避免夸张空话\n"
        "3. 不要填写任何图片 URL；heroImage 与 productItems.image 留空\n"
        "4. JSON 结构必须与示例完全一致（含 solutions/applicationsTitle/categories/applications/stats/productItems/mission/vision/milestones）\n"
        f"5. 示例结构：\n{_SITE_JSON_EXAMPLE}\n"
        f"{theme_hint}"
        "6. 客户只需说明卖什么产品：专业文案与分类由你生成，产品图由客户上传后系统自动挂接\n"
    )


async def generate_site_content(
    db: Session | None,
    *,
    product_name: str,
    company_name: str = "",
    tenant_id: str | None = None,
    use_ai: bool = True,
    design_manifest: dict[str, Any] | None = None,
    product_images: list[Any] | None = None,
    skip_i18n_ai: bool = False,
) -> dict[str, Any]:
    """
    返回 { site_content, source }，source 为 ai 或 template。
    AI 失败时自动降级模板。
    """
    name = (product_name or "").strip()
    if not name:
        raise ValueError("请填写产品名称")

    from app.services.site_product_assets import apply_customer_product_images
    image_count = len(product_images or [])
    if use_ai and db is not None:
        try:
            result = await invoke_llm(
                db,
                prompt=_build_llm_prompt(
                    name, company_name, design_manifest, product_image_count=image_count,
                ),
                scenario="article",
                max_tokens=2500,
                task_type="hermes_site_builder",
                tenant_id=tenant_id,
                lane="customer",
            )
            content = str(result.get("content") or "")
            parsed = _extract_json_object(content)
            if parsed:
                merged = _merge_with_template(parsed, name, company_name)
                merged = apply_customer_product_images(merged, product_images)
                from app.services.site_content_i18n_ai_service import enrich_site_content_i18n
                merged, i18n_stats = await enrich_site_content_i18n(
                    db,
                    merged,
                    tenant_id=tenant_id,
                    use_ai=not skip_i18n_ai,
                    overwrite_ai=True,
                    product_name=name,
                    company_name=company_name,
                )
                return {
                    "site_content": merged,
                    "source": "ai",
                    "i18n": i18n_stats,
                }
            logger.warning("site AI JSON parse failed, fallback template")
        except Exception as exc:
            logger.warning("site AI generate failed: %s", exc)

    template = build_template_site_content(name, company_name)
    return {
        "site_content": apply_customer_product_images(template, product_images),
        "source": "template",
    }
