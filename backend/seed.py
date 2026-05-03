import uuid
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timezone
from app.core.database import SessionLocal, engine, Base
from app.core.config import settings
from app.models import Category, Product, User, Keyword, Inquiry, ContentPage


def seed():
    db = SessionLocal()
    try:
        existing = db.query(Category).count()
        if existing > 0:
            print(f"已有 {existing} 条分类数据，跳过.")
            return

        now = datetime.now(timezone.utc)
        cid = lambda: str(uuid.uuid4())

        cat_eps = cid()
        cat_board = cid()
        cat_mortar = cid()
        cat_block = cid()
        cat_insulation = cid()

        categories = [
            Category(id=cat_eps, name="EPS聚苯板", slug="eps-board", description="EPS聚苯板系列产品，轻质高强保温", sort_order=1, created_at=now, updated_at=now),
            Category(id=cat_board, name="保温装饰一体板", slug="insulation-board", description="保温装饰一体板，集保温与装饰于一体", sort_order=2, created_at=now, updated_at=now),
            Category(id=cat_mortar, name="保温砂浆", slug="insulation-mortar", description="保温砂浆系列，施工便捷", sort_order=3, created_at=now, updated_at=now),
            Category(id=cat_block, name="加气混凝土砌块", slug="aac-block", description="蒸压加气混凝土砌块", sort_order=4, created_at=now, updated_at=now),
            Category(id=cat_insulation, name="岩棉制品", slug="rock-wool", description="岩棉保温系列产品", sort_order=5, created_at=now, updated_at=now),
        ]
        db.add_all(categories)
        db.flush()

        products_data = [
            # EPS聚苯板
            {"id": cid(), "category_id": cat_eps, "name": "优丁EPS聚苯板", "slug": "youding-eps-board", "subtitle": "高效保温·节能环保", "description": "优丁EPS聚苯板采用先进工艺生产，具有优异的保温隔热性能，适用于建筑外墙保温系统。", "technical_params": "导热系数: ≤0.039W/(m·K)\n表观密度: 18-30kg/m³\n燃烧性能: B1级\n尺寸稳定性: ≤0.3%", "application_scenarios": "建筑外墙外保温系统\n屋面保温\n地暖保温\n冷库保温", "advantages": "保温性能优异\n施工便捷\n成本经济\n环保可回收", "specifications": "1200×600×20-100mm", "density": "20kg/m³", "strength": "≥0.10MPa", "thermal_conductivity": "0.039W/(m·K)", "unit_weight": "12-18kg/块", "sort_order": 1, "view_count": 0, "created_at": now, "updated_at": now},
            {"id": cid(), "category_id": cat_eps, "name": "优丁EPS石墨聚苯板", "slug": "youding-graphite-eps", "subtitle": "石墨增强·超低导热", "description": "添加石墨颗粒的增强型EPS聚苯板，导热系数更低，保温效果更佳。", "advantages": "超低导热系数\n高强度\n防火性能优越\n尺寸稳定", "technical_params": "导热系数: ≤0.032W/(m·K)\n表观密度: 20-30kg/m³\n燃烧性能: B1级\n石墨含量: ≥5%", "specifications": "1200×600×20-100mm", "density": "22kg/m³", "strength": "≥0.12MPa", "thermal_conductivity": "0.032W/(m·K)", "unit_weight": "12-18kg/块", "sort_order": 2, "created_at": now, "updated_at": now, "application_scenarios": "建筑外墙外保温\n被动式超低能耗建筑", "view_count": 0},
            {"id": cid(), "category_id": cat_eps, "name": "优丁EPS线条", "slug": "youding-eps-lines", "subtitle": "造型多样·装饰美观", "description": "EPS装饰线条，质轻、安装便捷，可制作各种建筑装饰造型。", "specifications": "定制尺寸", "density": "25kg/m³", "strength": "≥0.15MPa", "thermal_conductivity": "0.041W/(m·K)", "unit_weight": "按实际尺寸", "sort_order": 3, "view_count": 0, "created_at": now, "updated_at": now, "application_scenarios": "建筑装饰线条\n窗套、门套\n柱饰、檐口", "advantages": "造型任意定制\n施工便捷\n成本低廉\n耐候性强", "technical_params": "导热系数: ≤0.041W/(m·K)\n表观密度: 20-30kg/m³\n燃烧性能: B1级"},

            # 保温装饰一体板
            {"id": cid(), "category_id": cat_board, "name": "优丁岩棉保温装饰一体板", "slug": "youding-rockwool-board", "subtitle": "A级防火·装饰一体化", "description": "以岩棉为保温芯材，面板为氟碳涂装金属板或无机面板，实现保温装饰一体化。", "specifications": "600×800×30-100mm", "density": "100-160kg/m³", "strength": "≥0.08MPa", "thermal_conductivity": "0.045W/(m·K)", "unit_weight": "15-30kg/块", "sort_order": 4, "view_count": 0, "created_at": now, "updated_at": now, "application_scenarios": "高层建筑外墙\n公共建筑\n商业综合体", "advantages": "A级防火\n装饰效果佳\n施工效率高\n耐久性强", "technical_params": "导热系数: ≤0.045W/(m·K)\n燃烧性能: A级\n面板: 氟碳涂层\n芯材: 岩棉"},
            {"id": cid(), "category_id": cat_board, "name": "优丁XPS保温装饰一体板", "slug": "youding-xps-board", "subtitle": "挤塑工艺·导热更低", "description": "以XPS挤塑板为保温芯材，导热系数更低，适合对保温要求更高的项目。", "specifications": "600×800×20-80mm", "density": "35-45kg/m³", "strength": "≥0.25MPa", "thermal_conductivity": "0.030W/(m·K)", "unit_weight": "12-25kg/块", "sort_order": 5, "view_count": 0, "created_at": now, "updated_at": now, "application_scenarios": "地下室顶板\n屋面保温\n地面保温", "advantages": "导热系数极低\n抗压强度高\n吸水率低\n施工便捷", "technical_params": "导热系数: ≤0.030W/(m·K)\n燃烧性能: B1级\n面板: 无机面板\n芯材: XPS"},

            # 保温砂浆
            {"id": cid(), "category_id": cat_mortar, "name": "优丁玻化微珠保温砂浆", "slug": "youding-gem-insulation-mortar", "subtitle": "无机保温·A级防火", "description": "以玻化微珠为骨料的无机保温砂浆，A级防火，适用于内外墙保温。", "specifications": "25kg/袋", "density": "280-350kg/m³", "strength": "≥0.5MPa", "thermal_conductivity": "0.070W/(m·K)", "unit_weight": "25kg/袋", "sort_order": 6, "view_count": 0, "created_at": now, "updated_at": now, "application_scenarios": "外墙内保温\n外墙外保温\n楼梯间保温", "advantages": "A级防火\n施工便捷\n粘结力强\n绿色环保", "technical_params": "导热系数: ≤0.070W/(m·K)\n燃烧性能: A级\n干密度: 280-350kg/m³\n抗压强度: ≥0.5MPa"},
            {"id": cid(), "category_id": cat_mortar, "name": "优丁聚苯颗粒保温砂浆", "slug": "youding-eps-mortar", "subtitle": "轻质保温·经济实用", "description": "以聚苯颗粒为轻骨料的保温砂浆，保温性能好，经济实惠。", "specifications": "25kg/袋", "density": "250-350kg/m³", "strength": "≥0.3MPa", "thermal_conductivity": "0.060W/(m·K)", "unit_weight": "25kg/袋", "sort_order": 7, "view_count": 0, "created_at": now, "updated_at": now, "application_scenarios": "外墙保温\n屋面保温\n地面保温", "advantages": "保温性能好\n施工简单\n成本经济\n适用性广", "technical_params": "导热系数: ≤0.060W/(m·K)\n燃烧性能: B1级\n干密度: 250-350kg/m³"},

            # 加气混凝土砌块
            {"id": cid(), "category_id": cat_block, "name": "优丁蒸压加气混凝土砌块", "slug": "youding-aac-block", "subtitle": "轻质高强·节能环保", "description": "蒸压加气混凝土砌块（AAC砌块），轻质、保温、防火、隔音、抗震。", "specifications": "600×200×100-300mm", "density": "500-700kg/m³", "strength": "≥3.5MPa", "thermal_conductivity": "0.140W/(m·K)", "unit_weight": "15-25kg/块", "sort_order": 8, "view_count": 0, "created_at": now, "updated_at": now, "application_scenarios": "框架结构填充墙\n外墙围护结构\n隔断墙", "advantages": "轻质高强\n保温隔热\nA级防火\n尺寸精确", "technical_params": "导热系数: ≤0.14W/(m·K)\n燃烧性能: A级\n干密度: 500-700kg/m³\n抗压强度: ≥3.5MPa"},
            {"id": cid(), "category_id": cat_block, "name": "优丁B06级加气块", "slug": "youding-b06-aac", "subtitle": "B06级·高性价比", "description": "B06级蒸压加气混凝土砌块，兼顾强度与保温，性价比高。", "specifications": "600×240×100-300mm", "density": "600kg/m³", "strength": "≥5.0MPa", "thermal_conductivity": "0.160W/(m·K)", "unit_weight": "18-28kg/块", "sort_order": 9, "view_count": 0, "created_at": now, "updated_at": now, "application_scenarios": "多层建筑填充墙\n内墙隔断", "advantages": "强度高\n保温好\n施工效率高\n尺寸标准", "technical_params": "导热系数: ≤0.16W/(m·K)\n燃烧性能: A级\n干密度: 600kg/m³\n抗压强度: ≥5.0MPa"},

            # 岩棉制品
            {"id": cid(), "category_id": cat_insulation, "name": "优丁岩棉板", "slug": "youding-rockwool-slab", "subtitle": "A级防火·优质保温", "description": "优质岩棉板，以天然岩石为原料，A级防火，保温隔音效果优异。", "specifications": "1200×600×30-100mm", "density": "80-160kg/m³", "strength": "≥0.06MPa", "thermal_conductivity": "0.045W/(m·K)", "unit_weight": "5-12kg/块", "sort_order": 10, "view_count": 0, "created_at": now, "updated_at": now, "application_scenarios": "建筑外墙保温\n工业设备保温\n船舶舱室", "advantages": "A级防火\n保温优异\n吸音隔音\n耐久性强", "technical_params": "导热系数: ≤0.045W/(m·K)\n燃烧性能: A级\n憎水率: ≥98%\n酸度系数: ≥1.6"},
            {"id": cid(), "category_id": cat_insulation, "name": "优丁岩棉毡", "slug": "youding-rockwool-felt", "subtitle": "柔性好·施工便捷", "description": "岩棉毡，柔性好，适用于管道、异形部位的保温包裹。", "specifications": "卷材: 1.2m×5m×50-100mm", "density": "60-100kg/m³", "strength": "≥0.04MPa", "thermal_conductivity": "0.045W/(m·K)", "unit_weight": "4-8kg/卷", "sort_order": 11, "view_count": 0, "created_at": now, "updated_at": now, "application_scenarios": "管道保温\n设备包裹\n异形面保温", "advantages": "柔性好\n易裁剪\n保温隔音\n防水透气", "technical_params": "导热系数: ≤0.045W/(m·K)\n燃烧性能: A级\n憎水率: ≥95%"},
        ]

        for p in products_data:
            db.add(Product(**p))
        db.flush()

        admin_id = str(uuid.uuid4())
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        admin_password = os.getenv("SEED_ADMIN_PASSWORD", "ChangeMe@2026!")
        admin = User(
            id=admin_id,
            username="admin",
            email="admin@youding.com",
            hashed_password=pwd_context.hash(admin_password),
            display_name="管理员",
            role="admin",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(admin)

        keywords_data = [
            Keyword(id=str(uuid.uuid4()), keyword="轻集料混凝土", slug="lightweight-aggregate-concrete", search_volume=1200, difficulty="medium", current_ranking=None, target_url="/products", created_at=now, updated_at=now),
            Keyword(id=str(uuid.uuid4()), keyword="EPS聚苯板", slug="eps-board", search_volume=800, difficulty="low", current_ranking=None, target_url="/products/eps-board", created_at=now, updated_at=now),
            Keyword(id=str(uuid.uuid4()), keyword="保温装饰一体板", slug="insulation-decorative-board", search_volume=650, difficulty="low", current_ranking=None, target_url="/products/insulation-board", created_at=now, updated_at=now),
            Keyword(id=str(uuid.uuid4()), keyword="加气混凝土砌块", slug="aac-block", search_volume=900, difficulty="low", current_ranking=5, target_url="/products/insulation-mortar", created_at=now, updated_at=now),
            Keyword(id=str(uuid.uuid4()), keyword="外墙保温材料", slug="exterior-insulation-material", search_volume=2000, difficulty="high", current_ranking=None, target_url="/products", created_at=now, updated_at=now),
            Keyword(id=str(uuid.uuid4()), keyword="洛阳保温材料", slug="luoyang-insulation", search_volume=300, difficulty="low", current_ranking=3, target_url="/products", created_at=now, updated_at=now),
            Keyword(id=str(uuid.uuid4()), keyword="岩棉板价格", slug="rockwool-price", search_volume=1500, difficulty="medium", current_ranking=8, target_url="/products/rock-wool", created_at=now, updated_at=now),
            Keyword(id=str(uuid.uuid4()), keyword="保温砂浆施工工艺", slug="insulation-mortar-construction", search_volume=400, difficulty="low", current_ranking=None, target_url="/products/insulation-mortar", created_at=now, updated_at=now),
        ]
        db.add_all(keywords_data)

        pages_data = [
            ContentPage(id=str(uuid.uuid4()), title="关于优丁", slug="about", content="# 关于优丁\n\n优丁建材科技有限公司是一家专注于轻集料混凝土及保温材料研发、生产和销售的高新技术企业。", summary="优丁建材科技有限公司简介", page_type="page", status="published", author_id=admin_id, is_active=True, published_at=now, created_at=now, updated_at=now),
            ContentPage(id=str(uuid.uuid4()), title="联系我们", slug="contact", content="# 联系我们\n\n地址: 河南省洛阳市\n电话: 400-xxx-xxxx\n邮箱: info@youding.com", summary="联系优丁建材", page_type="page", status="published", author_id=admin_id, is_active=True, published_at=now, created_at=now, updated_at=now),
            ContentPage(id=str(uuid.uuid4()), title="服务支持", slug="service", content="# 服务支持\n\n优丁建材提供全方位的技术支持和售后服务。", summary="技术支持与售后服务", page_type="page", status="draft", author_id=admin_id, is_active=True, created_at=now, updated_at=now),
        ]
        db.add_all(pages_data)

        db.commit()

        cat_count = db.query(Category).count()
        prod_count = db.query(Product).count()
        kw_count = db.query(Keyword).count()
        page_count = db.query(ContentPage).count()

        print(f"种子数据已成功创建!")
        print(f"  分类: {cat_count} 个")
        print(f"  产品: {prod_count} 个")
        print(f"  关键词: {kw_count} 个")
        print(f"  页面: {page_count} 个")
        print(f"  管理员: admin / admin123")

    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
