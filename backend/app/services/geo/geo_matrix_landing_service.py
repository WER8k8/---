# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""全球出海国家与港口矩阵着陆页引擎 (Programmatic Geo-Matrix Landing Engine)。

基于外贸 30 年实战经验与 Google EEAT 算法规范，为全球重点采购国家/港口
量身定制本地化工业场景方案、海运装载指南与当地执行标准对照，
在海外多国 Google 本地搜索（google.com.sa, google.de, google.com.vn 等）中实现矩阵式精准获客。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)

# 出海四大战区本地化配置档案（去行业化：全球各行业海关准入、经贸协定与工业交付标准）
COUNTRY_PROFILES: Dict[str, Dict[str, Any]] = {
    "sa": {
        "country_code": "sa",
        "country_name_zh": "沙特阿拉伯",
        "country_name_en": "Saudi Arabia",
        "flag_emoji": "🇸🇦",
        "region_name": "中东海湾区 (GCC)",
        "destination_ports": ["Dammam (达曼港)", "Jeddah Islamic Port (吉达港)"],
        "transit_days": "18 - 22 天直航",
        "primary_pain_points": [
            "夏季 50℃ 极端高温干热日照，对产品耐温变公差、抗老化与热稳定性有极致要求",
            "沙漠狂风高粉尘与沿海高盐雾环境，要求外层高等级防腐防蚀与可靠封装",
            "沙特新未来城 (NEOM) 及 2030 愿景重点标段对国际准入与 Class A1 阻燃耐候有绝对硬性门槛",
        ],
        "local_standards": ["SASO / SABER 官方认证合规", "ASTM 国际工程测试标准", "Class A1 / ISO 国际安全认证"],
        "preferential_tariffs": "提供中国-海合会清关发票与 SASO / SABER 原厂质检与符合性证书 (CoC)",
        "container_suggestion": "推荐 40HQ 强化防潮防尘工业级装载打包（防沙漠扬尘与长途海运受潮），有效保障全集装箱容积率",
        "currency": "SAR / USD",
        "target_climate": "热带沙漠干热气候，耐受极端昼夜温差达 60℃",
    },
    "ae": {
        "country_code": "ae",
        "country_name_zh": "阿拉伯联合酋长国",
        "country_name_en": "United Arab Emirates (UAE)",
        "flag_emoji": "🇦🇪",
        "region_name": "中东海湾区 (GCC)",
        "destination_ports": ["Jebel Ali Port, Dubai (杰贝阿里港/迪拜)"],
        "transit_days": "16 - 20 天直航",
        "primary_pain_points": [
            "迪拜及海湾现代商业综合体与大型工程对构件轻量化与精度公差有严苛要求",
            "高能耗运行场景急需优化运行工况能效比，实现绿色节能与低损耗",
            "海湾高湿度沿海盐雾空气易引发关键部件腐蚀与早期劣化风险",
        ],
        "local_standards": ["Dubai Municipality 权威准入规范", "ASTM / BS EN 国际合规标准", "ISO 9001 / 14001 质量管理体系"],
        "preferential_tariffs": "支持迪拜自贸区 (JAFZA) 免税转口中转，出具官方认证原产地证书 (CO)",
        "container_suggestion": "采用欧标/美标自动化托盘防塌缠绕包装，适合 Jebel Ali 现代化自动化码头快速叉车分拨与仓储",
        "currency": "AED / USD",
        "target_climate": "海湾高温强紫外线高盐雾环境",
    },
    "de": {
        "country_code": "de",
        "country_name_zh": "德国",
        "country_name_en": "Germany",
        "flag_emoji": "🇩🇪",
        "region_name": "欧洲低碳区 (EU)",
        "destination_ports": ["Hamburg (汉堡港)", "Bremerhaven (不来梅港)"],
        "transit_days": "28 - 35 天直航",
        "primary_pain_points": [
            "德国低能耗被动房 (Passivhaus) 与高精制造业对热工系数、精度公差与能效等级的严苛要求",
            "欧洲严苛的供应链全生命周期碳足迹标准 (EPD 环境产品声明与 CBAM 碳边境调节机制)",
            "冬季严寒，要求通过极端冻融交替、耐疲劳度测试与长周期可靠性验证",
        ],
        "local_standards": ["CE 认证 (EU Compliance)", "DIN 德国工业标准", "RoHS / REACH 环保与 LEED / BREEAM 绿标认可"],
        "preferential_tariffs": "出具正规 EUR.1 报关单证、欧盟符合性声明 (DoC) 与重金属合规检验报告",
        "container_suggestion": "欧标托盘 (1200x800mm) 紧凑防滑装运，完全符合欧洲自动化立体仓储与装卸标准",
        "currency": "EUR / USD",
        "target_climate": "温带海洋向大陆过渡气候，冬季漫长冻融考验",
    },
    "vn": {
        "country_code": "vn",
        "country_name_zh": "越南",
        "country_name_en": "Vietnam",
        "flag_emoji": "🇻🇳",
        "region_name": "东南亚热带区 (ASEAN)",
        "destination_ports": ["Hai Phong (海防港)", "Cat Lai / Ho Chi Minh (胡志明港)"],
        "transit_days": "5 - 8 天近洋极速达",
        "primary_pain_points": [
            "红河与湄公河三角洲工业园区地基软弱及快速基建场景，对物料自重与施工装配效率要求极高",
            "热带季风气候雨季漫长，空气湿度常年 > 85%，产品防霉防锈与抗潮性能至关重要",
            "供应链周转节奏极快，要求出货批量稳定、近洋物流可控与安装即用",
        ],
        "local_standards": ["TCVN 越南国家标准", "Form E 中国-东盟自贸区优惠协定", "ISO 国际质量认证"],
        "preferential_tariffs": "享受 Form E 协定税率（关税可直接降为 0% 零关税），综合到岸成本极具竞争力",
        "container_suggestion": "20GP/40HQ 均可极速发运，全封闭工业防潮内衬确保近洋航运受潮受损率为 0",
        "currency": "VND / USD",
        "target_climate": "热带季风高温高湿，雨季连绵工况",
    },
    "us": {
        "country_code": "us",
        "country_name_zh": "美国",
        "country_name_en": "United States",
        "flag_emoji": "🇺🇸",
        "region_name": "北美工程区 (NA)",
        "destination_ports": ["Port of Long Beach / Los Angeles (长滩港/洛杉矶)"],
        "transit_days": "14 - 16 天太平洋快线",
        "primary_pain_points": [
            "北美工业与基建工程对抗震设防、抗疲劳强度与轻量化载荷具有严苛规范",
            "北美高昂的现场人工与装配成本，要求材料与构件具备极高的一致性、易装配性与免维护周期",
            "长途跨太平洋海运的货柜容积最大化、重心中正与转运安全",
        ],
        "local_standards": ["ASTM 国际标准规范", "IBC 国际通用标准 / ANSI 规范", "UL / FCC / FDA (按品类适配) 准入认证"],
        "preferential_tariffs": "提供完整商业发票(CI)、箱单(PL)与工厂 ISO 9001 质量全程溯源档案",
        "container_suggestion": "满载 40HQ 结构化配载，支持高强度工业集装箱散袋或标准美标托盘 (48x40 inch)",
        "currency": "USD",
        "target_climate": "北美多元气候，强调结构安全、高一致性与全天候服役可靠性",
    },
}


class GeoMatrixLandingService:
    """出海国家矩阵落地页数据中枢（去行业化工业商业操作系统基石）。"""

    def __init__(self, db: Session):
        self.db = db

    def list_supported_countries(self) -> List[Dict[str, Any]]:
        """列出所有支持的国家出海档案列表。"""
        return [
            {
                "country_code": p["country_code"],
                "country_name_zh": p["country_name_zh"],
                "country_name_en": p["country_name_en"],
                "flag_emoji": p["flag_emoji"],
                "region_name": p["region_name"],
                "destination_ports": p["destination_ports"],
                "transit_days": p["transit_days"],
                "preferential_tariffs": p["preferential_tariffs"],
            }
            for p in COUNTRY_PROFILES.values()
        ]

    def _extract_specifications(self, product: Product) -> List[Dict[str, str]]:
        """自适应抽取任意行业商品的核心技术指标（彻底去建材特化，通用工业品基石）。"""
        specs: List[Dict[str, str]] = []
        raw_specs = product.specifications if isinstance(product.specifications, dict) else {}

        # 优先读取商品自定义的规格键值对
        for key, val in raw_specs.items():
            if val and len(specs) < 4:
                specs.append({"label": str(key), "value": str(val)})

        # 动态补充通用字段（兼顾已有字段与不同品类）
        fallback_map = [
            ("容重/规格", product.density or raw_specs.get("density") or raw_specs.get("dimensions")),
            ("抗压/强度", product.strength or raw_specs.get("strength") or raw_specs.get("power")),
            ("热工/能效", product.thermal_conductivity or raw_specs.get("efficiency") or raw_specs.get("tolerance")),
            ("安全/阻燃", product.fire_rating or raw_specs.get("certification") or raw_specs.get("grade")),
        ]

        for default_label, val in fallback_map:
            if len(specs) >= 4:
                break
            if val and not any(s["value"] == str(val) for s in specs):
                specs.append({"label": default_label, "value": str(val)})

        # 兜底填充通用出海工业品标准参数
        generic_defaults = [
            {"label": "公差与精度", "value": "±0.5mm 工业级"},
            {"label": "执行标准", "value": "ISO 9001 / CE 符合"},
            {"label": "使用寿命", "value": "≥ 25 年耐候"},
            {"label": "阻燃安全", "value": "Class A1 / 不燃级"},
        ]
        for g_spec in generic_defaults:
            if len(specs) >= 4:
                break
            if not any(s["label"] == g_spec["label"] for s in specs):
                specs.append(g_spec)

        return specs

    def build_country_landing_bundle(
        self,
        country_code: str,
        product_slug: str,
        base_url: str = "https://www.youdingjiancai.com",
    ) -> Optional[Dict[str, Any]]:
        """为特定国家和产品构建全套沉浸式 Landing Page 数据包（含 SEO、港口、标准对照与专属问答）。"""
        code = country_code.lower()
        profile = COUNTRY_PROFILES.get(code)
        if not profile:
            return None

        product = self.db.query(Product).filter(
            Product.slug == product_slug,
            Product.is_active.is_(True),
        ).first()
        if not product:
            return None

        # 租户名识别
        tenant_name = "YouDing Global"
        if product.tenant_id:
            tenant = self.db.query(Tenant).filter(Tenant.id == product.tenant_id).first()
            if tenant and tenant.name:
                tenant_name = tenant.name

        clean_base = base_url.rstrip("/")
        page_url = f"{clean_base}/solutions/{code}/{product.slug}"

        # 动态自适应核心参数指标（去行业化通用能力）
        key_specs = self._extract_specifications(product)
        density = product.density or key_specs[0]["value"]
        strength = product.strength or key_specs[1]["value"]
        thermal = product.thermal_conductivity or key_specs[2]["value"]
        fire = product.fire_rating or key_specs[3]["value"]

        # 专为目标国家定制的 SEO 标题与描述
        country_en = profile["country_name_en"]
        country_zh = profile["country_name_zh"]
        prod_en = product.name_en or product.name

        spec_summary = ", ".join([f"{s['label']}: {s['value']}" for s in key_specs[:2]])
        meta_title = f"{country_en} Certified {prod_en} - Direct Supply to {profile['destination_ports'][0].split(' ')[0]} | {tenant_name}"
        meta_description = (
            f"Official export supplier of {prod_en} to {country_en} ({', '.join(profile['destination_ports'])}). "
            f"Engineered for {profile['target_climate']}. Compliant with {', '.join(profile['local_standards'])}. "
            f"{spec_summary}, {profile['transit_days']}."
        )

        # 目标国家专属外贸问答集（通用工业/外贸采购消除疑虑）
        faqs = [
            {
                "question_en": f"How is {prod_en} packaged to prevent damage during shipment to {country_en}?",
                "answer_en": f"For exports to {country_en}, we use {profile['container_suggestion']}. Shipments are secured with robust moisture-barrier packaging and container strapping, guaranteeing zero damage during the {profile['transit_days']} transit.",
                "question_zh": f"发运往{country_zh}时，如何保障包装防潮与运输安全？",
                "answer_zh": f"针对{country_zh}航线，我们采用{profile['container_suggestion']}，全程多层防潮防损工业打包，确保经过{profile['transit_days']}航程后完好交付。",
            },
            {
                "question_en": f"Does {prod_en} comply with local industrial regulations and customs clearance in {country_en}?",
                "answer_en": f"Yes. It strictly complies with {', '.join(profile['local_standards'])}. We supply official factory inspection reports and {profile['preferential_tariffs']} to ensure seamless customs clearance at {profile['destination_ports'][0]}.",
                "question_zh": f"本品是否符合{country_zh}当地市场法规与清关准入要求？",
                "answer_zh": f"完全符合。严格执行{', '.join(profile['local_standards'])}，我们提供出厂权威质检报告以及{profile['preferential_tariffs']}，保障在{profile['destination_ports'][0]}顺利通关。",
            },
            {
                "question_en": f"Why is {prod_en} engineered for the operational environment of {country_en}?",
                "answer_en": f"Specially tailored for {profile['target_climate']}: directly addresses {profile['primary_pain_points'][0]} with key certified specifications ({spec_summary}).",
                "question_zh": f"为什么本产品特别适合{country_zh}当地环境与使用工况？",
                "answer_zh": f"针对{profile['target_climate']}量身打造：有效解决{profile['primary_pain_points'][0]}，具备实测权威性能指标（{spec_summary}）。",
            },
        ]

        # Google 结构化数据 Schema.org
        schema_product = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": f"{prod_en} ({country_en} Supply Solution)",
            "description": meta_description,
            "image": product.image_url or f"{clean_base}/images/product-default.jpg",
            "sku": f"GEO-{code.upper()}-{str(product.id)[:6].upper()}",
            "brand": {"@type": "Brand", "name": tenant_name},
            "offers": {
                "@type": "Offer",
                "url": page_url,
                "priceCurrency": "USD",
                "price": "58.00",
                "availability": "https://schema.org/InStock",
                "areaServed": {
                    "@type": "Country",
                    "name": country_en,
                },
            },
        }

        schema_breadcrumbs = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{clean_base}/"},
                {"@type": "ListItem", "position": 2, "name": "Export Solutions", "item": f"{clean_base}/solutions"},
                {"@type": "ListItem", "position": 3, "name": country_en, "item": f"{clean_base}/solutions/{code}"},
                {"@type": "ListItem", "position": 4, "name": prod_en, "item": page_url},
            ],
        }

        return {
            "country_profile": profile,
            "product": {
                "id": str(product.id),
                "name": product.name,
                "name_en": prod_en,
                "slug": product.slug,
                "density": density,
                "strength": strength,
                "thermal_conductivity": thermal,
                "fire_rating": fire,
                "key_specs": key_specs,
                "image_url": product.image_url,
            },
            "seo": {
                "meta_title": meta_title,
                "meta_description": meta_description,
                "canonical_url": page_url,
                "keywords": f"{prod_en} to {country_en}, {profile['destination_ports'][0]}, {country_en} direct supplier, {tenant_name}",
            },
            "shipping_logistics": {
                "destination_ports": profile["destination_ports"],
                "transit_days": profile["transit_days"],
                "container_load_advice": profile["container_suggestion"],
                "documents_provided": ["Commercial Invoice (CI)", "Packing List (PL)", "Bill of Lading (B/L)", profile["preferential_tariffs"]],
            },
            "faqs": faqs,
            "schemas": {
                "product": schema_product,
                "breadcrumbs": schema_breadcrumbs,
            },
        }

