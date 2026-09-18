# -*- coding: utf-8 -*-
"""出海获客线索、社媒养号与国别准入数据注水脚本.

覆盖表：
1. buyer_prospect_leads (真实海外工程买家线索库)
2. nurture_cycles (出海社媒账号 30 天合规养号周期)
3. social_interactions (社媒建材询盘与 AI 互动跟进)
4. trade_country_category (重点国别建材准入与权威认证档案)

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

SEED_NAMESPACE = uuid.UUID("b8c9d0e1-2345-6789-abcd-ef0123456789")


def gen_uuid(key: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, key)


def run_seed() -> None:
    print("🚀 开始执行 [出海获客线索、社媒养号与国别准入数据注水]...")
    now = datetime.now(timezone.utc)
    naive_now = datetime.now()

    with engine.connect() as conn:
        tenant_row = conn.execute(text("SELECT id FROM tenants LIMIT 1")).fetchone()
        tenant_id = tenant_row[0] if tenant_row else gen_uuid("default_tenant")
        tenant_id_str = str(tenant_id)

        # ----------------------------------------------------
        # 1. buyer_prospect_leads (25 条真实海外买家与工程商线索)
        # ----------------------------------------------------
        buyers = [
            ("中东及海湾地区", "SA", "contractor", "Al-Rashid Trading & Contracting Co. - Procurement Director", 96, "whatsapp", "Active buyer for Riyadh Metro expansion project. Looking for 120kg/m3 rock wool.", "Hi Mr. Al-Rashid, regarding your upcoming commercial project in Riyadh, we supply SABER-certified 50mm rock wool boards.", "qualified", "linkedin_hunter"),
            ("中东及海湾地区", "AE", "wholesaler", "Emaar Allied Building Materials LLC - Senior Sourcing Manager", 94, "whatsapp", "Major distributor in Dubai Industrial City. Distributes 30+ containers per month.", "Dear Sourcing Team, we are a leading manufacturer of CE/ASTM porcelain tiles and fiber blankets with direct shipping to Jebel Ali.", "contacted", "google_maps_lead"),
            ("西欧高端市场", "DE", "engineering_firm", "Hochtief Construction Procurement AG - Material Engineer", 92, "email", "Specialized in energy-saving building renovations in Berlin and Munich.", "Sehr geehrte Damen und Herren, wir bieten EN 13162 konforme Steinwollplatten mit WLG 035 für Ihr Sanierungsprojekt.", "qualified", "kompass_b2b"),
            ("西欧高端市场", "NL", "distributor", "Van Dijk Bouwmaterialen B.V. - Supply Chain Head", 90, "email", "Imports non-asbestos calcium silicate boards for Dutch pre-fab housing.", "Geachte heer Van Dijk, our factory supplies 100% non-asbestos calcium silicate boards with CE certificate.", "contacted", "thomasnet_crawler"),
            ("北美核心市场", "US", "general_contractor", "Turner Construction Partners - Subcontracting Director", 95, "email", "High-rise commercial developer in Texas. Inquiring structural steel pipes.", "Dear Director, our structural square hollow sections meet ASTM A500 Grade B with complete Mill Test Certificates (MTR).", "new", "import_genius_customs"),
            ("东南亚基建区", "VN", "project_developer", "Vingroup Infrastructure Division - Sourcing Lead", 88, "whatsapp", "Hai Phong new residential development project. Demands pre-galvanized round conduits.", "Xin chào, we supply BS 4568 certified steel conduits with Form E zero-tariff preferential origin.", "replied", "accio_osint"),
            ("中东及海湾地区", "KW", "importer", "Alghanim Industries Material Supply - Category Buyer", 91, "whatsapp", "Procuring industrial refractory bricks for oil refinery facility maintenance.", "Hello, we produce 1750C high-alumina refractory bricks with bulk density 2.6g/cm3 for Shuwaikh Port delivery.", "qualified", "tradekey_spider"),
            ("南美成长市场", "BR", "distributor", "Construtora Camargo Building Supply - Head of Imports", 86, "email", "Imports glass mosaics and ceramic tiles for condominium projects in Sao Paulo.", "Prezado Sr., somos fabricantes certificados de pastilhas de vidro e revestimentos cerâmicos para exportação.", "new", "panjiva_customs"),
            ("大洋洲市场", "AU", "fabricator", "Lendlease Facade Engineering Ltd. - Procurement Specialist", 93, "email", "Commercial curtain wall projects across Sydney and Melbourne.", "Dear Specialist, our thermal break aluminum window extrusions comply fully with AS 2047 and AS 1288.", "contacted", "yellowpages_oceania"),
            ("非洲快速增长区", "KE", "wholesaler", "Bamburi Industrial Hardware Nairobi - Managing Director", 85, "whatsapp", "Distributes construction rebar and wire rods in East Africa.", "Hello Sir, we offer Grade 60 deformed steel bars complying with BS 4449 with fast container delivery to Mombasa.", "new", "b2b_kenya_lead"),
            ("中东及海湾地区", "QA", "contractor", "Qatari Diar Construction Group - Sourcing Specialist", 93, "whatsapp", "FIFA legacy commercial projects in Lusail. Needs fireproof ceramic blankets.", "Good day, our high-temp aluminum silicate blankets are certified for Qatar Civil Defense requirements.", "qualified", "doha_chamber_leads"),
            ("东欧重工区", "PL", "wholesaler", "Budimex S.A. Material Purchasing - Import Dept", 89, "email", "Major construction enterprise in Warsaw. Regularly buys SBS bitumen membranes.", "Szanowni Państwo, dostarczamy zgrzewalne papy asfaltowe SBS 4mm z certyfikatem CE dla inwestycji komercyjnych.", "contacted", "eu_tenders_spider"),
        ]

        leads_inserted = 0
        for idx, item in enumerate(buyers * 2 + [buyers[0]]):
            reg, cc, btype, title, score, ch, notes, draft, stat, tool = item
            lead_id = gen_uuid(f"lead_{idx}_{cc}")
            conn.execute(text("""
                INSERT INTO buyer_prospect_leads
                  (id, tenant_id, region_label, country_code, buyer_type, title, fit_score, suggested_channel, notes, outreach_draft, status, source_tool, created_at)
                VALUES
                  (:id, :tenant_id, :reg, :cc, :btype, :title, :score, :ch, :notes, :draft, :stat, :tool, :now)
                ON CONFLICT (id) DO UPDATE SET
                  title = EXCLUDED.title,
                  fit_score = EXCLUDED.fit_score,
                  status = EXCLUDED.status
            """), {
                "id": lead_id, "tenant_id": tenant_id, "reg": reg, "cc": cc, "btype": btype,
                "title": title, "score": score, "ch": ch, "notes": notes, "draft": draft,
                "stat": stat, "tool": tool, "now": now - timedelta(days=idx)
            })
            leads_inserted += 1
        print(f"  ✓ buyer_prospect_leads: 处理 {leads_inserted} 条海外买家工程线索")

        # ----------------------------------------------------
        # 2. nurture_cycles (15 组出海社媒账号养号周期)
        # ----------------------------------------------------
        platforms = ["linkedin", "facebook", "instagram", "tiktok", "youtube"]
        nurture_inserted = 0
        for idx in range(15):
            plat = platforms[idx % len(platforms)]
            nid = gen_uuid(f"nurture_{idx}_{plat}")
            day = (idx * 2) % 30 + 1
            posts = day * 2
            likes = day * 8
            comments = day * 3
            follows = day * 5
            conn.execute(text("""
                INSERT INTO nurture_cycles
                  (id, tenant_id, platform, account_label, platform_account_id, status, rules, current_day, total_posts, total_likes, total_comments, total_follows, last_post_at, last_like_at, last_comment_at, last_follow_at, warning_count, cooldown_until, notes, started_at, updated_at, created_at)
                VALUES
                  (:id, :tenant_id, :plat, :label, null, :status, :rules, :day, :posts, :likes, :comments, :follows, :l_post, :l_like, :l_comment, :l_follow, 0, null, :notes, :started_at, :now, :now)
                ON CONFLICT (id) DO UPDATE SET
                  current_day = EXCLUDED.current_day,
                  total_posts = EXCLUDED.total_posts,
                  total_likes = EXCLUDED.total_likes,
                  status = EXCLUDED.status,
                  updated_at = EXCLUDED.updated_at
            """), {
                "id": nid, "tenant_id": tenant_id_str, "plat": plat,
                "label": f"出海主账号-{plat.upper()}-Slot#{idx + 1}",
                "status": "in_progress" if day < 28 else "matured",
                "rules": json.dumps({"max_posts_per_day": 3, "nurture_goal": "b2b_building_materials", "geo_targeting": ["MiddleEast", "Europe", "NorthAmerica"]}),
                "day": day, "posts": posts, "likes": likes, "comments": comments, "follows": follows,
                "l_post": now - timedelta(hours=4),
                "l_like": now - timedelta(hours=1),
                "l_comment": now - timedelta(hours=2),
                "l_follow": now - timedelta(hours=3),
                "notes": f"第 {day} 天外贸养号中，模拟建材采购商搜索行为与专业群组互动。",
                "started_at": now - timedelta(days=day),
                "now": now
            })
            nurture_inserted += 1
        print(f"  ✓ nurture_cycles: 处理 {nurture_inserted} 组出海社媒养号矩阵")

        # ----------------------------------------------------
        # 3. social_interactions (20 条真实社媒询盘与 AI 互动跟进)
        # ----------------------------------------------------
        social_samples = [
            ("linkedin", "inquiry_comment", "David Miller", "david_miller_builder", "What is the fire rating class for your 50mm rock wool panels? Do you ship to Long Beach?", "price_inquiry", "Hi David! Our panels achieve Class A1 Non-combustible per ASTM E84 / EN 13501-1. We have regular container shipments to Long Beach Port with 20-day transit. Sending you technical data sheet via DM!"),
            ("facebook", "direct_message", "Ahmed Al-Mansoor", "ahmed_mansoor_ksa", "Can you send the SABER certificate and catalog for glazed porcelain floor tiles?", "sample_request", "Marhaban Ahmed! Our tiles are fully registered on SABER with approved PC certificates. Please find our 2026 digital catalog and certificate copy attached!"),
            ("instagram", "post_comment", "Sophie Dubois", "sophie_arch_paris", "Beautiful texture! Are these ceramic fiber blankets resistant to 1260 degrees Celsius continuous working temp?", "technical_consult", "Merci Sophie! Yes, our refractory blankets maintain continuous thermal stability up to 1260°C with low shrinkage under 3%. Free sample box available for your design studio!"),
            ("tiktok", "video_comment", "Carlos Rodriguez", "carlos_rebar_mx", "What is the minimum order quantity for galvanized square pipes? Can you mix sizes in one 40HQ?", "moq_inquiry", "Hola Carlos! Yes, we allow up to 4 different wall thickness sizes mixed in one 40HQ container (approx 26-28 metric tons). FOB Tianjin is available!"),
            ("youtube", "video_comment", "Johan Schmidt", "schmidt_bau_de", "Is the calcium silicate board 100% free of asbestos? We need German lab test proof.", "compliance_inquiry", "Guten Tag Johan! Absolutely 100% non-asbestos, certified by TUV Rheinland and CE testing. We will email the full third-party test report to your team."),
        ]

        social_inserted = 0
        for idx in range(20):
            plat, itype, author, a_id, content, intent, draft_reply = social_samples[idx % len(social_samples)]
            si_id = gen_uuid(f"social_interact_{idx}")
            conn.execute(text("""
                INSERT INTO social_interactions
                  (id, tenant_id, platform, interaction_type, platform_post_id, platform_comment_id, author_name, author_platform_id, content, intent, status, draft_reply, final_reply, platform_send_receipt, inquiry_id, error_code, error_message, created_at, updated_at)
                VALUES
                  (:id, :tenant_id, :plat, :itype, :post_id, :comment_id, :author, :a_id, :content, :intent, 'replied', :draft, :final, :receipt, null, null, null, :now, :now)
                ON CONFLICT (id) DO UPDATE SET
                  content = EXCLUDED.content,
                  draft_reply = EXCLUDED.draft_reply,
                  updated_at = EXCLUDED.updated_at
            """), {
                "id": si_id, "tenant_id": tenant_id_str, "plat": plat, "itype": itype,
                "post_id": f"post_b2b_{1000 + idx}", "comment_id": f"comment_{2000 + idx}",
                "author": f"{author} #{idx + 1}", "a_id": f"{a_id}_{idx + 1}",
                "content": content, "intent": intent, "draft": draft_reply, "final": draft_reply,
                "receipt": json.dumps({"status": "sent", "api_timestamp": int(now.timestamp())}),
                "now": naive_now - timedelta(hours=idx * 3)
            })
            social_inserted += 1
        print(f"  ✓ social_interactions: 处理 {social_inserted} 笔社媒询盘互动")

        # ----------------------------------------------------
        # 4. trade_country_category (12 组重点国别准入与权威资质档案)
        # ----------------------------------------------------
        regulations = [
            ("thermal_insulation", "绝热节能保温建材", "68", "SA", "high_potential", "18.5%", "medium", ["SABER PC/SC Certification", "SASO Fire Safety Standard", "Civil Defense Approval"], "沙特红海及NEOM新城对A级防火岩棉需求巨大，强制要求SABER注册与出厂抽检。"),
            ("ceramic_tiles", "精工陶瓷与卫浴", "69", "SA", "medium_high", "12.0%", "high", ["SASO 2623 Standard", "Water Efficiency Label", "SABER Registration"], "需随附沙特水效标签认证，严查外包装阿英文双语商品标签。"),
            ("thermal_insulation", "绝热节能保温建材", "68", "DE", "high_potential", "14.2%", "medium", ["CE Mark EN 13162", "DoP (Declaration of Performance)", "REACH Compliance"], "德国建筑节能法规（GEG）要求严格传导系数Lambda值（<=0.035 W/mK），CE认证为硬门槛。"),
            ("structural_steel", "工程结构钢管及型材", "73", "US", "medium", "8.5%", "high", ["ASTM A500 / A53", "Mill Test Certificate (MTR)", "Buy America Exemption"], "美线要求提供完整炉号与热处理记录，清关注意反倾销与232条款税率。"),
            ("ceramic_fiber", "特种高温耐火纤维", "68", "AE", "high_potential", "16.0%", "low", ["Dubai Civil Defense (DCD)", "Abu Dhabi Quality Conformity (QCC)", "ASTM C892"], "迪拜高层建筑强制要求DCD准入证书，中东工业炉配套消耗量稳定。"),
            ("calcium_silicate", "无石棉硅酸钙板", "68", "NL", "high_potential", "11.0%", "low", ["100% Asbestos-Free Lab Report", "EN 12467 Category A", "CE Marking"], "荷兰装配式建筑首选基板，海关重点核验第三方权威机构出具的无石棉检测报告。"),
            ("electrical_conduit", "镀锌穿线金属导管", "73", "VN", "high_potential", "22.0%", "medium", ["BS 4568 Class 4", "Form E Origin Certificate", "Quatest 3 Lab Report"], "东南亚基建热潮拉动穿线管需求，Form E关税直降为零，性价比优势显著。"),
            ("waterproof_membrane", "SBS改性沥青防水卷材", "68", "PL", "medium_high", "9.5%", "medium", ["CE Mark EN 13707", "Cold Flexibility -20C", "ITB Technical Approval"], "波兰及东欧地区对冬季耐低温柔度要求高（-20℃无裂纹），随柜提供DoP声明。"),
            ("fasteners_screws", "干壁钉与自攻螺丝", "73", "KW", "high_potential", "15.0%", "low", ["ISO 898-1", "KOWS Kuwait Quality Mark", "Salt Spray Test 48h"], "中东室内隔墙装修消耗品，盐雾测试48小时无红锈，灰色磷化处理最受欢迎。"),
            ("aluminum_profiles", "断桥隔热铝型材", "76", "AU", "medium_high", "7.8%", "high", ["AS/NZS 1866", "AS 2047 Window Compliance", "BMSB Fumigation Treatment"], "澳洲对热处理及BMSB生物安全要求严苛，离港前必须执行指定机构熏蒸。"),
            ("glass_mosaic", "水晶艺术玻璃马赛克", "70", "BR", "medium", "10.5%", "medium", ["ABNT NBR 13818", "Anti-Slip Test DIN 51097", "Fumigation Certificate"], "南美高端泳池及酒店装潢需求回暖，强调防滑等级与耐酸碱测试。"),
            ("refractory_materials", "碳化硅特种耐火砖", "69", "QA", "high_potential", "13.0%", "low", ["ASTM C27", "Alumina Content >75%", "Qatar Petroleum Vendor Listed"], "石化及炼钢工业窑炉备品，高铝含量与抗热震性能为关键中标指标。"),
        ]

        reg_inserted = 0
        for item in regulations:
            ckey, clabel, hs, cc, verd, grow, comp, certs, notes = item
            reg_id = gen_uuid(f"reg_{ckey}_{cc}")
            conn.execute(text("""
                INSERT INTO trade_country_category
                  (id, category_key, category_label, hs_chapter, country_code, verdict, growth, competition, certs_json, notes, is_active, created_at, updated_at)
                VALUES
                  (:id, :ckey, :clabel, :hs, :cc, :verd, :grow, :comp, :certs, :notes, true, :now, :now)
                ON CONFLICT (id) DO UPDATE SET
                  category_label = EXCLUDED.category_label,
                  verdict = EXCLUDED.verdict,
                  certs_json = EXCLUDED.certs_json,
                  notes = EXCLUDED.notes,
                  updated_at = EXCLUDED.updated_at
            """), {
                "id": reg_id, "ckey": ckey, "clabel": clabel, "hs": hs, "cc": cc,
                "verd": verd, "grow": grow, "comp": comp, "certs": json.dumps(certs),
                "notes": notes, "now": now
            })
            reg_inserted += 1
        print(f"  ✓ trade_country_category: 处理 {reg_inserted} 组国别建材准入与资质认证档案")

        conn.commit()

    print("🎉 [出海获客线索、社媒养号与国别准入数据注水] 执行完毕，全部成功落库！")


if __name__ == "__main__":
    run_seed()
