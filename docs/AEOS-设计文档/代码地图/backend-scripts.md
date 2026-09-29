# 后端脚本 backend/scripts

> 根目录：`C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix\backend\scripts` · **46 个文件** · 后端脚本（含 orchestration_selfcheck.py）

| 文件 | 行 | 摘要 · 符号 · 标记 |
|---|---:|---|
| `backend/scripts/alipay_sandbox_e2e.py` | 183 | 支付宝沙箱 / 本地 E2E — 边界可控的一键联调。 · 函数:8 |
| `backend/scripts/alipay_sandbox_probe.py` | 149 | 支付宝沙箱 / 本地联调探针。 · 函数:5 · ⚑MOCK |
| `backend/scripts/audit_tier1_languages.py` | 190 | PM 巡检：Tier1 12 语种 visitor-context + 站点正文 i18n。 · 函数:4 · ⚑DEGRADED |
| `backend/scripts/b7_pilot_acceptance.py` | 137 | B-07: 5+5 试点 — seed 平台、创建母版、发布任务、跑 worker，输出验收 JSON。 · 函数:1 |
| `backend/scripts/bootstrap_greenfield.py` | 132 | 官方绿色部署引导（P0-B 处置：以 create_all + stamp 为正式建库路径）。 · 函数:3 |
| `backend/scripts/check_egress_suppliers.py` | 31 |  |
| `backend/scripts/check_openapi.py` | 73 | 函数:1 |
| `backend/scripts/check_schema_full.py` | 33 | 全表 schema 完整性检查:对比模型声明的列 vs 实际 DB 列 |
| `backend/scripts/create_admin.py` | 98 | 函数:2 · ⚑DEPRECATED |
| `backend/scripts/create_geo_tables.py` | 42 | Create GEO tables script · 函数:1 |
| `backend/scripts/create_test_users.py` | 121 | 创建测试用户脚本 - 用于开发和测试 · 函数:1 |
| `backend/scripts/db_performance_optimize.py` | 224 | 数据库性能优化迁移脚本 — FIX-23: 索引优化 · 函数:5 |
| `backend/scripts/ensure_dev_sqlite.py` | 531 | 开发 SQLite：补齐 users 缺列 + 确保三套演示账号可登录（超管/租户/代理）。 · 函数:12 · ⚑MOCK/STUB |
| `backend/scripts/export_seo_report_scheduled.py` | 82 | T-P2-05：定时 SEO 报告导出（HTML，可 cron）。 · 函数:1 |
| `backend/scripts/generate_production_config.py` | 185 | import logging · 函数:4 |
| `backend/scripts/greenchain_p0b_verify.py` | 143 | P0-B 绿色 PG 部署链测量：空库 001→heads 全量 upgrade。 · 函数:5 |
| `backend/scripts/init_mvp_tables.py` | 49 | 创建 MVP 新增表（content_masters / egress / 列扩展）。 · 函数:1 |
| `backend/scripts/migrate_full_schema.py` | 59 | 补齐剩余 3 张表的缺列 · 函数:1 |
| `backend/scripts/migrate_production.py` | 55 | 生产环境迁移与种子数据（Sprint H）。 · 函数:2 |
| `backend/scripts/migrate_publish_tasks_tenant.py` | 42 | 一次性迁移:补齐 publish_tasks.tenant_id 列 |
| `backend/scripts/orchestration_selfcheck.py` | 586 | 编排链路自检脚本 —— 一键验证「所有环节是否打通」。 · 函数:21 · ⚑STUB/DEGRADED |
| `backend/scripts/patch_sqlite_content_pages.py` | 55 | import logging · 函数:2 |
| `backend/scripts/payment_qrcode_demo.py` | 268 | 生成微信/支付宝 Native 收款二维码并跑通 mock 支付闭环。 · 函数:10 · ⚑MOCK |
| `backend/scripts/probe_cosmos_endpoint.py` | 74 | Probe NVIDIA Cosmos hosted infer endpoints (dev only). · 函数:2 |
| `backend/scripts/purge_old_egress_data.py` | 30 | 一次性清除平台池中遗留的演示/占位 egress 数据。 · 函数:1 · ⚑STUB |
| `backend/scripts/refactor_routes.py` | 135 | 函数:1 |
| `backend/scripts/repair_dev_inquiry_columns.py` | 44 | Dev-only: add missing inquiry columns when alembic chain is behind (SQLite). · 函数:1 |
| `backend/scripts/repair_dev_tenant_columns.py` | 49 | Dev-only: 为存量 SQLite 开发库补 products/orders/quotes 的 tenant_id 列（ADR-001 租户归一）。 · 函数:1 |
| `backend/scripts/reset_admin.py` | 75 | ⚑DEGRADED |
| `backend/scripts/run_ops_jobs.py` | 142 | ⚑DEGRADED |
| `backend/scripts/run_publish_worker.py` | 38 | CLI: 消费发布队列。用法: python scripts/run_publish_worker.py --once [--limit 10] · 函数:1 |
| `backend/scripts/run_tenant_lifecycle.py` | 54 | 租户生命周期定时任务 — 到期冻结 + 续费提醒。 · 函数:1 |
| `backend/scripts/seed_nvidia_provider.py` | 80 | Seed NVIDIA NIM provider and per-scenario model mappings. · 函数:1 |
| `backend/scripts/seed_platforms_full.py` | 72 | 正式 40 平台主数据（国内 20 + 海外 20）。 · 函数:2 |
| `backend/scripts/seed_platforms_pilot.py` | 52 | 试点 5+10 平台主数据（cn 5 + 海外十大社交/IM）。 · 函数:1 |
| `backend/scripts/seed_qa_passwords.py` | 38 | 重置 QA 三壳账号密码（dev sqlite）— 截图/E2E 前执行 · 函数:1 |
| `backend/scripts/seed_stress_tenant.py` | 98 | 压测种子：套餐 + 租户 + super_admin/tenant_admin 用户 + user_tenants 绑定。 · 函数:1 |
| `backend/scripts/send_communication_log.py` | 152 | import logging · 函数:4 |
| `backend/scripts/smoke_commercial_loop.py` | 275 | 商业闭环冒烟 — 验证 P0–P6 关键 API 是否可用。 · 函数:3 · ⚑MOCK |
| `backend/scripts/smoke_egress_suppliers_api.py` | 62 | Smoke-test /api/v1/egress/suppliers with admin login. · 函数:3 |
| `backend/scripts/staging_notify_http_check.py` | 217 | Staging 外网 notify 验收 — 经 HTTP 打本地/公网回调端点（模拟网关 POST）。 · 函数:2 |
| `backend/scripts/staging_payment_self_check.py` | 67 | Staging 支付自检 CLI — 与 POST /payment/ops/staging/self-check 同源逻辑。 · 函数:1 |
| `backend/scripts/start_simple.py` | 549 | 简化版启动脚本 - 不依赖Redis · 类:Product,Category,CaseStudy,News,Inquiry,InquiryCreate · 函数:16 · 路由:GET /api/v1/health; GET /api/v1/products; GET /api/v1/products/{product_id}; GET /api/v1/products/slug/{slug}; GET /api/v1/categories; GET /api/v1/categories/{category_id} |
| `backend/scripts/sync_nvidia_catalog.py` | 38 | 从 NVIDIA /v1/models 同步并生成分类目录 JSON（可入库/送检）。 · 函数:1 |
| `backend/scripts/update_admin_password.py` | 111 | 函数:2 · ⚑DEPRECATED |
| `backend/scripts/verify_ai_video_features.py` | 258 | 功能齐全性检验（需 backend :8001 + dev .env）。 · 类:Check · 函数:3 · ⚑MOCK |