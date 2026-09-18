# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""B2B 内容工厂、SEO/EEAT权威信号、多语术语表与媒体分发流水种子数据填充脚本。

覆盖表：
1. provinces, cities, districts
2. combinatorial_rules, content_templates
3. industry_keywords, keyword_groups, group_keywords
4. generated_keywords, generated_contents
5. content_versions, content_chunks, content_feedback_checks
6. glossary_terms, industry_insights, industry_patterns
7. news_categories, news_articles
8. eeat_authors, eeat_author_certifications, eeat_article_authors, eeat_scores, eeat_trust_signals
9. schema_templates, schema_markups
10. seo_metadata, seo_competitors, serp_snapshots, keyword_rankings, keyword_ranking_history
11. media_render_tasks, publish_tasks, publish_logs, scheduled_publishes
"""
from __future__ import annotations

import datetime
import io
import json
import sys
import uuid

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text
from app.core.database import SessionLocal

NOW = datetime.datetime.now(datetime.timezone.utc)


def run_seeding() -> None:
    db = SessionLocal()
    try:
        print("🌱 开始填充 [内容 / SEO / EEAT / 术语 / 媒体分发] 数据集...")

        # 0. 获取关联数据
        pages = db.execute(text("SELECT id, title, slug FROM content_pages LIMIT 10")).fetchall()
        materials = db.execute(text("SELECT id, product_slug, product_name FROM material_specs LIMIT 5")).fetchall()
        users = db.execute(text("SELECT id, username FROM users LIMIT 5")).fetchall()
        tenants = db.execute(text("SELECT id, name FROM tenants LIMIT 5")).fetchall()
        platforms = db.execute(text("SELECT id, name FROM platforms LIMIT 5")).fetchall()
        accounts = db.execute(text("SELECT id, account_name FROM platform_accounts LIMIT 5")).fetchall()

        t_id = tenants[0][0] if tenants else None
        u_id = users[0][0] if users else None
        p_id = pages[0][0] if pages else None
        mat_id = materials[0][0] if materials else None
        plat_id = platforms[0][0] if platforms else None
        acc_id = accounts[0][0] if accounts else None

        # 1. provinces, cities, districts
        prov_id = uuid.uuid4()
        city_id = uuid.uuid4()
        dist_id = uuid.uuid4()

        db.execute(text("""
            INSERT INTO provinces (id, code, name, name_en, is_active, created_at, updated_at)
            VALUES (:id, 'HEBEI', '河北省', 'Hebei Province', true, :now, :now)
        """), {"id": prov_id, "now": NOW})

        db.execute(text("""
            INSERT INTO cities (id, code, name, name_en, province_id, is_active, created_at, updated_at)
            VALUES (:id, 'SJZ', '石家庄市', 'Shijiazhuang', :pid, true, :now, :now)
        """), {"id": city_id, "pid": prov_id, "now": NOW})

        db.execute(text("""
            INSERT INTO districts (id, code, name, name_en, city_id, province_id, is_active, is_disabled, created_at, updated_at)
            VALUES (:id, 'ZD', '正定县', 'Zhengding County', :cid, :pid, true, false, :now, :now)
        """), {"id": dist_id, "cid": city_id, "pid": prov_id, "now": NOW})
        print("✓ provinces, cities, districts 填充完成")

        # 2. combinatorial_rules, content_templates
        rule_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO combinatorial_rules (id, name, template, description, is_active, priority, created_at, updated_at)
            VALUES (:id, 'Geo行业词长尾组合', '{district}{industry_keyword}批发厂家定制', '地区+核心产品长尾挖掘规则', true, 10, :now, :now)
        """), {"id": rule_id, "now": NOW})

        tpl_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO content_templates (id, name, description, template_type, content, variables, is_active, priority, created_at, updated_at)
            VALUES (:id, 'B2B外贸产品着陆页EEAT模板', '含技术规格表与CE认证说明的标准落地页', 'landing_page', '<h1>{title}</h1><p>{description}</p><div class=\"specs\">{specs}</div>', '["title", "description", "specs"]', true, 1, :now, :now)
        """), {"id": tpl_id, "now": NOW})
        print("✓ combinatorial_rules, content_templates 填充完成")

        # 3. industry_keywords, keyword_groups, group_keywords
        ind_kw_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO industry_keywords (id, keyword, keyword_type, search_volume, difficulty, is_active, category, created_at, updated_at)
            VALUES (:id, 'rockwool insulation panel', 'core_product', 18500, 42.5, true, 'Insulation', :now, :now)
        """), {"id": ind_kw_id, "now": NOW})

        kw_group_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO keyword_groups (id, name, description, is_active, created_at, updated_at)
            VALUES (:id, '中东沙特利雅得高转化外贸词群', '精准覆盖GCC幕墙与保温招标高意向搜索词', true, :now, :now)
        """), {"id": kw_group_id, "now": NOW})

        db.execute(text("""
            INSERT INTO group_keywords (id, group_id, keyword_id, created_at)
            VALUES (:id, :gid, :kid, :now)
        """), {"id": uuid.uuid4(), "gid": kw_group_id, "kid": ind_kw_id, "now": NOW})
        print("✓ industry_keywords, keyword_groups, group_keywords 填充完成")

        # 4. generated_keywords, generated_contents
        gen_kw_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO generated_keywords (id, keyword, district_id, industry_keyword_id, rule_id, search_volume, difficulty, is_valid, is_used, created_at)
            VALUES (:id, '正定岩棉保温板批发厂家定制', :did, :ikid, :rid, 1200, 28.0, true, true, :now)
        """), {"id": gen_kw_id, "did": dist_id, "ikid": ind_kw_id, "rid": rule_id, "now": NOW})

        gen_content_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO generated_contents (id, title, content, district_id, keyword_id, template_id, status, is_used, created_at, updated_at)
            VALUES (:id, '正定岩棉保温板生产厂家 - 优丁外贸工厂直供', '优丁建材正定制造基地，拥有全自动连续复合板生产线，年产能超过300万平米...', :did, :gkid, :tid, 'published', true, :now, :now)
        """), {"id": gen_content_id, "did": dist_id, "gkid": gen_kw_id, "tid": tpl_id, "now": NOW})
        print("✓ generated_keywords, generated_contents 填充完成")

        # 5. content_versions, content_chunks, content_feedback_checks
        if p_id:
            db.execute(text("""
                INSERT INTO content_versions (id, page_id, version_number, title, content, summary, change_log, author_id, created_at)
                VALUES (:id, :pid, 2, '外墙外保温复合一体板技术规格与施工工法 (V2.0)', '本文详细阐述双组份聚合物砂浆粘结锚固法与干挂法...', '新增CE A2级防火极限参数', 'Updated fire rating certifications', :uid, :now)
            """), {"id": uuid.uuid4(), "pid": p_id, "uid": u_id, "now": NOW})

        db.execute(text("""
            INSERT INTO content_chunks (id, product_id, keyword, intent, chunk_type, title, content, rag_score, quality_status, version, created_at, updated_at)
            VALUES (:id, :mid, 'rockwool fire resistance', 'informational', 'tech_spec', 'Fire Classification per EN 13501-1', 'YouDing rockwool core materials achieve Class A1 non-combustible rating with zero flame spread.', 0.96, 'verified', 1, :now, :now)
        """), {"id": uuid.uuid4(), "mid": mat_id, "now": NOW})

        db.execute(text("""
            INSERT INTO content_feedback_checks (id, content_id, publish_url, platform, keyword, status, check_at, is_indexed, rank_position, created_at, updated_at)
            VALUES (:id, :cid, 'https://youding-materials.com/products/rockwool-board', 'google', 'rockwool insulation board supplier', 'completed', :now, true, 4, :now, :now)
        """), {"id": uuid.uuid4(), "cid": gen_content_id, "now": NOW})
        print("✓ content_versions, content_chunks, content_feedback_checks 填充完成")

        # 6. glossary_terms, industry_insights, industry_patterns
        db.execute(text("""
            INSERT INTO glossary_terms (id, zh, en, ar, ru, category, status, is_active, created_at, updated_at)
            VALUES (:id, '保温装饰一体板', 'Integrated Thermal Insulation and Decorative Cladding Panel', 'لوحة عازلة للحرارة وديكورية متكاملة', 'Теплоизоляционная декоративная панель', 'exterior_wall', 'published', true, :now, :now)
        """), {"id": uuid.uuid4(), "now": NOW})

        db.execute(text("""
            INSERT INTO industry_insights (industry, pattern_type, pattern_data, success_score, sample_count, created_at, updated_at)
            VALUES ('building_materials', 'rfq_conversion', '{\"top_factor\": \"CE_test_report\", \"response_speed_hrs\": 2.5}', 0.88, 142, :now, :now)
        """), {"now": NOW})

        db.execute(text("""
            INSERT INTO industry_patterns (id, content_id, publish_url, platform, pattern_type, rank_position, details, created_at, updated_at)
            VALUES (:id, :cid, 'https://youding-materials.com/article/riyadh-facade-specs', 'google', 'eeat_authority', 3, '{\"factors\": [\"case_study_evidence\", \"astm_data\"]}', :now, :now)
        """), {"id": uuid.uuid4(), "cid": gen_content_id, "now": NOW})
        print("✓ glossary_terms, industry_insights, industry_patterns 填充完成")

        # 7. news_categories, news_articles
        ncat_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO news_categories (id, name, slug, description, sort_order, is_active, created_at)
            VALUES (:id, '海外工程动态', 'overseas-projects', '中东、东南亚、中亚重点建材项目追踪', 1, true, :now)
        """), {"id": ncat_id, "now": NOW})

        art_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO news_articles (id, title, slug, summary, content, category, author, is_published, published_at, is_active, created_at, updated_at)
            VALUES (:id, '优丁新型石墨聚苯一体板批量交付沙特利雅得商业中心', 'youding-seps-riyadh-delivery', '首批42,000平米高耐候一体板经天津港启运吉达港...', '详细工程交付记录与耐候测试...', 'overseas-projects', '优丁外贸海外部', true, :now, true, :now, :now)
        """), {"id": art_id, "now": NOW})
        print("✓ news_categories, news_articles 填充完成")

        # 8. eeat_authors, eeat_author_certifications, eeat_article_authors, eeat_scores, eeat_trust_signals
        author_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO eeat_authors (id, name, title, company, bio, expertise_areas, is_verified, trust_score, created_at, updated_at)
            VALUES (:id, 'Dr. Robert Vance, PE', 'Senior Facade & Thermal Engineering Consultant', 'International Cladding Consultants Ltd', '25+ years experience in building thermal envelope and ASTM/EN standard compliance.', '[\"Thermal Insulation\", \"Fire Safety EN13501\", \"Wind Load Analysis\"]', true, 94.5, :now, :now)
        """), {"id": author_id, "now": NOW})

        db.execute(text("""
            INSERT INTO eeat_author_certifications (id, author_id, certification_name, issuing_body, credential_number, is_valid, created_at)
            VALUES (:id, :aid, 'Certified Facade Engineer (CFE)', 'International Institute of Building Enclosure Consultants (IIBEC)', 'IIBEC-2018-8832', true, :now)
        """), {"id": uuid.uuid4(), "aid": author_id, "now": NOW})

        db.execute(text("""
            INSERT INTO eeat_article_authors (id, article_id, author_id, author_type, role, created_at)
            VALUES (:id, :art_id, :aid, 'expert_reviewer', 'Lead Technical Reviewer', :now)
        """), {"id": uuid.uuid4(), "art_id": str(art_id), "aid": author_id, "now": NOW})

        db.execute(text("""
            INSERT INTO eeat_scores (id, content_id, content_type, experience_score, expertise_score, authoritativeness_score, trustworthiness_score, overall_score, evaluated_at)
            VALUES (:id, :cid, 'article', 92.0, 95.0, 91.5, 96.0, 93.6, :now)
        """), {"id": uuid.uuid4(), "cid": str(art_id), "now": NOW})

        db.execute(text("""
            INSERT INTO eeat_trust_signals (id, content_id, signal_type, signal_value, score_impact, is_positive, created_at)
            VALUES (:id, :cid, 'third_party_lab_test', 'SGS Report No. GZMR26090012', 4.5, true, :now)
        """), {"id": uuid.uuid4(), "cid": str(art_id), "now": NOW})
        print("✓ eeat_authors, certifications, articles, scores, signals 填充完成")

        # 9. schema_templates, schema_markups
        db.execute(text("""
            INSERT INTO schema_templates (id, name, schema_type, template, description, is_active, created_at)
            VALUES (:id, 'B2B Product Schema LD+JSON', 'Product', '{\"@context\": \"https://schema.org\", \"@type\": \"Product\", \"name\": \"{{product_name}}\", \"brand\": \"YouDing\"}', 'Google SERP Product Rich Snippet', true, :now)
        """), {"id": uuid.uuid4(), "now": NOW})

        db.execute(text("""
            INSERT INTO schema_markups (id, name, schema_type, content, is_active, page_url, created_at, updated_at)
            VALUES (:id, 'Rockwool Board Rich Snippet', 'Product', '{\"@context\": \"https://schema.org\", \"@type\": \"Product\", \"name\": \"YouDing Rockwool Thermal Panel\"}', true, '/products/youding-rockwool-board', :now, :now)
        """), {"id": uuid.uuid4(), "now": NOW})
        print("✓ schema_templates, schema_markups 填充完成")

        # 10. seo_metadata, seo_competitors, serp_snapshots, keyword_rankings, keyword_ranking_history
        db.execute(text("""
            INSERT INTO seo_metadata (id, resource_type, resource_id, meta_title, meta_description, meta_keywords, canonical_url, noindex, created_at, updated_at)
            VALUES (:id, 'product', 'youding-rockwool-board', 'Rockwool Insulation Board Manufacturer | YouDing Factory Direct', 'High density A1 fireproof rockwool decorative wall panels from certified Chinese manufacturer. Fast export shipping to Middle East.', 'rockwool board, external wall insulation, fireproof cladding', 'https://youding-materials.com/products/youding-rockwool-board', false, :now, :now)
        """), {"id": uuid.uuid4(), "now": NOW})

        db.execute(text("""
            INSERT INTO seo_competitors (domain, name, authority_score, backlinks_count, organic_keywords, organic_traffic, is_active, created_at, updated_at)
            VALUES ('rockwool.com', 'Rockwool Global', 82, 1250000, 48000, 320000, true, :now, :now)
        """), {"now": NOW})

        db.execute(text("""
            INSERT INTO serp_snapshots (id, keyword, platform, rank_position, title, url, snippet, crawl_status, crawled_at)
            VALUES (:id, 'rockwool insulation panel china supplier', 'google', 3, 'Top China Rockwool Panel Manufacturer - YouDing B2B', 'https://youding-materials.com/products/rockwool-board', 'Direct factory prices for rockwool exterior panels with ASTM and EN certifications...', 'success', :now)
        """), {"id": uuid.uuid4(), "now": NOW})

        rk_id = db.execute(text("""
            INSERT INTO keyword_rankings (keyword, search_engine, target_url, current_position, previous_position, best_position, search_volume, is_tracking, created_at, updated_at, last_checked_at)
            VALUES ('exterior wall insulation panels factory', 'google', 'https://youding-materials.com/products', 4, 7, 3, 14200, true, :now, :now, :now)
            RETURNING id
        """), {"now": NOW}).scalar()

        db.execute(text("""
            INSERT INTO keyword_ranking_history (keyword_ranking_id, keyword, search_engine, position, search_volume, checked_at)
            VALUES (:rkid, 'exterior wall insulation panels factory', 'google', 4, 14200, :now)
        """), {"rkid": rk_id, "now": NOW})
        print("✓ seo_metadata, competitors, serp_snapshots, keyword_rankings 填充完成")

        # 11. media_render_tasks, publish_tasks, publish_logs, scheduled_publishes
        media_task_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO media_render_tasks (id, title, task_type, script, status, progress, priority, result_url, file_size_bytes, file_purged, created_at, updated_at)
            VALUES (:id, '优丁岩棉一体板英文解说视频渲染', 'video_render', 'Welcome to YouDing materials factory. Today we introduce our Class A1 fireproof rockwool cladding panel...', 'completed', 100, 'high', '/static/videos/rockwool_intro_en.mp4', 38500000, 0, :now, :now)
        """), {"id": media_task_id, "now": NOW})

        pub_task_id = uuid.uuid4()
        if plat_id and acc_id:
            db.execute(text("""
                INSERT INTO publish_tasks (id, platform_id, account_id, status, publish_type, published_url, created_at, updated_at, published_at)
                VALUES (:id, :platid, :accid, 'published', 'direct', 'https://youtube.com/watch?v=youding-sample', :now, :now, :now)
            """), {"id": pub_task_id, "platid": plat_id, "accid": acc_id, "now": NOW})

            db.execute(text("""
                INSERT INTO publish_logs (id, task_id, level, message, created_at)
                VALUES (:id, :tid, 'INFO', 'Video published successfully to platform with status 200 OK', :now)
            """), {"id": uuid.uuid4(), "tid": pub_task_id, "now": NOW})

            db.execute(text("""
                INSERT INTO scheduled_publishes (id, platform_account_id, platform_name, title, body, status, attempts, max_attempts, publish_task_id, scheduled_at, published_at, created_at, updated_at)
                VALUES (:id, :accid, 'YouTube', 'YouDing Exterior Wall Insulation Production Line Tour', 'Take a virtual tour of our 3,000,000 sqm capacity automated rockwool panel factory in Hebei, China.', 'published', 1, 3, :ptid, :now, :now, :now, :now)
            """), {"id": uuid.uuid4(), "accid": acc_id, "ptid": pub_task_id, "now": NOW})
        print("✓ media_render_tasks, publish_tasks, publish_logs, scheduled_publishes 填充完成")

        db.commit()
        print("🎉 Batch 3 [内容/SEO/EEAT/术语/媒体分发] 种子数据提交成功！")
    except Exception as exc:
        db.rollback()
        print(f"❌ 填充失败: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seeding()
