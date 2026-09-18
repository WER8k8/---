# -*- coding: utf-8 -*-
"""外贸 7 步履约核心表工业级数据注水脚本.

覆盖表：
1. purchase_orders (采购订单)
2. logistics_shipments (物流海运运单)
3. shipping_timeline (航运国别时效阶梯)
4. whatsapp_messages (WhatsApp 外贸多语种对话与双向翻译)
5. contact_events (全渠道触点事件)
6. experience_records (莫比乌斯经验记录)

幂等性保证：基于固定 UUID5 生成主键，重复执行只更新或跳过，不报主键冲突。
"""
from __future__ import annotations

import json
import os
import sys
import io
import uuid
from datetime import datetime, timedelta, timezone

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy import text
from app.core.database import engine

SEED_NAMESPACE = uuid.UUID("a7b8c9d0-1234-5678-9abc-def012345678")


def gen_uuid(key: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, key)


def run_seed() -> None:
    print("🚀 开始执行 [外贸 7 步履约与单证核心数据注水]...")
    now = datetime.now(timezone.utc)

    with engine.connect() as conn:
        # 获取真实有效 tenant_id 与 user_id 作为外键
        tenant_row = conn.execute(text("SELECT id FROM tenants LIMIT 1")).fetchone()
        tenant_id = tenant_row[0] if tenant_row else gen_uuid("default_tenant")

        user_row = conn.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
        merchant_id = user_row[0] if user_row else tenant_id

        order_row = conn.execute(text("SELECT id FROM orders LIMIT 1")).fetchone()
        order_id = order_row[0] if order_row else None

        inquiry_row = conn.execute(text("SELECT id FROM inquiries LIMIT 1")).fetchone()
        inquiry_id = inquiry_row[0] if inquiry_row else None

        # ----------------------------------------------------
        # 1. purchase_orders (15 条真实建材外贸 PO 采购单)
        # ----------------------------------------------------
        po_samples = [
            ("PO-2026-ME-001", "Hebei Dacheng Thermal Insulation Co.", "Rock Wool Board 50mm 120kg/m3 Hydrophobic", 1200, "sqm", 4.85, "USD", "confirmed", now + timedelta(days=20), "FOB Tianjin. SGS Inspection required."),
            ("PO-2026-ME-002", "Hebei Hejian Glass Wool Group", "Glass Wool Blanket with Alum Foil 50mm", 2500, "sqm", 2.30, "USD", "in_production", now + timedelta(days=15), "Packed in vacuum rolls. Destination: Jeddah Port."),
            ("PO-2026-EU-003", "Zibo Ceramic Export Ltd.", "Polished Glazed Porcelain Tiles 600x600mm", 1800, "sqm", 6.50, "USD", "confirmed", now + timedelta(days=25), "CE Certificate standard EN 14411. Hamburg Port."),
            ("PO-2026-EU-004", "Foshan Sanitary Ware Corp.", "Rimless Wall-Hung Ceramic Toilet Suite", 300, "sets", 45.00, "USD", "ready_to_ship", now + timedelta(days=8), "CUPC & CE Certified. 1x40HQ Container."),
            ("PO-2026-US-005", "Shandong Structural Steel Co.", "Galvanized Square Steel Pipe 100x100x4.0mm", 85, "tons", 680.00, "USD", "in_production", now + timedelta(days=30), "ASTM A500 Grade B. Houston Port."),
            ("PO-2026-ME-006", "Langfang Fireproof Materials Co.", "Aluminum Silicate Ceramic Fiber Blanket 1260C", 600, "rolls", 18.50, "USD", "confirmed", now + timedelta(days=18), "Density 128kg/m3. SABER certified for KSA."),
            ("PO-2026-SEA-007", "Tianjin Welded Pipe Works", "Pre-galvanized Round Steel Conduit 20mm", 50, "tons", 620.00, "USD", "completed", now - timedelta(days=5), "BS 4568 Standard. Shipped to Cat Lai, Vietnam."),
            ("PO-2026-ME-008", "Wuxi Color Coated Steel Ltd.", "Prepainted Galvanized Steel Coil (PPGI) 0.5mm", 120, "tons", 740.00, "USD", "confirmed", now + timedelta(days=22), "Ral 9002 White Grey. Dammam Port."),
            ("PO-2026-AF-009", "Tangshan Rebar Industry Co.", "Deformed Steel Bar Grade 60 16mm", 200, "tons", 530.00, "USD", "draft", now + timedelta(days=40), "BS 4449 standard. Mombasa Port."),
            ("PO-2026-EU-010", "Dezhou Composite Material Co.", "Calcium Silicate Board 1200x2400x9mm", 3200, "pcs", 5.20, "USD", "in_production", now + timedelta(days=14), "100% Non-Asbestos. Rotterdam Port."),
            ("PO-2026-ME-011", "Hebei Fastener Manufacturing", "Drywall Screws Bugle Head Phosphate 3.5x25mm", 5000, "boxes", 1.80, "USD", "ready_to_ship", now + timedelta(days=6), "Sharp point, grey phosphate. Dubai Jebel Ali."),
            ("PO-2026-SA-012", "Foshan Mosaic Art Tile", "Swimming Pool Crystal Glass Mosaic 25x25mm", 800, "sqm", 11.20, "USD", "draft", now + timedelta(days=35), "Anti-slip, frost resistant. Santos Port, Brazil."),
            ("PO-2026-ME-013", "Zhengzhou Abrasives Group", "Silicon Carbide Refractory Brick 230x114x65mm", 15000, "pcs", 1.45, "USD", "confirmed", now + timedelta(days=28), "Bulk density 2.6g/cm3. Shuwaikh Port, Kuwait."),
            ("PO-2026-EU-014", "Qingdao Waterproof Membrane Ltd.", "SBS Modified Bitumen Waterproof Membrane 4mm", 1500, "rolls", 21.00, "USD", "in_production", now + timedelta(days=16), "Mineral surface, polyester reinforced. Gdansk."),
            ("PO-2026-AU-015", "Guangzhou Aluminum Profile", "Thermal Break Aluminum Window Extrusions", 40, "tons", 2850.00, "USD", "confirmed", now + timedelta(days=32), "AS 2047 compliant. Sydney Port, Australia."),
        ]

        po_inserted = 0
        first_po_id = None
        for item in po_samples:
            po_no, supp, pdesc, qty, unit, price, curr, stat, eta, notes = item
            pid = gen_uuid(f"po_{po_no}")
            if not first_po_id:
                first_po_id = pid
            res = conn.execute(text("""
                INSERT INTO purchase_orders 
                  (id, tenant_id, order_id, po_number, supplier_name, product_desc, quantity, unit, unit_price, currency, status, eta_date, notes, created_at, updated_at)
                VALUES 
                  (:id, :tenant_id, :order_id, :po_no, :supp, :pdesc, :qty, :unit, :price, :curr, :stat, :eta, :notes, :now, :now)
                ON CONFLICT (po_number) DO UPDATE SET
                  status = EXCLUDED.status,
                  supplier_name = EXCLUDED.supplier_name,
                  updated_at = EXCLUDED.updated_at
            """), {
                "id": pid, "tenant_id": tenant_id, "order_id": order_id, "po_no": po_no,
                "supp": supp, "pdesc": pdesc, "qty": qty, "unit": unit, "price": price,
                "curr": curr, "stat": stat, "eta": eta, "notes": notes, "now": now
            })
            po_inserted += 1
        print(f"  ✓ purchase_orders: 处理 {po_inserted} 条采购订单")

        # ----------------------------------------------------
        # 2. logistics_shipments (15 条真实海运物流提单运单)
        # ----------------------------------------------------
        shipment_samples = [
            ("COSU632891001", "COSCO SHIPPING", "Qingdao, China (CNTAO)", "Jeddah Islamic Port (SAJED)", "in_transit", now - timedelta(days=8), now + timedelta(days=14), None, "1x40HQ COSU9821443, Rock Wool Boards, B/L Original Released"),
            ("MSKU982104002", "MAERSK LINE", "Tianjin Xingang (CNTXG)", "Hamburg Port (DEHAM)", "customs_cleared", now - timedelta(days=22), now + timedelta(days=3), None, "2x40HQ MSKU1209341, Porcelain Tiles, EUR.1 Certificate attached"),
            ("CMAU492817003", "CMA CGM", "Shanghai Port (CNSHA)", "Jebel Ali, Dubai (AEJEA)", "delivered", now - timedelta(days=30), now - timedelta(days=2), now - timedelta(days=2), "1x20GP CMAU7718290, Glass Wool Rolls, Consignee Signed"),
            ("OOCU281903004", "OOCL", "Qingdao, China (CNTAO)", "Rotterdam (NLRTM)", "in_transit", now - timedelta(days=12), now + timedelta(days=16), None, "1x40HQ OOCU8829104, Calcium Silicate Boards, VSL: OOCL POLAND"),
            ("EGLV582910005", "EVERGREEN LINE", "Ningbo Zhoushan (CNNGB)", "Dammam King Abdulaziz (SADMM)", "booking_confirmed", None, now + timedelta(days=28), None, "Space booked on EVER GIVEN V.042W. ETD in 3 days."),
            ("HLCU192830006", "HAPAG-LLOYD", "Tianjin Xingang (CNTXG)", "Houston Port (USHOU)", "in_transit", now - timedelta(days=15), now + timedelta(days=18), None, "Steel square pipes. EPA & MTR Test reports dispatched."),
            ("ONEY883910007", "ONE (Ocean Network Express)", "Qingdao (CNTAO)", "Cat Lai, HCMC (VNCLI)", "delivered", now - timedelta(days=14), now - timedelta(days=3), now - timedelta(days=3), "Pre-galvanized pipes. Telex Release Telex B/L."),
            ("YMLU392811008", "YANG MING", "Shanghai (CNSHA)", "Shuwaikh (KWSHU)", "in_transit", now - timedelta(days=6), now + timedelta(days=19), None, "Refractory Bricks. Commercial Invoice legalised."),
            ("MSKU772819009", "MAERSK LINE", "Qingdao (CNTAO)", "Doha Hamad Port (QAHMD)", "in_transit", now - timedelta(days=10), now + timedelta(days=12), None, "Ceramic Fiber Blankets, Temperature sensors inside container."),
            ("COSU441920010", "COSCO SHIPPING", "Tianjin (CNTXG)", "Mombasa Port (KEMBA)", "booking_confirmed", None, now + timedelta(days=35), None, "Deformed Rebars. Pre-shipment PVOC Inspection booked."),
            ("PILU991823011", "PACIFIC INTERNATIONAL LINES", "Ningbo (CNNGB)", "Alexandria (EGALY)", "in_transit", now - timedelta(days=9), now + timedelta(days=17), None, "Waterproof Bitumen Membrane, Stow away from boiler."),
            ("ZIMU281920012", "ZIM LINE", "Shenzhen Yantian (CNSZX)", "Sydney Port (AUSYD)", "customs_cleared", now - timedelta(days=18), now + timedelta(days=2), None, "Aluminum profiles. Fumigation Certificate certified."),
            ("WHLU102938013", "WAN HAI LINES", "Qingdao (CNTAO)", "Port Klang (MYPKG)", "delivered", now - timedelta(days=16), now - timedelta(days=5), now - timedelta(days=5), "Drywall Screws. Cleared smoothly with Form E."),
            ("SMCU881920014", "MEDITERRANEAN SHIPPING CO (MSC)", "Shanghai (CNSHA)", "Gdansk Port (PLGDN)", "in_transit", now - timedelta(days=14), now + timedelta(days=20), None, "Wall-hung toilet suites. Anti-vibration palletized."),
            ("KMTC992019015", "KMTC LINE", "Tianjin (CNTXG)", "Incheon Port (KRINC)", "delivered", now - timedelta(days=8), now - timedelta(days=2), now - timedelta(days=2), "Glass mosaic tiles. Delivered to warehouse."),
        ]

        ship_inserted = 0
        for item in shipment_samples:
            tno, carrier, orig, dest, stat, ship_at, eta_at, del_at, payload_text = item
            sid = gen_uuid(f"ship_{tno}")
            conn.execute(text("""
                INSERT INTO logistics_shipments
                  (id, tenant_id, order_id, purchase_order_id, tracking_no, carrier, origin_port, dest_port, status, shipped_at, eta_at, delivered_at, payload_json, created_at, updated_at)
                VALUES
                  (:id, :tenant_id, :order_id, :po_id, :tno, :carrier, :orig, :dest, :stat, :shipped_at, :eta_at, :del_at, :payload, :now, :now)
                ON CONFLICT (id) DO UPDATE SET
                  status = EXCLUDED.status,
                  carrier = EXCLUDED.carrier,
                  updated_at = EXCLUDED.updated_at
            """), {
                "id": sid, "tenant_id": tenant_id, "order_id": order_id, "po_id": first_po_id,
                "tno": tno, "carrier": carrier, "orig": orig, "dest": dest, "stat": stat,
                "shipped_at": ship_at, "eta_at": eta_at, "del_at": del_at,
                "payload": json.dumps({"notes": payload_text, "auto_synced": True}),
                "now": now
            })
            ship_inserted += 1
        print(f"  ✓ logistics_shipments: 处理 {ship_inserted} 条海运物流运单")

        # ----------------------------------------------------
        # 3. shipping_timeline (6 国建材海运时效阶梯)
        # ----------------------------------------------------
        timeline_samples = [
            ("SA", "工厂备料与质检", "根据客户技术规格定制，严查密度与防水等级", "7-10天", "进港报关与订舱", "安排集装箱拖车进天津/青岛港，办理出口通关", "3-5天", "SABER绿色通道", "国际海运直航", "中远海运直航阿拉伯海，途径红海航道直达吉达", "18-22天", "清关与内陆派送", "沙特本土清关行换单提货，专车送达利雅得工程现场", "3-4天"),
            ("AE", "外贸订单生产", "自动化生产线加急排期，打托贴英文出口唛头", "5-7天", "装箱报关放行", "装运港青岛，全封闭防潮柜配载", "3天", "迪拜免税清关", "海运直航阿联酋", "直航挂靠杰贝阿里港，实时船期定位跟踪", "16-20天", "提柜入库分发", "阿联酋本地自提或指定仓库配送", "2-3天"),
            ("DE", "CE标准定制制造", "严格执行欧盟EN 14411建筑指令与防火阻燃A级标准", "10-14天", "中欧专线配载", "上海港监管仓拼箱，取得EUR.1原产地证明", "4天", "TUV欧盟认证", "鹿特丹/汉堡远洋航行", "苏伊士运河西行直达汉堡港，船期稳定", "28-32天", "欧盟自由流转派送", "汉堡免税保税区清关，公路卡航直发柏林/慕尼黑", "3-5天"),
            ("US", "美标ASTM合规加工", "按ASTM标准抽检抗拉强度，附第三方质检报告MTR", "12-15天", "集港熏蒸与预申报", "美线ISF 10+2提前申报，免熏蒸胶合板托盘", "4-5天", "FDA/CUPC合规", "太平洋跨洋海运", "美西美东干线大船，经巴拿马运河或直达休斯敦", "22-26天", "美国内陆清关派送", "美国本地报关行即刻申报，安排卡车派送到门", "4-6天"),
            ("VN", "东南亚快速出货", "标准规格常备库存，接单后48小时内调拨集港", "3-5天", "边贸/海运通关", "申请中国-东盟全面经济合作框架协议Form E优惠关税", "2-3天", "Form E零关税", "近洋海运班轮", "深圳/南沙港密集班轮，隔天即可开航", "5-7天", "胡志明清关提货", "卡莱港本地清关，当天提柜送往平阳工业园", "1-2天"),
            ("AU", "澳标AS认证配货", "执行澳洲AS/NZS严格标准，外包装注明生产批次", "8-10天", "装船与全流程熏蒸", "指定出具权威BMSB热处理/熏蒸证明，杜绝生物侵害", "3-4天", "BMSB生物安全证明", "大洋洲南北快线", "直航悉尼/墨尔本港口，中途无转运换船风险", "14-17天", "澳洲码头清关与配送", "澳洲本地边境执法局放行，合规拖车送仓", "2-4天"),
        ]

        tl_inserted = 0
        for item in timeline_samples:
            cc, s1_t, s1_d, s1_days, s2_t, s2_d, s2_days, s2_b, s3_t, s3_d, s3_days, s4_t, s4_d, s4_days = item
            tl_id = gen_uuid(f"timeline_{cc}")
            conn.execute(text("""
                INSERT INTO shipping_timeline
                  (id, merchant_id, country_code, step_1_title, step_1_desc, step_1_days,
                   step_2_title, step_2_desc, step_2_days, step_2_badge,
                   step_3_title, step_3_desc, step_3_days,
                   step_4_title, step_4_desc, step_4_days,
                   is_active, sort_order, created_at, updated_at)
                VALUES
                  (:id, :m_id, :cc, :s1_t, :s1_d, :s1_days,
                   :s2_t, :s2_d, :s2_days, :s2_b,
                   :s3_t, :s3_d, :s3_days,
                   :s4_t, :s4_d, :s4_days,
                   true, 10, :now, :now)
                ON CONFLICT (id) DO UPDATE SET
                  step_1_title = EXCLUDED.step_1_title,
                  step_2_title = EXCLUDED.step_2_title,
                  step_3_title = EXCLUDED.step_3_title,
                  step_4_title = EXCLUDED.step_4_title,
                  updated_at = EXCLUDED.updated_at
            """), {
                "id": tl_id, "m_id": merchant_id, "cc": cc,
                "s1_t": s1_t, "s1_d": s1_d, "s1_days": s1_days,
                "s2_t": s2_t, "s2_d": s2_d, "s2_days": s2_days, "s2_b": s2_b,
                "s3_t": s3_t, "s3_d": s3_d, "s3_days": s3_days,
                "s4_t": s4_t, "s4_d": s4_d, "s4_days": s4_days,
                "now": now
            })
            tl_inserted += 1
        print(f"  ✓ shipping_timeline: 处理 {tl_inserted} 组国别海运时效阶梯")

        # ----------------------------------------------------
        # 4. whatsapp_messages (30 条外贸多语种 WhatsApp 真实对话)
        # ----------------------------------------------------
        wa_dialogues = [
            ("inbound", "مرحبا، أحتاج عرض سعر لـ 1500 متر مربع من ألواح الصوف الصخري 50 مم لمشروع في الرياض.", "Hello, I need a quotation for 1500 sqm of 50mm rock wool boards for a project in Riyadh.", "+966501234567", "delivered"),
            ("outbound", "أهلاً بك! لدينا صوف صخري بكثافة 120 كجم/م3 مطابق لمواصفات سابر (SABER). السعر 4.85 دولار/متر مربع FOB تيانجين. هل ترغب في إرسال عينات مجانية؟", "Welcome! We supply 120kg/m3 rock wool compliant with SABER specs at $4.85/sqm FOB Tianjin. Would you like free samples?", "+966501234567", "read"),
            ("inbound", "نعم من فضلك، أرسل العينات عبر DHL إلى عنوان مكتبنا في السليمانية.", "Yes please, send the samples via DHL to our office address in As Sulimaniyah.", "+966501234567", "delivered"),
            ("outbound", "تم ترتيب إرسال العينات اليوم ورقم التتبع هو DHL 8829103940. أرسلت لك أيضاً الفاتورة المبدئية PI للاطلاع.", "Samples dispatched today via DHL 8829103940. Proforma Invoice (PI) has also been sent for your review.", "+966501234567", "sent"),
            ("inbound", "Guten Tag, wir suchen nach polierten Feinsteinzeugfliesen 60x60cm für ein Hotelprojekt in Hamburg.", "Good day, we are looking for polished porcelain tiles 60x60cm for a hotel project in Hamburg.", "+491701234567", "delivered"),
            ("outbound", "Guten Tag! Wir haben CE-zertifizierte Fliesen nach EN 14411. Mindestbestellmenge ist ein 20-Fuß-Container. Preis: 6,50 USD/m² FOB Qingdao.", "Good day! We offer CE-certified tiles per EN 14411. MOQ is 1x20GP container. Price: $6.50/sqm FOB Qingdao.", "+491701234567", "read"),
            ("inbound", "Können Sie die Seefracht bis Hamburg CIF anbieten und die Verpackungsdetails zusenden?", "Can you offer CIF Hamburg ocean freight and provide packing details?", "+491701234567", "delivered"),
            ("outbound", "CIF Hamburg liegt bei 7,85 USD/m². Jede Kiste fasst 4 Stück (1,44 m²), 40 Kisten pro Palette mit wasserdichter Schrumpffolie.", "CIF Hamburg is $7.85/sqm. Each box holds 4 pcs (1.44 sqm), 40 boxes per pallet with waterproof shrink wrap.", "+491701234567", "sent"),
            ("inbound", "Hello, we are a general contractor in Dubai. Do you have ASTM approved ceramic fiber blankets?", "Hello, we are a general contractor in Dubai. Do you have ASTM approved ceramic fiber blankets?", "+971521234567", "delivered"),
            ("outbound", "Hi! Yes, our 1260C ceramic fiber blankets meet ASTM C892 with bulk density 128kg/m3. 2 rolls per carton. Stock is ready for immediate container loading.", "Hi! Yes, our 1260C ceramic fiber blankets meet ASTM C892 with bulk density 128kg/m3. 2 rolls per carton. Stock is ready for immediate container loading.", "+971521234567", "read"),
            ("inbound", "Great. What is your payment term for the first trial order of 1x40HQ?", "Great. What is your payment term for the first trial order of 1x40HQ?", "+971521234567", "delivered"),
            ("outbound", "Standard term is 30% T/T deposit upon PI confirmation, 70% balance against Copy of Bill of Lading (B/L). We also accept 100% LC at sight.", "Standard term is 30% T/T deposit upon PI confirmation, 70% balance against Copy of Bill of Lading (B/L). We also accept 100% LC at sight.", "+971521234567", "sent"),
            ("inbound", "السلام عليكم، هل لديكم مواسير حديد مجلفنة مربعة 100*100 مم؟", "Peace be upon you, do you have galvanized square steel pipes 100x100mm?", "+966551239876", "delivered"),
            ("outbound", "وعليكم السلام ورحمة الله! نعم متوفرة بسماكة 4 مم و 6 أمتار طول، جلفنة 275 جم/م2. جاهزون للشحن الفوري.", "And peace be upon you! Yes, available in 4mm thickness, 6m length, 275g/m2 galvanizing. Ready for prompt shipment.", "+966551239876", "read"),
            ("inbound", "ممتاز، جهز لي فاتورة أولية لـ 50 طن مع الشحن لميناء الدمام.", "Excellent, please prepare a proforma invoice for 50 tons with freight to Dammam Port.", "+966551239876", "delivered"),
        ]

        # 扩展到 30 条对话
        wa_inserted = 0
        for idx, (direction, msg, trans, phone, stat) in enumerate(wa_dialogues * 2):
            msg_id = gen_uuid(f"wa_msg_{idx}_{phone}")
            conn.execute(text("""
                INSERT INTO whatsapp_messages
                  (id, tenant_id, inquiry_id, lead_id, phone_e164, direction, message_body, template_id, status, external_msg_id, simulated, degraded, error, sent_at, created_at, updated_at)
                VALUES
                  (:id, :tenant_id, :inquiry_id, :lead_id, :phone, :direction, :body, :template_id, :status, :ext_id, false, false, null, :sent_at, :now, :now)
                ON CONFLICT (id) DO UPDATE SET
                  message_body = EXCLUDED.message_body,
                  status = EXCLUDED.status,
                  updated_at = EXCLUDED.updated_at
            """), {
                "id": msg_id, "tenant_id": tenant_id, "inquiry_id": inquiry_id,
                "lead_id": f"lead_ksa_{idx%5 + 1}", "phone": phone, "direction": direction,
                "body": f"{msg} \n[AI Translation: {trans}]",
                "template_id": f"b2b_inquiry_reply_v{idx%3 + 1}",
                "status": stat, "ext_id": f"wamid_HBgM_{uuid.uuid4().hex[:12]}",
                "sent_at": now - timedelta(hours=(30 - idx) * 3), "now": now
            })
            wa_inserted += 1
        print(f"  ✓ whatsapp_messages: 处理 {wa_inserted} 条外贸真实双向对话")

        # ----------------------------------------------------
        # 5. contact_events (20 条全渠道触点事件)
        # ----------------------------------------------------
        channels = ["whatsapp", "email", "inquiry_form", "boq_calculator", "phone"]
        event_types = ["message_received", "quote_viewed", "sample_requested", "pi_downloaded", "payment_notified"]
        ce_inserted = 0
        for i in range(20):
            ce_id = gen_uuid(f"contact_event_{i}")
            ch = channels[i % len(channels)]
            et = event_types[i % len(event_types)]
            conn.execute(text("""
                INSERT INTO contact_events
                  (id, tenant_id, inquiry_id, lead_id, channel, event_type, direction, summary, payload_json, occurred_at, created_at)
                VALUES
                  (:id, :tenant_id, :inquiry_id, :lead_id, :ch, :et, :direction, :summary, :payload, :occurred_at, :now)
                ON CONFLICT (id) DO UPDATE SET
                  summary = EXCLUDED.summary,
                  event_type = EXCLUDED.event_type
            """), {
                "id": ce_id, "tenant_id": tenant_id, "inquiry_id": inquiry_id,
                "lead_id": f"lead_global_{i + 1}", "ch": ch, "et": et,
                "direction": "inbound" if i % 2 == 0 else "outbound",
                "summary": f"海外采购商在渠道 [{ch}] 触发 [{et}] 操作，涉及询价与技术规格核对。",
                "payload": json.dumps({"source_ip": f"194.26.29.{10 + i}", "country": "Saudi Arabia" if i % 2 == 0 else "Germany"}),
                "occurred_at": now - timedelta(hours=i * 5),
                "now": now
            })
            ce_inserted += 1
        print(f"  ✓ contact_events: 处理 {ce_inserted} 笔触点追踪事件")

        # ----------------------------------------------------
        # 6. experience_records (12 条外贸履约经验记录)
        # ----------------------------------------------------
        experiences = [
            ("payment_behavior", "中东大客户信用证处理要点", "沙特及阿联酋客户开具的不可撤销信用证（L/C at sight）需严格核对提单上的通知人（Notify Party）与发票金额大写，杜绝不符点被扣费。", 95.0),
            ("packaging_tip", "绝热保温岩棉板集装箱防潮防挤压装载规程", "岩棉板高密度装箱需使用底部双层胶合板托盘，并在箱门处加装尼龙固定绑带，箱内放置高吸湿氯化钙干燥棒。", 98.5),
            ("customs_clearance", "出口沙特 SABER 系统 PC 与 SC 证书快速出证", "在产品出运前 10 天必须在 SABER 平台完成 PC 产品认证注册，并在海关报关单生成后即刻关联申请 SC 运输放行证书。", 92.0),
            ("price_negotiation", "面对欧美采购商还盘 8% 的组合防御策略", "欧美买家要求降价时，可通过增加 40HQ 整柜装载率分摊单件海运费，或提供阶梯采购量折扣方案，维持基础单价不动摇。", 88.0),
            ("shipping_risk", "红海绕行好望角航线船期延误预案", "苏伊士运河突发事件时船期需增加 10-14 天，必须在 PI 中将交货条款（Incoterms）与交期声明加上不可抗力条款与在途免责。", 91.5),
            ("quality_dispute", "瓷砖外贸色差与吸水率客户异议处理", "发货前寄送留样并由客户签署确认封样（Gold Sample），大货随柜附带第三方检测报告（SGS/BV），避免到港以色差索赔。", 94.0),
        ]

        exp_inserted = 0
        for idx, (etype, title, content, score) in enumerate(experiences * 2):
            exp_id = gen_uuid(f"exp_rec_{idx}")
            conn.execute(text("""
                INSERT INTO experience_records
                  (id, tenant_id, source_type, source_id, experience_type, title, content, score, status, metadata_json, created_at, updated_at)
                VALUES
                  (:id, :tenant_id, 'fulfillment_audit', :source_id, :etype, :title, :content, :score, 'verified', :meta, :now, :now)
                ON CONFLICT (id) DO UPDATE SET
                  title = EXCLUDED.title,
                  content = EXCLUDED.content,
                  score = EXCLUDED.score,
                  updated_at = EXCLUDED.updated_at
            """), {
                "id": exp_id, "tenant_id": tenant_id, "source_id": f"audit_case_{idx + 1}",
                "etype": etype, "title": title, "content": content, "score": score,
                "meta": json.dumps({"tags": ["外贸履约", "风险防范", "建材出海"], "verified_by": "YouDing AI System"}),
                "now": now
            })
            exp_inserted += 1
        print(f"  ✓ experience_records: 处理 {exp_inserted} 条外贸实操经验记录")

        conn.commit()

    print("🎉 [外贸 7 步履约与单证核心数据注水] 执行完毕，全部成功落库！")


if __name__ == "__main__":
    run_seed()
