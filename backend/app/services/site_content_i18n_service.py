"""site_content 多语种 i18n 生成 · 建站补全 · 存量租户回填。"""

from __future__ import annotations

import copy
import json
from typing import Any

from app.services.site_content_array_i18n import build_array_i18n_pack, default_product_items_zh
from app.services.im_locale_service import SUPPORTED_LANGUAGES

# 英文走 pages 基字段；以下语种写入 pages.*.i18n
EXPORT_SITE_I18N_LANGS: tuple[str, ...] = tuple(
    code for code in SUPPORTED_LANGUAGES if code != "en"
)


def _short_label(name: str, brand: str) -> str:
    """_short_label。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :return: 返回处理结果。
    """
    base = (name or brand or "Product").strip()
    return base[:20] or "Product"


def infer_product_context(site_content: dict[str, Any]) -> tuple[str, str, str]:
    """从已有 site_content 推断 (product_name, company_name, short)。"""
    brand_info = site_content.get("brand") if isinstance(site_content.get("brand"), dict) else {}
    pages = site_content.get("pages") if isinstance(site_content.get("pages"), dict) else {}
    home = pages.get("home") if isinstance(pages.get("home"), dict) else {}
    products = pages.get("products") if isinstance(pages.get("products"), dict) else {}
    brand = str(brand_info.get("name") or "").strip()
    name = ""
    items = products.get("productItems")
    if isinstance(items, list) and items:
        first = items[0]
        if isinstance(first, dict) and first.get("name"):
            name = str(first["name"]).strip()
    if home.get("title"):
        title = str(home["title"])
        for sep in (" Manufacturer", " Supplier", " · ", "生产厂家", " ·供应商"):
            if sep in title:
                candidate = title.split(sep)[0].strip()
                if candidate:
                    name = candidate
                break
        if not name:
            name = title.strip()
    if not name:
        name = brand
    if not brand:
        brand = name
    return name, brand, _short_label(name, brand)


def _pack_zh(name: str, brand: str, short: str) -> dict[str, dict[str, str]]:
    """_pack_zh。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    return {
        "brand": {"tagline": f"中国 {short} 制造商 · OEM/ODM 定制出口"},
        "home": {
            "title": f"{short} 生产厂家 · 供应商",
            "description": (
                f"{brand} 专注 {name} 研发、生产与出口。"
                f"拥有现代化生产基地，产品远销欧美、中东、东南亚等市场，支持 OEM/ODM 与样品打样。"
            ),
            "ctaPrimary": "获取报价",
            "ctaSecondary": "联系我们",
            "sectionTitle": "为什么选择我们",
            "applicationsTitle": "应用场景",
        },
        "about": {
            "title": "关于我们",
            "aboutText": (
                f"{brand} 是中国专业的 {name} 制造商，集研发、生产、质检与出口服务于一体。"
                f"工厂具备批量订单与定制方案能力，欢迎全球经销商与工程项目采购咨询报价与样品。"
            ),
            "mission": f"以稳定工厂品质、透明沟通与准时交付，为全球合作伙伴提供可靠的 {name} 解决方案。",
            "vision": f"将 {brand} 打造为在技术支持、可持续制造与长期合作方面值得信赖的全球供应商。",
            "capacitySummary": (
                f"{brand} 拥有现代化产线、批量仓储与货柜级包装能力，"
                f"支持混装 SKU、项目报价与出货前第三方验货。"
            ),
        },
        "products": {
            "title": "产品中心",
            "description": f"面向经销商与工程承包商的热门 {name} 系列 — 板/卷/管多规格",
            "productItems": default_product_items_zh(name, short, short),
        },
    }


def _pack_ar(name: str, brand: str, short: str) -> dict[str, dict[str, str]]:
    """_pack_ar。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    return {
        "brand": {"tagline": f"مصنع {short} في الصين · OEM/ODM للتصدير"},
        "home": {
            "title": f"مصنع ومورد {short}",
            "description": (
                f"{brand} متخصص في {name} — البحث والتطوير والإنتاج والتصدير. "
                f"مصنع حديث، شحن إلى أوروبا والشرق الأوسط وآسيا، OEM/ODM وعينات متاحة."
            ),
            "ctaPrimary": "احصل على عرض سعر",
            "ctaSecondary": "تواصل معنا",
            "sectionTitle": "لماذا نحن",
            "applicationsTitle": "مجالات الاستخدام",
        },
        "about": {
            "title": "من نحن",
            "aboutText": (
                f"{brand} مصنع محترف لـ {name} في الصين — البحث والإنتاج والجودة والتصدير. "
                f"نرحب بالموزعين ومقاولي المشاريع للاستفسار عن الأسعار والعينات."
            ),
            "mission": f"تقديم حلول {name} موثوقة بجودة مصنع ثابتة وتواصل شفاف وتسليم في الوقت.",
            "vision": f"أن نكون مورداً عالمياً موثوقاً في {name} والدعم الفني والتصنيع المستدام.",
            "capacitySummary": f"خطوط إنتاج حديثة ومستودعات وتعبئة حاويات — {brand} يدعم طلبات مختلطة ومعاينة قبل الشحن.",
        },
        "products": {
            "title": "المنتجات",
            "description": f"سلسلة {name} للموزعين ومقاولي EPC — ألواح ولفائف وأنابيب",
        },
    }


def _pack_es(name: str, brand: str, short: str) -> dict[str, dict[str, str]]:
    """_pack_es。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    return {
        "brand": {"tagline": f"Fabricante de {short} en China · OEM/ODM exportación"},
        "home": {
            "title": f"Fabricante y proveedor de {short}",
            "description": (
                f"{brand} se especializa en {name}: I+D, producción y exportación. "
                f"Fábrica moderna, envíos a Europa, Oriente Medio y ASEAN; OEM/ODM y muestras."
            ),
            "ctaPrimary": "Solicitar cotización",
            "ctaSecondary": "Contáctenos",
            "sectionTitle": "Por qué elegirnos",
            "applicationsTitle": "Aplicaciones",
        },
        "about": {
            "title": "Sobre nosotros",
            "aboutText": (
                f"{brand} es un fabricante profesional de {name} en China con I+D, producción, "
                f"control de calidad y exportación. Distribuidores y EPC: consulte precios y muestras."
            ),
            "mission": f"Ofrecer soluciones de {name} fiables con calidad de fábrica y entrega puntual.",
            "vision": f"Ser un proveedor global de confianza en {name}, soporte técnico y fabricación sostenible.",
            "capacitySummary": f"{brand}: líneas modernas, almacén a granel y embalaje para contenedores; pedidos mixtos e inspección previa al envío.",
        },
        "products": {
            "title": "Productos",
            "description": f"Series de {name} para distribuidores y EPC — placas, rollos y tubos",
        },
    }


def _pack_pt(name: str, brand: str, short: str) -> dict[str, dict[str, str]]:
    """_pack_pt。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    return {
        "brand": {"tagline": f"Fabricante de {short} na China · OEM/ODM exportação"},
        "home": {
            "title": f"Fabricante e fornecedor de {short}",
            "description": (
                f"{brand} especializado em {name}: P&D, produção e exportação. "
                f"Fábrica moderna, envio para Europa, Oriente Médio e ASEAN; OEM/ODM e amostras."
            ),
            "ctaPrimary": "Solicitar cotação",
            "ctaSecondary": "Fale conosco",
            "sectionTitle": "Por que nos escolher",
            "applicationsTitle": "Aplicações",
        },
        "about": {
            "title": "Sobre nós",
            "aboutText": (
                f"{brand} é fabricante profissional de {name} na China. "
                f"Distribuidores e EPC: consulte preços e amostras."
            ),
            "mission": f"Entregar soluções de {name} confiáveis com qualidade de fábrica e prazo de exportação.",
            "vision": f"Ser fornecedor global reconhecido em {name} e cooperação de longo prazo.",
            "capacitySummary": f"{brand}: linhas modernas, armazém e embalagem para contêineres; SKUs mistos e inspeção antes do embarque.",
        },
        "products": {
            "title": "Produtos",
            "description": f"Séries de {name} para distribuidores e EPC",
        },
    }


def _pack_ru(name: str, brand: str, short: str) -> dict[str, dict[str, str]]:
    """_pack_ru。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    return {
        "brand": {"tagline": f"Производитель {short} в Китае · OEM/ODM экспорт"},
        "home": {
            "title": f"Производитель и поставщик {short}",
            "description": (
                f"{brand} — {name}: НИОКР, производство и экспорт. "
                f"Современный завод, поставки в Европу, Ближний Восток и ASEAN; OEM/ODM и образцы."
            ),
            "seoDescription": (
                f"{brand} — производитель {name} из Китая. OEM/ODM, экспорт, образцы."
            ),
            "seoKeywords": f"{short}, теплоизоляция, минеральная вата, производитель, завод, поставщик",
            "ctaPrimary": "Запросить цену",
            "ctaSecondary": "Связаться с нами",
            "sectionTitle": "Почему мы",
            "applicationsTitle": "Применение",
        },
        "about": {
            "title": "О компании",
            "aboutText": (
                f"{brand} — профессиональный производитель {name} в Китае. "
                f"Дистрибьюторы и EPC: запрос цен и образцов."
            ),
            "mission": f"Надёжные решения {name} с стабильным качеством завода и своевременной поставкой.",
            "vision": f"Быть надёжным глобальным поставщиком {name} и технической поддержки.",
            "capacitySummary": f"{brand}: современные линии, склад и упаковка для контейнеров; смешанные заказы и инспекция перед отгрузкой.",
        },
        "products": {
            "title": "Продукция",
            "description": f"Серии {name} для дистрибьюторов и EPC",
        },
    }


def _pack_th(name: str, brand: str, short: str) -> dict[str, dict[str, str]]:
    """_pack_th。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    return {
        "brand": {"tagline": f"ผู้ผลิต {short} ในจีน · OEM/ODM ส่งออก"},
        "home": {
            "title": f"ผู้ผลิตและซัพพลายเออร์ {short}",
            "description": (
                f"{brand} เชี่ยวชาญ {name} — วิจัย ผลิต และส่งออก "
                f"โรงงานทันสมัย ส่งออกยุโรป ตะวันออกกลาง ASEAN รองรับ OEM/ODM และตัวอย่าง"
            ),
            "ctaPrimary": "ขอใบเสนอราคา",
            "ctaSecondary": "ติดต่อเรา",
            "sectionTitle": "ทำไมต้องเลือกเรา",
            "applicationsTitle": "การใช้งาน",
        },
        "about": {
            "title": "เกี่ยวกับเรา",
            "aboutText": f"{brand} เป็นผู้ผลิต {name} มืออาชีพในจีน ยินดีรับตัวแทนจำหน่ายและ EPC",
            "mission": f"มอบโซลูชัน {name} ที่เชื่อถือได้ด้วยคุณภาพโรงงานและส่งตรงเวลา",
            "vision": f"เป็นซัพพลายเออร์ {name} ระดับโลกที่ไว้วางใจ",
            "capacitySummary": f"{brand} มีสายการผลิต คลังสินค้า และบรรจุตู้คอนเทนเนอร์",
        },
        "products": {
            "title": "ผลิตภัณฑ์",
            "description": f"ซีรีส์ {name} สำหรับตัวแทนจำหน่ายและ EPC",
        },
    }


def _pack_vi(name: str, brand: str, short: str) -> dict[str, dict[str, str]]:
    """_pack_vi。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    return {
        "brand": {"tagline": f"Nhà sản xuất {short} tại Trung Quốc · OEM/ODM xuất khẩu"},
        "home": {
            "title": f"Nhà sản xuất & nhà cung cấp {short}",
            "description": (
                f"{brand} chuyên {name} — R&D, sản xuất và xuất khẩu. "
                f"Nhà máy hiện đại, giao Châu Âu, Trung Đông, ASEAN; OEM/ODM và mẫu."
            ),
            "ctaPrimary": "Yêu cầu báo giá",
            "ctaSecondary": "Liên hệ",
            "sectionTitle": "Vì sao chọn chúng tôi",
            "applicationsTitle": "Ứng dụng",
        },
        "about": {
            "title": "Về chúng tôi",
            "aboutText": f"{brand} là nhà sản xuất {name} chuyên nghiệp tại Trung Quốc.",
            "mission": f"Cung cấp giải pháp {name} tin cậy với chất lượng nhà máy ổn định.",
            "vision": f"Trở thành nhà cung cấp {name} toàn cầu đáng tin cậy.",
            "capacitySummary": f"{brand}: dây chuyền hiện đại, kho bãi và đóng gói container.",
        },
        "products": {
            "title": "Sản phẩm",
            "description": f"Dòng {name} cho nhà phân phối và EPC",
        },
    }


def _pack_id(name: str, brand: str, short: str) -> dict[str, dict[str, str]]:
    """_pack_id。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    return {
        "brand": {"tagline": f"Produsen {short} di Tiongkok · OEM/ODM ekspor"},
        "home": {
            "title": f"Produsen & pemasok {short}",
            "description": (
                f"{brand} spesialis {name} — R&D, produksi, ekspor. "
                f"Pabrik modern, kirim ke Eropa, Timur Tengah, ASEAN; OEM/ODM & sampel."
            ),
            "ctaPrimary": "Minta penawaran",
            "ctaSecondary": "Hubungi kami",
            "sectionTitle": "Mengapa kami",
            "applicationsTitle": "Aplikasi",
        },
        "about": {
            "title": "Tentang kami",
            "aboutText": f"{brand} produsen profesional {name} di Tiongkok.",
            "mission": f"Solusi {name} andal dengan kualitas pabrik konsisten.",
            "vision": f"Pemasok global {name} yang dipercaya.",
            "capacitySummary": f"{brand}: lini produksi modern, gudang & kemasan kontainer.",
        },
        "products": {
            "title": "Produk",
            "description": f"Seri {name} untuk distributor & EPC",
        },
    }


def _pack_ms(name: str, brand: str, short: str) -> dict[str, dict[str, str]]:
    """_pack_ms。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    return {
        "brand": {"tagline": f"Pengeluar {short} di China · OEM/ODM eksport"},
        "home": {
            "title": f"Pengeluar & pembekal {short}",
            "description": (
                f"{brand} pakar {name} — R&D, pengeluaran & eksport. "
                f"Kilang moden; OEM/ODM & sampel."
            ),
            "ctaPrimary": "Minta sebut harga",
            "ctaSecondary": "Hubungi kami",
            "sectionTitle": "Mengapa kami",
            "applicationsTitle": "Aplikasi",
        },
        "about": {
            "title": "Tentang kami",
            "aboutText": f"{brand} pengeluar profesional {name} di China.",
            "mission": f"Penyelesaian {name} boleh dipercayai dengan kualiti kilang.",
            "vision": f"Pembekal global {name} yang diiktiraf.",
            "capacitySummary": f"{brand}: talian pengeluaran moden & pembungkusan kontena.",
        },
        "products": {
            "title": "Produk",
            "description": f"Siri {name} untuk pengedar & EPC",
        },
    }


def _pack_ja(name: str, brand: str, short: str) -> dict[str, dict[str, str]]:
    """_pack_ja。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    return {
        "brand": {"tagline": f"中国の{short}メーカー · OEM/ODM 輸出"},
        "home": {
            "title": f"{short} メーカー・サプライヤー",
            "description": (
                f"{brand} は {name} の研究開発・生産・輸出に特化。"
                f"現代工場、欧州・中東・ASEAN 向け出荷、OEM/ODM・サンプル対応。"
            ),
            "ctaPrimary": "見積依頼",
            "ctaSecondary": "お問い合わせ",
            "sectionTitle": "選ばれる理由",
            "applicationsTitle": "用途",
        },
        "about": {
            "title": "会社概要",
            "aboutText": f"{brand} は中国の専門 {name} メーカーです。ディストリビューター・EPC 様はお気軽にお問い合わせください。",
            "mission": f"安定した工場品質と納期で信頼できる {name} ソリューションを提供。",
            "vision": f"{name} 分野で技術支援と持続可能な製造で信頼されるグローバルサプライヤーへ。",
            "capacitySummary": f"{brand} は現代化ライン・倉庫・コンテナ梱包、混載 SKU と出荷前検査に対応。",
        },
        "products": {
            "title": "製品",
            "description": f"ディストリビューター・EPC 向け {name} シリーズ",
        },
    }


def _pack_ko(name: str, brand: str, short: str) -> dict[str, dict[str, str]]:
    """_pack_ko。

    参数说明：
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    return {
        "brand": {"tagline": f"중국 {short} 제조사 · OEM/ODM 수출"},
        "home": {
            "title": f"{short} 제조사 및 공급업체",
            "description": (
                f"{brand}는 {name} 연구개발·생산·수출 전문. "
                f"현대 공장, 유럽·중동·ASEAN 출하, OEM/ODM 및 샘플 지원."
            ),
            "ctaPrimary": "견적 요청",
            "ctaSecondary": "문의하기",
            "sectionTitle": "왜 우리인가",
            "applicationsTitle": "응용 분야",
        },
        "about": {
            "title": "회사 소개",
            "aboutText": f"{brand}는 중국의 전문 {name} 제조사입니다. 유통사·EPC 문의 환영.",
            "mission": f"안정적인 공장 품질과 납기로 신뢰할 수 있는 {name} 솔루션 제공.",
            "vision": f"{name} 분야에서 기술 지원과 지속 가능한 제조로 신뢰받는 글로벌 공급사.",
            "capacitySummary": f"{brand}: 현대화 라인·창고·컨테이너 포장, 혼합 SKU 및 선적 전 검사.",
        },
        "products": {
            "title": "제품",
            "description": f"유통사·EPC용 {name} 시리즈",
        },
    }


def _pack_fr(name: str, brand: str, short: str) -> dict[str, dict[str, str]]:
    """_pack_fr — Tier2 法语模板回退。"""
    return {
        "brand": {"tagline": f"Fabricant de {short} en Chine · OEM/ODM exportation"},
        "home": {
            "title": f"Fabricant et fournisseur de {short}",
            "description": (
                f"{brand} est spécialisé dans {name} : R&D, production et exportation. "
                f"Usine moderne, livraisons en Europe, Moyen-Orient et ASEAN ; OEM/ODM et échantillons."
            ),
            "ctaPrimary": "Demander un devis",
            "ctaSecondary": "Nous contacter",
            "sectionTitle": "Pourquoi nous choisir",
            "applicationsTitle": "Applications",
        },
        "about": {
            "title": "À propos",
            "aboutText": (
                f"{brand} est un fabricant professionnel de {name} en Chine. "
                f"Distributeurs et EPC : contactez-nous pour prix et échantillons."
            ),
            "mission": f"Fournir des solutions {name} fiables avec qualité d'usine et livraison ponctuelle.",
            "vision": f"Être un fournisseur mondial de confiance en {name} et support technique.",
            "capacitySummary": f"{brand} : lignes modernes, entrepôt et emballage conteneur ; SKU mixtes et inspection avant expédition.",
        },
        "products": {
            "title": "Produits",
            "description": f"Gamme {name} pour distributeurs et EPC",
        },
    }


def _pack_de(name: str, brand: str, short: str) -> dict[str, dict[str, str]]:
    """_pack_de — Tier2 德语模板回退。"""
    return {
        "brand": {"tagline": f"{short} Hersteller in China · OEM/ODM Export"},
        "home": {
            "title": f"{short} Hersteller und Lieferant",
            "description": (
                f"{brand} ist spezialisiert auf {name}: F&E, Produktion und Export. "
                f"Moderne Fabrik, Lieferungen nach Europa, Nahen Osten und ASEAN; OEM/ODM und Muster."
            ),
            "ctaPrimary": "Angebot anfordern",
            "ctaSecondary": "Kontakt",
            "sectionTitle": "Warum wir",
            "applicationsTitle": "Anwendungen",
        },
        "about": {
            "title": "Über uns",
            "aboutText": (
                f"{brand} ist ein professioneller Hersteller von {name} in China. "
                f"Händler und EPC: Preise und Muster anfragen."
            ),
            "mission": f"Zuverlässige {name}-Lösungen mit konstanter Fabrikqualität und pünktlicher Lieferung.",
            "vision": f"Ein vertrauenswürdiger globaler Lieferant für {name} und technischen Support sein.",
            "capacitySummary": f"{brand}: moderne Linien, Lager und Containerverpackung; gemischte SKU und Vorversandinspektion.",
        },
        "products": {
            "title": "Produkte",
            "description": f"{name}-Serie für Händler und EPC",
        },
    }


def _pack_it(name: str, brand: str, short: str) -> dict[str, dict[str, str]]:
    """_pack_it — Tier2 意大利语模板回退。"""
    return {
        "brand": {"tagline": f"Produttore di {short} in Cina · OEM/ODM esportazione"},
        "home": {
            "title": f"Produttore e fornitore di {short}",
            "description": (
                f"{brand} è specializzato in {name}: R&S, produzione ed esportazione. "
                f"Stabilimento moderno, spedizioni in Europa, Medio Oriente e ASEAN; OEM/ODM e campioni."
            ),
            "ctaPrimary": "Richiedi preventivo",
            "ctaSecondary": "Contattaci",
            "sectionTitle": "Perché sceglierci",
            "applicationsTitle": "Applicazioni",
        },
        "about": {
            "title": "Chi siamo",
            "aboutText": (
                f"{brand} è un produttore professionale di {name} in Cina. "
                f"Distributori e EPC: richiedete prezzi e campioni."
            ),
            "mission": f"Fornire soluzioni {name} affidabili con qualità di fabbrica e consegna puntuale.",
            "vision": f"Essere un fornitore globale affidabile di {name} e supporto tecnico.",
            "capacitySummary": f"{brand}: linee moderne, magazzino e imballaggio container; SKU misti e ispezione pre-spedizione.",
        },
        "products": {
            "title": "Prodotti",
            "description": f"Serie {name} per distributori e EPC",
        },
    }


def _pack_nl(name: str, brand: str, short: str) -> dict[str, dict[str, str]]:
    """_pack_nl — Tier2 荷兰语模板回退。"""
    return {
        "brand": {"tagline": f"{short} fabrikant in China · OEM/ODM export"},
        "home": {
            "title": f"{short} fabrikant en leverancier",
            "description": (
                f"{brand} is gespecialiseerd in {name}: R&D, productie en export. "
                f"Moderne fabriek, leveringen aan Europa, Midden-Oosten en ASEAN; OEM/ODM en monsters."
            ),
            "ctaPrimary": "Offerte aanvragen",
            "ctaSecondary": "Contact",
            "sectionTitle": "Waarom wij",
            "applicationsTitle": "Toepassingen",
        },
        "about": {
            "title": "Over ons",
            "aboutText": (
                f"{brand} is een professionele fabrikant van {name} in China. "
                f"Distributeurs en EPC: vraag prijzen en monsters aan."
            ),
            "mission": f"Betrouwbare {name}-oplossingen met constante fabriekskwaliteit en tijdige levering.",
            "vision": f"Een vertrouwde wereldwijde leverancier van {name} en technische ondersteuning zijn.",
            "capacitySummary": f"{brand}: moderne lijnen, magazijn en containerverpakking; gemengde SKU en inspectie voor verzending.",
        },
        "products": {
            "title": "Producten",
            "description": f"{name}-serie voor distributeurs en EPC",
        },
    }


def _pack_pl(name: str, brand: str, short: str) -> dict[str, dict[str, str]]:
    """_pack_pl — Tier2 波兰语模板回退。"""
    return {
        "brand": {"tagline": f"Producent {short} w Chinach · OEM/ODM eksport"},
        "home": {
            "title": f"Producent i dostawca {short}",
            "description": (
                f"{brand} specjalizuje się w {name}: badania, produkcja i eksport. "
                f"Nowoczesna fabryka, dostawy do Europy, Bliskiego Wschodu i ASEAN; OEM/ODM i próbki."
            ),
            "ctaPrimary": "Zapytaj o cenę",
            "ctaSecondary": "Kontakt",
            "sectionTitle": "Dlaczego my",
            "applicationsTitle": "Zastosowania",
        },
        "about": {
            "title": "O nas",
            "aboutText": (
                f"{brand} jest profesjonalnym producentem {name} w Chinach. "
                f"Dystrybutorzy i EPC: zapytaj o ceny i próbki."
            ),
            "mission": f"Dostarczać niezawodne rozwiązania {name} ze stabilną jakością fabryczną i terminową dostawą.",
            "vision": f"Być zaufanym globalnym dostawcą {name} i wsparcia technicznego.",
            "capacitySummary": f"{brand}: nowoczesne linie, magazyn i pakowanie kontenerowe; mieszane SKU i inspekcja przed wysyłką.",
        },
        "products": {
            "title": "Produkty",
            "description": f"Seria {name} dla dystrybutorów i EPC",
        },
    }


def _pack_tr(name: str, brand: str, short: str) -> dict[str, dict[str, str]]:
    """_pack_tr — Tier2 土耳其语模板回退。"""
    return {
        "brand": {"tagline": f"Çin'de {short} üreticisi · OEM/ODM ihracat"},
        "home": {
            "title": f"{short} üreticisi ve tedarikçisi",
            "description": (
                f"{brand}, {name} alanında uzman: Ar-Ge, üretim ve ihracat. "
                f"Modern fabrika, Avrupa, Orta Doğu ve ASEAN'a sevkiyat; OEM/ODM ve numuneler."
            ),
            "ctaPrimary": "Teklif talep et",
            "ctaSecondary": "İletişim",
            "sectionTitle": "Neden biz",
            "applicationsTitle": "Uygulamalar",
        },
        "about": {
            "title": "Hakkımızda",
            "aboutText": (
                f"{brand}, Çin'de profesyonel bir {name} üreticisidir. "
                f"Distribütörler ve EPC: fiyat ve numune için başvurun."
            ),
            "mission": f"Kararlı fabrika kalitesi ve zamanında teslimat ile güvenilir {name} çözümleri sunmak.",
            "vision": f"{name} ve teknik destek alanında güvenilir bir küresel tedarikçi olmak.",
            "capacitySummary": f"{brand}: modern hatlar, depo ve konteyner paketleme; karışık SKU ve sevkiyat öncesi denetim.",
        },
        "products": {
            "title": "Ürünler",
            "description": f"Distribütörler ve EPC için {name} serisi",
        },
    }


_PACKERS = {
    "zh": _pack_zh,
    "ar": _pack_ar,
    "es": _pack_es,
    "pt": _pack_pt,
    "ru": _pack_ru,
    "th": _pack_th,
    "vi": _pack_vi,
    "id": _pack_id,
    "ms": _pack_ms,
    "ja": _pack_ja,
    "ko": _pack_ko,
    "fr": _pack_fr,
    "de": _pack_de,
    "it": _pack_it,
    "nl": _pack_nl,
    "pl": _pack_pl,
    "tr": _pack_tr,
}


def build_locale_i18n_pack(language: str, *, name: str, brand: str, short: str) -> dict[str, dict[str, Any]]:
    """build_locale_i18n_pack。

    参数说明：
    :param language: 参数 language
    :param name: 参数 name
    :param brand: 参数 brand
    :param short: 参数 short
    :return: 返回处理结果。
    """
    fn = _PACKERS.get(language)
    if not fn:
        return {}
    pack = fn(name, brand, short)
    arrays = build_array_i18n_pack(language, name=name, brand=brand, short=short)
    for section in ("home", "about"):
        if section in arrays and section in pack:
            pack[section] = {**pack[section], **arrays[section]}
        elif section in arrays:
            pack[section] = arrays[section]
    return pack


HOME_ARRAY_KEYS = (
    "stats",
    "trustBadges",
    "applications",
    "solutions",
    "advantages",
    "categories",
)
ABOUT_ARRAY_KEYS = ("milestones",)

I18N_SECTION_FIELDS: dict[str, tuple[str, ...]] = {
    "brand": ("tagline",),
    "home": (
        "title",
        "description",
        "seoDescription",
        "seoKeywords",
        "ctaPrimary",
        "ctaSecondary",
        "sectionTitle",
        "applicationsTitle",
        "inquiryHook",
        *HOME_ARRAY_KEYS,
    ),
    "about": ("title", "aboutText", "mission", "vision", "capacitySummary", *ABOUT_ARRAY_KEYS),
    "products": ("title", "description", "productItems"),
}


def _site_page_map(out: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """_site_page_map。

    参数说明：
    :param out: 参数 out
    :return: 返回处理结果。
    """
    pages = out.setdefault("pages", {})
    if not isinstance(pages, dict):
        pages = {}
        out["pages"] = pages
    brand_page = out.setdefault("brand", {})
    if not isinstance(brand_page, dict):
        brand_page = {}
        out["brand"] = brand_page

    def _page(key: str) -> dict[str, Any]:
        """_page。

        参数说明：
        :param key: 参数 key
        :return: 返回处理结果。
        """
        page = pages.get(key)
        if not isinstance(page, dict):
            page = {}
            pages[key] = page
        return page

    return {
        "brand": brand_page,
        "home": _page("home"),
        "about": _page("about"),
        "products": _page("products"),
    }


def _section_source_texts(page: dict[str, Any] | None, fields: tuple[str, ...]) -> dict[str, str]:
    """_section_source_texts。

    参数说明：
    :param page: 参数 page
    :param fields: 参数 fields
    :return: 返回处理结果。
    """
    if not isinstance(page, dict):
        return {}
    zh_block = {}
    i18n = page.get("i18n")
    if isinstance(i18n, dict) and isinstance(i18n.get("zh"), dict):
        zh_block = i18n["zh"]
    picked: dict[str, str] = {}
    for field in fields:
        raw = zh_block.get(field) or page.get(field)
        if isinstance(raw, str) and raw.strip():
            picked[field] = raw.strip()
    return picked


def extract_i18n_source_texts(site_content: dict[str, Any]) -> dict[str, dict[str, str]]:
    """提取用于 AI 翻译的 canonical 文案（优先 zh i18n，否则 pages 基字段）。"""
    if not isinstance(site_content, dict):
        return {}
    pages = site_content.get("pages") if isinstance(site_content.get("pages"), dict) else {}
    brand = site_content.get("brand") if isinstance(site_content.get("brand"), dict) else {}
    out: dict[str, dict[str, str]] = {}
    for section, fields in I18N_SECTION_FIELDS.items():
        page = brand if section == "brand" else pages.get(section)
        block = _section_source_texts(page if isinstance(page, dict) else {}, fields)
        if block:
            out[section] = block
    return out


def apply_i18n_translations(
    site_content: dict[str, Any],
    translations: dict[str, dict[str, dict[str, str]]],
    *,
    overwrite: bool = False,
) -> tuple[dict[str, Any], dict[str, int]]:
    """将 AI/外部翻译结果写入 pages.*.i18n。"""
    if not isinstance(site_content, dict) or not translations:
        return site_content, {"fields_added": 0, "langs_touched": 0}

    out = copy.deepcopy(site_content)
    page_map = _site_page_map(out)
    fields_added = 0
    langs_touched: set[str] = set()
    for lang, sections in translations.items():
        if not isinstance(sections, dict):
            continue
        lang_added = 0
        for section, fields in sections.items():
            if section not in I18N_SECTION_FIELDS or not isinstance(fields, dict):
                continue
            target = page_map.get(section)
            if not isinstance(target, dict):
                continue
            lang_added += _merge_block(target, lang, fields, overwrite=overwrite)
        if lang_added:
            langs_touched.add(lang)
            fields_added += lang_added

    return out, {"fields_added": fields_added, "langs_touched": len(langs_touched)}


def _merge_block(
    page: dict[str, Any],
    lang: str,
    fields: dict[str, Any],
    *,
    overwrite: bool,
) -> int:
    """_merge_block。

    参数说明：
    :param page: 参数 page
    :param lang: 参数 lang
    :param fields: 参数 fields
    :param overwrite: 参数 overwrite
    :return: 返回处理结果。
    """
    def _filled(value: Any) -> bool:
        """_filled。

        参数说明：
        :param value: 参数 value
        :return: 返回处理结果。
        """
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, dict)):
            return len(value) > 0
        return True

    added = 0
    i18n_root = page.get("i18n")
    if not isinstance(i18n_root, dict):
        i18n_root = {}
        page["i18n"] = i18n_root
    lang_block = i18n_root.get(lang)
    if not isinstance(lang_block, dict):
        lang_block = {}
        i18n_root[lang] = lang_block
    for key, value in fields.items():
        if not _filled(value):
            continue
        existing = lang_block.get(key)
        if overwrite or not _filled(existing):
            lang_block[key] = copy.deepcopy(value) if isinstance(value, (list, dict)) else value
            added += 1
    return added


def ensure_site_content_i18n(
    site_content: dict[str, Any],
    *,
    product_name: str | None = None,
    company_name: str | None = None,
    langs: tuple[str, ...] | None = None,
    overwrite: bool = False,
) -> tuple[dict[str, Any], dict[str, int]]:
    """
    为 site_content 补全 pages/brand 的 i18n 块（缺则填，默认不覆盖已有键）。
    返回 (新 site_content, stats)。
    """
    if not isinstance(site_content, dict):
        return site_content, {"fields_added": 0, "langs_touched": 0}

    out = copy.deepcopy(site_content)
    name, brand, short = infer_product_context(out)
    if product_name and product_name.strip():
        name = product_name.strip()
        short = _short_label(name, brand)
    if company_name and company_name.strip():
        brand = company_name.strip()

    target_langs = langs or EXPORT_SITE_I18N_LANGS
    page_map = _site_page_map(out)
    fields_added = 0
    langs_touched: set[str] = set()
    for lang in target_langs:
        pack = build_locale_i18n_pack(lang, name=name, brand=brand, short=short)
        if not pack:
            continue
        lang_added = 0
        for section, fields in pack.items():
            target = page_map.get(section)
            if not isinstance(target, dict):
                continue
            lang_added += _merge_block(target, lang, fields, overwrite=overwrite)
        if lang_added:
            langs_touched.add(lang)
            fields_added += lang_added

    return out, {"fields_added": fields_added, "langs_touched": len(langs_touched)}


def backfill_tenant_site_content_i18n(db: Any, *, dry_run: bool = False, overwrite: bool = False) -> dict[str, Any]:
    """扫描全部租户，补全 brand.site_content 的 i18n 字段。"""
    from app.models.tenant import Tenant
    from app.services.onboarding_im_contacts_service import _safe_settings
    from app.services.site_content_bridge import sync_site_content_to_brand
    tenants = db.query(Tenant).all()
    tenants_scanned = 0
    tenants_updated = 0
    fields_added_total = 0
    skipped_no_site = 0
    samples: list[dict[str, str]] = []
    for tenant in tenants:
        tenants_scanned += 1
        settings = _safe_settings(tenant.settings)
        brand = settings.get("brand") if isinstance(settings.get("brand"), dict) else {}
        site = brand.get("site_content") if isinstance(brand.get("site_content"), dict) else None
        if not site:
            skipped_no_site += 1
            continue

        updated, stats = ensure_site_content_i18n(site, overwrite=overwrite)
        added = int(stats.get("fields_added") or 0)
        if added <= 0:
            continue

        tenants_updated += 1
        fields_added_total += added
        if len(samples) < 5:
            samples.append({"domain": tenant.domain, "fields_added": str(added)})

        if dry_run:
            continue

        brand = {**brand, "site_content": updated}
        settings["brand"] = sync_site_content_to_brand(brand, updated)
        tenant.settings = json.dumps(settings, ensure_ascii=False)

    if not dry_run and tenants_updated:
        db.commit()

    return {
        "tenants_scanned": tenants_scanned,
        "tenants_updated": tenants_updated,
        "fields_added_total": fields_added_total,
        "skipped_no_site": skipped_no_site,
        "dry_run": dry_run,
        "overwrite": overwrite,
        "langs": list(EXPORT_SITE_I18N_LANGS),
        "samples": samples,
    }
