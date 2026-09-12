"""租户入驻引导服务 — 3步入驻 + 示例数据 + 成就系统"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger("uj-admin.onboarding")

# ── 入驻步骤定义 ──
ONBOARDING_STEPS = [
    {
        "id": "company_setup",
        "title": "基础配置",
        "subtitle": "设置公司信息",
        "tasks": [
            {"id": "company_name", "title": "公司名称", "auto": True},
            {"id": "upload_logo", "title": "上传品牌 Logo"},
            {"id": "set_industry", "title": "选择行业"},
            {"id": "set_contact", "title": "填写联系方式"},
        ],
    },
    {
        "id": "product_launch",
        "title": "产品上线",
        "subtitle": "添加您的第一个产品",
        "tasks": [
            {"id": "add_product", "title": "添加产品"},
            {"id": "add_faq", "title": "添加 FAQ"},
            {"id": "add_images", "title": "上传产品图片"},
            {"id": "preview_page", "title": "预览产品页"},
        ],
    },
    {
        "id": "acquisition_start",
        "title": "获客启动",
        "subtitle": "开启自动获客引擎",
        "tasks": [
            {"id": "enable_seo", "title": "开启 SEO 矩阵"},
            {"id": "config_geo", "title": "配置 GEO 引擎"},
            {"id": "publish_article", "title": "发布第一篇文章"},
            {"id": "setup_inquiry", "title": "配置询盘表单"},
        ],
    },
]

# ── 成就定义 ──
ACHIEVEMENTS = [
    {"id": "first_step", "title": "第一步", "desc": "完成公司基础配置", "icon": "🎯", "condition": "company_setup_done"},
    {"id": "product_ready", "title": "产品就绪", "desc": "发布第一个产品", "icon": "📦", "condition": "product_published"},
    {"id": "faq_master", "title": "FAQ 达人", "desc": "添加 5 条以上 FAQ", "icon": "❓", "condition": "faq_count_5"},
    {"id": "seo_launch", "title": "SEO 启航", "desc": "发布第一篇 SEO 文章", "icon": "🚀", "condition": "article_published"},
    {"id": "geo_pioneer", "title": "GEO 先锋", "desc": "完成首次 GEO 探测", "icon": "🌍", "condition": "geo_probed"},
    {"id": "first_inquiry", "title": "首条询盘", "desc": "收到第一条询盘", "icon": "💬", "condition": "inquiry_received"},
    {"id": "full_loop", "title": "全链路打通", "desc": "完成全部入驻流程", "icon": "🏆", "condition": "onboarding_complete"},
]


def get_onboarding_status(db: Session, tenant_id: str) -> dict[str, Any]:
    """获取入驻进度"""
    from app.models.tenant import Tenant
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        return {"progress": 0, "steps": [], "achievements": []}

    # 从 tenant settings 读取进度
    settings = getattr(tenant, "settings", None) or {}
    if isinstance(settings, str):
        import json
        try:
            settings = json.loads(settings)
        except (json.JSONDecodeError, TypeError):
            settings = {}
    onboarding = settings.get("onboarding", {})
    completed_tasks = set(onboarding.get("completed_tasks", []))
    # 构建步骤状态
    steps = []
    total_tasks = 0
    done_tasks = 0
    for step in ONBOARDING_STEPS:
        task_statuses = []
        for task in step["tasks"]:
            is_done = task["id"] in completed_tasks or task.get("auto", False)
            task_statuses.append({**task, "done": is_done})
            total_tasks += 1
            if is_done:
                done_tasks += 1
        steps.append({
            **step,
            "tasks": task_statuses,
            "done": all(t["done"] for t in task_statuses),
        })

    progress = round(done_tasks / max(total_tasks, 1) * 100)
    # 检查成就
    earned = _check_achievements(db, tenant_id, completed_tasks, onboarding)
    return {
        "progress": progress,
        "steps": steps,
        "achievements": earned,
        "is_complete": progress == 100,
    }


def complete_step(db: Session, tenant_id: str, task_id: str) -> dict[str, Any]:
    """完成一个入驻任务"""
    from app.models.tenant import Tenant
    import json
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        return {"error": "tenant not found"}

    settings = getattr(tenant, "settings", None) or {}
    if isinstance(settings, str):
        try:
            settings = json.loads(settings)
        except (json.JSONDecodeError, TypeError):
            settings = {}

    onboarding = settings.get("onboarding", {})
    completed = set(onboarding.get("completed_tasks", []))
    completed.add(task_id)
    onboarding["completed_tasks"] = list(completed)
    onboarding["last_updated"] = datetime.now(timezone.utc).isoformat()
    settings["onboarding"] = onboarding
    tenant.settings = json.dumps(settings) if isinstance(getattr(tenant, "settings", None), str) else settings
    db.commit()
    return {"completed_task": task_id, "total_completed": len(completed)}


def generate_sample_data(db: Session, tenant_id: str) -> dict[str, Any]:
    """生成示例数据"""
    from app.models.product import Product, ProductFaq
    created = {"products": 0, "faqs": 0}
    sample_products = [
        {
            "name": "LC30 轻集料混凝土",
            "name_en": "LC30 Lightweight Aggregate Concrete",
            "subtitle": "高强度、轻质、保温隔热",
            "subtitle_en": "High strength, lightweight, thermal insulation",
            "description": "LC30轻集料混凝土，采用优质陶粒为骨料，抗压强度≥30MPa，密度1400-1800kg/m³。广泛应用于高层建筑楼面、屋面保温找坡层、桥梁减重工程。",
            "description_en": "LC30 lightweight aggregate concrete using high-quality ceramsite as aggregate. Compressive strength ≥30MPa, density 1400-1800kg/m³. Widely used in high-rise building floors, roof insulation, bridge weight reduction.",
            "technical_params": "密度: 1400-1800 kg/m³\n抗压强度: ≥30 MPa\n导热系数: 0.4-0.8 W/(m·K)\n防火等级: A级不燃\n收缩率: ≤0.05%",
            "technical_params_en": "Density: 1400-1800 kg/m³\nCompressive Strength: ≥30 MPa\nThermal Conductivity: 0.4-0.8 W/(m·K)\nFire Rating: Class A non-combustible\nShrinkage: ≤0.05%",
            "density": "1400-1800 kg/m³",
            "strength": "≥30 MPa",
            "thermal_conductivity": "0.4-0.8 W/(m·K)",
            "fire_rating": "A级",
            "is_active": True,
        },
        {
            "name": "岩棉保温板",
            "name_en": "Rock Wool Insulation Board",
            "subtitle": "A级防火、隔音降噪、保温隔热",
            "subtitle_en": "Class A fireproof, sound insulation, thermal insulation",
            "description": "岩棉保温板以天然玄武岩为主要原料，经高温熔融制成。导热系数0.035-0.045W/(m·K)，防火等级A级不燃。适用于外墙保温、幕墙填充、工业管道保温。",
            "description_en": "Rock wool insulation board made from natural basalt. Thermal conductivity 0.035-0.045 W/(m·K), Class A fireproof. Suitable for exterior wall insulation, curtain wall filling, industrial pipeline insulation.",
            "technical_params": "密度: 60-200 kg/m³\n导热系数: 0.035-0.045 W/(m·K)\n防火等级: A级不燃\n吸水率: ≤5%\n熔点: >1000℃",
            "technical_params_en": "Density: 60-200 kg/m³\nThermal Conductivity: 0.035-0.045 W/(m·K)\nFire Rating: Class A non-combustible\nWater Absorption: ≤5%\nMelting Point: >1000°C",
            "density": "60-200 kg/m³",
            "strength": "≥40 kPa",
            "thermal_conductivity": "0.035-0.045 W/(m·K)",
            "fire_rating": "A级",
            "is_active": True,
        },
        {
            "name": "JS-II 聚合物水泥防水涂料",
            "name_en": "JS-II Polymer Cement Waterproof Coating",
            "subtitle": "双组份、高弹性、耐候性强",
            "subtitle_en": "Two-component, high elasticity, strong weather resistance",
            "description": "JS-II型聚合物水泥防水涂料，由有机聚合物液料和无机粉料双组份组成。拉伸强度≥1.8MPa，断裂延伸率≥200%。适用于屋面、卫生间、地下室防水工程。",
            "description_en": "JS-II polymer cement waterproof coating, two-component system. Tensile strength ≥1.8MPa, elongation at break ≥200%. Suitable for roofing, bathroom, basement waterproofing.",
            "technical_params": "拉伸强度: ≥1.8 MPa\n断裂延伸率: ≥200%\n不透水性: 0.3MPa/30min\n耐热度: 80℃\n低温柔性: -10℃",
            "technical_params_en": "Tensile Strength: ≥1.8 MPa\nElongation at Break: ≥200%\nImpermeability: 0.3MPa/30min\nHeat Resistance: 80°C\nLow Temp Flexibility: -10°C",
            "density": "液料1.3 kg/L",
            "strength": "≥1.8 MPa",
            "thermal_conductivity": "N/A",
            "fire_rating": "N/A",
            "is_active": True,
        },
    ]
    sample_faqs = {
        "LC30": [
            ("LC30轻集料混凝土的最小起订量是多少？", "最小起订量50立方米，大城县工厂直发，支持CIF天津港交货。", "What is the MOQ for LC30 lightweight concrete?", "MOQ is 50 CBM, shipped directly from Dacheng factory, CIF Tianjin Port available."),
            ("LC30和普通C30混凝土有什么区别？", "LC30密度1400-1800kg/m³，比普通C30轻30-50%，同时保温性能更好，导热系数0.4-0.8W/(m·K)。", "What is the difference between LC30 and normal C30?", "LC30 density is 1400-1800 kg/m³, 30-50% lighter than normal C30, with better thermal insulation (0.4-0.8 W/(m·K))."),
            ("LC30的货期是多少天？", "常规规格7-15天，定制配方20-30天。具体取决于数量和配方要求。", "What is the lead time for LC30?", "Standard specs: 7-15 days. Custom formulas: 20-30 days. Depends on quantity and requirements."),
            ("能提供第三方检测报告吗？", "可以，我们提供GB/T 50081标准的第三方检测报告，包含抗压强度、密度、导热系数等完整数据。", "Can you provide third-party test reports?", "Yes, we provide GB/T 50081 standard third-party test reports with complete data on compressive strength, density, and thermal conductivity."),
            ("LC30适用于哪些工程？", "适用于高层建筑楼面减重、屋面保温找坡层、桥梁工程、装配式建筑等。已完成200+项目。", "What projects is LC30 suitable for?", "Suitable for high-rise building floors, roof insulation, bridge projects, prefabricated buildings. 200+ projects completed."),
        ],
    }
    # 创建产品
    for p_data in sample_products:
        slug = p_data["name_en"].lower().replace(" ", "-")[:200]
        existing = db.query(Product).filter(Product.slug == slug).first()
        if existing:
            continue
        product = Product(
            tenant_id=tenant_id,
            slug=slug,
            **p_data,
        )
        db.add(product)
        db.flush()
        created["products"] += 1
        # 创建 FAQ
        faq_key = None
        for key in sample_faqs:
            if key in p_data["name"]:
                faq_key = key
                break
        if faq_key:
            for i, (q_zh, a_zh, q_en, a_en) in enumerate(sample_faqs[faq_key]):
                faq = ProductFaq(
                    product_id=product.id,
                    question_zh=q_zh, answer_zh=a_zh,
                    question_en=q_en, answer_en=a_en,
                    sort_order=i,
                )
                db.add(faq)
                created["faqs"] += 1

    db.commit()
    return created


def _check_achievements(db: Session, tenant_id: str, completed_tasks: set, onboarding: dict) -> list[dict]:
    """检查已获得的成就"""
    earned = []
    for ach in ACHIEVEMENTS:
        cond = ach["condition"]
        is_earned = False
        if cond == "company_setup_done":
            is_earned = all(t in completed_tasks for t in ["upload_logo", "set_industry", "set_contact"])
        elif cond == "product_published":
            is_earned = "add_product" in completed_tasks
        elif cond == "faq_count_5":
            from app.models.product import ProductFaq, Product
            count = db.query(ProductFaq).join(Product).filter(Product.tenant_id == tenant_id).count()
            is_earned = count >= 5
        elif cond == "article_published":
            is_earned = "publish_article" in completed_tasks
        elif cond == "geo_probed":
            is_earned = "config_geo" in completed_tasks
        elif cond == "inquiry_received":
            from app.models.inquiry import Inquiry
            count = db.query(Inquiry).filter(Inquiry.tenant_id == tenant_id).count()
            is_earned = count > 0
        elif cond == "onboarding_complete":
            is_earned = len(completed_tasks) >= 12

        earned.append({**ach, "earned": is_earned})

    return earned
