"""访客 IP / 请求头 → 国家与语言；外贸站与旺财 UI 随地域自动切换。"""

from __future__ import annotations

import re
from typing import Any

from app.services.im_locale_service import (
    COUNTRY_DEFAULT_LANG,
    SUPPORTED_LANGUAGES,
    localized_channel_label,
    normalize_language,
)

# 内网 / 本地开发 IP — 用语种推断默认国家
_PRIVATE_IP_PREFIXES = (
    "127.",
    "10.",
    "192.168.",
    "172.16.",
    "172.17.",
    "172.18.",
    "172.19.",
    "172.2",
    "172.30.",
    "172.31.",
    "::1",
    "localhost",
    "unknown",
)

# Accept-Language 首段 → 无 CF 头时的默认国家
_LANG_DEFAULT_COUNTRY: dict[str, str] = {
    "zh": "CN",
    "en": "US",
    "ar": "SA",
    "es": "ES",
    "pt": "BR",
    "ru": "RU",
    "th": "TH",
    "vi": "VN",
    "id": "ID",
    "ms": "MY",
    "ja": "JP",
    "ko": "KR",
}

# 外贸站导航 / 区块标题（12 语种，de/fr 等回退 en）
SITE_UI: dict[str, dict[str, str]] = {
    "zh": {
        "loading": "加载中…",
        "site_unavailable": "站点暂不可用",
        "nav_home": "首页",
        "nav_products": "产品",
        "nav_solutions": "解决方案",
        "nav_applications": "应用",
        "nav_about": "关于我们",
        "nav_video": "视频",
        "nav_qa": "买家问答",
        "nav_contact": "联系我们",
        "cta_primary": "获取报价",
        "cta_secondary": "联系我们",
        "stats_eyebrow": "我们的优势",
        "stats_title": "规模化可信制造",
        "section_stages_eyebrow": "项目阶段",
        "section_stages_title": "这单你现在处于哪一步？",
        "section_stages_desc": "询盘 → 打样 → 小批 → 量产，按客户决策链展示。",
        "section_solutions": "行业解决方案",
        "section_solutions_desc": "按买家任务划分，不是按仓库分区陈列",
        "section_knowledge_eyebrow": "技术内容",
        "section_knowledge_title": "先接住搜索意图，再导询盘",
        "section_knowledge_desc": "工艺/选型干货，证明你懂行，而不是口号墙",
        "section_cta_title": "准备开始？",
        "section_cta_desc": "发送规格或图纸 — 我们回复范围与下一步",
        "section_products": "产品中心",
        "section_contact": "联系我们",
        "tel_label": "电话",
        "email_label": "邮箱",
        "whatsapp_label": "WhatsApp",
        "wechat_label": "微信",
        "hero_since": "自 {year} 年起",
        "section_categories": "产品分类",
        "section_categories_desc": "专业出口产品系列",
        "section_products_default": "产品中心",
        "section_products_desc": "出口询价热门产品",
        "inquiry_link": "立即询价 →",
        "section_about": "关于 {name}",
        "mission": "使命",
        "vision": "愿景",
        "company_history": "发展历程",
        "video_center": "视频中心",
        "factory_label": "工厂地址",
        "footer_quick_links": "快速链接",
        "footer_contact": "联系我们",
        "why_choose_us": "为什么选择我们",
        "applications_title_default": "应用场景",
        "tenant_not_found": "未找到站点",
        "load_failed": "加载失败",
        "contact_qq_label": "QQ",
        "menu_open": "打开菜单",
        "menu_close": "关闭菜单",
        "hero_placeholder_hint": "专业制造 · 出口就绪",
        "mobile_quick_actions": "快捷联系",
        "form_name": "姓名",
        "form_email": "邮箱",
        "form_phone": "电话 / WhatsApp",
        "form_phone_cn": "手机号",
        "form_product": "产品 / 规格",
        "form_message": "询盘内容",
        "form_submit": "提交询盘",
        "form_submitting": "提交中…",
        "form_hint": "工作日 24 小时内回复",
        "form_required_name": "请填写姓名",
        "form_required_contact": "请填写邮箱或电话",
        "form_required_message": "请填写询盘内容",
        "form_success": "提交成功，我们会尽快联系您",
        "form_error": "提交失败，请稍后重试",
        "footer_copyright": "Copyright © {year} {name} 版权所有",
    },
    "en": {
        "loading": "Loading…",
        "site_unavailable": "Site unavailable",
        "nav_home": "Home",
        "nav_products": "Products",
        "nav_solutions": "Solutions",
        "nav_applications": "Applications",
        "nav_about": "About",
        "nav_video": "Video",
        "nav_qa": "Buyer Q&A",
        "nav_contact": "Contact",
        "cta_primary": "Get a Quote",
        "cta_secondary": "Contact Us",
        "stats_eyebrow": "What We Do",
        "stats_title": "Trusted Manufacturing at Scale",
        "section_stages_eyebrow": "Project path",
        "section_stages_title": "Can you take my order at this stage?",
        "section_stages_desc": "RFQ → sample → pilot → volume — structured for how buyers decide.",
        "section_solutions": "Industry Solutions",
        "section_solutions_desc": "Solutions mapped to buyer jobs — not warehouse aisles.",
        "section_knowledge_eyebrow": "Technical content",
        "section_knowledge_title": "Answer search intent before the RFQ",
        "section_knowledge_desc": "Guides that prove spec fluency — then route to inquiry.",
        "section_cta_title": "Ready to start?",
        "section_cta_desc": "Send specs or drawings — we reply with scope and next steps.",
        "section_products": "Products",
        "section_contact": "Contact Us",
        "tel_label": "Tel",
        "email_label": "E-mail",
        "whatsapp_label": "WhatsApp",
        "hero_since": "Since {year}",
        "section_categories": "Product Classification",
        "section_categories_desc": "Professional export product lines",
        "section_products_default": "Our Products",
        "section_products_desc": "Hot products for export inquiry",
        "inquiry_link": "Inquiry →",
        "section_about": "About {name}",
        "mission": "Mission",
        "vision": "Vision",
        "company_history": "Company History",
        "video_center": "Video Center",
        "factory_label": "Factory",
        "footer_quick_links": "Quick Links",
        "footer_contact": "Contact",
        "why_choose_us": "Why Choose Us",
        "applications_title_default": "What Are You Insulating?",
        "tenant_not_found": "Tenant not found",
        "load_failed": "Load failed",
        "contact_wechat_label": "WeChat",
        "contact_qq_label": "QQ",
        "menu_open": "Open menu",
        "menu_close": "Close menu",
        "hero_placeholder_hint": "Professional manufacturing · Export ready",
        "mobile_quick_actions": "Quick contact",
        "form_name": "Your Name",
        "form_email": "Email",
        "form_phone": "Phone / WhatsApp",
        "form_phone_cn": "Mobile",
        "form_product": "Product / Specs",
        "form_message": "Inquiry details",
        "form_submit": "Submit Inquiry",
        "form_submitting": "Submitting…",
        "form_hint": "We reply within 24 hours on business days.",
        "form_required_name": "Please enter your name",
        "form_required_contact": "Please enter email or phone",
        "form_required_message": "Please enter inquiry details",
        "form_success": "Submitted! We will contact you soon.",
        "form_error": "Submission failed. Please try again.",
        "footer_copyright": "Copyright © {year} {name}. All Rights Reserved.",
    },
    "ar": {
        "loading": "جاري التحميل…",
        "site_unavailable": "الموقع غير متاح",
        "nav_home": "الرئيسية",
        "nav_products": "المنتجات",
        "nav_solutions": "الحلول",
        "nav_applications": "التطبيقات",
        "nav_about": "من نحن",
        "nav_video": "فيديو",
        "nav_contact": "اتصل بنا",
        "cta_primary": "طلب عرض سعر",
        "cta_secondary": "تواصل معنا",
        "stats_eyebrow": "ما نقدمه",
        "stats_title": "تصنيع موثوق على نطاق واسع",
        "section_solutions": "حلول صناعية",
        "section_solutions_desc": "حلول عزل شاملة لقطاعات رئيسية",
        "section_products": "المنتجات",
        "section_contact": "اتصل بنا",
        "tel_label": "هاتف",
        "email_label": "بريد",
        "whatsapp_label": "واتساب",
    },
    "es": {
        "loading": "Cargando…",
        "site_unavailable": "Sitio no disponible",
        "nav_home": "Inicio",
        "nav_products": "Productos",
        "nav_solutions": "Soluciones",
        "nav_applications": "Aplicaciones",
        "nav_about": "Nosotros",
        "nav_video": "Video",
        "nav_contact": "Contacto",
        "cta_primary": "Solicitar cotización",
        "cta_secondary": "Contáctenos",
        "stats_eyebrow": "Lo que hacemos",
        "stats_title": "Fabricación confiable a escala",
        "section_solutions": "Soluciones industriales",
        "section_solutions_desc": "Soluciones de aislamiento para sectores clave",
        "section_products": "Productos",
        "section_contact": "Contacto",
        "tel_label": "Tel",
        "email_label": "Correo",
        "whatsapp_label": "WhatsApp",
    },
    "pt": {
        "loading": "Carregando…",
        "site_unavailable": "Site indisponível",
        "nav_home": "Início",
        "nav_products": "Produtos",
        "nav_solutions": "Soluções",
        "nav_applications": "Aplicações",
        "nav_about": "Sobre",
        "nav_video": "Vídeo",
        "nav_contact": "Contato",
        "cta_primary": "Solicitar cotação",
        "cta_secondary": "Fale conosco",
        "stats_eyebrow": "O que fazemos",
        "stats_title": "Fabricação confiável em escala",
        "section_solutions": "Soluções industriais",
        "section_solutions_desc": "Soluções de isolamento para setores-chave",
        "section_products": "Produtos",
        "section_contact": "Contato",
        "tel_label": "Tel",
        "email_label": "E-mail",
        "whatsapp_label": "WhatsApp",
    },
    "ru": {
        "loading": "Загрузка…",
        "site_unavailable": "Сайт недоступен",
        "nav_home": "Главная",
        "nav_products": "Продукция",
        "nav_solutions": "Решения",
        "nav_applications": "Применение",
        "nav_about": "О нас",
        "nav_video": "Видео",
        "nav_contact": "Контакты",
        "cta_primary": "Запросить цену",
        "cta_secondary": "Связаться",
        "stats_eyebrow": "Чем занимаемся",
        "stats_title": "Надёжное производство",
        "section_solutions": "Отраслевые решения",
        "section_solutions_desc": "Комплексные решения по изоляции",
        "section_products": "Продукция",
        "section_contact": "Контакты",
        "tel_label": "Тел",
        "email_label": "Email",
        "whatsapp_label": "WhatsApp",
    },
    "th": {
        "loading": "กำลังโหลด…",
        "site_unavailable": "เว็บไซต์ไม่พร้อมใช้งาน",
        "nav_home": "หน้าแรก",
        "nav_products": "ผลิตภัณฑ์",
        "nav_solutions": "โซลูชัน",
        "nav_applications": "การใช้งาน",
        "nav_about": "เกี่ยวกับเรา",
        "nav_video": "วิดีโอ",
        "nav_contact": "ติดต่อ",
        "cta_primary": "ขอใบเสนอราคา",
        "cta_secondary": "ติดต่อเรา",
        "stats_eyebrow": "สิ่งที่เราทำ",
        "stats_title": "การผลิตที่เชื่อถือได้",
        "section_solutions": "โซลูชันอุตสาหกรรม",
        "section_solutions_desc": "โซลูชันฉนวนกันครบวงจร",
        "section_products": "ผลิตภัณฑ์",
        "section_contact": "ติดต่อ",
        "tel_label": "โทร",
        "email_label": "อีเมล",
        "whatsapp_label": "WhatsApp",
    },
    "vi": {
        "loading": "Đang tải…",
        "site_unavailable": "Trang web không khả dụng",
        "nav_home": "Trang chủ",
        "nav_products": "Sản phẩm",
        "nav_solutions": "Giải pháp",
        "nav_applications": "Ứng dụng",
        "nav_about": "Giới thiệu",
        "nav_video": "Video",
        "nav_contact": "Liên hệ",
        "cta_primary": "Báo giá",
        "cta_secondary": "Liên hệ",
        "stats_eyebrow": "Chúng tôi làm gì",
        "stats_title": "Sản xuất đáng tin cậy",
        "section_solutions": "Giải pháp ngành",
        "section_solutions_desc": "Giải pháp cách nhiệt toàn diện",
        "section_products": "Sản phẩm",
        "section_contact": "Liên hệ",
        "tel_label": "ĐT",
        "email_label": "Email",
        "whatsapp_label": "WhatsApp",
    },
    "id": {
        "loading": "Memuat…",
        "site_unavailable": "Situs tidak tersedia",
        "nav_home": "Beranda",
        "nav_products": "Produk",
        "nav_solutions": "Solusi",
        "nav_applications": "Aplikasi",
        "nav_about": "Tentang",
        "nav_video": "Video",
        "nav_contact": "Kontak",
        "cta_primary": "Minta penawaran",
        "cta_secondary": "Hubungi kami",
        "stats_eyebrow": "Apa yang kami lakukan",
        "stats_title": "Manufaktur terpercaya",
        "section_solutions": "Solusi industri",
        "section_solutions_desc": "Solusi insulasi lengkap",
        "section_products": "Produk",
        "section_contact": "Kontak",
        "tel_label": "Tel",
        "email_label": "Email",
        "whatsapp_label": "WhatsApp",
    },
    "ms": {
        "loading": "Memuatkan…",
        "site_unavailable": "Laman tidak tersedia",
        "nav_home": "Laman Utama",
        "nav_products": "Produk",
        "nav_solutions": "Penyelesaian",
        "nav_applications": "Aplikasi",
        "nav_about": "Tentang",
        "nav_video": "Video",
        "nav_contact": "Hubungi",
        "cta_primary": "Minta sebut harga",
        "cta_secondary": "Hubungi kami",
        "stats_eyebrow": "Apa yang kami buat",
        "stats_title": "Pembuatan yang dipercayai",
        "section_solutions": "Penyelesaian industri",
        "section_solutions_desc": "Penyelesaian penebat menyeluruh",
        "section_products": "Produk",
        "section_contact": "Hubungi",
        "tel_label": "Tel",
        "email_label": "E-mel",
        "whatsapp_label": "WhatsApp",
    },
    "ja": {
        "loading": "読み込み中…",
        "site_unavailable": "サイトを利用できません",
        "nav_home": "ホーム",
        "nav_products": "製品",
        "nav_solutions": "ソリューション",
        "nav_applications": "用途",
        "nav_about": "会社概要",
        "nav_video": "動画",
        "nav_contact": "お問い合わせ",
        "cta_primary": "見積依頼",
        "cta_secondary": "お問い合わせ",
        "stats_eyebrow": "事業内容",
        "stats_title": "信頼できる製造",
        "section_solutions": "業界ソリューション",
        "section_solutions_desc": "主要分野向け断熱ソリューション",
        "section_products": "製品",
        "section_contact": "お問い合わせ",
        "tel_label": "Tel",
        "email_label": "Email",
        "whatsapp_label": "WhatsApp",
    },
    "ko": {
        "loading": "로딩 중…",
        "site_unavailable": "사이트를 사용할 수 없습니다",
        "nav_home": "홈",
        "nav_products": "제품",
        "nav_solutions": "솔루션",
        "nav_applications": "응용",
        "nav_about": "회사 소개",
        "nav_video": "동영상",
        "nav_contact": "문의",
        "cta_primary": "견적 요청",
        "cta_secondary": "문의하기",
        "stats_eyebrow": "사업 영역",
        "stats_title": "신뢰할 수 있는 제조",
        "section_solutions": "산업 솔루션",
        "section_solutions_desc": "주요 분야 단열 솔루션",
        "section_products": "제품",
        "section_contact": "문의",
        "tel_label": "전화",
        "email_label": "이메일",
        "whatsapp_label": "WhatsApp",
    },
}

_JTBD_UI_KEYS = (
    "section_stages_eyebrow",
    "section_stages_title",
    "section_stages_desc",
    "section_knowledge_eyebrow",
    "section_knowledge_title",
    "section_knowledge_desc",
    "section_cta_title",
    "section_cta_desc",
)
_JTBD_EN_PACK = {k: SITE_UI["en"][k] for k in _JTBD_UI_KEYS if k in SITE_UI["en"]}
for _lang, _ui in SITE_UI.items():
    if _lang not in ("zh", "en"):
        for _k, _v in _JTBD_EN_PACK.items():
            _ui.setdefault(_k, _v)

# 旺财挂件 UI（客户站 Trade Q&A 顾问）
WANGCAI_UI: dict[str, dict[str, str]] = {
    "zh": {
        "panel_sub": "出口销售 · 快速回复",
        "tab_contact": "联系",
        "tab_ask": "贸易问答",
        "panel_tip_default": "告知数量、规格与目的港 — 24 小时内回复。",
        "contact_wa_sub": "国际聊天",
        "contact_wechat_sub_copied": "微信号已复制",
        "contact_email_sub": "邮件",
        "contact_call_sub": "电话",
        "contact_form_sub": "完整工厂信息",
        "contact_form_label": "联系表单",
        "close": "关闭",
        "chat_hint": "不确定 HS 编码或出口市场？在此提问 — 20 品类 × 50 国公开数据。",
        "chat_loading": "正在查询贸易数据…",
        "ask_placeholder": "例如：岩棉板适合出口哪些国家？",
        "ask_button": "提问",
        "error_retry": "抱歉，请重试或使用联系表单。",
        "error_network": "网络错误，请使用 WhatsApp 或联系表单。",
        "mascot_aria": "销售助手",
        "bubble_1": "您好！{name} 出口团队 — 需要报价吗？",
        "bubble_2": "问我出口市场与 HS 编码 — 点「贸易问答」。",
        "bubble_3": "点我获取 WhatsApp、微信、邮箱或电话。",
        "bubble_4": "合格项目可申请免费样品与数据表。",
        "bubble_product": "在找 {product}？欢迎咨询！",
        "cn_no_contact": "暂未配置微信/QQ/电话，请通过页面下方联系区块留言。",
    },
    "en": {
        "panel_sub": "Export sales · Quick reply",
        "tab_contact": "Contact",
        "tab_ask": "Trade Q&A",
        "panel_tip_default": "Tell us quantity, specs & destination port — we reply within 24 hours.",
        "contact_wa_sub": "International chat",
        "contact_wechat_sub_copied": "ID copied!",
        "contact_email_sub": "Email",
        "contact_call_sub": "Call",
        "contact_form_sub": "Full factory details",
        "contact_form_label": "Contact form",
        "close": "Close",
        "chat_hint": "Not sure about HS codes or export markets? Ask here — 20 categories × 50 countries.",
        "chat_loading": "Checking trade data…",
        "ask_placeholder": "e.g. Best markets for rock wool?",
        "ask_button": "Ask",
        "error_retry": "Sorry — try again or use the contact form.",
        "error_network": "Network error. Please use WhatsApp or the contact form.",
        "mascot_aria": "sales assistant",
        "bubble_1": "Hi! {name} export team here — need a quotation?",
        "bubble_2": "Ask me export markets & HS codes — tap Trade Q&A.",
        "bubble_3": "Tap for WhatsApp, email or phone.",
        "bubble_4": "Free sample & datasheet for qualified projects.",
        "bubble_product": "Looking for {product}? Ask us!",
    },
}

# 其余语种从 en 复制并翻译关键字段（简化：复用 en 模板 + 覆盖 tab/按钮）
for _lang in ("ar", "es", "pt", "ru", "th", "vi", "id", "ms", "ja", "ko"):
    if _lang not in WANGCAI_UI:
        WANGCAI_UI[_lang] = {**WANGCAI_UI["en"]}

WANGCAI_UI["ar"].update({
    "tab_contact": "تواصل",
    "tab_ask": "أسئلة التجارة",
    "chat_loading": "جاري فحص بيانات التجارة…",
    "ask_button": "اسأل",
    "panel_sub": "مبيعات التصدير · رد سريع",
    "bubble_1": "مرحباً! فريق تصدير {name} — هل تحتاج عرض سعر؟",
    "bubble_2": "اسأل عن أسواق التصدير ورموز HS — اضغط «أسئلة التجارة».",
    "bubble_3": "اضغط للتواصل عبر WhatsApp أو البريد أو الهاتف.",
    "bubble_4": "عينة مجانية وورقة بيانات للمشاريع المؤهلة.",
    "bubble_product": "تبحث عن {product}؟ اسألنا!",
})
WANGCAI_UI["es"].update({
    "tab_contact": "Contacto",
    "tab_ask": "Consultas comerciales",
    "chat_loading": "Consultando datos comerciales…",
    "ask_button": "Preguntar",
    "bubble_1": "¡Hola! Equipo de exportación de {name} — ¿necesita cotización?",
    "bubble_2": "Pregúnteme mercados de exportación y códigos HS — toque Consultas comerciales.",
    "bubble_3": "Toque para WhatsApp, email o teléfono.",
    "bubble_4": "Muestra gratis y ficha técnica para proyectos calificados.",
    "bubble_product": "¿Busca {product}? ¡Consúltenos!",
})
WANGCAI_UI["pt"].update({
    "tab_contact": "Contato",
    "tab_ask": "Perguntas comerciais",
    "chat_loading": "Consultando dados comerciais…",
    "ask_button": "Perguntar",
})
WANGCAI_UI["ru"].update({
    "tab_contact": "Контакты",
    "tab_ask": "Торговые вопросы",
    "chat_loading": "Проверка торговых данных…",
    "ask_button": "Спросить",
})
WANGCAI_UI["th"].update({
    "tab_contact": "ติดต่อ",
    "tab_ask": "คำถามการค้า",
    "chat_loading": "กำลังตรวจสอบข้อมูลการค้า…",
    "ask_button": "ถาม",
})
WANGCAI_UI["vi"].update({
    "tab_contact": "Liên hệ",
    "tab_ask": "Hỏi đáp thương mại",
    "chat_loading": "Đang tra cứu dữ liệu…",
    "ask_button": "Hỏi",
})
WANGCAI_UI["ja"].update({
    "tab_contact": "連絡",
    "tab_ask": "貿易Q&A",
    "chat_loading": "貿易データを確認中…",
    "ask_button": "質問",
    "bubble_1": "こんにちは！{name} 輸出チームです — お見積りはいかがですか？",
    "bubble_2": "輸出市場や HS コードは「貿易Q&A」でご質問ください。",
    "bubble_3": "WhatsApp・メール・電話はこちらをタップ。",
    "bubble_4": "条件を満たす案件には無料サンプルとデータシートを提供。",
    "bubble_product": "{product} をお探しですか？お気軽にどうぞ！",
})
WANGCAI_UI["ko"].update({
    "tab_contact": "문의",
    "tab_ask": "무역 Q&A",
    "chat_loading": "무역 데이터 확인 중…",
    "ask_button": "질문",
    "bubble_1": "안녕하세요! {name} 수출팀입니다 — 견적이 필요하신가요?",
    "bubble_2": "수출 시장·HS 코드는 «무역 Q&A»에서 질문하세요.",
    "bubble_3": "WhatsApp, 이메일, 전화는 여기를 누르세요.",
    "bubble_4": "적격 프로젝트에 무료 샘플·데이터시트 제공.",
    "bubble_product": "{product} 찾으시나요? 문의 주세요!",
})

WANGCAI_DISCLAIMERS: dict[str, str] = {
    "zh": "仅供参考，不构成法律意见；签约前请专业报关/律师确认。",
    "en": "For reference only — not legal advice. Confirm with customs broker or counsel before signing.",
    "ar": "للمرجعية فقط — ليس استشارة قانونية. تأكد مع وسيط جمركي قبل التوقيع.",
    "es": "Solo referencia — no es asesoramiento legal. Confirme con agente aduanal antes de firmar.",
    "pt": "Apenas referência — não é aconselhamento jurídico. Confirme com despachante antes de assinar.",
    "ru": "Только справочно — не юридическая консультация. Уточните у таможенного брокера.",
    "th": "เพื่ออ้างอิงเท่านั้น — ไม่ใช่คำแนะนำทางกฎหมาย",
    "vi": "Chỉ mang tính tham khảo — không phải tư vấn pháp lý.",
    "id": "Hanya referensi — bukan nasihat hukum.",
    "ms": "Untuk rujukan sahaja — bukan nasihat undang-undang.",
    "ja": "参考情報のみ — 法的助言ではありません。",
    "ko": "참고용 — 법률 자문이 아닙니다.",
}

# 中国大陆 IP：仅展示合规国内联系方式（微信 / QQ / 电话）
CN_MAINLAND_CODE = "CN"
CN_COMPLIANT_CHANNELS: frozenset[str] = frozenset({"wechat", "qq", "phone"})
# 境外 IM / 邮箱等在国内不可合规展示
CN_BLOCKED_CHANNELS: frozenset[str] = frozenset({
    "whatsapp", "telegram", "line", "zalo", "email", "form",
    "live_chat", "wecom_inquiry", "douyin_inquiry",
})

# 按国家优先展示的 IM 渠道顺序
_COUNTRY_CHANNEL_ORDER: dict[str, tuple[str, ...]] = {
    "CN": ("wechat", "qq", "phone"),
    "TW": ("line", "wechat", "phone", "email", "whatsapp"),
    "HK": ("whatsapp", "wechat", "phone", "email"),
    "JP": ("line", "email", "phone", "whatsapp", "wechat"),
    "KR": ("phone", "email", "whatsapp", "wechat"),
    "TH": ("line", "phone", "whatsapp", "email", "wechat"),
    "VN": ("zalo", "phone", "whatsapp", "email", "wechat"),
    "RU": ("telegram", "whatsapp", "email", "phone", "wechat"),
    "SA": ("whatsapp", "email", "phone", "telegram", "wechat"),
    "AE": ("whatsapp", "email", "phone", "telegram", "wechat"),
}
_DEFAULT_CHANNEL_ORDER = ("whatsapp", "email", "phone", "wechat", "qq", "telegram", "line")


def wangcai_trade_qa_enabled(country_code: str | None) -> bool:
    """大陆 IP 访客不展示/不提供外贸 Trade Q&A（合规：仅联系渠道）。"""
    return not is_cn_mainland(country_code)


def is_cn_mainland(country_code: str | None) -> bool:
    """is_cn_mainland。

    参数说明：
    :param country_code: 参数 country_code
    :return: 返回处理结果。
    """
    return (country_code or "").strip().upper()[:2] == CN_MAINLAND_CODE


def sanitize_contacts_for_country(
    contacts: dict[str, str],
    country_code: str,
) -> dict[str, str]:
    """中国大陆访客 API 响应中不返回境外 IM 字段。"""
    if not is_cn_mainland(country_code):
        return dict(contacts)
    return {
        k: (contacts.get(k) or "").strip()
        for k in CN_COMPLIANT_CHANNELS
        if (contacts.get(k) or "").strip()
    }


def _is_private_ip(ip: str) -> bool:
    """_is_private_ip。

    参数说明：
    :param ip: 参数 ip
    :return: 返回处理结果。
    """
    ip = (ip or "").strip().lower()
    if not ip or ip == "unknown":
        return True
    for prefix in _PRIVATE_IP_PREFIXES:
        if ip.startswith(prefix):
            return True
    return False


def _parse_accept_language(header: str | None) -> str | None:
    """_parse_accept_language。

    参数说明：
    :param header: 参数 header
    :return: 返回处理结果。
    """
    if not header:
        return None
    first = header.split(",")[0].strip()
    m = re.match(r"([a-zA-Z]{2})", first)
    return m.group(1).lower() if m else None


def country_from_request(
    request: Any,
    *,
    country_override: str | None = None,
) -> str:
    """从 CF-IPCountry / 测试头 / 查询参数解析 ISO 3166-1 alpha-2。"""
    if country_override:
        cc = country_override.strip().upper()[:2]
        if cc and cc != "XX":
            return cc

    headers = getattr(request, "headers", None)
    if headers is not None:
        for key in ("x-visitor-country", "X-Visitor-Country", "cf-ipcountry", "CF-IPCountry"):
            raw = headers.get(key)
            if raw:
                cc = raw.strip().upper()[:2]
                if cc and cc not in ("XX", "T1"):
                    return cc

    from app.core.login_bruteforce import client_ip_from_request
    ip = client_ip_from_request(request)
    if not _is_private_ip(ip):
        # 无 GeoIP 库时非公网 IP 仍走语种推断
        pass

    accept = None
    if headers is not None:
        accept = _parse_accept_language(
            headers.get("accept-language") or headers.get("Accept-Language")
        )
    if accept and accept in _LANG_DEFAULT_COUNTRY:
        return _LANG_DEFAULT_COUNTRY[accept]
    return "US"


def language_from_request(
    request: Any,
    country_code: str,
    *,
    language_override: str | None = None,
) -> str:
    """language_from_request。

    参数说明：
    :param request: 参数 request
    :param country_code: 参数 country_code
    :param language_override: 参数 language_override
    :return: 返回处理结果。
    """
    if language_override:
        return normalize_language(language_override, country_code)
    headers = getattr(request, "headers", None)
    accept = None
    if headers is not None:
        accept = _parse_accept_language(
            headers.get("accept-language") or headers.get("Accept-Language")
        )
    return normalize_language(accept, country_code)


def resolve_visitor_locale(
    request: Any,
    *,
    country_override: str | None = None,
    language_override: str | None = None,
) -> dict[str, str]:
    """resolve_visitor_locale。

    参数说明：
    :param request: 参数 request
    :param country_override: 参数 country_override
    :param language_override: 参数 language_override
    :return: 返回处理结果。
    """
    cc = country_from_request(request, country_override=country_override)
    lang = language_from_request(
        request, cc, language_override=language_override
    )
    return {
        "country_code": cc,
        "language": lang,
        "language_name": SUPPORTED_LANGUAGES.get(lang, lang),
    }


def site_ui_strings(language: str) -> dict[str, str]:
    """site_ui_strings。

    参数说明：
    :param language: 参数 language
    :return: 返回处理结果。
    """
    lang = normalize_language(language, None)
    base = SITE_UI.get("en", {})
    return {**base, **SITE_UI.get(lang, base)}


def wangcai_ui_strings(language: str, country_code: str | None = None) -> dict[str, str]:
    """wangcai_ui_strings。

    参数说明：
    :param language: 参数 language
    :param country_code: 参数 country_code
    :return: 返回处理结果。
    """
    lang = normalize_language(language, None)
    base = WANGCAI_UI.get("en", {})
    ui = {**base, **WANGCAI_UI.get(lang, base)}
    # 大陆合规文案仅在中文字界面；访客显式选英文等外语时气泡须跟随语言
    if is_cn_mainland(country_code) and lang == "zh":
        ui.update({
            "panel_sub": "国内销售 · 快速回复",
            "bubble_2": "需要报价或样品？点我联系微信、QQ 或电话。",
            "bubble_3": "点我获取微信、QQ 或电话。",
            "error_network": "网络错误，请使用微信或电话联系。",
            "contact_qq_sub": "点击复制 QQ 号",
            "contact_qq_sub_copied": "QQ 号已复制",
            "trade_qa_disabled": "贸易问答仅面向海外买家；国内请通过微信、QQ 或电话联系。",
        })
    return ui


def wangcai_disclaimer(language: str) -> str:
    """wangcai_disclaimer。

    参数说明：
    :param language: 参数 language
    :return: 返回处理结果。
    """
    lang = normalize_language(language, None)
    return WANGCAI_DISCLAIMERS.get(lang) or WANGCAI_DISCLAIMERS["en"]


def channel_order_for_country(country_code: str) -> tuple[str, ...]:
    """channel_order_for_country。

    参数说明：
    :param country_code: 参数 country_code
    :return: 返回处理结果。
    """
    cc = (country_code or "").strip().upper()[:2]
    return _COUNTRY_CHANNEL_ORDER.get(cc, _DEFAULT_CHANNEL_ORDER)


def build_visitor_contact_channels(
    contacts: dict[str, str],
    *,
    country_code: str,
    language: str,
) -> list[dict[str, str]]:
    """按 IP 国家排序租户 contact 字段，供旺财 Contact 面板渲染。"""
    lang = normalize_language(language, country_code)
    cc = (country_code or "").strip().upper()[:2]
    cn = is_cn_mainland(cc)
    order = channel_order_for_country(cc)
    seen: set[str] = set()
    items: list[dict[str, str]] = []
    channel_type_map = {
        "whatsapp": "whatsapp",
        "wechat": "wechat",
        "qq": "qq",
        "telegram": "telegram",
        "line": "line",
        "phone": "phone",
        "email": "email",
    }
    for key in order:
        if key in seen:
            continue
        if cn and key not in CN_COMPLIANT_CHANNELS:
            continue
        val = (contacts.get(key) or "").strip()
        if not val:
            continue
        seen.add(key)
        ctype = channel_type_map.get(key, key)
        label = localized_channel_label(ctype, lang) if ctype in (
            "whatsapp", "telegram", "line", "form", "live_chat"
        ) else _extra_channel_label(ctype, lang)
        items.append({
            "channel_type": ctype,
            "value": val,
            "label": label,
            "im_link": _contact_link(ctype, val),
        })

    if not cn:
        for key in IM_FIELD_KEYS:
            if key in seen:
                continue
            val = (contacts.get(key) or "").strip()
            if not val:
                continue
            ctype = channel_type_map.get(key, key)
            label = _extra_channel_label(ctype, lang)
            items.append({
                "channel_type": ctype,
                "value": val,
                "label": label,
                "im_link": _contact_link(ctype, val),
            })
        items.append({
            "channel_type": "form",
            "value": "",
            "label": localized_channel_label("form", lang),
            "im_link": "#contact",
        })
    if lang != "zh":
        items = [x for x in items if x["channel_type"] not in ("wechat", "qq")]
    return items


IM_FIELD_KEYS = ("whatsapp", "wechat", "qq", "telegram", "line", "phone", "email")


def _extra_channel_label(channel_type: str, language: str) -> str:
    """_extra_channel_label。

    参数说明：
    :param channel_type: 参数 channel_type
    :param language: 参数 language
    :return: 返回处理结果。
    """
    lang = normalize_language(language, None)
    labels: dict[str, dict[str, str]] = {
        "wechat": {
            "zh": "微信",
            "en": "WeChat",
            "ja": "WeChat",
            "ko": "WeChat",
        },
        "qq": {
            "zh": "QQ",
            "en": "QQ",
        },
        "phone": {
            "zh": "电话",
            "en": "Call",
            "ar": "اتصال",
            "es": "Llamar",
            "ja": "電話",
            "ko": "전화",
        },
        "email": {
            "zh": "邮箱",
            "en": "Email",
            "ar": "بريد",
            "es": "Correo",
            "ja": "メール",
            "ko": "이메일",
        },
    }
    by_type = labels.get(channel_type, {})
    return by_type.get(lang) or by_type.get("en") or channel_type.title()


def _contact_link(channel_type: str, value: str) -> str:
    """_contact_link。

    参数说明：
    :param channel_type: 参数 channel_type
    :param value: 参数 value
    :return: 返回处理结果。
    """
    if channel_type == "whatsapp":
        n = re.sub(r"\D", "", value)
        return f"https://wa.me/{n}" if n else ""
    if channel_type == "telegram":
        handle = value.lstrip("@")
        return f"https://t.me/{handle}" if handle else ""
    if channel_type == "line":
        return f"https://line.me/ti/p/{value}" if value else ""
    if channel_type == "email":
        return f"mailto:{value}" if value else ""
    if channel_type == "phone":
        return f"tel:{value}" if value else ""
    if channel_type == "wechat":
        return "#"
    if channel_type == "qq":
        digits = re.sub(r"\D", "", value)
        return f"tencent://message/?uin={digits}" if digits else "#"
    return "#contact"
