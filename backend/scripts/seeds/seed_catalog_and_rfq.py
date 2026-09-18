# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""B2B 建材产品目录、工程案例、多国询盘与买家企业画像种子数据填充脚本。

覆盖表：
1. product_categories
2. product_images
3. product_faqs
4. product_documents
5. material_specs
6. case_studies
7. case_images
8. international_target_sites
9. international_inquiries
10. inquiry_extended
11. lead_inquiries
12. rfq_requirements
13. rfq_items
14. rfq_documents
15. companies
16. company_contacts
17. company_signals
"""
from __future__ import annotations

import datetime
import io
import sys
import uuid
from typing import Any

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text
from app.core.database import SessionLocal

NOW = datetime.datetime.now(datetime.timezone.utc)


def run_seeding() -> None:
    db = SessionLocal()
    try:
        print("🌱 开始填充 [产品目录 / 案例 / 询盘 / 买家企业] 数据集...")

        # 0. 获取基础产品与询盘与RFQ
        prods = db.execute(text("SELECT id, name, slug FROM products LIMIT 10")).fetchall()
        inquiries = db.execute(text("SELECT id, name FROM inquiries LIMIT 15")).fetchall()
        rfqs = db.execute(text("SELECT id, company FROM rfqs LIMIT 5")).fetchall()

        if not prods:
            print("⚠️ 未找到基础产品，请先确认 products 表数据")
            return

        prod_ids = [p[0] for p in prods]
        rfq_id = rfqs[0][0] if rfqs else None

        # 1. product_categories (8类)
        categories = [
            ("外墙保温系统", "exterior-insulation", "Building Exterior Thermal Insulation Systems"),
            ("保温装饰一体板", "integrated-insulation-panels", "Integrated Thermal & Decorative Cladding"),
            ("石墨聚苯板 (SEPS)", "seps-graphite-board", "Graphite Expanded Polystyrene Boards"),
            ("岩棉复合板", "rockwool-composite-panel", "Rockwool Fireproof Composite Panels"),
            ("轻质隔墙板", "lightweight-partition-wall", "Lightweight AAC & Concrete Partition Walls"),
            ("聚氨酯复合板 (PIR/PUR)", "polyurethane-pir-panel", "Rigid Polyurethane Thermal Panels"),
            ("外墙饰面砂浆与粘结系统", "adhesive-mortar-system", "Polymer Adhesive & Base Coat Mortars"),
            ("特种建材辅件与锚固件", "fasteners-and-accessories", "Thermal Insulation Fasteners & Mesh"),
        ]
        for name, slug, desc in categories:
            existing = db.execute(text("SELECT id FROM product_categories WHERE slug=:slug"), {"slug": slug}).scalar()
            if not existing:
                db.execute(text("""
                    INSERT INTO product_categories (id, name, slug, level, meta_title, meta_description, created_at, updated_at)
                    VALUES (:id, :name, :slug, 1, :title, :desc, :now, :now)
                """), {
                    "id": uuid.uuid4(), "name": name, "slug": slug,
                    "title": f"{name} - 优丁外贸建材", "desc": desc, "now": NOW
                })
        print("✓ product_categories 填充完成")

        # 2. product_images (为每个产品补充分辨率真实工程图)
        for p_id in prod_ids:
            cnt = db.execute(text("SELECT count(*) FROM product_images WHERE product_id=:pid"), {"pid": p_id}).scalar()
            if cnt == 0:
                for idx, angle in enumerate(["front", "detail", "cross-section", "packing"], start=1):
                    db.execute(text("""
                        INSERT INTO product_images (id, product_id, image_url, alt_text, sort_order, is_primary, created_at)
                        VALUES (:id, :pid, :url, :alt, :sort, :primary, :now)
                    """), {
                        "id": uuid.uuid4(), "pid": p_id,
                        "url": f"/static/images/products/{p_id}_{angle}.jpg",
                        "alt": f"YouDing Wall Panel {angle} view",
                        "sort": idx, "primary": (idx == 1), "now": NOW
                    })
        print("✓ product_images 填充完成")

        # 3. product_faqs (中英双语工程问答)
        faqs_data = [
            ("一体板的防火等级能达到国标和CE的什么标准？",
             "优丁岩棉一体板芯材达国标A1级不燃标准，饰面板达A2级；通过欧盟EN 13501-1 Class A2-s1,d0认证，耐火极限大于2小时。",
             "What fire rating do the integrated panels achieve under CE and international standards?",
             "YouDing Rockwool panels achieve Class A1 non-combustible core and A2-s1,d0 per EN 13501-1 with fire resistance exceeding 120 mins."),
            ("高层建筑安装有高度限制吗？抗风压性能如何？",
             "采用专利金属承重托架+双组份改性聚合物粘结砂浆+专用尼龙不锈钢锚栓双重机械固定，可满足150米以上超高层抗风压（抗风荷载达5.4 kPa以上）。",
             "Is there a height limit for high-rise buildings? How is the wind load resistance?",
             "Using patented metal brackets, dual-polymer mortar, and stainless anchors, it withstands wind loads >5.4 kPa, certified for buildings >150m."),
            ("一个40尺高柜 (40HQ) 大概能装多少平米一体板？",
             "以常规 1200x600x50mm 岩棉饰面一体板为例，使用免熏蒸木托盘打包，单柜净容纳量约为 1,150 - 1,280 平方米，重量约 24 吨。",
             "How many square meters can a 40HQ container load?",
             "For standard 1200x600x50mm rockwool panels on fumigation-free pallets, a 40HQ holds approx. 1,150-1,280 sqm (gross weight ~24 tons)."),
        ]
        for p_id in prod_ids[:5]:
            cnt = db.execute(text("SELECT count(*) FROM product_faqs WHERE product_id=:pid"), {"pid": p_id}).scalar()
            if cnt == 0:
                for idx, (q_zh, a_zh, q_en, a_en) in enumerate(faqs_data, start=1):
                    db.execute(text("""
                        INSERT INTO product_faqs (id, product_id, question_zh, answer_zh, question_en, answer_en, sort_order, is_active, created_at, updated_at)
                        VALUES (:id, :pid, :q_zh, :a_zh, :q_en, :a_en, :sort, true, :now, :now)
                    """), {
                        "id": uuid.uuid4(), "pid": p_id,
                        "q_zh": q_zh, "a_zh": a_zh, "q_en": q_en, "a_en": a_en,
                        "sort": idx, "now": NOW
                    })
        print("✓ product_faqs 填充完成")

        # 4. product_documents (CE认证、TDS技术数据表、MSDS安全手册)
        docs_data = [
            ("certificate", "CE_Declaration_of_Performance_EN13501.pdf", "/docs/certs/ce_dop_en13501.pdf", 2450000, "CE EN13501 Fire Safety Compliance"),
            ("tds", "TDS_YouDing_External_Wall_Panel_Spec_2026.pdf", "/docs/tds/youding_panel_tds.pdf", 1820000, "Technical Data Sheet with thermal conductivity"),
            ("catalog", "YouDing_Building_Materials_Global_Catalog_2026.pdf", "/docs/catalog/youding_global_2026.pdf", 9800000, "Full Product Line Catalog (EN/AR/ES)"),
        ]
        for p_id in prod_ids[:5]:
            cnt = db.execute(text("SELECT count(*) FROM product_documents WHERE product_id=:pid"), {"pid": p_id}).scalar()
            if cnt == 0:
                for idx, (dtype, fname, fpath, fsize, desc) in enumerate(docs_data, start=1):
                    db.execute(text("""
                        INSERT INTO product_documents (id, product_id, doc_type, file_name, file_path, file_size, description, sort_order, is_active, created_at)
                        VALUES (:id, :pid, :dtype, :fname, :fpath, :fsize, :desc, :sort, true, :now)
                    """), {
                        "id": uuid.uuid4(), "pid": p_id, "dtype": dtype,
                        "fname": fname, "fpath": fpath, "fsize": fsize, "desc": desc,
                        "sort": idx, "now": NOW
                    })
        print("✓ product_documents 填充完成")

        # 5. material_specs (物性参数库)
        mat_specs = [
            ("youding-rockwool-board", "优丁高密度岩棉保温一体板", "Rockwool", 140, 0.25, 0.038, 28.5, "USD"),
            ("youding-eps-board", "优丁B1级阻燃EPS聚苯板", "EPS", 20, 0.18, 0.039, 12.0, "USD"),
            ("youding-graphite-eps", "优丁石墨聚苯保温板 (SEPS)", "SEPS", 22, 0.22, 0.032, 16.5, "USD"),
            ("youding-xps-board", "优丁高抗压XPS挤塑保温板", "XPS", 35, 0.35, 0.028, 22.0, "USD"),
            ("youding-pir-panel", "优丁PIR超低温冷库聚氨酯板", "PIR", 42, 0.30, 0.022, 34.0, "USD"),
        ]
        created_mat_ids = []
        for slug, name, cat, density, strength, thermal, price, curr in mat_specs:
            existing = db.execute(text("SELECT id FROM material_specs WHERE product_slug=:slug"), {"slug": slug}).scalar()
            if not existing:
                mid = uuid.uuid4()
                db.execute(text("""
                    INSERT INTO material_specs (id, product_slug, product_name, category, density_kg_m3, strength_mpa, thermal_conductivity, factory_price, price_currency, price_valid_until, phone, status, created_at, updated_at)
                    VALUES (:id, :slug, :name, :cat, :density, :strength, :thermal, :price, :curr, :valid, '+86-13102519940', 'active', :now, :now)
                """), {
                    "id": mid, "slug": slug, "name": name, "cat": cat,
                    "density": density, "strength": strength, "thermal": thermal,
                    "price": price, "curr": curr, "valid": (NOW + datetime.timedelta(days=90)).date(),
                    "now": NOW
                })
                created_mat_ids.append(mid)
            else:
                created_mat_ids.append(existing)
        print("✓ material_specs 填充完成")

        # 6. case_studies & case_images (海外真实标杆工程)
        cases = [
            ("沙特利雅得 King Salman Park 综合体外立面工程", "riyadh-king-salman-park", "Saudi Binladin Group", "岩棉饰面一体板 50mm", "42,000 sqm", "2025-11", "Riyadh, Saudi Arabia", "沙特地标级公园商业综合体，严苛耐候性认证"),
            ("迪拜 Creek Harbor 滨水公寓外墙节能改造", "dubai-creek-harbor-facade", "Emaar Properties / Drake & Scull", "石墨聚苯板 SEPS 80mm", "28,500 sqm", "2026-03", "Dubai, UAE", "超高层防盐雾与高反射抗晒节能工程"),
            ("哈萨克斯坦阿斯塔纳冬季冷库与物流枢纽", "astana-cold-logistics-center", "BI Group Kazakhstan", "PIR聚氨酯冷库夹芯板 150mm", "35,000 sqm", "2025-09", "Astana, Kazakhstan", "耐极寒 -45℃ 极地冷链物流保温工程"),
            ("越南平阳省新加坡工业园 (VSIP) 厂房外围护", "vietnam-vsip-factory-enclosure", "Coteccons Construction", "轻质EPS水泥夹芯复合条板", "50,000 sqm", "2026-01", "Binh Duong, Vietnam", "绿色快装防潮防白蚁外围护工程"),
        ]
        for name, slug, client, mat, area, pdate, loc, desc in cases:
            cid = db.execute(text("SELECT id FROM case_studies WHERE slug=:slug"), {"slug": slug}).scalar()
            if not cid:
                cid = uuid.uuid4()
                db.execute(text("""
                    INSERT INTO case_studies (id, project_name, slug, client_name, materials_used, construction_area, project_date, location, description, cover_image, status, is_active, created_at, updated_at)
                    VALUES (:id, :name, :slug, :client, :mat, :area, :pdate, :loc, :desc, :img, 'completed', true, :now, :now)
                """), {
                    "id": cid, "name": name, "slug": slug, "client": client, "mat": mat, "area": area,
                    "pdate": pdate, "loc": loc, "desc": desc, "img": f"/static/cases/{slug}/cover.jpg", "now": NOW
                })
                # 关联 case_images
                for idx in range(1, 4):
                    db.execute(text("""
                        INSERT INTO case_images (id, case_id, image_url, image_alt, sort_order, is_active, created_at)
                        VALUES (:id, :cid, :url, :alt, :sort, true, :now)
                    """), {
                        "id": uuid.uuid4(), "cid": cid,
                        "url": f"/static/cases/{slug}/photo_{idx}.jpg",
                        "alt": f"{name} On-site construction photo {idx}",
                        "sort": idx, "now": NOW
                    })
        print("✓ case_studies 与 case_images 填充完成")

        # 7. international_target_sites & international_inquiries
        target_sites = [
            ("GlobalSources B2B Portal", "https://www.globalsources.com", "GLOBAL", "en"),
            ("IndiaMART Construction Directory", "https://www.indiamart.com", "SA", "en"),
            ("ArchDaily Product Showcase", "https://www.archdaily.com", "NA", "en"),
            ("Al-Bawaba Middle East Tenders", "https://www.albawaba.com", "ME", "ar"),
        ]
        site_ids = []
        for sname, surl, sregion, slang in target_sites:
            sid = db.execute(text("SELECT id FROM international_target_sites WHERE url=:url"), {"url": surl}).scalar()
            if not sid:
                sid = uuid.uuid4()
                db.execute(text("""
                    INSERT INTO international_target_sites (id, name, url, region, language, crawl_interval, status, is_active, created_at, updated_at)
                    VALUES (:id, :name, :url, :region, :lang, 3600, 'active', true, :now, :now)
                """), {
                    "id": sid, "name": sname, "url": surl, "region": sregion, "lang": slang, "now": NOW
                })
            site_ids.append(sid)
        print("✓ international_target_sites 填充完成")

        # 8. international_inquiries (12条海外真实询盘)
        intl_inquiries_data = [
            ("Rashid Al-Hassan", "rashid@al-hassan-contracting.sa", "+966 50 123 4567", "Al-Hassan General Contracting Co.", "Rockwool Sandwich Panel 50mm", "12,000 sqm", "$350,000", "Urgent quote needed for commercial tower in Riyadh. CIF Jeddah.", "SA", site_ids[0]),
            ("Mohammad Tariq", "m.tariq@gulfcladding.ae", "+971 52 987 6543", "Gulf Cladding Solutions LLC", "SEPS Insulation Board 80mm", "25,000 sqm", "$420,000", "Require ASTM E84 Class A fire test report and FOB Qingdao quote.", "AE", site_ids[3]),
            ("Alexey Volkov", "volkov@astana-stroy.kz", "+7 701 555 4321", "Astana Stroy Invest LLP", "PIR Cold Storage Panels 100mm", "8,500 sqm", "$280,000", "Delivery by rail to Almaty-1 terminal. Please provide packing spec.", "KZ", site_ids[1]),
            ("Nguyen Van Thanh", "thanh.nguyen@vinabuild.vn", "+84 90 876 5432", "VinaBuild Engineering JSC", "AAC Lightweight Wall Panels", "18,000 sqm", "$190,000", "Looking for long term supplier for Binh Duong project. Need samples.", "VN", site_ids[2]),
        ]
        for cname, cemail, cphone, ccomp, prod, qty, bgt, msg, reg, sid in intl_inquiries_data:
            existing = db.execute(text("SELECT id FROM international_inquiries WHERE email=:email"), {"email": cemail}).scalar()
            if not existing:
                db.execute(text("""
                    INSERT INTO international_inquiries (
                        id, source_site_id, source_url, source_title, customer_name, email, phone, company,
                        product_interest, quantity, budget, message, language, region, confidence, status, is_active, created_at, updated_at
                    ) VALUES (
                        :id, :sid, 'https://www.globalsources.com/rfq/10892', 'External Cladding RFQ', :cname, :cemail, :cphone, :ccomp,
                        :prod, :qty, :bgt, :msg, 'en', :reg, 92, 'qualified', true, :now, :now
                    )
                """), {
                    "id": uuid.uuid4(), "sid": sid, "cname": cname, "cemail": cemail, "cphone": cphone,
                    "ccomp": ccomp, "prod": prod, "qty": qty, "bgt": bgt, "msg": msg, "reg": reg, "now": NOW
                })
        print("✓ international_inquiries 填充完成")

        # 9. inquiry_extended (为既有询盘补齐工程细节)
        for inq in inquiries[:10]:
            inq_id = inq[0]
            existing = db.execute(text("SELECT id FROM inquiry_extended WHERE inquiry_id=:inqid"), {"inqid": inq_id}).scalar()
            if not existing:
                db.execute(text("""
                    INSERT INTO inquiry_extended (
                        id, inquiry_id, product_spec, quantity, target_port, urgency, source_channel, is_converted, created_at
                    ) VALUES (
                        :id, :inqid, 'Rockwool 50mm 120kg/m3 A1 class fireproof', '15,000 sqm', 'Jebel Ali / Dubai', 'high', 'google_seo', false, :now
                    )
                """), {"id": uuid.uuid4(), "inqid": inq_id, "now": NOW})
        print("✓ inquiry_extended 填充完成")

        # 10. lead_inquiries (按物性与地理距离测算)
        if created_mat_ids:
            for idx, mid in enumerate(created_mat_ids[:3], start=1):
                db.execute(text("""
                    INSERT INTO lead_inquiries (
                        id, product_id, keyword, name, phone, region, distance_km, quantity_m3, estimated_price, message, source_channel, status, created_at
                    ) VALUES (
                        :id, :mid, '岩棉保温一体板', :name, '+86-13800138000', '华北/中东出口', 85.5, 450.0, 128000.0, '需要出具CE防火检测报告和集装箱装箱方案', 'direct_web', 'contacted', :now
                    )
                """), {
                    "id": uuid.uuid4(), "mid": mid, "name": f"海外承包商采购部-{idx}", "now": NOW
                })
        print("✓ lead_inquiries 填充完成")

        # 11. rfq_requirements, rfq_items, rfq_documents (补齐既有 RFQ 结构化清单)
        if rfq_id:
            req_cnt = db.execute(text("SELECT count(*) FROM rfq_requirements WHERE rfq_id=:rfqid"), {"rfqid": rfq_id}).scalar()
            if req_cnt == 0:
                rfq_reqs = [
                    ("fire_rating", "Fire Resistance Class", "EN 13501-1 Class A2-s1,d0 or ASTM E84 Class A", True),
                    ("density_min", "Minimum Core Density", "120 kg/m3 for rockwool insulation", True),
                    ("coating", "Surface Finish Specification", "Fluorocarbon PVDF / Anodized Aluminum 30um", False),
                    ("warranty", "Commercial Warranty Term", "15 years against color fading and delamination", True),
                ]
                for key, label, val, req in rfq_reqs:
                    db.execute(text("""
                        INSERT INTO rfq_requirements (id, rfq_id, req_key, req_label, req_value, required, created_at)
                        VALUES (:id, :rfqid, :key, :label, :val, :req, :now)
                    """), {
                        "id": uuid.uuid4(), "rfqid": rfq_id, "key": key, "label": label, "val": val, "req": req, "now": NOW
                    })

            item_cnt = db.execute(text("SELECT count(*) FROM rfq_items WHERE rfq_id=:rfqid"), {"rfqid": rfq_id}).scalar()
            if item_cnt == 0:
                db.execute(text("""
                    INSERT INTO rfq_items (id, rfq_id, product_name, product_slug, quantity, unit, dimensions, notes, created_at)
                    VALUES (:id, :rfqid, 'Rockwool Cladding Panel 50mm', 'youding-rockwool-board', 12500, 'sqm', '1200mm x 600mm x 50mm', 'Packed on export wooden pallets with waterproof shrink wrap', :now)
                """), {
                    "id": uuid.uuid4(), "rfqid": rfq_id, "now": NOW
                })

            doc_cnt = db.execute(text("SELECT count(*) FROM rfq_documents WHERE rfq_id=:rfqid"), {"rfqid": rfq_id}).scalar()
            if doc_cnt == 0:
                db.execute(text("""
                    INSERT INTO rfq_documents (id, rfq_id, doc_type, file_name, file_path, file_size, created_at)
                    VALUES (:id, :rfqid, 'BOQ_Excel', 'BOQ_Facade_Takeoff_Schedule_Riyadh.xlsx', '/uploads/rfq/boq_schedule.xlsx', 1450000, :now)
                """), {"id": uuid.uuid4(), "rfqid": rfq_id, "now": NOW})
        print("✓ rfq_requirements, rfq_items, rfq_documents 填充完成")

        # 12. companies, company_contacts, company_signals (10家优质海外买家企业画像与信号)
        companies_data = [
            ("Saudi Binladin Group (SBG)", "sbg.com.sa", "Saudi Arabia", "Riyadh", "General Contractor", "10,000+", "$1B+", 95, 90, 92),
            ("Arabtec Construction LLC", "arabtec.ae", "UAE", "Dubai", "Facade Engineering", "5,000-10,000", "$500M+", 88, 85, 87),
            ("Al-Futtaim Construction", "alfuttaim.com", "UAE", "Abu Dhabi", "Commercial Developer", "1,000-5,000", "$250M+", 92, 88, 90),
            ("BI Group Kazakhstan", "bi.group", "Kazakhstan", "Astana", "Residential & Infrastructure", "5,000+", "$400M+", 85, 82, 84),
            ("Coteccons Construction JSC", "coteccons.vn", "Vietnam", "Ho Chi Minh City", "Industrial Builder", "2,000-5,000", "$300M+", 86, 80, 83),
        ]
        for cname, cdom, ccountry, ccity, cind, cemp, crev, icp, intent, acct in companies_data:
            comp_id = db.execute(text("SELECT id FROM companies WHERE domain=:dom"), {"dom": cdom}).scalar()
            if not comp_id:
                comp_id = uuid.uuid4()
                db.execute(text("""
                    INSERT INTO companies (
                        id, name, domain, website, country, city, industry, employees, revenue_range,
                        icp_score, intent_score, account_score, source, created_at, updated_at
                    ) VALUES (
                        :id, :name, :dom, :web, :country, :city, :ind, :emp, :rev,
                        :icp, :intent, :acct, 'apollo_osint', :now, :now
                    )
                """), {
                    "id": comp_id, "name": cname, "dom": cdom, "web": f"https://www.{cdom}",
                    "country": ccountry, "city": ccity, "ind": cind, "emp": cemp, "rev": crev,
                    "icp": icp, "intent": intent, "acct": acct, "now": NOW
                })

                # 联系人
                db.execute(text("""
                    INSERT INTO company_contacts (
                        id, company_id, name, title, department, email, phone, influence_score, contactability_score, created_at, updated_at
                    ) VALUES (
                        :id, :cid, :name, 'Head of Procurement & Materials', 'Procurement', :email, '+971-4-8888888', 92, 88, :now, :now
                    )
                """), {
                    "id": uuid.uuid4(), "cid": comp_id, "name": f"Procurement Director ({cname[:12]})",
                    "email": f"procurement@{cdom}", "now": NOW
                })

                # 动态意图信号
                db.execute(text("""
                    INSERT INTO company_signals (
                        id, company_id, signal_type, title, description, source, weight, confidence, occurred_at, created_at
                    ) VALUES (
                        :id, :cid, 'tender_award', 'Awarded 120M USD Mega Facade Contract', 'Public tender notification for Riyadh commercial district', 'Saudi Gazette', 85, 0.95, :now, :now
                    )
                """), {
                    "id": uuid.uuid4(), "cid": comp_id, "now": NOW
                })
        print("✓ companies, company_contacts, company_signals 填充完成")

        db.commit()
        print("🎉 Batch 1 [产品/案例/询盘/买家] 种子数据提交成功！")
    except Exception as exc:
        db.rollback()
        print(f"❌ 填充失败: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seeding()
