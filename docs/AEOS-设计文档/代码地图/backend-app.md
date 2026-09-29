# 后端主应用 backend/app

> 根目录：`C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix\backend\app` · **1163 个文件** · 后端主应用（api/models/services/core/tasks…）

| 文件 | 行 | 摘要 · 符号 · 标记 |
|---|---:|---|
| `backend/app/__init__.py` | 0 |  |
| `backend/app/api/__init__.py` | 14 | API模块 · 函数:1 |
| `backend/app/api/v1/__init__.py` | 1 |  |
| `backend/app/api/v1/ab_test.py` | 581 | 函数:17 · 路由:GET /; GET /{test_id}; POST /; PUT /{test_id}; DELETE /{test_id}; POST /{test_id}/start |
| `backend/app/api/v1/admin_bff/__init__.py` | 40 | Admin BFF — 统一接入契约 (UAC) · 函数:1 · 路由:POST /logout |
| `backend/app/api/v1/admin_bff/auth_adapter.py` | 112 | 认证 BFF — HTTP 薄层；转发 legacy auth，输出 Vben 契约 · 类:UacLoginBody · 函数:5 · 路由:POST /login; POST /refresh; POST /logout; GET /captcha; GET /tenant/search |
| `backend/app/api/v1/admin_bff/bridge.py` | 64 | Legacy APIResponse ↔ UAC 契约桥接（仅 BFF 层使用，不泄漏到 domain） · 函数:3 · ⚑DEGRADED |
| `backend/app/api/v1/admin_bff/dict_adapter.py` | 16 | 字典 BFF — 只读配置出口 · 函数:1 · 路由:GET /plan_features |
| `backend/app/api/v1/admin_bff/lab_adapter.py` | 79 | Lab BFF — FE-11 站点编辑器试点草稿 · 类:SiteEditorDraftBody · 函数:2 · 路由:GET /site-editor; PUT /site-editor |
| `backend/app/api/v1/admin_bff/menu_adapter.py` | 69 | 菜单 BFF — HTTP 薄层；DB 菜单优先，否则静态 seed · 函数:2 · 路由:GET /routes; GET /permissions |
| `backend/app/api/v1/admin_bff/menu_seeds.py` | 191 | 四壳菜单静态种子 — 纯数据，无 HTTP / 无 DB · 函数:1 |
| `backend/app/api/v1/admin_bff/menu_transform.py` | 67 | 菜单树 → UacMenuRoute 转换（无 HTTP） · 函数:3 |
| `backend/app/api/v1/admin_bff/plan_adapter.py` | 40 | Plan Gate BFF — 只读校验出口 · 函数:1 · 路由:GET /check |
| `backend/app/api/v1/admin_bff/plan_catalog.py` | 47 | 套餐功能矩阵 — 与 docs/marketing/plan-copy-deck.md §四 对齐（BFF 只读出口） |
| `backend/app/api/v1/admin_bff/schemas.py` | 60 | UAC 响应模型 · 类:UacAuthMark,UacRouteMeta,UacMenuRoute,UacUserInfo,UacPermissionBundle |
| `backend/app/api/v1/admin_bff/shell.py` | 48 | 四壳解析 — 角色 → shell / homePath（UAC 唯一源） · 函数:2 |
| `backend/app/api/v1/admin_bff/tenant_lookup.py` | 33 | 租户登录页搜索 — 只读查询，不含认证逻辑 · 函数:1 |
| `backend/app/api/v1/admin_bff/user_adapter.py` | 28 | 用户 BFF — HTTP 薄层 · 函数:1 · 路由:GET /info |
| `backend/app/api/v1/admin_bff/user_context.py` | 130 | 组装 UacUserInfo — 用户域 + 租户域，adapter 层不堆业务细节 · 函数:5 |
| `backend/app/api/v1/ai/dashboard.py` | 419 | AI增强的数据可视化Dashboard API · 类:DashboardInsightRequest,AnomalyDetectionRequest,TrendPredictionRequest · 函数:5 · 路由:POST /insights; POST /anomaly-detection; POST /trend-prediction; GET /seo-dashboard-insights |
| `backend/app/api/v1/ai/ws.py` | 229 | AI实时消息推送WebSocket · 类:AIConnectionManager · 函数:4 |
| `backend/app/api/v1/ai_config.py` | 313 | AI模型配置API路由 · 函数:15 · 路由:GET /providers; GET /providers/{provider_id}; POST /providers; PUT /providers/{provider_id}; DELETE /providers/{provider_id}; POST /providers/{provider_id}/set-default |
| `backend/app/api/v1/ai_recommendations.py` | 133 | AI Recommendations API Router - AI推荐API · 函数:5 · 路由:POST /; GET /for-user/{user_id}; GET /{recommendation_id}; DELETE /{recommendation_id}; GET / |
| `backend/app/api/v1/analytics.py` | 85 | 函数:1 · 路由:GET /dashboard |
| `backend/app/api/v1/building_specs.py` | 158 | 建材垂直参数 API路由 · 函数:6 · 路由:POST /; GET /; GET /{spec_id}; PUT /{spec_id}; DELETE /{spec_id}; GET /product/{product_id}/mobile |
| `backend/app/api/v1/chat.py` | 188 | 函数:7 · 路由:POST /chat/webhook; GET /chat/sessions/{session_id}; POST /chat/sessions/{session_id}/email · ⚑MOCK/STUB |
| `backend/app/api/v1/chat/__init__.py` | 406 | 聊天模块API路由 · 类:SendMessageRequest,MessageResponse,SessionResponse,UserStatusResponse,ConnectionManager · 函数:7 · 路由:GET /sessions; GET /messages/{partner_id}; POST /messages; GET /status/{user_id}; PUT /status; GET /online-users |
| `backend/app/api/v1/chat_sessions.py` | 195 | Chat Sessions API Router - AI对话会话API · 函数:7 · 路由:POST /; GET /{session_id}; GET /by-user/{user_id}; PUT /{session_id}; DELETE /{session_id}; POST /{session_id}/add-message |
| `backend/app/api/v1/commercial_loop.py` | 98 | 商业闭环 API — 一键执行从产品到成交的完整链路。 · 类:CommercialLoopRequest · 函数:3 · 路由:POST /execute; GET /status/{trace_id}; GET /steps · ⚑DEGRADED |
| `backend/app/api/v1/compliance.py` | 497 | 函数:16 · 路由:GET /rules; GET /rules/{rule_id}; POST /rules; PUT /rules/{rule_id}; DELETE /rules/{rule_id}; POST /scan |
| `backend/app/api/v1/content.py` | 883 | 类:BatchDeleteRequest,BatchUpdateStatusRequest,BatchPublishRequest · 函数:26 · 路由:POST /upload; GET /pages; GET /pages/search; GET /pages/{page_id}; GET /pages/slug/{slug}; POST /pages · ⚑MOCK |
| `backend/app/api/v1/content_pages.py` | 182 | Content Pages API Router - 内容页面API · 函数:6 · 路由:POST /; GET /{page_id}; GET /; PUT /{page_id}; DELETE /{page_id}; POST /{page_id}/view |
| `backend/app/api/v1/deerflow.py` | 464 | DeerFlow 执行引擎 API 路由。 · 类:CreateJobRequest,TransitionRequest,HumanDecisionRequest,ApiResponse · 函数:18 · 路由:POST /jobs; GET /jobs; GET /jobs/{job_id}; DELETE /jobs/{job_id}; POST /jobs/{job_id}/start; POST /jobs/{job_id}/execute |
| `backend/app/api/v1/evolution.py` | 542 | AI 进化引擎 API 路由。 · 函数:19 · 路由:GET /overview; POST /records; GET /records; POST /experiences/extract; GET /experiences; GET /experiences/stats |
| `backend/app/api/v1/im_routing.py` | 256 | 商家IM路由配置 API路由 · 函数:11 · 路由:POST /; GET /; GET /languages; GET /channels; GET /resolve; GET /channel/{country_code} |
| `backend/app/api/v1/inquiries.py` | 104 | 询盘 API v2 兼容层 — 全部转发至 /api/v1/inquiries/unified（T-P0-14）。 · 函数:4 · 路由:GET /; GET /{inquiry_id}; POST / · ⚑DEPRECATED |
| `backend/app/api/v1/merchant_profiles.py` | 157 | Merchant Profiles API Router - 商家资料API · 函数:5 · 路由:POST /; GET /{profile_id}; PUT /{profile_id}; DELETE /{profile_id}; GET / |
| `backend/app/api/v1/metrics.py` | 85 | Prometheus指标导出器 - 提供系统性能指标 · 函数:6 · 路由:GET /metrics |
| `backend/app/api/v1/n8n.py` | 376 | n8n 集成 API 路由。 · 类:WorkflowRegisterRequest,WorkflowUpdateRequest,WorkflowTriggerRequest,WorkflowToggleRequest · 函数:11 · 路由:POST /webhook/{workflow_id}; POST /workflows; GET /workflows; GET /workflows/{workflow_id}; PUT /workflows/{workflow_id}; DELETE /workflows/{workflow_id} |
| `backend/app/api/v1/orders.py` | 196 | Orders API Router - 订单API · 类:TrackingNumberUpdate,PaymentStatusUpdate · 函数:7 · 路由:POST /; GET /{order_id}; PATCH /{order_id}/payment-status; PUT /{order_id}/status; GET /; PATCH /{order_id}/tracking |
| `backend/app/api/v1/product_categories.py` | 161 | Product Categories API Router - 产品分类API · 函数:5 · 路由:POST /; GET /{category_id}; GET /; PUT /{category_id}; DELETE /{category_id} |
| `backend/app/api/v1/product_images.py` | 157 | Product Images API Router - 产品图片API · 函数:5 · 路由:POST /; GET /{image_id}; GET /by-product/{product_id}; PUT /{image_id}; DELETE /{image_id} |
| `backend/app/api/v1/products.py` | 634 | 类:BatchDeleteRequest,BatchUpdateStatusRequest,ProductExportItem · 函数:21 · 路由:GET /categories/tree; GET /categories; GET /categories/{category_id}; POST /categories; PUT /categories/{category_id}; DELETE /categories/{category_id} |
| `backend/app/api/v1/products_mobile.py` | 106 | 函数:3 · 路由:GET /product/{product_id}; GET /mobile/product/{product_id} · ⚑STUB |
| `backend/app/api/v1/quotes.py` | 198 | Quotes API Router - 报价管理（RFQ 关联 + 审批 + 版本） · 函数:8 · 路由:POST /from-rfq; POST /{quote_id}/approve; POST /{quote_id}/version; GET /{quote_id}/versions; GET /{quote_id}; GET / |
| `backend/app/api/v1/routes/__init__.py` | 87 | API v1 路由模块汇聚层。 · 函数:2 · 路由:GET /health |
| `backend/app/api/v1/routes/ab_test.py` | 108 | A/B测试路由 - 模块化架构 · 函数:7 · 路由:GET /; GET /{test_id}; POST /; PUT /{test_id}; DELETE /{test_id}; POST /{test_id}/start |
| `backend/app/api/v1/routes/agent_bff.py` | 57 | Agent 代理壳 BFF — 首屏聚合（T-ARCH-2）。 · 函数:1 · 路由:GET /summary |
| `backend/app/api/v1/routes/agent_hub.py` | 192 | 智能体协同中心路由 - 模块化架构 · 函数:11 · 路由:GET /; GET /mcp-bridge; POST /mcp-bridge; GET /mcp-bridge/tools; GET /mcp-bridge/health; GET /task-orchestrator |
| `backend/app/api/v1/routes/agent_portal.py` | 294 | 代理独立壳 API（UX-3a）— L2/L3 业绩与下级汇总。 · 类:AccountOpeningRequest,CollectPaymentRequest · 函数:10 · 路由:GET /dashboard; GET /clients; GET /payments; GET /trends; POST /account-opening; GET /plans · ⚑MOCK |
| `backend/app/api/v1/routes/agent_tree.py` | 326 | 代理层级树路由 · 类:AgentNodeWriteBody,AgentNodeUpdateBody · 函数:10 · 路由:POST /nodes; PUT /nodes/{node_id}; DELETE /nodes/{node_id}; GET /stats; GET /chain; GET /children |
| `backend/app/api/v1/routes/ai_config.py` | 104 | AI配置路由 - 真实数据库，禁止硬编码统计 · 函数:4 · 路由:GET /; PUT /; POST /provider/{provider_id}/toggle; GET /stats |
| `backend/app/api/v1/routes/ai_generate.py` | 180 | AI 生成/优化路由 — 统一走场景调度与用量落库。 · 类:GenerateRequest,OptimizeRequest,AiWriteRequest,ProductAIGenerateBody,ProductAIPolishBody · 函数:4 · 路由:POST /generate; POST /optimize; POST /product/generate; POST /product/polish |
| `backend/app/api/v1/routes/ai_learning.py` | 256 | AI深度学习与自我进化路由 - 模块化架构 · 函数:10 · 路由:GET /; GET /behavior; GET /conversion-funnel; GET /auto-ab-test; POST /auto-ab-test; POST /auto-ab-test/{test_id}/start · ⚑MOCK/DEGRADED |
| `backend/app/api/v1/routes/ai_templates.py` | 162 | AI 内容生成模板 API · 类:AITemplateCreate,AITemplateUpdate · 函数:4 · 路由:GET /; POST /; PUT /{tpl_id}; DELETE /{tpl_id} |
| `backend/app/api/v1/routes/ai_usage.py` | 362 | AI Token 用量监控与告警路由 - 模块化架构（真实数据库查询，无 mock 回退） · 函数:9 · 路由:GET /overview; GET /daily; GET /models; GET /logs; GET /alerts; POST /alerts/config · ⚑MOCK |
| `backend/app/api/v1/routes/ai_visibility.py` | 181 | GEO / AI Visibility 路由 — AI 搜索可见性监控（Phase 6）。 · 函数:4 · 路由:GET /queries; POST /queries; POST /runs; GET /visibility |
| `backend/app/api/v1/routes/aitoearn_hub.py` | 152 | AiToEarn 能力 Hub API — 对齐 Create/Publish/Engage/Analytics。 · 类:EngageReplyBody,EngageListBody · 函数:4 · 路由:GET /capabilities; POST /engage/reply; POST /engage/comments |
| `backend/app/api/v1/routes/analytics.py` | 594 | 数据分析路由 - 流量埋点与运营看板 · 类:AnalyticsEventBody,RumBeaconBody · 函数:16 · 路由:GET /site-context; POST /event; GET /operations/traffic-board; GET /traffic-board; GET /traffic; GET / |
| `backend/app/api/v1/routes/annex.py` | 84 | 附属统一登录路由 · annex_ticket 签发与校验（§9.3）. · 类:AnnexTicketBody,AnnexRedeemBody · 函数:3 · 路由:POST /annex/ticket; POST /annex/redeem |
| `backend/app/api/v1/routes/app_bff.py` | 333 | 出海计 App BFF — 聚合首页数据。 · 类:DeviceRegisterRequest,AppChatRequest,VoiceTranscribeRequest · 函数:11 · 路由:GET /home; POST /devices/register; POST /push/test; GET /config; GET /store-release; GET /today · ⚑STUB |
| `backend/app/api/v1/routes/attribution.py` | 112 | Full-Funnel Attribution Report API — Connection ⑥ · 类:EmailReplyBody · 函数:2 · 路由:GET /attribution; POST /attribution/email-reply |
| `backend/app/api/v1/routes/auth.py` | 650 | 认证模块路由 · 函数:19 · 路由:POST /login; POST /refresh; POST /logout; POST /change-password; POST /send-email-code; POST /login-by-email · ⚑DEGRADED |
| `backend/app/api/v1/routes/auto_discovery.py` | 262 | API 路由自动发现 — FIX-30: 按业务域分包 + 自动注册 · 函数:3 |
| `backend/app/api/v1/routes/baidu_webmaster.py` | 52 | 百度站长工具 API 路由 · 函数:3 · 路由:POST /baidu/sitemap/submit; GET /baidu/index-count; GET /baidu/search-queries |
| `backend/app/api/v1/routes/building_wiki.py` | 421 | AI建材百科路由 - 建材行业知识文章生成与管理 · 类:GenerateRequest,UpdateRequest · 函数:9 · 路由:POST /generate; GET /articles; GET /articles/{article_id}; PUT /articles/{article_id}; POST /publish/{article_id}; POST /unpublish/{article_id} |
| `backend/app/api/v1/routes/calculator.py` | 39 | Calculator 路由 — 工程计算器（Thermal / Fire Protection / Quantity）。 · 函数:3 · 路由:POST /thermal; POST /fire-protection; POST /quantity |
| `backend/app/api/v1/routes/campaign.py` | 141 | Campaign 路由 — ABM / AI Outbound 活动管理（Phase 5）。 · 类:CampaignCreate · 函数:4 · 路由:GET /; GET /{campaign_id}; POST / |
| `backend/app/api/v1/routes/case_studies.py` | 244 | 案例管理路由 - 优化版 - 解决N+1查询和添加缓存 · 类:CaseImageCreate · 函数:8 · 路由:GET /; GET /{case_id}; POST /{case_id}/images; POST /; PUT /{case_id}; DELETE /{case_id} |
| `backend/app/api/v1/routes/churn.py` | 80 | 客户流失预警 API · 函数:5 · 路由:GET /at-risk; GET /tips; POST /mark-contacted/{tenant_id}; GET /trend |
| `backend/app/api/v1/routes/client.py` | 589 | SaaS 客户管理后台 - 仪表盘与品牌接口 · 函数:21 · 路由:GET /dashboard; GET /publish-readiness; GET /ai-connect; GET /ai-traffic-recharge-catalog; GET /branding; GET /wecom-push-config |
| `backend/app/api/v1/routes/client_bff.py` | 67 | 租户端 BFF — 首屏聚合（T-ARCH-2）。 · 函数:2 · 路由:GET /bootstrap; GET /dashboard |
| `backend/app/api/v1/routes/code_quality.py` | 146 | 代码质量 API — FIX-70~73 · 函数:13 · 路由:GET /config/eslint; GET /config/prettier; GET /config/vitest; GET /config/all; GET /type-compliance/report; GET /type-compliance/tsconfig |
| `backend/app/api/v1/routes/cognitive.py` | 78 | 认知智能与知识图谱路由 - 模块化架构 · 函数:4 · 路由:GET /; GET /qa-engine; GET /expert-system; GET /semantic-index |
| `backend/app/api/v1/routes/company.py` | 295 | Company 360 路由 — 公司主数据 + 联系人 + 信号聚合（Account 360 后端）。 · 类:CompanyCreate,SignalCreate · 函数:6 · 路由:GET /; GET /{company_id}; POST /; POST /{company_id}/signals |
| `backend/app/api/v1/routes/compliance.py` | 199 | 合规审计路由 - 模块化架构 · 函数:7 · 路由:GET /; GET /security-alerts; GET /audit; GET /issues; PUT /issues/{issue_id}/resolve; GET /report |
| `backend/app/api/v1/routes/content.py` | 539 | 内容管理路由 - 优化版 - 添加缓存和分页验证 · 类:ProductAIGenerateBody,ProductAIPolishBody · 函数:24 · 路由:GET /; GET /; GET /pages; GET /pages/search; GET /pages/slug/{slug}; GET /pages/stats |
| `backend/app/api/v1/routes/content_master.py` | 516 | 统一发布母版 API · 类:ContentMasterCreate,ContentMasterUpdate,PublishFromMasterRequest,PublishAutoVariantsRequest · 函数:12 · 路由:GET /; POST /; POST /publish-auto-variants; GET /{master_id}; GET /{master_id}/link-preview; PUT /{master_id} · ⚑DEGRADED |
| `backend/app/api/v1/routes/crm_pipeline.py` | 525 | CRM 销售管线路由 — 商机（Opportunity）管理 · 类:OpportunityCreate,OpportunityUpdate,OpportunityResponse,StageAdvanceRequest,StageStat,PipelineStats · 函数:10 · 路由:GET /opportunities/stages; GET /pipeline/stats; GET /opportunities; POST /opportunities; GET /opportunities/{opportunity_id}; PATCH /opportunities/{opportunity_id} |
| `backend/app/api/v1/routes/cross_border.py` | 734 | 跨境语言桥 API — W1 中文片出海 / W2 询盘桥 / W3 报价+SEO。 · 类:ReplyDraftBody,ImapPollBody,ExportQuoteBody,VideoDubBody,PremiumDubBody,StudioProjectBody,TranscribeBody,ImportCandidatesBody · 函数:28 · 路由:GET /inquiries/bridge-status; POST /inquiries/imap-poll; GET /inquiries/pipeline/summary; PATCH /inquiries/{inquiry_id}/pipeline-stage; GET /geo-visibility; GET /unified-geo-score |
| `backend/app/api/v1/routes/cross_platform_dashboard.py` | 130 | 跨平台数据看板 API — 聚合 AiToEarn 各平台数据。 · 函数:6 · 路由:GET /overview; GET /nurture; GET /publish; GET /summary |
| `backend/app/api/v1/routes/customer_support.py` | 33 | 多渠道海外客服路由。 · 类:MessageInboundRequest · 函数:1 · 路由:POST /message |
| `backend/app/api/v1/routes/daily_report.py` | 38 | 每日经营日报 API · 函数:2 · 路由:GET /; GET /history |
| `backend/app/api/v1/routes/deepseek_harness.py` | 102 | DeepSeek Harness 外层运行时接入路由（总纲 §外层 / 轮次续接）。 · 类:InvokeRequest,InvokeResponse,HealthResponse · 函数:2 · 路由:GET /health; POST /invoke |
| `backend/app/api/v1/routes/developer.py` | 78 | 开发者生态与低代码路由 - 模块化架构 · 函数:4 · 路由:GET /; GET /sdk; GET /low-code; GET /plugins |
| `backend/app/api/v1/routes/domain.py` | 372 | SaaS 租户自定义域名绑定路由 · 函数:13 · 路由:GET /resolve; GET /tenants/{tenant_id}/domains; POST /tenants/{tenant_id}/domains; DELETE /tenants/{tenant_id}/domains/{domain:path}; GET /tenants/{tenant_id}/domains/{domain:path}/verify; POST /tenants/{tenant_id}/domains/{domain:path}/ssl · ⚑MOCK |
| `backend/app/api/v1/routes/domain_registry.py` | 39 | 领域注册状态 API — FIX-31 · 函数:1 · 路由:GET / |
| `backend/app/api/v1/routes/edge_cdn.py` | 100 | 边缘计算与CDN路由 - 模块化架构 · 函数:6 · 路由:GET /; GET /nodes; POST /nodes; GET /preheat; POST /preheat; GET /protocol |
| `backend/app/api/v1/routes/egress.py` | 892 | 静态 IP 槽位与浏览器指纹 API · 类:EgressCreate,ProfileCreate,AssignRequest,FulfillEndpointRequest,SupplierCreate,SupplierUpdate · 函数:29 · 路由:GET /overview; GET /tenants; GET /endpoints; POST /endpoints; POST /endpoints/{endpoint_id}/assign; POST /endpoints/{endpoint_id}/release |
| `backend/app/api/v1/routes/email_queue.py` | 313 | 邮件发送队列 + 数据飞轮 + 加密审计 + AI 安全 API — FIX-62 ~ FIX-65 · 函数:22 · 路由:POST /enqueue; POST /enqueue/batch; POST /dequeue; GET /stats; POST /clear; POST /domain-limits |
| `backend/app/api/v1/routes/email_tracking.py` | 79 | 邮件追踪像素路由（P1-3）—— 无需登录鉴权，内置安全防护。 · 函数:2 · 路由:GET /pixel/{message_id}.png |
| `backend/app/api/v1/routes/feishu.py` | 368 | 函数:10 · 路由:POST /webhook; POST /send; POST /send/inquiry/{inquiry_id}; GET /bind; POST /bind; POST /unbind |
| `backend/app/api/v1/routes/files.py` | 448 | 文件管理路由 - 上传、列表、删除（国内七牛 / 海外 R2 分轨） · 函数:12 · 路由:GET /storage-profile; POST /upload; POST /upload-multi; GET /; DELETE /{file_id}; GET /stats |
| `backend/app/api/v1/routes/finance.py` | 597 | 财务中台 MVP — 营收/成本流水 · 类:LedgerCreate,CommissionRuleUpdate,FinanceImportValidateBody,FinanceImportCommitBody,CommissionCreate · 函数:17 · 路由:GET /commission-rules; PUT /commission-rules/{rule_id}; GET /expiring-tenants; GET /ledger; POST /ledger; GET /summary |
| `backend/app/api/v1/routes/follow_up.py` | 200 | 智能 Follow-up API 路由 — FIX-57 · 函数:7 · 路由:POST /sequence/build; POST /sequence/advance; POST /next-action; GET /best-send-time; POST /should-stop; POST /multi-channel-strategy |
| `backend/app/api/v1/routes/foreign_trade.py` | 879 | 外贸 B2B 工具·技能·生态 API — 随源码部署。 · 类:LinkedInDecisionMakerBody,CustomsBuyerResearchBody,EcommerceSpiderRunBody,EcommerceQuickRunBody,UserActionQuickRunBody,MeddpiccUpdate,ExpandVariantsRequest,PreflightRequest · 函数:36 · 路由:GET /ecosystem/overview; GET /ecosystem/catalog; GET /integrations/sidecars/status; GET /integrations/matrix-oauth-gate; POST /integrations/linkedin/decision-makers; GET /trade-intel/customs-buyer-brief |
| `backend/app/api/v1/routes/foreign_trade_skills.py` | 78 | 外贸 AI 技能 API 路由。 · 函数:3 · 路由:GET /; POST /{skill_name} |
| `backend/app/api/v1/routes/forum.py` | 220 | 论坛 Sidecar API — 状态、租户配置、Webhook（Apache Answer）。 · 类:ForumConfigBody,ForumTranslateBody · 函数:7 · 路由:GET /status; GET /config; PUT /config; GET /setup-guide; POST /translate-qa; POST /webhook |
| `backend/app/api/v1/routes/founder_ops.py` | 237 | 创始人运维 / 国密调试（国密 + 微信唯一，浏览器可用，不返回源码）。 · 类:SealRequest,UnsealRequest · 函数:7 · 路由:GET /preflight; GET /status; GET /crypto/self-test; POST /crypto/seal; POST /crypto/unseal; GET /security-events |
| `backend/app/api/v1/routes/gdpr.py` | 239 | GDPR Data Deletion Endpoint · 类:GDPRDeleteRequest,GDPRDeleteResponse · 函数:5 · 路由:POST /delete-data |
| `backend/app/api/v1/routes/gdpr_compliance.py` | 38 | GDPR 出海隐私合规路由模块。 · 类:AnonymizeRequest · 函数:2 · 路由:GET /export/{user_id}; POST /anonymize |
| `backend/app/api/v1/routes/global_search.py` | 130 | 工作区全局搜索（UX-2c）— 菜单 + 询盘 + 母版 + 订单。 · 函数:2 · 路由:GET /workspace |
| `backend/app/api/v1/routes/globalization.py` | 230 | 全球化与多语言路由 — 对接真实数据库 · 函数:11 · 路由:GET /; GET /glossary; POST /glossary; PUT /glossary/{term_id}; DELETE /glossary/{term_id}; GET /glossary/stats |
| `backend/app/api/v1/routes/growth_loop.py` | 33 | 获客闭环路由。 · 类:CampaignLaunchRequest · 函数:1 · 路由:POST /launch |
| `backend/app/api/v1/routes/growth_tools.py` | 434 | 三大增长内置工具 API。 · 类:GrowthAgentRunBody,KeywordCreateBody,ContentInspectBody,HeadlessProbeBody,BaiduProbeBody,ConversionProbeBody · 函数:16 · 路由:GET /dashboard; GET /agent/presets; GET /agent/runs; GET /keywords/hot; GET /keywords/library; POST /keywords/library |
| `backend/app/api/v1/routes/health.py` | 115 | 系统健康检查端点 · 函数:3 · 路由:GET /health; GET /health/db; GET /health/ready |
| `backend/app/api/v1/routes/hermes.py` | 1829 | Hermes 内部插件平台 API — 运维/编排；租户侧请用旺财插件市场。 · 类:FlywheelRunRequest,PluginRunBody,AgencyWorkflowRunBody,OpsInstructBody,A2ANegotiateBody,SurvivalRecordBody,WorldFirstSurvivalBody,GreedyRevenueLoopRunBody · 函数:60 · 路由:GET /plugins/catalog; POST /plugins/{plugin_id}/run; GET /agency/providers/setup-plan; POST /agency/providers/bootstrap; GET /agency/providers; GET /agency/catalog · ⚑STUB |
| `backend/app/api/v1/routes/hub.py` | 159 | 公开内容枢纽 API — 租户站聚合页只读数据 · 函数:5 · 路由:GET /pages/{tenant_slug}/{content_id}; GET /sitemap.xml; GET /search-console/checklist; POST /search-console/ping · ⚑STUB |
| `backend/app/api/v1/routes/inquiries.py` | 613 | 询盘管理路由 - 模块化架构 · 类:InquiryStatusUpdate,InquiryAssignRequest,PublicInquiryCreate · 函数:19 · 路由:GET /portal; GET /unified; GET /; GET /export; GET /assignees; GET /assignment-audit · ⚑DEPRECATED |
| `backend/app/api/v1/routes/inquiry_channels.py` | 141 | 企微 / 抖音等 IM 渠道 webhook（七步⑤ 框架入口）。 · 类:ChannelInquiryBody · 函数:5 · 路由:GET /config; POST /wecom; POST /douyin |
| `backend/app/api/v1/routes/integrations.py` | 32 | 集成栈状态 API。 · 函数:1 · 路由:GET /status |
| `backend/app/api/v1/routes/international.py` | 374 | 国际询盘采集系统路由 - 独立于国内业务 · 函数:14 · 路由:POST /webhook; GET /inquiries; GET /inquiries/{inquiry_id}; PUT /inquiries/{inquiry_id}; GET /sites; POST /sites |
| `backend/app/api/v1/routes/invoice_applications.py` | 434 | 开票申请 API — 租户提交 + 财务审核。 · 类:InvoiceApplicationCreate,PlatformConfigUpdate,ReviewBody,MarkIssuedBody · 函数:13 |
| `backend/app/api/v1/routes/knowledge.py` | 98 | 知识库 API 路由 · 类:ValidateQuoteBody · 函数:6 · 路由:GET /categories; GET /search; POST /ask; GET /info; POST /validate-quote |
| `backend/app/api/v1/routes/knowledge_graph.py` | 361 | Knowledge Graph API - 知识图谱路由 · 类:CypherQueryRequest,EntitySearchRequest,PathRequest,BuildGraphRequest,CreateNodeRequest,CreateRelationshipRequest,NeighborsRequest · 函数:11 · 路由:POST /query; POST /entity-search; GET /path/{from_id}/{to_id}; POST /path; POST /build; POST /node · ⚑DEGRADED |
| `backend/app/api/v1/routes/knowledge_ingestion.py` | 194 | 知识库沉淀 API 路由 · 类:MarketReportRequest,BuyerPersonaRequest,CompetitorAnalysisRequest,GeoStrategyRequest,EmailTemplateRequest,ComplianceInfoRequest,ResearchReportRequest · 函数:9 · 路由:POST /market-report; POST /buyer-persona; POST /competitor-analysis; POST /geo-strategy; POST /email-template; POST /compliance |
| `backend/app/api/v1/routes/lead_enrichment.py` | 188 | Hunter.io / Apollo.io 付费 API 路由 — FIX-53 · 函数:10 · 路由:GET /status; GET /hunter/domain-search; GET /hunter/email-verify; POST /hunter/batch-verify; GET /hunter/email-finder; GET /hunter/account |
| `backend/app/api/v1/routes/lead_generation.py` | 674 | 零成本获客 API —— 完全免费的客户开发能力 · 类:LeadSearchRequest,FoundLeadEmail,FoundLead,LeadSearchResponse,SendOutreachRequest,SequenceStep,CreateSequenceRequest · 函数:16 · 路由:POST /search; GET /verify-email; GET /scrape-website; POST /send-outreach; GET /outreach/pending-review; POST /outreach/{email_id}/approve |
| `backend/app/api/v1/routes/lead_pipeline.py` | 137 | 线索处理 Pipeline + 评分 API — FIX-35/36 · 函数:4 · 路由:POST /pipeline/process; POST /pipeline/process-batch; POST /score; POST /score-batch |
| `backend/app/api/v1/routes/lead_search.py` | 124 | 线索搜索引擎 API — FIX-61 · 函数:7 · 路由:POST /index; POST /index/batch; POST /index/remove; GET /search; GET /suggest; GET /stats |
| `backend/app/api/v1/routes/lead_tools.py` | 291 | 获客工具集 API — FIX-38/39/40 · 函数:6 · 路由:POST /import/csv; POST /import/csv/validate; GET /export/csv; GET /funnel; GET /roi; GET /onboarding |
| `backend/app/api/v1/routes/license.py` | 505 | License Management API - 许可证管理接口（P1-5 扩展：设备指纹 + 授权码 + 套餐订单） · 函数:16 · 路由:POST /generate; POST /activate; POST /{license_id}/revoke; GET /; GET /{license_id}; PUT /{license_id} |
| `backend/app/api/v1/routes/linkedin_sales.py` | 240 | LinkedIn Sales Navigator API 路由 — FIX-55 · 函数:12 · 路由:GET /status; GET /auth/url; POST /auth/exchange; GET /people/search; GET /people/{person_id}; GET /people/me |
| `backend/app/api/v1/routes/logistics.py` | 157 | 智能物流与定价路由 - 模块化架构 · 函数:7 · 路由:GET /track; POST /orders/{order_id}/sync-tracking; GET /; GET /lbs-routing; GET /freight-calc; GET /quotation |
| `backend/app/api/v1/routes/matching.py` | 88 | 产品智能匹配（Product Finder）公开路由。 · 函数:2 · 路由:POST /product-match |
| `backend/app/api/v1/routes/mcp_sse.py` | 84 | MCP SSE Transport Route for Hermes Brain. · 函数:2 · 路由:GET /sse; POST /messages |
| `backend/app/api/v1/routes/media_factory.py` | 1432 | 多媒体内容工厂路由。 · 类:AiWriteBody,GenerateVideoBody,ArticleToVideoBody,HandoffBody,MediaPublishBody,MediaPublishTrafficBody,GuestBindBody,ClipBody · 函数:35 · 路由:GET /; GET /videos; POST /upload; POST /ai-write; POST /article-to-video; POST /generate · ⚑MOCK/DEGRADED |
| `backend/app/api/v1/routes/metrics.py` | 105 | Prometheus指标导出器 - 提供系统性能指标 · 函数:6 · 路由:GET /metrics |
| `backend/app/api/v1/routes/mobile_public.py` | 85 | 租户站 / 移动端公开 API（无需登录）。 · 函数:3 · 路由:GET /im-routing; GET /site-policy |
| `backend/app/api/v1/routes/moss_vl_clip_publish.py` | 137 | MOSS-VL AI 剪辑、一键分发、热更新/回滚及官方整仓管理路由。 · 类:MossAnalyzeRequest,MossAutoClipRequest,MossClipAndPublishRequest,MossHotReloadRequest,MossRollbackRequest · 函数:9 · 路由:POST /analyze; POST /auto-clip; POST /clip-and-publish; GET /version/status; POST /version/check-upstream; POST /version/hot-reload |
| `backend/app/api/v1/routes/multimodal_studio.py` | 36 | 多模态营销工厂路由。 · 类:ImagePromptRequest,SocialPostRequest · 函数:2 · 路由:POST /image-prompt; POST /social-post |
| `backend/app/api/v1/routes/news.py` | 194 | 新闻管理路由 - 模块化架构 · 函数:7 · 路由:GET /; GET /; GET /{news_id_or_slug}; POST /; POST /; PUT /{news_id} · ⚑STUB |
| `backend/app/api/v1/routes/notifications.py` | 203 | 通知管理路由 · 函数:8 · 路由:POST /; GET /; GET /{notification_id}; PUT /{notification_id}/read; PUT /read-all; DELETE /{notification_id} |
| `backend/app/api/v1/routes/onboarding.py` | 62 | 租户入驻引导 API · 类:CompleteStepBody · 函数:4 · 路由:GET /status; POST /complete-step; POST /generate-sample; GET /achievements |
| `backend/app/api/v1/routes/opportunity.py` | 372 | Opportunity 路由 — CRM 销售机会管道（管理端）。 · 类:OpportunityCreateIn,OpportunityCreate,StageUpdate,AssignIn · 函数:8 · 路由:GET /stats; GET /; GET /{opportunity_id}; POST /; PUT /{opportunity_id}/stage; PUT /{opportunity_id}/assign |
| `backend/app/api/v1/routes/ops_jobs.py` | 755 | 运维定时任务入口（需超管）— 供 cron / 手动触发。 · 类:OpsHermesInstructBody,DouyinCommentBatchBody · 函数:40 · 路由:GET /readiness; GET /readiness/public; POST /backup/run; GET /backup/status; POST /ai-scenario-health/run; GET /ai-scenario-health/status |
| `backend/app/api/v1/routes/orchestration.py` | 196 | 统一编排摄入 API（对接总纲 §4.6 统一任务面）。 · 类:OrchestrationTaskRequest,OrchestrationTaskResponse,OrchestrationFromIntentRequest,OrchestrationFromIntentResponse · 函数:4 · 路由:POST /tasks; POST /tasks/from-intent; GET /tasks/{task_id} · ⚑DEGRADED |
| `backend/app/api/v1/routes/outreach_quality.py` | 229 | 开发信质量评估 + A/B 测试 + 获客流程 API 路由 — FIX-58 & FIX-59 · 函数:10 · 路由:POST /evaluate; POST /ab-test/create; POST /ab-test/analyze; POST /ab-test/generate-variants; POST /workflow/create; POST /workflow/advance |
| `backend/app/api/v1/routes/p2_enhancement.py` | 290 | P2 增强 API — 完成剩余 19 项 · 函数:28 · 路由:POST /acquisition/channel-optimal; POST /acquisition/route-lead; POST /acquisition/predict-time; POST /acquisition/predict-churn; GET /acquisition/mcp-tools; POST /performance/partition-sql |
| `backend/app/api/v1/routes/paperclip.py` | 668 | Paperclip Agent 编排 API — 公司 / Agent / 目标 / 任务 / 心跳 / 预算 / 审批 · 类:CompanyCreateBody,CompanyUpdateBody,AgentHireBody,AgentUpdateBody,GoalCreateBody,GoalUpdateBody,TaskCreateBody,TaskAssignBody · 函数:37 · 路由:POST /companies; GET /companies; GET /companies/{company_id}; PUT /companies/{company_id}; POST /companies/{company_id}/agents; GET /companies/{company_id}/agents |
| `backend/app/api/v1/routes/payment.py` | 643 | 支付路由 - 支付订单创建、查询、回调、套餐查询 · 类:CreatePaymentRequest,CreateNativePaymentRequest,NotifyRequest,MockPayRequest,AlipayProbeRequest,WechatProbeRequest,CreateEgressAddonRequest,CreateTokenPackRequest · 函数:36 · 路由:GET /channels/status; GET /ops/status; POST /ops/wechat/refresh-certs; POST /ops/alipay/probe; POST /ops/wechat/probe; POST /ops/staging/self-check · ⚑MOCK/DEPRECATED |
| `backend/app/api/v1/routes/payment_international.py` | 87 | 国际支付路由模块。 · 类:StripeCheckoutRequest,PayPalCreateRequest,PayPalCaptureRequest · 函数:4 · 路由:POST /stripe/checkout; POST /stripe/webhook; POST /paypal/create; POST /paypal/capture |
| `backend/app/api/v1/routes/performance.py` | 225 | 性能优化 API — FIX-66~69 · 函数:17 · 路由:POST /message-bus/publish; GET /message-bus/stats; POST /message-bus/process; POST /cdn/cache-rules; GET /cdn/page-rules; POST /cdn/purge |
| `backend/app/api/v1/routes/platform.py` | 529 | 多平台分发 API 路由 - 平台账号管理、内容分发、会话保持 · 类:ConnectPlatformBody,PublishContentBody,BatchPublishItem,BatchPublishBody,SchedulePublishBody · 函数:21 · 路由:GET /; GET /catalog/alignment; GET /catalog; GET /rank-priority; GET /discovery; GET /pilot |
| `backend/app/api/v1/routes/platform_bff.py` | 103 | Platform 超管壳 BFF — 首屏聚合（T-ARCH-2）。 · 函数:2 · 路由:GET /overview |
| `backend/app/api/v1/routes/product_commerce.py` | 138 | 产品商业化 API — FIX-32/33/34 · 函数:6 · 路由:GET /plans; GET /value-proposition; GET /credits/system; GET /credits/balance; POST /credits/purchase; GET /referral/info |
| `backend/app/api/v1/routes/product_commercial.py` | 260 | 产品商业化 API — FIX-74~81 · 函数:22 · 路由:POST /agent/register; POST /agent/commission; GET /agent/report/{user_id}; GET /agent/tiers; GET /templates; GET /templates/{template_id} |
| `backend/app/api/v1/routes/product_faqs.py` | 96 | 产品 FAQ API — 中英双语 CRUD · 类:FaqCreate,FaqUpdate · 函数:5 · 路由:GET /product/{product_id}; POST /; PUT /{faq_id}; DELETE /{faq_id} |
| `backend/app/api/v1/routes/products.py` | 617 | 产品管理路由 - 优化版 - 添加缓存和优化查询 · 类:BatchProductIdsBody,BatchStatusBody · 函数:23 · 路由:GET /categories; GET /categories/tree; GET /categories/{category_id}; POST /categories; PUT /categories/{category_id}; DELETE /categories/{category_id} |
| `backend/app/api/v1/routes/project.py` | 212 | Project Intelligence 路由 — 项目/招标情报（Phase 4）。 · 类:ProjectCreate · 函数:5 · 路由:GET /; GET /stats; GET /{project_id}; POST / |
| `backend/app/api/v1/routes/prospect_research.py` | 120 | RAG 客户洞察 API 路由 — FIX-56 · 函数:3 · 路由:POST /research; POST /generate-email; POST /generate-email/from-research |
| `backend/app/api/v1/routes/public_forum.py` | 50 | 公开站 — 租户论坛嵌入配置（iframe）。 · 函数:1 · 路由:GET /tenants/{domain}/forum-embed |
| `backend/app/api/v1/routes/public_tenant_geo.py` | 112 | 公开 API — 租户 llms.txt / GEO 统一评分 / AI 搜索探针。 · 函数:4 · 路由:GET /tenants/{domain}/llms.txt; GET /tenants/{domain}/llms-full.txt; GET /tenants/{domain}/geo-score; GET /tenants/{domain}/ai-search-probes |
| `backend/app/api/v1/routes/public_tenant_media.py` | 64 | 租户官网公开视频页（SEO/GEO 收录，无需登录）。 · 函数:3 · 路由:GET /tenants/{domain}/videos; GET /tenants/{domain}/videos/{task_id}; GET /tenants/{domain}/videos-sitemap.xml |
| `backend/app/api/v1/routes/public_visitor_context.py` | 78 | 公开站访客地域上下文 — IP/Accept-Language → 语言 + 旺财/站点 UI 文案。 · 函数:1 · 路由:GET /tenants/{domain}/visitor-context |
| `backend/app/api/v1/routes/public_wangcai.py` | 252 | 公开站旺财 — 海关全量数据 + 出口问答（无需登录）。 · 类:WangcaiAskBody · 函数:4 · 路由:GET /tenants/{domain}/wangcai/prompts; POST /tenants/{domain}/wangcai/ask; GET /tenants/{domain}/wangcai/customs |
| `backend/app/api/v1/routes/publish_tasks.py` | 142 | Publish Task API Routes - Unified Publishing Platform MVP. · 函数:5 · 路由:GET /; GET /queue/stats; GET /{task_id}; PUT /{task_id}; POST /{task_id}/retry |
| `backend/app/api/v1/routes/rank_check.py` | 61 | 关键词排名查询 API 路由 — 对接 rank_checker.py 真实爬虫 · 类:RankCheckResponse,BatchRankCheckRequest · 函数:2 · 路由:GET /rank/check; POST /rank/batch-check · ⚑MOCK/DEGRADED |
| `backend/app/api/v1/routes/recycle_bin.py` | 144 | 回收站 API — 软删除内容的查询、恢复、永久删除 · 函数:4 · 路由:GET /; POST /{item_type}/{item_id}/restore; DELETE /{item_type}/{item_id}; POST /batch-delete |
| `backend/app/api/v1/routes/referral.py` | 192 | 客户裂变推荐系统路由 · 函数:10 · 路由:GET /my-code; POST /generate; GET /stats; GET /records; POST /apply/{code}; POST /sync-rewards |
| `backend/app/api/v1/routes/reviews.py` | 422 | 评价反馈API路由 · 类:ReviewCreate,ReviewUpdate,ReviewResponse,ReviewStatsResponse · 函数:9 · 路由:POST /; GET /; GET /{review_id}; PUT /{review_id}; DELETE /{review_id}; PUT /{review_id}/approve |
| `backend/app/api/v1/routes/rfq.py` | 506 | RFQ 需求单路由 — 买家结构化的询价请求（公开提交 + 管理端管理）。 · 函数:16 · 路由:POST /; GET /; GET /stats; GET /{rfq_id}; PUT /{rfq_id}/status; PUT /{rfq_id}/assign · ⚑DEGRADED |
| `backend/app/api/v1/routes/sales_task.py` | 205 | Sales Task 路由 — 销售任务队列（管理端）。 · 类:TaskCreate,TaskStatusUpdate · 函数:5 · 路由:GET /; GET /{task_id}; POST /; PUT /{task_id}/status |
| `backend/app/api/v1/routes/search_strategy.py` | 151 | AI 智能搜索策略 API 路由 — FIX-60 · 函数:8 · 路由:POST /build; POST /google-dork; POST /linkedin-url; GET /industry-insights; GET /industries; GET /countries |
| `backend/app/api/v1/routes/security_advanced.py` | 233 | 高级安全 API — FIX-13 国密算法 + FIX-14 零信任架构 · 函数:13 · 路由:POST /gmssl/encrypt; POST /gmssl/decrypt; POST /gmssl/hash; POST /gmssl/hmac; POST /gmssl/encrypt-record; GET /gmssl/status |
| `backend/app/api/v1/routes/seo_diagnosis.py` | 40 | SEO诊断工具路由 - 免费SEO诊断线索收集 · 类:DiagnosisLeadBody · 函数:1 · 路由:POST /seo-diagnosis |
| `backend/app/api/v1/routes/seo_matrix.py` | 2278 | 全国县域建材SEO矩阵系统 API路由 · 类:GenerateKeywordsBody,GenerateContentBody,PublishTaskCreate,RegionKeywordCreate,BatchIdsBody · 函数:60 · 路由:GET /settings; PUT /settings; GET /ai-config; POST /ai-config; GET /provinces; GET /provinces/{province_id}/cities · ⚑MOCK/DEGRADED |
| `backend/app/api/v1/routes/settings.py` | 83 | 系统设置路由 - 模块化架构 · 函数:4 · 路由:GET /; PUT /site; PUT /seo; PUT /system |
| `backend/app/api/v1/routes/site_ai_generator.py` | 76 | AI 独立站生成与发布路由。 · 类:GenerateSiteRequest,TranslateSiteRequest,PublishSiteRequest · 函数:4 · 路由:POST /generate; POST /translate; GET /locales; POST /publish |
| `backend/app/api/v1/routes/skill_store.py` | 100 | 技能商店 API — 参考 CocoLoop Skill Store 体系。 · 函数:8 · 路由:GET /catalog; GET /skills; GET /skills/{skill_id}; POST /skills/{skill_id}/risk-analyze; POST /code-scan; GET /featured |
| `backend/app/api/v1/routes/social_interactions.py` | 376 | Lane I · 社媒评论/私信自动谈单 API。 · 类:DouyinWebhookBody,ApproveBody,MarkSentBody,MarkFailedBody · 函数:13 · 路由:GET /worker/config; GET /summary; GET /; GET /negotiations; POST /webhook/douyin; POST /{interaction_id}/approve · ⚑MOCK |
| `backend/app/api/v1/routes/social_nurture.py` | 373 | 海外养号周期 API（持久化 + 频控 + 互动管理）。 · 类:NurtureCreateBody,NurtureTransitionBody,SchedulePublishBody,EngagementRecordBody · 函数:14 · 路由:GET /rules; GET /cycles; POST /cycles; POST /cycles/{cycle_id}/transition; POST /cycles/{cycle_id}/check; POST /cycles/{cycle_id}/advance |
| `backend/app/api/v1/routes/ssl_certificates.py` | 198 | SSL Certificate API Routes - Auto-issuance via Let's Encrypt. · 函数:5 · 路由:POST /; GET /; GET /{cert_id}; POST /{cert_id}/renew; POST /auto-renew |
| `backend/app/api/v1/routes/super_agent.py` | 1159 | UBrain 超级智能体 API 路由 · 类:ResearchRequest,InstructionRequest,ExecuteRequest,SkillExecuteRequest,CustomerFinderRequest,AutoNegotiatorRequest,EmailAutomationRequest,PerformanceRequest · 函数:32 · 路由:POST /research/start; GET /research/{report_id}; GET /research/{report_id}/status; POST /instructions/generate; POST /execute/{instruction_id}; GET /execution/{execution_id}/status · ⚑MOCK/STUB/DEGRADED |
| `backend/app/api/v1/routes/system.py` | 406 | 系统管理路由 - 整合版（合并 routes/system.py + system_routes.py） · 函数:17 · 路由:GET /health; GET /info; GET /logs; POST /cache/clear; GET /jwt/keys/status; POST /jwt/keys/rotate · ⚑DEGRADED |
| `backend/app/api/v1/routes/system_health.py` | 223 | 系统健康与压测路由 - 模块化架构 · 函数:10 · 路由:GET /; GET /cache-stats; GET /audit-logs; GET /stress-test; POST /stress-test; GET /resource-monitor · ⚑DEGRADED |
| `backend/app/api/v1/routes/talking_stick.py` | 155 | Talking-Stick 安全扫描API · 类:ScanRequest,ScanResponse,TaskStatusResponse · 函数:8 · 路由:POST /scan; GET /scan/{task_id}/status; GET /scan/{task_id}/result; DELETE /scan/{task_id}; GET /scans; DELETE /scans/completed |
| `backend/app/api/v1/routes/task_control_admin.py` | 277 | 统一任务控制面管理与人审干预 API 路由 (Human-in-the-Loop)。 · 类:TaskResumeRequest,TaskCancelRequest · 函数:7 · 路由:GET /pending-reviews; GET /{task_id}; POST /{task_id}/resume; POST /{task_id}/cancel; POST /{task_id}/retry |
| `backend/app/api/v1/routes/tech_radar.py` | 99 | GEO 技术雷达 API — 定时抓取 + 自动进化 · 类:ApplyFindingsRequest · 函数:4 · 路由:GET /tech-radar; GET /tech-radar/latest-techniques; GET /tech-radar/sources; POST /apply-findings |
| `backend/app/api/v1/routes/technical_qna.py` | 52 | Technical Q&A 路由 — 基于批准知识库的带引用技术问答（公开端点）。 · 类:TechnicalQnaRequest · 函数:1 · 路由:POST / |
| `backend/app/api/v1/routes/tenant_ai_config.py` | 291 | 租户级 AI 配置路由 · 函数:6 · 路由:GET /my-configs; POST /my-configs; PUT /my-configs/{config_id}; DELETE /my-configs/{config_id}; POST /test-config/{config_id}; GET /providers |
| `backend/app/api/v1/routes/tenants.py` | 1484 | SaaS多租户与商业化路由 - 真实数据库实现 · 类:TenantInvoiceGenerateBody,TenantInvoiceStatusBody,SiteAiGenerateRequest,OnboardingWizardCompleteRequest,OnboardingWangcaiPreviewRequest,OnboardingImContactsRequest,OnboardingPlatformBindRequest,OnboardingAutopilotRequest · 函数:49 · 路由:GET /invoices; POST /invoices/generate; PUT /invoices/{invoice_id}; GET /; GET /current; PUT /self |
| `backend/app/api/v1/routes/token_ledger.py` | 273 | Token 账本 API · 类:ConsumeRequest,TopUpRequest · 函数:8 · 路由:GET /balance/{tenant_id}; POST /consume; POST /topup; GET /my-quota; GET /my-ledger; GET /quota-status/{tenant_id} |
| `backend/app/api/v1/routes/trade_intel.py` | 214 | 出海参谋 — 公开查询 + 超管维护。 · 函数:11 · 路由:GET /feasibility; GET /blue-ocean; GET /matrix-stats; GET /market-sources; GET /customs-catalog; GET /customs-stats |
| `backend/app/api/v1/routes/ubrain.py` | 567 | UBrain 统一助手 API。 · 类:UBrainChatRequest,GeoContentMatrixRequest,UBrainMemoryPatch,MarkProspectContactedBody,ConfirmOutreachBody · 函数:19 · 路由:POST /chat; POST /geo-content-matrix; GET /inquiries/latest; GET /ops-snapshot; GET /action-audit; GET /action-audit/summary |
| `backend/app/api/v1/routes/ubrain_analytics.py` | 243 | UBrain AI Agent 决策追踪与效果归因 API · 类:TrackDecisionRequest,TrackExecutionRequest,TrackFeedbackRequest · 函数:7 · 路由:POST /track-decision; POST /track-execution; POST /track-feedback; GET /decision-chain/{decision_id}; GET /agent-performance/{node_id}; GET /attribution |
| `backend/app/api/v1/routes/ubrain_commercial_os.py` | 466 | 商业 OS 飞轮 API — Mem0/n8n/PostHog 外挂槽位。 · 类:GapExecuteRequest,ResearchBriefRequest,N8nWebhookBody · 函数:17 · 路由:GET /gaps; GET /partial-skills; GET /gap/{skill_id}; POST /gap/{skill_id}/execute; GET /skill-catalog; GET /research-brief/templates · ⚑STUB |
| `backend/app/api/v1/routes/unified_publish.py` | 411 | 统一发布台 API — 汇聚母版、任务、状态的一站式入口 · 类:BatchRetryRequest,BatchCancelRequest,QuickPublishRequest · 函数:8 · 路由:GET /dashboard; GET /tasks; POST /tasks/batch-retry; POST /tasks/batch-cancel; GET /tasks/{task_id}; POST /quick-publish |
| `backend/app/api/v1/routes/users.py` | 224 | 用户管理路由 · 函数:10 · 路由:GET /; GET /me; GET /logs; GET /{user_id}; POST /; PUT /{user_id} |
| `backend/app/api/v1/routes/vector_search.py` | 253 | Vector Search API - 向量检索路由 · 类:VectorSearchRequest,VectorUpsertRequest,HybridSearchRequest,VectorDeleteRequest · 函数:7 · 路由:POST /search; POST /upsert; POST /hybrid-search; DELETE /{collection}/{point_id}; POST /delete-batch; GET /collections |
| `backend/app/api/v1/routes/video_publish.py` | 575 | 统一视频发布 API — Hermes 编排，一个入口，真发到各视频平台。 · 类:AitoearnAssignBody,VideoDistributeBody,VideoMatrixHermesBody,VideoNoteDistributeBody · 函数:15 · 路由:GET /video/bind-hub; GET /video/sau-check; POST /video/note-distribute; GET /video/scheduled-queue; POST /video/sync-aitoearn; POST /video/admin/assign-aitoearn-slot |
| `backend/app/api/v1/routes/wallet.py` | 146 | 用户钱包路由 · 函数:7 · 路由:GET /balance; POST /deposit; POST /withdraw; POST /transfer; GET /transactions; GET /monthly-stats · ⚑MOCK |
| `backend/app/api/v1/routes/wangcai_marketplace.py` | 225 | 旺财插件市场 — 对外 API（不含 Hermes / 第三方商标）。 · 类:InstallBody,ToggleBody,RunBody · 函数:6 · 路由:GET /marketplace; GET /browser-companions; GET /installed; POST /{plugin_id}/install; PATCH /{plugin_id}/enabled; POST /{plugin_id}/run |
| `backend/app/api/v1/routes/whatsapp_business.py` | 361 | WhatsApp Business Cloud API 路由 — FIX-54 · 函数:17 · 路由:POST /send/text; POST /send/template; POST /send/image; POST /send/document; POST /send/interactive; POST /templates |
| `backend/app/api/v1/routes/workflow_canvas.py` | 30 | 类:WorkflowNode,WorkflowEdge,WorkflowRequest · 函数:1 · 路由:POST /execute |
| `backend/app/api/v1/routes/workspace.py` | 277 | 搜客执行台 + 写信台 路由（P1-1 + P1-2）。 · 函数:9 · 路由:POST /prospecting/search; GET /prospecting/leads; GET /prospecting/leads/{lead_id}; POST /prospecting/leads/{lead_id}/convert; POST /outreach/ai-generate; POST /outreach/drafts |
| `backend/app/api/v1/seo/__init__.py` | 111 | 函数:6 · 路由:POST /audits; GET /audits; GET /audits/{audit_id}; GET /llms; POST /llms; PUT /llms/{config_id} |
| `backend/app/api/v1/seo/batch_seo.py` | 309 | 类:BatchApplyRuleRequest · 函数:6 · 路由:GET /seo-batch-list; GET /pages; PUT /pages/{resource_id}; POST /pages/{resource_id}/optimize; POST /seo-batch-apply-rule |
| `backend/app/api/v1/seo/compliance.py` | 358 | 合规检查API路由 - 广告法检测 · 函数:13 · 路由:POST /scan; POST /scan-batch; GET /scan-result/{scan_id}; GET /scan-history; GET /keywords; GET /keywords/categories |
| `backend/app/api/v1/seo/content_optimizer.py` | 101 | 类:OptimizeRequest,ValidateRequest,ExtractParamsRequest · 函数:3 · 路由:POST /optimize; POST /validate-content; POST /extract-params |
| `backend/app/api/v1/seo/dashboard.py` | 484 | 类:AuditRunRequest · 函数:13 · 路由:GET /dashboard; GET /keyword-ranking/{keyword_id}; GET /keyword-groups; GET /seo-pages-summary; POST /run-audit · ⚑DEGRADED |
| `backend/app/api/v1/seo/eeat.py` | 479 | 函数:15 · 路由:POST /authors; GET /authors; GET /authors/{author_id}; PUT /authors/{author_id}; DELETE /authors/{author_id}; POST /authors/{author_id}/certifications |
| `backend/app/api/v1/seo/keyword_ranking.py` | 288 | 关键词排名API - Phase 4 · 类:KeywordCreate,KeywordUpdate,KeywordResponse,RankingHistoryResponse,TrackKeywordsRequest,TrackKeywordsResponse · 函数:9 · 路由:GET /dashboard/summary; GET /; POST /; PUT /{keyword_id}; DELETE /{keyword_id}; POST /track |
| `backend/app/api/v1/seo/llms_txt.py` | 166 | 类:GenerateRequest,ValidateRequest · 函数:3 · 路由:POST /generate; POST /validate-llms-txt; GET /llms-txt-template |
| `backend/app/api/v1/seo/llms_txt_generator.py` | 178 | 函数:4 · 路由:GET /llms.txt |
| `backend/app/api/v1/seo/report_export.py` | 71 | SEO 报告导出。 · 函数:1 · 路由:GET /report/export |
| `backend/app/api/v1/seo/schema_markup.py` | 175 | 函数:11 · 路由:GET /types; GET /template/{schema_type}; POST /generate; POST /validate; GET /; GET /{markup_id} |
| `backend/app/api/v1/seo/site_audit.py` | 63 | 函数:3 · 路由:POST /; GET /; GET /{audit_id} |
| `backend/app/api/v1/seo_metadata.py` | 185 | SEO Metadata API Router - SEO元数据API · 函数:6 · 路由:POST /; GET /{seo_id}; GET /by-entity; PUT /{seo_id}; DELETE /{seo_id}; GET / |
| `backend/app/api/v1/site_builder.py` | 143 | 一键建站 API 路由 — POST /api/v1/sites/build。 · 类:SiteBuildRequest,SiteBuildPageResponse,SiteBuildResponse · 函数:2 · 路由:POST /build; POST /build/async · ⚑STUB |
| `backend/app/api/v1/sitemap.py` | 77 | 函数:1 · 路由:GET /sitemap.xml |
| `backend/app/api/v1/super_admin/__init__.py` | 58 | 超级管理员后台 API - 统一路由分组 |
| `backend/app/api/v1/super_admin/agent.py` | 249 | 智能代理工作流 API — 进程监控/管理 + MCP Bridge · 类:MCPConfigUpdate · 函数:7 · 路由:GET /status; POST /{agent_id}/start; POST /{agent_id}/stop; GET /system/resources; GET /mcp/config; POST /mcp/config |
| `backend/app/api/v1/super_admin/aggregation.py` | 231 | 超管数据中心 — 代理层级 + 全平台流量汇总。 · 函数:7 · 路由:GET /aggregation; GET /traffic-board |
| `backend/app/api/v1/super_admin/ai_config.py` | 585 | AI 模型配置管理接口 · 类:AIProviderCreate,AIProviderPatch,AIModelCreate,AIModelPatch · 函数:24 · 路由:GET /providers; POST /providers; PUT /providers/{provider_id}; DELETE /providers/{provider_id}; GET /models; POST /models/probe |
| `backend/app/api/v1/super_admin/ai_cost.py` | 161 | AI 成本分析 API · 函数:7 · 路由:GET /summary; GET /by-model; GET /overview; GET /daily; GET /alerts; POST /alarm-config |
| `backend/app/api/v1/super_admin/alerts.py` | 218 | 告警中心 API · 类:AlertRuleCreate · 函数:9 · 路由:GET /rules; POST /rules; PUT /rules/{rule_id}; DELETE /rules/{rule_id}; GET /events; POST /events/{event_id}/acknowledge |
| `backend/app/api/v1/super_admin/audit.py` | 115 | 操作日志接口 · 函数:4 · 路由:GET /; GET /actions; POST /; DELETE / |
| `backend/app/api/v1/super_admin/auth.py` | 212 | 超级管理员认证接口 · 类:AdminLoginRequest,AdminCreateRequest,AdminPasswordReset · 函数:5 · 路由:POST /login; POST /logout; GET /me; POST /create-first-admin |
| `backend/app/api/v1/super_admin/backup.py` | 36 | 自动备份 API · 函数:2 · 路由:GET /status; POST /run |
| `backend/app/api/v1/super_admin/cc_switch.py` | 176 | CC Haha / CC Switch 中转配置管理接口 · 类:CCSwitchCreate,CCSwitchUpdate · 函数:6 · 路由:GET /; POST /; PUT /{config_id}; DELETE /{config_id}; POST /{config_id}/health-check |
| `backend/app/api/v1/super_admin/dashboard.py` | 129 | 控制台大盘接口 · 函数:4 · 路由:GET /stats; GET /ai-usage; GET /system-status; POST /score-content |
| `backend/app/api/v1/super_admin/geo_engine.py` | 1034 | GEO 引擎 API — 各大模型关键词收录查询 · 类:CheckRequest,BatchCheckRequest,EvaluateContentRequest,RankGuardCheckRequest,MonitorPlanRequest,CreateGEORankRuleRequest,CreateGEOInquiryRuleRequest,GenerateRequest · 函数:45 · 路由:POST /recommend-probe; GET /models; POST /check; POST /batch-check; POST /score; POST /competitor · ⚑MOCK |
| `backend/app/api/v1/super_admin/langchain.py` | 135 | LangChain 控制台 API — 流式对话 + 会话管理 + 知识库 RAG · 类:ChatRequest,RAGRequest · 函数:6 · 路由:POST /chat/stream; POST /rag/query; GET /sessions; GET /sessions/{session_id}; DELETE /sessions/{session_id}; GET /models/available · ⚑DEGRADED |
| `backend/app/api/v1/super_admin/menus.py` | 32 | 后台菜单接口 · 函数:2 · 路由:GET /tree; POST /refresh |
| `backend/app/api/v1/super_admin/monitor.py` | 159 | 系统监控 & 运维接口 · 函数:5 · 路由:GET /system; GET /redis; POST /cache/clear; GET /cache/keys; GET /ai-stats |
| `backend/app/api/v1/super_admin/permissions.py` | 260 | 角色 & 权限管理接口 · 类:RoleCreate,RoleUpdate,MenuCreate · 函数:9 · 路由:GET /roles; POST /roles; PUT /roles/{role_id}; DELETE /roles/{role_id}; GET /codes; GET /codes/groups |
| `backend/app/api/v1/super_admin/platform_registry.py` | 97 | 超管：客户新增/自填平台来源审计（只读）。 · 函数:1 · 路由:GET /platform-origins |
| `backend/app/api/v1/super_admin/products.py` | 24 | 产品 API — 材料规格查询 · 函数:2 · 路由:GET /; GET /{slug} |
| `backend/app/api/v1/super_admin/reports.py` | 158 | 数据导出报表 API · 函数:4 · 路由:GET /weekly; GET /monthly; GET /export/csv |
| `backend/app/api/v1/super_admin/search.py` | 91 | 全局搜索 API — 跨模块搜索 · 函数:2 · 路由:GET / |
| `backend/app/api/v1/super_admin/seo_proxy.py` | 121 | SEO Backend 反向代理 — 统一 API 网关 · 函数:7 · 路由:GET /health; GET /{path:path}; POST /{path:path}; PUT /{path:path}; DELETE /{path:path}; PATCH /{path:path} |
| `backend/app/api/v1/super_admin/storage_provision.py` | 149 | 超管：平台产品图存储（七牛 / R2）开通与验收。 · 类:QiniuVerifyBody,R2VerifyBody,VerifyRequest · 函数:5 · 路由:GET /status; GET /checklist; GET /env-snippet; POST /verify-current; POST /verify · ⚑MOCK |
| `backend/app/api/v1/super_admin/tenants.py` | 30 | 超级管理员 - 租户管理接口 · 函数:1 · 路由:GET / |
| `backend/app/api/v1/super_admin/users.py` | 214 | 管理员用户管理接口 · 类:AdminUserCreate,AdminUserUpdate · 函数:7 · 路由:GET /; POST /; PUT /{user_id}; DELETE /{user_id}; POST /{user_id}/reset-password; GET /login-logs |
| `backend/app/api/v1/super_admin/v2ray_subscriptions.py` | 119 | V2Ray 订阅管理 API — 与前端 v2rayAPI / subscription.vue 对齐。 · 类:SubscriptionCreate · 函数:7 · 路由:GET /subscriptions; POST /subscriptions; POST /subscriptions/{sub_id}/refresh; DELETE /subscriptions/{sub_id}; GET /routing; GET /servers |
| `backend/app/api/v1/super_admin/v2ray_tracker.py` | 76 | V2Ray Tracker API - 版本追踪与状态检查 · 函数:5 · 路由:GET /status; GET /releases; POST /check-now; POST /start; GET /traffic |
| `backend/app/api/v1/system/performance.py` | 94 | 性能和安全管理API · 函数:6 · 路由:GET /metrics; GET /health; GET /report; POST /security/audit; GET /security/report; GET /security/issues |
| `backend/app/api/v1/system_config.py` | 149 | System Config API Router - 系统配置API · 函数:6 · 路由:POST /; GET /{config_id}; GET /by-key/{key}; PUT /{config_id}; DELETE /{config_id}; GET / |
| `backend/app/api/v1/system_routes.py` | 206 | 函数:8 · 路由:POST /login; POST /contact; GET /audit/logs; GET /audit/logs/{log_id}; DELETE /audit/logs/{log_id}; DELETE /audit/logs |
| `backend/app/api/v1/users.py` | 190 | 类:UserCreate,UserUpdate,UserResponse · 函数:6 · 路由:GET /users; POST /users; PUT /users/{user_id}; DELETE /users/{user_id}; GET /roles |
| `backend/app/core/__init__.py` | 1 | Core package |
| `backend/app/core/access_token_blacklist.py` | 104 | Access Token 黑名单：登出后将 JWT jti 加入黑名单，阻止已登出令牌继续使用。 · 函数:5 · ⚑DEGRADED |
| `backend/app/core/admin_auth.py` | 265 | 超级管理员 RBAC 权限鉴权 · 函数:11 |
| `backend/app/core/audit.py` | 116 | 类:AuditMiddleware |
| `backend/app/core/bootstrap.py` | 325 | 应用启动引导模块 — 从 main.py lifespan 中提取调度器启动逻辑，保持行为一致。 · 类:SchedulerSlot · 函数:11 |
| `backend/app/core/brand_guard_middleware.py` | 81 | UB-06：租户可见 API 响应统一品牌脱敏。 · 类:BrandGuardResponseMiddleware |
| `backend/app/core/cache.py` | 566 | 缓存工具模块 — FIX-24: 三级缓存架构 · 函数:32 |
| `backend/app/core/cache_decorator.py` | 163 | 函数:5 |
| `backend/app/core/celery_app.py` | 231 | Celery 异步任务队列 — FIX-43 · 类:AsyncTaskFallback · 函数:6 · ⚑DEGRADED |
| `backend/app/core/circuit_breaker.py` | 165 | 类:CircuitState,CircuitBreakerError,CircuitOpenError,CircuitBreaker,CircuitBreakerRegistry |
| `backend/app/core/config.py` | 1106 | 类:Settings · 函数:1 · ⚑MOCK/STUB/DEGRADED |
| `backend/app/core/csrf_middleware.py` | 164 | CSRF Protection Middleware · 类:CSRFMiddleware · 函数:2 · ⚑DEGRADED |
| `backend/app/core/data_classification.py` | 237 | 数据安全分级分类 — FIX-26: 数据安全分级 + 字段级敏感标签 · 类:DataClassification · 函数:9 |
| `backend/app/core/data_export_guard.py` | 97 | 数据导出门禁：平台级导出仅创始人 + 全量留痕。 · 函数:2 |
| `backend/app/core/database.py` | 250 | 类:RoutingSession,Base · 函数:9 · ⚑STUB |
| `backend/app/core/deps/tenant_quota.py` | 18 | 租户 Token 配额 — AI 类路由统一扣费入口。 · 函数:1 |
| `backend/app/core/event_bus.py` | 430 | 事件总线 + 事件驱动架构 — FIX-41 · 类:EventPriority,Event,EventEnvelope,EventTypes,EventBus · 函数:5 |
| `backend/app/core/events/__init__.py` | 14 | 领域事件定义模块。 |
| `backend/app/core/events/task_events.py` | 93 | 任务控制相关的领域事件定义。 · 类:TaskEventPayload,TaskCompletedPayload,TaskFailedPayload · 函数:2 |
| `backend/app/core/exceptions.py` | 306 | 类:ErrorCode,AppException · 函数:10 · ⚑MOCK |
| `backend/app/core/executable_resolver.py` | 154 | Resolve CLI executables on Windows (uvicorn subprocess often lacks WinGet shim PATH). · 函数:6 |
| `backend/app/core/execution_context.py` | 115 | Skill 执行上下文（移植自 Trade AI Agent `app/core/context.py`，MIT，保留出处）。 · 类:ExecutionContext · 函数:1 |
| `backend/app/core/field_crypto.py` | 56 | 字段级加密：AES-256-GCM，用于敏感 PII 字段（email/phone）。 · 函数:3 |
| `backend/app/core/founder_debug_gate.py` | 223 | 创始人专属调试门禁：超管 + 微信唯一（优先）或开发令牌 + 可选 IP。 · 函数:9 |
| `backend/app/core/gm_crypto.py` | 186 | 国密 SM2/SM3/SM4 工具（敏感字段加密、完整性校验、接口签名）。 · 类:GMCryptoError · 函数:11 · ⚑DEGRADED |
| `backend/app/core/i18n.py` | 55 | 后端 i18n 脚手架（M7，ADR-002 附带交付）。 · 函数:2 |
| `backend/app/core/jwt_cookie.py` | 208 | JWT HttpOnly Cookie 工具 — FIX-22: 安全升级，Token 不再暴露给 JavaScript。 · 函数:7 |
| `backend/app/core/jwt_key_rotation.py` | 363 | JWT 密钥轮换服务 · 类:JWTKeyRotationService |
| `backend/app/core/layer_marker.py` | 21 | 函数:5 |
| `backend/app/core/log_context.py` | 31 | 函数:3 |
| `backend/app/core/logging.py` | 10 | 日志模块 — app.core.logging_config 的兼容层。 · 函数:1 |
| `backend/app/core/logging_config.py` | 393 | 日志轮转和监控告警配置 · 类:ContextEnrichFilter,StructuredJsonFormatter,MaskedConsoleFormatter,LogConfig,AlertManager · 函数:4 |
| `backend/app/core/login_bruteforce.py` | 394 | 登录暴力破解防护：优先 Redis（多实例共享），失败降级进程内内存；接口与阈值行为保持不变。 · 类:_Entry · 函数:18 · ⚑DEGRADED |
| `backend/app/core/middleware_fastlane.py` | 67 | 中间件快速通道 — 探针/静态/大响应体跳过昂贵逻辑。 · 函数:4 |
| `backend/app/core/no_fake_delivery.py` | 136 | 禁止假交付 — 生产路径门控助手。 · 类:NotConfiguredError,FakeDeliveryViolation · 函数:8 · ⚑MOCK |
| `backend/app/core/no_fake_delivery_guard.py` | 155 | 禁止假交付 — 出站响应扫描（生产路径硬拒绝）。 · 函数:6 · ⚑MOCK |
| `backend/app/core/no_fake_delivery_middleware.py` | 86 | 生产路径出站 JSON 假交付扫描中间件。 · 类:NoFakeDeliveryResponseMiddleware · ⚑MOCK |
| `backend/app/core/opentelemetry_config.py` | 180 | OpenTelemetry配置 - 分布式追踪 (租户隔离增强) · 函数:7 · ⚑DEGRADED |
| `backend/app/core/performance_middleware.py` | 99 | 性能监控中间件 - 自动追踪API请求性能 · 类:PerformanceMiddleware |
| `backend/app/core/permission_deps.py` | 129 | 权限依赖模块 - 统一权限检查 · 类:PermissionChecker · 函数:3 |
| `backend/app/core/permissions.py` | 318 | 类:Role · 函数:6 |
| `backend/app/core/product_commerce.py` | 427 | 产品价值主张与计费体系 — FIX-32/33/34: 产品商业化核心 · 类:ValueProposition,PlanTier,PlanConfig,CreditType,CreditAction,CreditPack · 函数:3 |
| `backend/app/core/rate_limit.py` | 597 | API限流中间件 · 类:SlidingWindowRateLimiter,RedisSlidingWindowRateLimiter,RateLimitMiddleware · 函数:10 · ⚑DEGRADED |
| `backend/app/core/refresh_token_blacklist.py` | 245 | Refresh 令牌轮转黑名单：优先 Redis（多实例 / 重启后仍拒绝已吊销 refresh），失败降级进程内内存。 · 函数:13 · ⚑DEGRADED |
| `backend/app/core/repository.py` | 411 | Repository 层 — FIX-42 · 类:BaseRepository,ProspectLeadRepository,EmailOutreachRepository · 函数:2 |
| `backend/app/core/request_id_middleware.py` | 103 | 请求 ID / trace_id 贯穿中间件（审计 CLOSE-09）。 · 类:TraceIdLogFilter,RequestIdMiddleware · 函数:3 |
| `backend/app/core/request_signature.py` | 216 | API 请求签名 + 防重放中间件 — FIX-29: 安全增强 · 类:RequestSignatureMiddleware · 函数:4 · ⚑DEGRADED |
| `backend/app/core/resilience.py` | 110 | 函数:5 · ⚑DEGRADED |
| `backend/app/core/response.py` | 106 | 统一API响应格式 · 类:APIResponse,ErrorDetail,ValidationErrorResponse · 函数:4 · ⚑STUB |
| `backend/app/core/security.py` | 350 | 函数:15 · ⚑DEPRECATED |
| `backend/app/core/security/__init__.py` | 65 | Security package: ClawPatrol + JWT/auth (re-export from app.core.security.py). |
| `backend/app/core/security/claw_patrol.py` | 361 | Claw Patrol - AI安全防火墙 · 类:ThreatLevel,SecurityIssue,ClawPatrolFirewall · 函数:2 |
| `backend/app/core/security/rls.py` | 284 | PostgreSQL Row Level Security (RLS) — 数据库层租户隔离 · 函数:8 · ⚑STUB |
| `backend/app/core/security/runtime_isolation.py` | 209 | 运行时租户隔离 — 应用层访问控制 · 类:TenantAccessDenied · 函数:4 |
| `backend/app/core/security_headers.py` | 182 | HTTP安全响应头中间件 · 类:SecurityHeadersMiddleware,APISecurityHeadersMiddleware |
| `backend/app/core/security_middleware.py` | 199 | 安全中间件模块 — 路径安全 + 限流 · 类:SecurityMiddleware,RateLimitMiddleware · 函数:1 · ⚑DEGRADED |
| `backend/app/core/security_tools.py` | 222 | 函数:11 |
| `backend/app/core/sqlite_paths.py` | 66 | Resolve SQLite DATABASE_URL to a real file (backend vs repo root). · 函数:3 · ⚑STUB |
| `backend/app/core/ssl_config.py` | 216 | HTTPS证书配置和SSL中间件 · 类:SSLConfig · 函数:1 |
| `backend/app/core/tasks.py` | 155 | 异步任务模块 · 函数:6 |
| `backend/app/core/tenant_access.py` | 224 | 租户侧访问控制 — ROLE_PERMISSIONS + 超管 DB 权限码 + 路由守卫。 · 函数:13 |
| `backend/app/core/tenant_middleware.py` | 417 | SaaS 租户中间件 - 从请求域名识别租户 · 类:TenantMiddleware · 函数:5 · ⚑STUB/DEGRADED |
| `backend/app/core/tenant_scope.py` | 44 | 共享租户作用域助手（ADR-002 应用层隔离第一道防线）。 · 函数:3 |
| `backend/app/core/unify_response_middleware.py` | 188 | 将 /api/v1 下「未带 code 字段」的 JSON 成功响应统一包装为 APIResponse， · 类:UnifyV1ApiResponseMiddleware · 函数:1 |
| `backend/app/core/uploads_path.py` | 39 | 本地上传目录 — files API 与 StaticFiles 挂载须共用同一路径。 · 函数:3 |
| `backend/app/core/validation.py` | 245 | 输入验证模块 · 类:ValidationResult · 函数:14 |
| `backend/app/core/waf.py` | 466 | WAF防火墙规则配置 · 类:WAFMiddleware,IPBlacklistMiddleware,RequestSizeLimitMiddleware · 函数:1 |
| `backend/app/data/__init__.py` | 238 | 平台配置加载 —— 数据库优先，JSON 兜底。 · 函数:6 · ⚑STUB/DEGRADED |
| `backend/app/db/__init__.py` | 0 |  |
| `backend/app/db/rls_policies.py` | 267 | RLS 试点策略（总纲 §8 088_rls_pilot，轮 25-A）。 · 类:RLSPolicy · 函数:6 |
| `backend/app/db/schema_healer.py` | 142 | 数据库 Schema 自动修复 — 启动时检测并补全缺失列 · 函数:4 |
| `backend/app/db/seed.py` | 363 | 超级管理员种子数据初始化 · 函数:10 |
| `backend/app/db/session.py` | 325 | 数据库会话 — 从 app.core.database 统一 get_db，避免双引擎问题 · 函数:8 |
| `backend/app/domains/__init__.py` | 57 | 领域模块注册中心 — FIX-31: 模块单体架构 · 函数:2 |
| `backend/app/domains/ai/__init__.py` | 20 | AI智能领域 — stub（待从 routes/ai_*.py 迁移） · 类:AiDomain |
| `backend/app/domains/auth/__init__.py` | 20 | 认证授权领域 — stub（待从 routes/auth.py 迁移） · 类:AuthDomain |
| `backend/app/domains/base.py` | 69 | 领域模块基类 — FIX-31: 模块单体架构 · 类:DomainModule |
| `backend/app/domains/content/__init__.py` | 20 | 内容管理领域 — stub（待从 routes/content.py 迁移） · 类:ContentDomain |
| `backend/app/domains/inquiry/__init__.py` | 20 | 询盘管理领域 — stub（待从 routes/inquiries.py 迁移） · 类:InquiryDomain |
| `backend/app/domains/lead/__init__.py` | 40 | 获客引擎领域 — FIX-31: 首个完整领域模块迁移 · 类:LeadDomain |
| `backend/app/domains/lead/routes.py` | 343 | 获客引擎领域 API 路由 — FIX-31 · 函数:11 · 路由:POST /search; GET /search/{task_id}/progress; POST /verify-email; POST /verify-emails/batch; POST /scrape-emails; POST /send · ⚑DEGRADED |
| `backend/app/domains/payment/__init__.py` | 20 | 支付财务领域 — stub（待从 routes/payment.py, finance.py 迁移） · 类:PaymentDomain |
| `backend/app/domains/product/__init__.py` | 20 | 产品管理领域 — stub（待从 routes/products.py 迁移） · 类:ProductDomain |
| `backend/app/domains/public/__init__.py` | 20 | 公开API领域 — stub（待从 routes/public_*.py 迁移） · 类:PublicDomain |
| `backend/app/domains/seo/__init__.py` | 20 | SEO优化领域 — stub（待从 routes/seo_*.py 迁移） · 类:SeoDomain |
| `backend/app/domains/system/__init__.py` | 20 | 系统管理领域 — stub（待从 routes/system.py, settings.py 迁移） · 类:SystemDomain |
| `backend/app/domains/tenant/__init__.py` | 20 | 租户管理领域 — stub（待从 routes/tenants.py 迁移） · 类:TenantDomain |
| `backend/app/geo_engine/database_new.py` | 96 | GEO Engine Database Module - Using databases library · 类:GeoDatabase |
| `backend/app/geo_engine/geo_optimizer.py` | 638 | 类:GEORecommendation,GEOScore,GEOOptimizer,ABTestVariant,ABTestResult,GEOABTestFramework |
| `backend/app/geo_engine/rank_monitor.py` | 504 | Rank Monitor - 排名监控器 · 类:SearchEngine,RankChangeType,RankPosition,RankChange,RankMonitor · ⚑MOCK/DEGRADED |
| `backend/app/geo_engine/repositories.py` | 1011 | 函数:21 |
| `backend/app/graduation/manager.py` | 262 | 灰度发布管理服务 · 类:GraduationManager · 函数:1 |
| `backend/app/graduation/models.py` | 138 | 功能开关（Feature Flag）模型 · 类:FeatureStatus,RolloutStrategy,FeatureFlag |
| `backend/app/main.py` | 743 | FastAPI主应用 · 函数:15 · 路由:GET /; GET /health; GET /health/ready · ⚑MOCK |
| `backend/app/models/__init__.py` | 287 |  |
| `backend/app/models/ab_test.py` | 190 | A/B 测试数据模型 · 类:ABTest,ABTestVariant,ABTestEvent,ABTestConversion · 表:ab_tests,ab_test_variants,ab_test_events,ab_test_conversions |
| `backend/app/models/admin.py` | 168 | 超级管理员 RBAC 模型 · 类:AdminRole,AdminPermission,RolePermission,AdminMenu,LoginLog · 函数:1 · 表:admin_roles,admin_permissions,role_permissions,admin_menus,super_admin_login_logs |
| `backend/app/models/agent_commission_rule.py` | 29 | 多级代理分润规则表（首单 / 续费 × 层级）。 · 类:AgentCommissionRule · 表:agent_commission_rules |
| `backend/app/models/agent_tree.py` | 82 | 代理层级关系树 · 类:AgentNode · 表:agent_nodes |
| `backend/app/models/ai_config.py` | 148 | 类:TenantAiProviderConfig,AIModelProvider,AIModelConfig,CCSwitchConfig,AIUsageLog · 表:tenant_ai_provider_configs,ai_model_providers,ai_model_configs,cc_switch_configs,ai_usage_logs |
| `backend/app/models/ai_knowledge.py` | 63 | 类:AiKnowledgeBase,AiChatSession,AiChatMessage · 表:ai_knowledge_base,ai_chat_sessions,ai_chat_messages |
| `backend/app/models/ai_recommendation.py` | 33 | AI Recommendation Model - AI推荐模型 · 类:AIRecommendation · 表:ai_recommendations |
| `backend/app/models/ai_task.py` | 103 | 统一任务控制面模型（总纲 §4.6-1 / §8 082_unify_ai_tasks；轮23 补 ORM 映射）。 · 类:AiTask · 函数:2 · 表:ai_tasks · ⚑DEGRADED |
| `backend/app/models/ai_template.py` | 44 | AI 内容生成模板模型 · 类:AITemplate · 表:ai_templates |
| `backend/app/models/ai_visibility.py` | 89 | GEO / AI Visibility 数据模型 — AI 搜索可见性监控（Phase 6） · 类:AIQuery,AIQueryRun,AIMention,AICitation,CompetitorMention,VisibilityScore · 表:ai_queries,ai_query_runs,ai_mentions,ai_citations,competitor_mentions,visibility_scores |
| `backend/app/models/alert.py` | 63 | 告警中心模型 · 类:AlertRule,AlertEvent · 表:alert_rules,alert_events |
| `backend/app/models/app_device.py` | 29 | 出海计 App — 推送设备注册。 · 类:AppDevice · 表:app_devices |
| `backend/app/models/campaign.py` | 75 | Campaign / ABM 数据模型 — AI Outbound 序列（Phase 5） · 类:Campaign,CampaignStep,CampaignRecipient,CampaignEvent · 表:campaigns,campaign_steps,campaign_recipients,campaign_events |
| `backend/app/models/case_study.py` | 68 | 类:CaseStudy,CaseImage · 表:case_studies,case_images |
| `backend/app/models/chat_message.py` | 32 | Chat Message Model - AI对话消息模型 · 类:ChatMessage · 表:chat_messages |
| `backend/app/models/chat_session.py` | 34 | Chat Session Model - AI对话会话模型 · 类:ChatSession · 表:chat_sessions |
| `backend/app/models/commission_settlement.py` | 25 | 代理分润结算单 · 类:AgentCommissionSettlement · 表:agent_commission_settlements |
| `backend/app/models/company.py` | 142 | Company 360 - B2B 公司主数据 + 联系人 + 采购信号（Phase 3 地基） · 类:JSONType,Company,CompanyContact,CompanySignal,IntentEngineRun · 表:companies,company_contacts,company_signals,intent_engine_runs |
| `backend/app/models/compliance.py` | 80 | 合规检查相关数据库模型 · 类:ComplianceRule,ComplianceScanResult,ComplianceViolation,AdvertisementLawKeyword · 表:compliance_rules,compliance_scan_results,compliance_violations,ad_law_keywords |
| `backend/app/models/content.py` | 372 | 类:ContentPage,ContentVersion,ContentTemplate,GeneratedContent,Platform,PlatformAccount,PlatformConfig,PublishTask · 表:content_pages,content_versions,content_templates,generated_contents,platforms,platform_accounts,platform_configs,publish_tasks,publish_logs,inclusion_status,system_settings,ai_generation_configs,risk_control_configs |
| `backend/app/models/content_feedback.py` | 85 | Content Feedback Loop — DB models for feedback checks and industry patterns. · 类:ContentFeedbackCheck,IndustryPattern · 表:content_feedback_checks,industry_patterns |
| `backend/app/models/content_master.py` | 37 | 统一发布母版 — 一篇内容多发各平台 · 类:ContentMaster · 表:content_masters |
| `backend/app/models/deerflow_job.py` | 37 | DeerFlow / UBrain-X 异步任务队列。 · 类:DeerflowJob · 表:deerflow_jobs |
| `backend/app/models/eeat.py` | 90 | 类:Author,AuthorCertification,ArticleAuthor,EEATScore,TrustSignal · 表:eeat_authors,eeat_author_certifications,eeat_article_authors,eeat_scores,eeat_trust_signals |
| `backend/app/models/egress.py` | 168 | 静态 IP 槽位与浏览器指纹环境 · 类:EgressEndpoint,EgressProvisionJob,EgressCostRecord,EgressPoolReplenishJob,BrowserProfile,EgressSupplier · 表:egress_endpoints,egress_provision_jobs,egress_cost_records,egress_pool_replenish_jobs,browser_profiles,egress_suppliers · ⚑MOCK |
| `backend/app/models/email_outreach.py` | 179 | 邮件外联模型 —— 状态机 + 幂等 + 全链路追踪 · 类:EmailStatus,BounceType,EmailOutreach · 表:email_outreachs |
| `backend/app/models/email_tracking_event.py` | 49 | 邮件追踪事件模型（P1-3）—— 打开/点击/回复事件记录。 · 类:EmailEventType,EmailTrackingEvent · 表:email_tracking_events |
| `backend/app/models/enums.py` | 112 | 状态枚举定义 —— ORCH-08/09/10 修复 · 类:OrderStatus,PaymentStatus,OpportunityStage,LeadStatus · 函数:1 |
| `backend/app/models/evolution.py` | 253 | AI 进化引擎数据模型。 · 类:EvolutionTaskRecord,ExperienceEntry,SkillVersion,SOPVersion,ApprovalRecord,CanaryRouteRecord · 表:evolution_task_records,evolution_experiences,evolution_skill_versions,evolution_sop_versions,evolution_approvals,evolution_canary_routes |
| `backend/app/models/feishu.py` | 44 | 类:FeishuBinding,FeishuMessageLog · 表:feishu_bindings,feishu_message_logs |
| `backend/app/models/finance_ledger.py` | 28 | 财务台账 — 营收/成本流水（MVP） · 类:FinanceLedgerEntry · 表:finance_ledger_entries |
| `backend/app/models/geo_alert_db_models.py` | 68 | GEO Alert Models - SQLAlchemy 模型 · 类:GEOAlertRule,GEOAlert,GEOAlertHistory · 表:geo_alert_rules,geo_alerts,geo_alert_histories |
| `backend/app/models/geo_alert_models.py` | 116 | GEO Alert Models - 预警数据模型 · 类:AlertSeverity,AlertType,AlertStatus,AlertRuleCreate,AlertRuleResponse,AlertCreate,AlertResponse,AlertAcknowledge |
| `backend/app/models/geo_sourcechain_models.py` | 114 | GEO SourceChain Models - SourceChain GEO Engine database models (non-alert tables) · 类:MaterialSpec,ContentChunk,SERPSnapshot,LeadInquiry,ReleaseGuard · 表:material_specs,content_chunks,serp_snapshots,lead_inquiries,release_guards |
| `backend/app/models/globalization.py` | 93 | 全球化多语言模型 · 类:GlossaryTerm,TranslationTask,TranslationRecord · 表:glossary_terms,translation_tasks,translation_records |
| `backend/app/models/growth_tools.py` | 58 | 增长工具 — 专属词库条目（行业/品牌/竞品/需求）+ Agent 跑盘记录。 · 类:GrowthKeywordEntry,GrowthAgentRun · 表:growth_keyword_entries,growth_agent_runs |
| `backend/app/models/hermes_plugin.py` | 31 | Hermes 插件安装态（租户级）。 · 类:HermesPluginInstall · 表:hermes_plugin_installs |
| `backend/app/models/im_chat.py` | 65 | 聊天消息数据库模型（IM用户间聊天，与AI聊天分开） · 类:IMMessage,IMSession,UserStatus · 表:im_messages,im_sessions,user_status |
| `backend/app/models/im_routing_and_specs.py` | 118 | 商家IM路由配置表和建材垂直参数表 - SQLAlchemy ORM模型 · 类:MerchantIMRouting,BuildingMaterialSpec · 表:merchant_im_routing,building_material_specs |
| `backend/app/models/inquiry.py` | 53 | Inquiry Model - 询盘模型 · 类:Inquiry · 表:inquiries |
| `backend/app/models/international.py` | 69 | 国际询盘采集系统 - 独立于国内业务的数据库模型 · 类:InternationalTargetSite,InternationalInquiry,InternationalCrawlLog · 表:international_target_sites,international_inquiries,international_crawl_logs |
| `backend/app/models/invoice_application.py` | 99 | 增值税发票开票申请（合规：申请≠已开票，须财务审核及税控开具）。 · 类:PlatformInvoiceConfig,TenantInvoiceProfile,InvoiceApplication · 表:platform_invoice_configs,tenant_invoice_profiles,invoice_applications |
| `backend/app/models/license.py` | 110 | License Model - 许可证管理模型（P1-5 扩展：设备指纹 + 授权码 + 套餐订单） · 类:License,DeviceFingerprint,LicenseCode,LicenseOrder · 表:licenses,device_fingerprints,license_codes,license_orders |
| `backend/app/models/media_factory.py` | 62 | 多媒体工厂：渲染任务模型。 · 类:MediaRenderTask · 表:media_render_tasks |
| `backend/app/models/merchant_profile.py` | 41 | Merchant Profile Model - 商家资料模型 · 类:MerchantProfile · 表:merchant_profiles |
| `backend/app/models/meter.py` | 70 | 统一计量埋点（总纲 §4.6-8 / §6.6 P4 / 迁移总表 086） · 类:MeterEvent · 函数:1 · 表:meter_events |
| `backend/app/models/n8n_workflow.py` | 51 | n8n 工作流注册表模型。 · 类:N8nWorkflow · 表:n8n_workflows |
| `backend/app/models/news.py` | 42 | 类:NewsArticle,NewsCategory · 表:news_articles,news_categories |
| `backend/app/models/notification.py` | 36 | 通知模型 · 类:Notification · 表:notifications |
| `backend/app/models/nurture_cycle.py` | 116 | 持久化养号周期 + 平台养号规则模板（从 AiToEarn 互动管理模型合并）。 · 类:NurtureCycle,ScheduledPublish,EngagementRecord · 表:nurture_cycles,scheduled_publishes,engagement_records |
| `backend/app/models/opportunity.py` | 62 | Opportunity Model - CRM 销售机会（Lead → RFQ → Quote → Opportunity → Won） · 类:Opportunity,OpportunityStage · 表:opportunities,opportunity_stages |
| `backend/app/models/order.py` | 56 | Order Model - 订单模型 · 类:Order · 表:orders |
| `backend/app/models/order_item.py` | 34 | Order Item Model - 订单明细模型 · 类:OrderItem · 表:order_items |
| `backend/app/models/paperclip.py` | 124 | Paperclip Agent 编排层数据模型。 · 类:PaperclipCompany,PaperclipAgent,PaperclipGoal,PaperclipHeartbeat,PaperclipApproval,PaperclipTask · 表:paperclip_companies,paperclip_agents,paperclip_goals,paperclip_heartbeats,paperclip_approvals,paperclip_tasks |
| `backend/app/models/payment.py` | 84 | 支付模块模型 - 支付订单与支付渠道配置 · 类:PaymentOrder,PaymentOpsAudit,PaymentChannel,PaymentCompensationTask · 表:payment_orders,payment_ops_audit,payment_channels,payment_compensation_tasks |
| `backend/app/models/platform_registry.py` | 34 | 客户侧新增/自填平台与租户的关联审计（仅超管可见，客户 API 不暴露）。 · 类:PlatformTenantOrigin · 表:platform_tenant_origins |
| `backend/app/models/platform_survival_ledger.py` | 50 | 平台生存基金台账 — 仅超管收款账号；与租户 PaymentOrder / 代理分润完全隔离。 · 类:PlatformSurvivalLedgerEntry · 表:platform_survival_ledger_entries |
| `backend/app/models/product.py` | 156 | 产品和分类模型 — 支持 JSON 规格参数、文档管理。 · 类:JSONType,Category,Product,ProductDocument,ProductFaq · 表:categories,products,product_documents,product_faqs |
| `backend/app/models/product_category.py` | 38 | Product Category Model - 产品分类模型 · 类:ProductCategory · 表:product_categories |
| `backend/app/models/product_image.py` | 32 | Product Image Model - 产品图片模型 · 类:ProductImage · 表:product_images |
| `backend/app/models/project.py` | 56 | Project Intelligence 数据模型 — 项目/招标信号（Phase 4） · 类:Project,ProjectSignal · 表:projects,project_signals |
| `backend/app/models/prospect_lead.py` | 200 | 统一线索数据模型 —— 所有渠道的线索收敛到单一模型 · 类:LeadSource,LeadStatus,ProspectLead · 表:prospect_leads |
| `backend/app/models/publish_task.py` | 3 | Publish Task model - re-export from content module to avoid circular imports. |
| `backend/app/models/push_event.py` | 31 | Lane P · 销售推送事件（企微应用消息 / 群机器人）。 · 类:PushEvent · 表:push_events |
| `backend/app/models/quote.py` | 59 | Quote Model - 报价模型，商家向买家提供的报价单（B2B RFQ 闭环）。 · 类:Quote,QuoteItem · 表:quotes,quote_items |
| `backend/app/models/referral.py` | 37 | 客户裂变推荐系统模型 · 类:ReferralCode,ReferralRecord · 表:referral_codes,referral_records |
| `backend/app/models/region.py` | 197 | 类:Province,City,District,IndustryKeyword,KeywordGroup,GroupKeyword,CombinatorialRule,GeneratedKeyword · 表:provinces,cities,districts,industry_keywords,keyword_groups,group_keywords,combinatorial_rules,generated_keywords |
| `backend/app/models/registry.py` | 398 | 能力注册表持久化模型（总纲 §4.6-4 / §5.2.4 / §8；迁移 083）。 · 类:RegistrySkill,RegistrySkillVersion,McpServer,McpTool,RegistryPlugin,RegistryPluginVersion,DataSourceProvider,TenantCapabilityToggle · 函数:4 · 表:skills,skill_versions,mcp_servers,mcp_tools,plugins,plugin_versions,data_source_providers,tenant_capability_toggles |
| `backend/app/models/review.py` | 62 | 评价反馈模型 · 类:Review · 表:reviews |
| `backend/app/models/rfq.py` | 152 | RFQ Model - 买家需求单（B2B 询价请求，Finder→RFQ 核心转化闭环） · 类:JSONType,RFQ,RFQItem,RFQRequirement,RFQDocument · 表:rfqs,rfq_items,rfq_requirements,rfq_documents |
| `backend/app/models/sales_task.py` | 42 | Sales Task 模型 — 销售任务/通知（RFQ → 销售任务闭环） · 类:SalesTask · 表:sales_tasks |
| `backend/app/models/schema_markup.py` | 41 | 类:SchemaMarkup,SchemaTemplate · 表:schema_markups,schema_templates |
| `backend/app/models/seo.py` | 111 | 类:Keyword,KeywordRanking,SiteAudit,AiOptimizationLog,LlmsConfig · 表:keywords,keyword_rankings,site_audits,ai_optimization_logs,llms_config |
| `backend/app/models/seo_metadata.py` | 51 | SEO 元数据 — 单表 seo_metadata，resource_* 为主键列，entity_* 为历史别名。 · 类:SeoMetadata · 表:seo_metadata |
| `backend/app/models/shipping_timeline.py` | 72 | 类:ShippingTimeline,AnalyticsEvent,InquiryExtended · 表:shipping_timeline,analytics_events,inquiry_extended |
| `backend/app/models/site_analytics.py` | 44 | 站点流量与行为埋点（租户站 → 运营看板）。 · 类:SiteAnalyticsEvent · 表:site_analytics_events |
| `backend/app/models/social_interaction.py` | 43 | 社媒互动（评论/私信）— 自动谈单状态机落库。 · 类:SocialInteraction · 表:social_interactions |
| `backend/app/models/soft_delete.py` | 46 | 软删除 Mixin — 给模型添加 deleted_at 字段和软删除能力 · 类:SoftDeleteMixin |
| `backend/app/models/ssl_certificate.py` | 39 | SSL Certificate model for independent domain SSL auto-issuance. · 类:SSLCertificate · 表:ssl_certificates |
| `backend/app/models/system_config.py` | 30 | System Config Model - 系统配置模型 · 类:SystemConfig · 表:system_config |
| `backend/app/models/tenant.py` | 116 | SaaS多租户模型 · 类:TenantPlan,Tenant,TenantSubscription,TenantInvoice,UserTenant · 表:tenant_plans,tenants,tenant_subscriptions,tenant_invoices,user_tenants |
| `backend/app/models/tenant_wecom_push.py` | 24 | 租户企微推送配置 — 客户自有 CorpID / 应用 / 接收人。 · 类:TenantWecomPushConfig · 表:tenant_wecom_push_configs |
| `backend/app/models/token_ledger.py` | 23 | Token 账本流水 · 类:TokenLedgerEntry · 表:token_ledger_entries |
| `backend/app/models/trace.py` | 143 | 统一 Trace 与记分卡数据模型（总纲 §4.6-7 / §8 085_traces）。 · 类:TaskTrace,SkillPerformance,AgentScorecard · 函数:1 · 表:task_traces,skill_performance,agent_scorecards |
| `backend/app/models/trade_intel.py` | 34 | 出海参谋 — 品类×国家规则（M0 可落库维护）。 · 类:TradeCountryCategory · 表:trade_country_category |
| `backend/app/models/ubrain_accio.py` | 43 | UBrain-X / Accio 卖货：租户记忆与采购商候选线索。 · 类:UbrainTenantMemory,BuyerProspectLead · 表:ubrain_tenant_memory,buyer_prospect_leads |
| `backend/app/models/ubrain_commercial_os.py` | 83 | DeerFlow ↔ Accio 商业 OS：研究洞察、编排执行、效果回流。 · 类:UbrainResearchInsight,UbrainPipelineRun,UbrainActionAudit,UbrainFeedbackSnapshot · 表:ubrain_research_insights,ubrain_pipeline_runs,ubrain_action_audits,ubrain_feedback_snapshots |
| `backend/app/models/ubrain_decision.py` | 102 | UBrain AI Agent 决策追踪模型 · 类:UBrainDecisionRecord,UBrainExecutionRecord,UBrainFeedbackRecord · 表:ubrain_decision_records,ubrain_execution_records,ubrain_feedback_records |
| `backend/app/models/unified_lead.py` | 284 | 获客数据模型统一（六段式） — FIX-37 · 类:LeadStatus,OutreachStatus,IdentitySegment,CompanySegment,PositionSegment,SourceSegment,ScoringSegment,StatusSegment |
| `backend/app/models/user.py` | 88 | 用户模型 — 支持多角色、第三方登录、AI 推荐等。 · 类:User,ThirdPartyLogin,EmailVerification,OperationLog · 表:users,third_party_logins,email_verifications,operation_logs |
| `backend/app/models/vault.py` | 114 | 凭证库持久化模型（总纲 §1.2 / §4.6 / §8 迁移 087；轮20）。 · 类:VaultCredential,CredentialGrant · 函数:1 · 表:credentials,credential_grants |
| `backend/app/models/wallet.py` | 52 | 用户钱包 — 余额账户与交易流水（BUG-04 修复：DB 落库唯一真相源） · 类:WalletAccount,WalletTransaction · 表:wallet_accounts,wallet_transactions |
| `backend/app/models/wangcai.py` | 66 | Wangcai Session / QA Log Models - 旺财访客会话与问答日志（总纲 §7A.3 / 迁移 094） · 类:WangcaiSession,WangcaiQaLog · 表:wangcai_sessions,wangcai_qa_log |
| `backend/app/orchestration/__init__.py` | 1 | 编排层公共契约（适配器契约目录，见架构体检 P1 缺口与设计文档 §10.16）。 |
| `backend/app/orchestration/executors/__init__.py` | 1 | 执行器适配器实现目录（六插槽契约的 EXECUTOR 落点，见 §10.16/§10.19）。 |
| `backend/app/orchestration/executors/goodjob_executor.py` | 202 | GoodJob 执行器适配器 · 批次 B 桥的 UJ 侧端口. · 类:GoodJobBridgeError,GoodJobBridgeDisabledError,BridgeTransport,GoodJobExecutor · 函数:2 |
| `backend/app/orchestration/interfaces.py` | 204 | 通用能力插槽契约 · Universal Capability Slot Contract. · 类:SlotArchetype,TaskPackage,ExecutionResult,ExecutorAdapter,McpToolProvider,SkillPackageSource,DataSourceProvider,ChannelFrontendContract · 函数:1 |
| `backend/app/performance/alert_trigger.py` | 213 | 性能告警触发器 · 类:PerformanceAlertTrigger |
| `backend/app/performance/models.py` | 154 | 性能预算配置模型 · 类:BudgetMetric,BudgetSeverity,PerformanceBudget |
| `backend/app/performance/monitor.py` | 243 | 性能监控服务 · 类:LighthouseResult,PerformanceMonitor |
| `backend/app/repositories/base_repository.py` | 191 | 基础Repository类，提供通用CRUD操作 · 类:BaseRepository |
| `backend/app/repositories/content_repository.py` | 246 | 内容数据访问层 · 类:ContentPageRepository,SeoMetadataRepository,ContentVersionRepository |
| `backend/app/repositories/product_repository.py` | 163 | 产品数据访问层 · 类:CategoryRepository,ProductRepository,ProductDocumentRepository |
| `backend/app/repositories/tenant_repository.py` | 213 | 租户数据访问层 · 类:TenantPlanRepository,TenantRepository,TenantSubscriptionRepository,TenantInvoiceRepository · ⚑MOCK |
| `backend/app/repositories/user_repository.py` | 242 | 用户数据访问层 · 类:UserRepository,OperationLogRepository |
| `backend/app/schemas/__init__.py` | 141 |  |
| `backend/app/schemas/ab_test.py` | 217 | 类:ABTestVariantCreate,ABTestVariantUpdate,ABTestVariantResponse,ABTestCreate,ABTestUpdate,ABTestResponse,ABTestDetailResponse,ABTestEventResponse |
| `backend/app/schemas/ai_config.py` | 113 | 类:AIModelProviderCreate,AIModelProviderUpdate,AIModelProviderResponse,AIModelConfigCreate,AIModelConfigUpdate,AIModelConfigResponse,ModelSwitchRequest,CurrentModelResponse |
| `backend/app/schemas/auth.py` | 72 | 类:TokenResponse,LoginRequest,TokenRefreshRequest,LogoutResponse,UserResponse,EmailVerificationRequest,EmailLoginRequest,OAuthAuthorizeResponse |
| `backend/app/schemas/case_study.py` | 85 | 类:CaseImageCreate,CaseImageResponse,CaseStudyCreate,CaseStudyUpdate,CaseStudyResponse,CaseStudyDetailResponse,CaseStudyListResponse,BatchDeleteRequest |
| `backend/app/schemas/compliance.py` | 109 | 类:ComplianceRuleCreate,ComplianceRuleUpdate,ComplianceRuleResponse,ComplianceScanResultCreate,ComplianceScanResultResponse,ComplianceViolationResponse,AdvertisementLawKeywordCreate,AdvertisementLawKeywordUpdate |
| `backend/app/schemas/content.py` | 114 | 类:ContentPageCreate,ContentPageUpdate,ContentPageResponse,ContentPageListResponse,ContentVersionCreate,ContentVersionResponse,ContentRollbackRequest,SeoMetadataCreate |
| `backend/app/schemas/geo_schemas.py` | 50 | GEO Schemas - Pydantic models for GEO engine · 类:GenerateRequest,LeadRequest,GuardRequest,ProductResponse |
| `backend/app/schemas/globalization.py` | 151 | 全球化多语言 Schema · 类:GlossaryTermCreate,GlossaryTermUpdate,GlossaryTermResponse,TranslationTaskCreate,TranslationTaskResponse,TranslationRecordResponse |
| `backend/app/schemas/hermes_orchestration.py` | 59 | Hermes TaskGraph and Intent Orchestration Schemas (Plan-as-Data). · 类:ReplyToConfig,IntentEvent,TaskBudget,TaskRetryPolicy,TaskNode,GraphPolicies,TaskGraph,ExecutorResult · ⚑DEGRADED |
| `backend/app/schemas/im_routing_and_specs.py` | 182 | 商家IM路由配置和建材垂直参数的Pydantic Schemas · 类:MerchantIMRoutingBase,MerchantIMRoutingCreate,MerchantIMRoutingUpdate,MerchantIMRoutingResponse,IMChannelResponse,BuildingMaterialSpecBase,BuildingMaterialSpecCreate,BuildingMaterialSpecUpdate |
| `backend/app/schemas/inquiry.py` | 40 | 类:InquiryCreate,InquiryUpdate,InquiryResponse |
| `backend/app/schemas/international.py` | 88 | 国际询盘采集系统 Schema · 类:InternationalTargetSiteCreate,InternationalTargetSiteUpdate,InternationalTargetSiteResponse,InternationalInquiryUpdate,InternationalInquiryResponse,InternationalStats |
| `backend/app/schemas/news.py` | 90 | 类:NewsCategoryBase,NewsCategoryCreate,NewsCategoryUpdate,NewsCategoryResponse,NewsArticleBase,NewsArticleCreate,NewsArticleUpdate,NewsArticleResponse |
| `backend/app/schemas/product.py` | 148 | 类:ProductDocumentCreate,ProductDocumentResponse,CategoryCreate,CategoryUpdate,CategoryResponse,CategoryTreeResponse,ProductCreate,ProductUpdate |
| `backend/app/schemas/publish_task.py` | 47 | Pydantic schemas for PublishTask. · 类:PublishTaskBase,PublishTaskCreate,PublishTaskUpdate,PublishTaskResponse |
| `backend/app/schemas/referral.py` | 50 | 客户裂变推荐系统 Schema · 类:ReferralCodeResponse,ReferralRecordResponse,ReferralStatsResponse,ReferralLeaderboardItem,ApplyReferralResponse |
| `backend/app/schemas/rfq.py` | 138 | RFQ 请求 / 响应 Pydantic 模型 — 买家需求单（B2B 询价）。 · 类:RFQItemIn,RFQRequirementIn,RFQCreate,RFQStatusUpdate,RFQAssignRequest |
| `backend/app/schemas/schema_markup.py` | 64 | 类:SchemaMarkupCreate,SchemaMarkupUpdate,SchemaMarkupResponse,SchemaTemplateResponse,GenerateSchemaRequest,ValidateSchemaRequest,SchemaValidationResult |
| `backend/app/schemas/schema_markup_enhanced.py` | 225 | 类:OrganizationSchema,ProductSchema,ArticleSchema,BreadcrumbSchema,FAQSchema,LocalBusinessSchema · 函数:1 |
| `backend/app/schemas/seo.py` | 99 | 类:KeywordCreate,KeywordUpdate,KeywordResponse,KeywordRankingResponse,SiteAuditCreate,SiteAuditResponse,AiOptimizationLogResponse,LlmsConfigCreate |
| `backend/app/schemas/ssl_certificate.py` | 45 | Pydantic schemas for SSLCertificate. · 类:SSLCertificateBase,SSLCertificateCreate,SSLCertificateUpdate,SSLCertificateResponse |
| `backend/app/schemas/tenant.py` | 258 | SaaS多租户Schema · 类:DomainBinding,DomainBindingResponse,DomainListResponse,TenantPlanCreate,TenantPlanUpdate,TenantPlanResponse,TenantCreate,TenantUpdate |
| `backend/app/schemas/user.py` | 71 | 类:LoginRequest,TokenResponse,UserCreate,UserUpdate,UserResponse,UserListResponse,ChangePasswordRequest,UserStatusUpdate |
| `backend/app/services/__init__.py` | 21 |  |
| `backend/app/services/_scan_long.py` | 39 | 函数:2 |
| `backend/app/services/acme_service.py` | 749 | ACME Service - Let's Encrypt SSL certificate auto-issuance. · 类:ACMEClient,SSLCertificateService · 函数:3 · ⚑DEGRADED |
| `backend/app/services/acquisition_outreach_service.py` | 374 | 获客邮件序列 — 复用 EmailOutreach，经 JobGateway 真发。 · 函数:9 · ⚑MOCK |
| `backend/app/services/adapters/__init__.py` | 7 | Adapter 层（Execution Plane 平级适配器集合，总纲 §3.1）。 |
| `backend/app/services/adapters/tradeai/__init__.py` | 214 | Trade AI Agent 适配器（总纲 §5.2：代码级嫁接，MIT）。 · 函数:7 · ⚑STUB |
| `backend/app/services/agent_aggregation_service.py` | 576 | 代理层级数据汇总服务 · 类:AgentAggregationService · ⚑MOCK |
| `backend/app/services/agent_commission_service.py` | 201 | 支付成功 → 多级代理分润（沿 agent-tree 向上拆分，幂等）。 · 函数:7 |
| `backend/app/services/agent_hub_service.py` | 437 | 智能体协同中心 — DeerFlow 任务真实数据（非硬编码队列）。 · 类:AgentHubService · 函数:14 |
| `backend/app/services/agent_loop/__init__.py` | 9 | Agent 任务循环 —  bounded 工作流（非开放域 Autonomous Agent）。 |
| `backend/app/services/agent_loop/growth_workflow.py` | 608 | 增长工具 Agent 工作流 — 热词 → 成稿 → 质检 → 引流监测快照。 · 类:_GrowthRunExecutor · 函数:7 · ⚑DEGRADED |
| `backend/app/services/agent_loop/run_repository.py` | 170 | Agent run 持久化与查询。 · 函数:8 |
| `backend/app/services/agent_loop/session_store.py` | 92 | Agent run 状态存储（内存 + 可选 Redis）。 · 函数:6 |
| `backend/app/services/agent_loop/workflow_presets.py` | 58 | 增长跑盘预设模板。 · 函数:2 |
| `backend/app/services/agent_node_write_service.py` | 198 | 代理层级节点写操作（超管/管理员）。 · 函数:6 |
| `backend/app/services/agent_portal_service.py` | 536 | 代理业绩看板 — 聚合租户、支付、财务台账与分润结算。 · 类:AgentPortalService · 函数:4 · ⚑MOCK |
| `backend/app/services/ai/ai_engine_v2.py` | 402 | AI引擎 v2 - 基于真实LLM调用的完整实现 · 类:LLMProvider,OpenAIProvider,GeminiProvider,ClaudeProvider,DeepSeekProvider,AIEngineV2 · 函数:2 · ⚑DEGRADED |
| `backend/app/services/ai/analytics_insight_service.py` | 570 | AI数据洞察服务 - 基于真实LLM调用 · 类:InsightRequest,Insight,InsightResult · 函数:8 · ⚑DEGRADED |
| `backend/app/services/ai/recommendation_service.py` | 455 | AI推荐系统服务 - 基于真实协同过滤算法与LLM解释生成 · 类:RecommendationRequest,RecommendedItem,RecommendationResult · 函数:8 |
| `backend/app/services/ai/security_scan_service.py` | 355 | AI安全扫描服务 - 基于真实LLM调用 · 类:SecurityScanRequest,SecurityIssue,SecurityScanResult · 函数:4 · ⚑DEGRADED/DEPRECATED |
| `backend/app/services/ai_config_service.py` | 395 | AI模型配置服务层 · 类:AIConfigService |
| `backend/app/services/ai_engine.py` | 1141 | 类:SmartAIResponse,AIEngine,MockLLM · 函数:1 · ⚑MOCK/DEGRADED |
| `backend/app/services/ai_invocation_service.py` | 323 | 统一 AI 调用：场景解析、引擎调用、用量落库、降级。 · 函数:8 · ⚑DEGRADED |
| `backend/app/services/ai_key_probe.py` | 99 | T-QA-08 / G4：检测是否配置可用 AI Key（非仅 Mock）。 · 函数:4 · ⚑MOCK/STUB |
| `backend/app/services/ai_learning_service.py` | 139 | AI 学习 / 自我进化概览 — 从 UBrain 与操作日志聚合真实计数。 · 类:AiLearningService |
| `backend/app/services/ai_model_capability_service.py` | 349 | AI 模型能力解析与健康探测（供超管配置页展示）。 · 函数:9 · ⚑MOCK |
| `backend/app/services/ai_multimodal_studio.py` | 243 | 多模态外贸营销工厂服务 - 真实大模型驱动的生图提示词、社媒营销发帖、外贸短视频分镜生成与视频剪辑装配。 · 类:AIMultimodalStudio · 函数:1 · ⚑DEGRADED |
| `backend/app/services/ai_recommendation_service.py` | 335 | AI推荐系统服务 - 协同过滤与内容推荐算法 · 类:RecommendationService |
| `backend/app/services/ai_search_probe_service.py` | 185 | Perplexity / Copilot 等 AI 搜索探针 — 无 Key 时诚实跳过，禁止假收录。 · 函数:5 |
| `backend/app/services/ai_site_engine.py` | 109 | AI 智能多语言外贸独立站生成引擎。 · 类:AISiteEngine |
| `backend/app/services/ai_traffic_connect_service.py` | 291 | 租户 AI 通道自动对接：充值后接通所选平台 Key；无 Key 时无缝降级免费 NVIDIA。 · 函数:10 · ⚑DEGRADED |
| `backend/app/services/ai_traffic_provider_service.py` | 130 | 客户自选 AI 大模型平台（AI 流量充值与租户偏好）。 · 函数:6 |
| `backend/app/services/aitoearn_engage_send_service.py` | 86 | 社媒互动 — 批准后经 AiToEarn 真发回复（禁止无回执假成功）。 · 函数:2 |
| `backend/app/services/aitoearn_hub_service.py` | 169 | AiToEarn 能力 Hub — Publish / Engage / Create 对齐（Phase 4 复刻优化）。 · 函数:4 |
| `backend/app/services/aitoearn_local_proxy.py` | 302 | AiToEarn MCP 本地代理 — 离线回退 + 缓存层。 · 函数:17 · ⚑DEGRADED |
| `backend/app/services/aitoearn_publish_adapter.py` | 627 | AiToEarn Relay — 抖音/快手/B站等短视频平台真发。 · 函数:25 |
| `backend/app/services/alert_service.py` | 175 | 告警引擎：检测 + 通知 · 函数:6 |
| `backend/app/services/alipay_client.py` | 268 | 支付宝 Native 支付（alipay.trade.precreate）与回调验签。 · 类:AlipayConfig,AlipayClient · 函数:5 · ⚑MOCK |
| `backend/app/services/analytics/__init__.py` | 0 |  |
| `backend/app/services/analytics/user_action_analytics_compliance.py` | 188 | UserActionAnalyzePlatform 合规门禁。 · 类:ComplianceDecision · 函数:4 |
| `backend/app/services/analytics/user_action_analytics_registry.py` | 142 | UserActionAnalyzePlatform 模块注册 — Spark 电商行为分析 → 本系统 Lane。 · 类:AnalyticsModule · 函数:3 · ⚑MOCK |
| `backend/app/services/analytics/user_action_analytics_sidecar.py` | 196 | UserActionAnalyzePlatform Sidecar HTTP 客户端。 · 函数:6 · ⚑DEGRADED |
| `backend/app/services/analytics/user_action_analytics_smart.py` | 204 | UserActionAnalyzePlatform 智能层 — 中文状态与一键分析。 · 函数:7 · ⚑MOCK |
| `backend/app/services/annex/__init__.py` | 1 | 附属统一身份域：UJ 为唯一身份源（annex_ticket 短时票据，§9.3）。 |
| `backend/app/services/annex/ticket_service.py` | 233 | 附属统一登录票据服务 · UJ 为唯一身份源. · 类:TicketRejected · 函数:9 · ⚑DEGRADED |
| `backend/app/services/attribution_service.py` | 604 | 归因服务 — 连接各模块的自动化桥接层。 · 函数:14 · ⚑DEGRADED |
| `backend/app/services/auto_backup.py` | 170 | 自动备份服务 — 每日凌晨3点执行，保留最近7天 · 类:AutoBackup · 函数:1 |
| `backend/app/services/backup_service.py` | 44 | 自动备份服务 · 类:BackupService |
| `backend/app/services/baidu_webmaster_service.py` | 165 | 百度搜索资源平台（站长平台）API 集成服务 · 类:BaiduWebmasterService · ⚑MOCK |
| `backend/app/services/bff_cache_service.py` | 76 | BFF 首屏缓存 — Redis 优先，开发环境内存兜底（Phase 4 / T-ARCH-2）。 · 函数:4 |
| `backend/app/services/billing/meter_event.py` | 471 | 统一计量埋点与账单对账（总纲 §4.6-8 / §6.6 P4 / §7.6） · 类:MeterEventService · 函数:2 |
| `backend/app/services/billing/subscription_countdown.py` | 86 | 订阅到期倒计时 · 纯函数服务（零迁移、零外部依赖）. · 类:CountdownState · 函数:3 |
| `backend/app/services/browser_runtime/__init__.py` | 16 | Browser Runtime（P5）— Playwright + CDP 浏览器执行层（总纲 §4.7）。 · ⚑DEGRADED |
| `backend/app/services/browser_runtime/evidence.py` | 308 | 证据回传模型（总纲 §4.7 P5：合规执行须留证）。 · 类:EvidenceRecord · 函数:3 · ⚑DEGRADED |
| `backend/app/services/browser_runtime/exceptions.py` | 21 | Browser Runtime 异常体系。 · 类:BrowserRuntimeError,BrowserRuntimeDisabled,BrowserRuntimeUnavailable,BrowserRuntimePolicyDenied,ProfileIsolationError · ⚑DEGRADED |
| `backend/app/services/browser_runtime/executor.py` | 854 | Browser Runtime 真实执行器（轮25-C，Playwright 真接入）。 · 函数:14 · ⚑STUB/DEGRADED |
| `backend/app/services/browser_runtime/policy.py` | 387 | Browser Runtime Policy 闸门（总纲 §4.7 + 既有 Policy Engine 复用）。 · 类:PolicyVerdict · 函数:6 |
| `backend/app/services/browser_runtime/profile.py` | 154 | 租户 Profile 隔离（总纲 §4.7：每租户独立 Profile 防跨租户泄漏）。 · 类:ProfilePath · 函数:9 · ⚑DEGRADED |
| `backend/app/services/browser_runtime/runtime.py` | 227 | Browser Runtime 核心（总纲 §4.7 P5：Playwright + CDP）。 · 函数:3 · ⚑DEGRADED |
| `backend/app/services/cache_service.py` | 260 | 缓存服务 - 提供Redis缓存和响应缓存功能 · 类:CacheService,ResponseCacheMiddleware · 函数:1 |
| `backend/app/services/calculators/__init__.py` | 5 | Calculator 包 — 工程计算器（Thermal / Fire Protection / Quantity）。 |
| `backend/app/services/calculators/engine.py` | 140 | 工程计算器引擎 — 纯函数，无 Web 依赖，可单元测试。 · 函数:6 |
| `backend/app/services/churn_service.py` | 256 | 客户流失预警服务 · 类:ChurnService |
| `backend/app/services/client_bff_service.py` | 163 | 租户 Client 壳 BFF 聚合（T-ARCH-2）。 · 函数:4 |
| `backend/app/services/client_today_service.py` | 190 | Client / 出海计 App — 今日一件事 + 出海参谋蓝海 Top1。 · 函数:4 |
| `backend/app/services/client_today_three_service.py` | 98 | Client「今日三步」状态 — 填产品 → 发内容 → 看询盘。 · 函数:1 |
| `backend/app/services/cognitive_service.py` | 80 | 认知智能与知识图谱服务层 — 仅返回真实可核对数据或诚实空态。 · 类:CognitiveService · ⚑MOCK |
| `backend/app/services/commission_rule_service.py` | 146 | 多级分润规则：加载、种子、校验。 · 类:CommissionRuleService |
| `backend/app/services/compliance_scanner.py` | 512 | 合规检查服务 - 广告法检测引擎 · 类:ComplianceScanner · 函数:2 |
| `backend/app/services/content_feedback_loop.py` | 532 | 内容反馈闭环 — publish -> rank probe -> feedback -> adjust tactics · 类:ContentFeedbackLoop · 函数:3 |
| `backend/app/services/content_master_publish_service.py` | 264 | 统一发布母版 — 按平台名匹配变体并创建 PublishTask。 · 类:_NullGateReport · 函数:4 · ⚑DEGRADED |
| `backend/app/services/content_optimizer.py` | 256 | 类:ContentOptimizer |
| `backend/app/services/content_scorer.py` | 190 | 内容质量评分引擎 — 多维规则打分 · 函数:8 |
| `backend/app/services/content_service.py` | 383 | 内容服务层 · 类:ContentPageService,SeoMetadataService,ContentVersionService |
| `backend/app/services/cosmos_infer_service.py` | 300 | NVIDIA Cosmos NIM /v1/infer 客户端（文生视频等）。 · 类:CosmosInferError · 函数:11 · ⚑MOCK/STUB |
| `backend/app/services/crawlers/__init__.py` | 1 | Crawler sidecar integrations. |
| `backend/app/services/crawlers/ecommerce_crawlers_compliance.py` | 238 | ECommerceCrawlers 合规门禁 — 无 Sidecar / 无授权 / 无 evidence 一律拒绝。 · 类:ComplianceDecision · 函数:7 |
| `backend/app/services/crawlers/ecommerce_crawlers_registry.py` | 424 | ECommerceCrawlers 爬虫配方注册表 — 映射 GitHub 子项目到本系统能力。 · 类:SpiderRecipe · 函数:5 |
| `backend/app/services/crawlers/ecommerce_crawlers_sidecar.py` | 209 | ECommerceCrawlers Sidecar — 外置 Python 爬虫 Worker HTTP 网关。 · 函数:7 · ⚑DEGRADED |
| `backend/app/services/crawlers/ecommerce_crawlers_smart.py` | 358 | ECommerceCrawlers 智能层 — 大白话状态、自动补全合规字段、一键探测。 · 函数:12 · ⚑MOCK |
| `backend/app/services/crawlers/media_crawler_sidecar.py` | 142 | MediaCrawler Sidecar — NanmiCoder/MediaCrawler HTTP gateway (social_restricted). · 函数:5 · ⚑DEGRADED |
| `backend/app/services/cross_border/__init__.py` | 1 | 跨境语言桥 — 询盘翻译、中文片出海、出口报价（W1–W3）。 |
| `backend/app/services/cross_border/audio_asr_service.py` | 537 | 视频/音频 → 中文听写（Whisper 多后端 + 讯飞 LFASR 直传，长媒体分片扇出扇入）。 · 函数:12 · ⚑MOCK/DEGRADED |
| `backend/app/services/cross_border/audio_chunk_service.py` | 193 | 长媒体听写分片：ffmpeg 切段、并行转写、扇入合并。 · 函数:5 |
| `backend/app/services/cross_border/cross_border_job_service.py` | 370 | 中文片出海异步任务：入队、调度、查询（复用 media_render_tasks）。 · 函数:14 · ⚑DEGRADED |
| `backend/app/services/cross_border/cross_border_sse.py` | 44 | 跨境任务 SSE 事件流。 · 函数:1 |
| `backend/app/services/cross_border/cross_border_worker.py` | 384 | 中文片出海 Worker：听写 / 出海（Celery 或后台线程调用）。 · 函数:25 |
| `backend/app/services/cross_border/export_quote_service.py` | 145 | FOB/MOQ 出口报价一页 — 绑定产品库（W3 / XF-D2）。 · 函数:3 |
| `backend/app/services/cross_border/forum_language_bridge_service.py` | 124 | 论坛语言桥 — 英文问→中文摘要；老板中文答→英文发布草稿（FORUM-05）。 · 函数:3 |
| `backend/app/services/cross_border/gemini_audio_asr_service.py` | 242 | Gemini 音频听写兜底（多模态 generateContent，非专用 ASR）。 · 函数:9 |
| `backend/app/services/cross_border/glossary_helper.py` | 38 | 建材术语库片段 — 供 LLM 翻译/回复时引用。 · 函数:1 |
| `backend/app/services/cross_border/imap_inquiry_ingest_service.py` | 139 | 只读 IMAP 询盘入库 — 去重 + 诚实门禁（禁止假询盘、禁止自动回复）。 · 函数:4 |
| `backend/app/services/cross_border/industry_belt_product_import_service.py` | 233 | 产业带 AI 调研 → 产品库候选（须人工勾选导入，默认未上架）。 · 函数:6 |
| `backend/app/services/cross_border/inquiry_bridge_service.py` | 225 | 询盘语言桥 — 外文询盘→中文摘要；老板中文→英文回复草稿（W2 / XF-C1/C2）。 · 函数:6 · ⚑MOCK/STUB |
| `backend/app/services/cross_border/krillinai_sidecar_adapter.py` | 84 | KrillinAI sidecar/CLI 适配器 — 仅在上游就绪时调用，禁止假成功。 · 函数:2 |
| `backend/app/services/cross_border/libretranslate_sidecar.py` | 125 | LibreTranslate 旁路 — 跨境文案机翻（须标注 machine_translated）。 · 函数:5 · ⚑MOCK/DEGRADED |
| `backend/app/services/cross_border/media_studio_capability_registry.py` | 230 | 全媒体工作室能力注册表 — ASR / 剪辑适配器 / TTS，供前端枢纽页与运维探测。 · 函数:6 · ⚑MOCK |
| `backend/app/services/cross_border/media_studio_project_service.py` | 101 | 全媒体工作室项目持久化 — SRT/segments 存于 media_task edit_config。 · 函数:2 |
| `backend/app/services/cross_border/opensource_localization_registry.py` | 528 | 开源视频本地化上游注册表 — 对标 Vozo / 山海智影；智能优先级见 OPTIMAL_PICK_ORDER。 · 函数:20 |
| `backend/app/services/cross_border/opensource_localization_service.py` | 486 | 开源精品轨执行器 — 统一 sidecar 契约或 KrillinAI CLI；未配置则明确失败。 · 函数:11 · ⚑STUB |
| `backend/app/services/cross_border/premium_video_dub_service.py` | 348 | 精品出海轨编排 — 开源 sidecar / Vozo / 回退禁止假成功。 · 函数:22 |
| `backend/app/services/cross_border/seo_belt_service.py` | 74 | 大城+河间 SEO/GEO 词库 — Client 预览与入库（W3）。 · 函数:2 |
| `backend/app/services/cross_border/sidecar_health.py` | 60 | Sidecar 健康探测 — mock/reference 不得计为已配置。 · 函数:2 · ⚑MOCK |
| `backend/app/services/cross_border/tts_service.py` | 376 | 英文 TTS — edge-tts（无需 API Key）。 · 函数:9 |
| `backend/app/services/cross_border/video_dub_service.py` | 583 | 中文产品片 → 听写 / 英文字幕 / 英文配音出海（W1 / LV-07~10）。 · 函数:31 |
| `backend/app/services/cross_border/voice_gender_infer.py` | 130 | 从原片音轨粗估解说者性别（基频启发式），用于英文 TTS 音色匹配。 · 函数:3 |
| `backend/app/services/cross_border/vozo_localization_service.py` | 185 | Vozo Enterprise 精品轨 — 有 Key 才调用；无 Key / 失败禁止假成功。 · 函数:4 |
| `backend/app/services/cross_border/whisper_model_pool.py` | 44 | Whisper 模型单例预热（Worker 启动后复用）。 · 函数:3 |
| `backend/app/services/cross_border/xfyun_ifasr_llm_service.py` | 342 | 讯飞「录音文件转写大模型」WebAPI（Ifasr LLM）。 · 函数:12 |
| `backend/app/services/cross_border/xfyun_lfasr_service.py` | 362 | 讯飞语音转写（LFASR / raasr）— 云端听写兜底。 · 类:_SliceIdGenerator · 函数:15 |
| `backend/app/services/cross_border/youding_self_hosted_provider.py` | 77 | 优丁内置真实出海链 — 无 sidecar、无 mock，走 video_dub_service 全链路。 · 函数:4 · ⚑MOCK/STUB |
| `backend/app/services/cross_platform_dashboard_service.py` | 295 | 跨平台数据聚合服务 — 从 AiToEarn 拉取各平台数据并聚合。 · 函数:11 |
| `backend/app/services/dacheng_keyword_seed_service.py` | 324 | 廊坊大城 + 沧州河间 建筑主材/附属 SEO 词库入库 — P0-4。 · 函数:9 |
| `backend/app/services/daily_report_service.py` | 140 | 每日经营日报生成服务 · 类:DailyReportService |
| `backend/app/services/deepseek_harness/__init__.py` | 15 | DeepSeek Harness 外层智能体运行时接入包。 |
| `backend/app/services/deepseek_harness/client.py` | 118 | DeepSeek Harness 客户端（懒加载官方 SDK，绝不污染导入期）。 · 函数:5 |
| `backend/app/services/deepseek_harness/config.py` | 127 | DeepSeek Harness 接入配置（纯标准库，无重依赖，保证本包可随时安全导入）。 · 类:DeepSeekHarnessSettings · 函数:6 |
| `backend/app/services/deerflow/__init__.py` | 29 | DeerFlow 执行引擎 — 状态机驱动的任务编排。 |
| `backend/app/services/deerflow/checkpoint.py` | 371 | DeerFlow 断点管理器。 · 类:Checkpoint,CheckpointSnapshot,CheckpointManager |
| `backend/app/services/deerflow/executor.py` | 1041 | DeerFlow 子任务执行器。 · 类:SubTaskResult,SubTaskExecutor,SubTaskExecutionError · 函数:2 · ⚑STUB/DEGRADED |
| `backend/app/services/deerflow/planner.py` | 341 | DeerFlow 任务规划器。 · 类:SubTask,ExecutionPlan,TaskPlanner |
| `backend/app/services/deerflow/reviewer.py` | 309 | DeerFlow 结果审核器。 · 类:ReviewDecision,ReviewResult,ReviewRule,ResultReviewer |
| `backend/app/services/deerflow/state_machine.py` | 365 | DeerFlow 执行引擎状态机核心。 · 类:DeerFlowStatus,TransitionResult,DeerFlowStateMachine,DeerFlowStateMachineError,DeerFlowJobNotFoundError |
| `backend/app/services/developer_service.py` | 64 | 开发者生态服务层 — 仅返回真实可核对数据或诚实空态。 · 类:DeveloperService · ⚑MOCK |
| `backend/app/services/douyin_comment_pull_service.py` | 289 | ITER-03b · 抖音评论真实拉取 — AiToEarn / SAU 导出 / Inbox 文件（禁止造评论）。 · 函数:6 · ⚑MOCK/DEGRADED |
| `backend/app/services/douyin_comment_sync_service.py` | 135 | 抖音评论采集 Worker — 批量入库（文件/HTTP 批处理，禁止假评论）。 · 函数:4 |
| `backend/app/services/eeat_scorer.py` | 299 | 类:EEATScorer |
| `backend/app/services/egress/__init__.py` | 13 | 出口 IP 上游采购适配器。 |
| `backend/app/services/egress/demo_guard.py` | 68 | 清除历史演示 IP 槽位（禁止假数据进入平台池统计）。 · 函数:3 · ⚑MOCK/STUB |
| `backend/app/services/egress/iproyal_client.py` | 268 | IPRoyal Reseller API 客户端 — 静态住宅IP自动采购。 · 类:IPRoyalAPIError,IPRoyalOrderResult,IPRoyalClient |
| `backend/app/services/egress/iproyal_provisioner.py` | 104 | IPRoyal 缓冲池适配器 — 从预购池中分配IP，非实时下单。 · 类:PoolExhaustedError,IPRoyalProvisioner |
| `backend/app/services/egress/provisioner.py` | 558 | 出口 IP — manual 运营录入 / mock 演示 / asocks JIT 采购 / iproyal 长期养号。 · 类:EgressProvisionerError,PurchasedProxy,EgressProvisioner,MockProvisioner,AsocksProvisioner · 函数:13 · ⚑MOCK/DEGRADED |
| `backend/app/services/egress_addon_service.py` | 80 | IP 槽位加购 — 支付成功后增加租户 egress_ip_quota。 · 函数:5 |
| `backend/app/services/egress_jit_provision_service.py` | 386 | 出口 IP 槽位：manual 运营录入 / mock 演示 / asocks JIT 采购 / iproyal 长期养号。 · 函数:10 · ⚑MOCK |
| `backend/app/services/egress_quota_service.py` | 235 | 租户 IP 槽位配额与自助分配。 · 函数:8 · ⚑MOCK |
| `backend/app/services/egress_replenish_service.py` | 401 | IPRoyal 缓冲池补充与永续续费服务（长期养号核心）。 · 函数:10 |
| `backend/app/services/egress_supplier_service.py` | 497 | 静态 IP 上游供应商 — 增删改查与切换启用。 · 函数:16 · ⚑MOCK |
| `backend/app/services/einvoice_provider.py` | 206 | 全电发票 Provider 适配层 — 诺诺/百望等可插拔；未配置时走人工 mark-issued。 · 类:EInvoiceIssueRequest,EInvoiceIssueResult,BaseEInvoiceProvider,ManualEInvoiceProvider,NuonuoEInvoiceProvider · 函数:2 |
| `backend/app/services/email_recovery_service.py` | 160 | EmailOutreach 状态恢复服务 —— ORCH-11 修复 · 函数:4 |
| `backend/app/services/email_service.py` | 201 | 类:EmailService · 函数:1 |
| `backend/app/services/email_tracking_service.py` | 146 | 邮件追踪服务（P1-3）—— 像素回调 + 发送追踪。 · 函数:4 |
| `backend/app/services/evolution/__init__.py` | 23 | AI 进化引擎 — 闭环自进化系统。 |
| `backend/app/services/evolution/canary.py` | 452 | 灰度发布 — Draft → Evaluation → Canary → Approved → Production。 · 类:CanaryRelease · 函数:1 |
| `backend/app/services/evolution/engine.py` | 626 | 核心进化引擎 — 编排完整闭环。 · 类:EvolutionEngine · ⚑DEGRADED |
| `backend/app/services/evolution/experience_store.py` | 380 | 经验存储 — 经验沉淀阶段。 · 类:ExperienceStore |
| `backend/app/services/evolution/version_control.py` | 422 | Skill/SOP 版本管理 — 语义化版本 + 状态机。 · 类:VersionControl · 函数:4 · ⚑STUB |
| `backend/app/services/facade/model_gateway_facade.py` | 51 | 大模型网关防腐层 (Anti-Corruption Layer) - 改造 10 · 类:ModelGatewayFacade · ⚑MOCK/DEGRADED |
| `backend/app/services/feishu/__init__.py` | 16 |  |
| `backend/app/services/feishu/cards.py` | 243 | 类:FeishuCardBuilder |
| `backend/app/services/feishu/client.py` | 487 | 类:FeishuClient |
| `backend/app/services/feishu/handlers.py` | 538 | 类:FeishuMessageHandler |
| `backend/app/services/feishu/report.py` | 259 | 类:FeishuReportService |
| `backend/app/services/finance_honesty.py` | 192 | 财务实收与汇总诚实过滤 — 排除 mock-pay、种子询盘、探针埋点。 · 函数:11 · ⚑MOCK |
| `backend/app/services/finance_service.py` | 417 | 财务中台业务逻辑：成本归集、对账导出。 · 类:FinanceService · 函数:1 |
| `backend/app/services/foreign_trade/__init__.py` | 5 | 外贸 AI 技能引擎 — 统一入口。 |
| `backend/app/services/foreign_trade/aeo_fact_audit_service.py` | 115 | GW-G-AEO-01 — 站点/母版文案 vs 禁泄露品牌词 + 租户事实一致性。 · 函数:3 |
| `backend/app/services/foreign_trade/benchmark_catalog_service.py` | 56 | 标杆来源取长补短 — 供研究员 / Admin / ecosystem API 引用。 · 函数:3 |
| `backend/app/services/foreign_trade/cold_email_skill.py` | 53 | 开发信生成技能 — 对应 cold-email SKILL.md。 |
| `backend/app/services/foreign_trade/competitor_profile_skill.py` | 55 | 竞品画像技能 — 对应 competitor-profiling SKILL.md。 |
| `backend/app/services/foreign_trade/content_one_to_many_service.py` | 166 | GW-G-CC-02 — 1 长文 → 多平台变体 + 开发信摘要。 · 函数:5 |
| `backend/app/services/foreign_trade/copywriting_skill.py` | 56 | 营销文案技能 — 对应 copywriting SKILL.md。 |
| `backend/app/services/foreign_trade/customer_research_skill.py` | 55 | 客户调研技能 — 对应 customer-research SKILL.md。 |
| `backend/app/services/foreign_trade/customs_buyer_brief_service.py` | 82 | 海关/买家情报 brief — 公开统计 + playbook，禁止无来源 buyer 列表落库。 · 函数:1 |
| `backend/app/services/foreign_trade/customs_data_spider_sidecar.py` | 175 | CustomsDataSpider Sidecar — 海关买家 research brief，须 evidence_url + 人工核实。 · 函数:6 · ⚑MOCK/DEGRADED |
| `backend/app/services/foreign_trade/foreign_trade_agent_service.py` | 431 | 外贸标杆能力 — 智能体编排门面（UBrain / Hermes / DeerFlow 统一入口）。 · 函数:15 |
| `backend/app/services/foreign_trade/geo_visibility_dashboard_service.py` | 115 | GW-G-GEO-DASH — GEO/AEO 客户可见性看板（对标迈富时效果报告）。 · 函数:2 |
| `backend/app/services/foreign_trade/gsc_ads_attribution_webhook_service.py` | 205 | GW-P-GSC-02 — Google Search Console / Google Ads 归因 webhook 回环。 · 函数:7 |
| `backend/app/services/foreign_trade/inquiry_meddpicc_service.py` | 147 | GW-L-DC-01 — 询盘 MEDDPICC 字段提取与评分。 · 函数:5 |
| `backend/app/services/foreign_trade/inquiry_pipeline_service.py` | 169 | GW-L-PL-01 — 询盘管道阶段 MQL→SQL→报价→PI→定金。 · 函数:6 |
| `backend/app/services/foreign_trade/integrations_sidecars_status_service.py` | 68 | 并行聚合 B2B / GEO 旁路就绪态（避免 /integrations/sidecars/status 串行超时）。 · 函数:2 |
| `backend/app/services/foreign_trade/matrix_oauth_publish_gate_service.py` | 137 | GW-S-MAT-01 — 矩阵真发 OAuth 绑定 SLA 门禁。 · 函数:4 · ⚑STUB |
| `backend/app/services/foreign_trade/osint/__init__.py` | 34 | OSINT 六层背调 — 改编自 chefroger/smart-trade-ai (MIT)，见 THIRD_PARTY_ATTRIBUTION.md。 |
| `backend/app/services/foreign_trade/osint/constants.py` | 103 | Trade AI Assistant — OSINT 模块：常量和共享工具。 · 函数:3 |
| `backend/app/services/foreign_trade/osint/email_verify.py` | 295 | Trade AI Assistant — OSINT Layer 3: 企业邮箱验证。 · 函数:6 · ⚑DEGRADED |
| `backend/app/services/foreign_trade/osint/linkedin_verify.py` | 65 | Trade AI Assistant — OSINT Layer 6: LinkedIn 公司页验证。 · 函数:1 |
| `backend/app/services/foreign_trade/osint/orchestrator.py` | 276 | Trade AI Assistant — OSINT 编排器：完整尽职调查流程。 · 函数:15 |
| `backend/app/services/foreign_trade/osint/sanctions.py` | 353 | Trade AI Assistant — OSINT Layer 4: 制裁名单筛查。 · 函数:11 · ⚑DEGRADED |
| `backend/app/services/foreign_trade/osint/scoring.py` | 131 | Trade AI Assistant — OSINT 模块：风险评分与建议生成。 · 函数:2 |
| `backend/app/services/foreign_trade/osint/tech_stack.py` | 159 | Trade AI Assistant — OSINT Layer 5: 技术栈检测（BuiltWith-style）。 · 函数:2 |
| `backend/app/services/foreign_trade/osint/whois.py` | 304 | Trade AI Assistant — OSINT Layer 2: WHOIS 域名查询。 · 函数:5 · ⚑DEGRADED |
| `backend/app/services/foreign_trade/osint_service.py` | 26 | OSINT 背调 API 封装。 · 函数:1 |
| `backend/app/services/foreign_trade/platform_health_alert_service.py` | 98 | GW-G-SM-04 — 平台账号 login_status 超时告警。 · 函数:2 |
| `backend/app/services/foreign_trade/prospect_cleaner_service.py` | 109 | 潜客数据清洗 — 改编自 EricHong123/Eric_Frank DataCleanerSkill（核心逻辑，无 pandas）。 · 函数:5 |
| `backend/app/services/foreign_trade/prospect_skill.py` | 45 | 智能搜客技能 — 对应 prospecting SKILL.md。 |
| `backend/app/services/foreign_trade/publish_preflight_checklist_service.py` | 161 | GW-G-CC-04 — 发布前人审清单（数字/认证/MOQ）。 · 函数:5 |
| `backend/app/services/foreign_trade/sales_enablement_skill.py` | 55 | 销售赋能技能 — 对应 sales-enablement SKILL.md。 |
| `backend/app/services/foreign_trade/seo_audit_skill.py` | 57 | SEO 审计技能 — 对应 seo-audit SKILL.md。 |
| `backend/app/services/foreign_trade/skill_registry.py` | 118 | 外贸 AI 技能注册表 — 动态发现、注册、调用技能。 · 类:SkillResult,SkillMeta,SkillRegistry |
| `backend/app/services/foreign_trade/trade_document_export_service.py` | 199 | PI / 报价单导出 — DOCX（OOXML）与可打印 HTML。 · 函数:4 |
| `backend/app/services/foreign_trade/trade_document_service.py` | 121 | 形式发票 PI / 报价单 — 改编自 smart-trade-ai 商务文档能力（Markdown 结构化输出）。 · 函数:2 |
| `backend/app/services/foreign_trade/utm_attribution_service.py` | 276 | GW-P-TR-01 — UTM 全链路：矩阵 publish_task → 独立域 → 询盘。 · 函数:8 |
| `backend/app/services/foreign_trade/website_icp_service.py` | 139 | 官网 ICP 画像 — 改编自 qingchuh/sale_agent_factory WebAnalyzer（MIT）。 · 函数:4 |
| `backend/app/services/foreign_trade_ecosystem_service.py` | 151 | 外贸工具·技能·生态目录 — 随源码部署，供 Admin/API/研究员引用。 · 函数:8 |
| `backend/app/services/forum_sidecar_service.py` | 144 | Apache Answer 论坛 Sidecar — 健康检查、租户嵌入配置。 · 函数:6 |
| `backend/app/services/forum_webhook_service.py` | 319 | 论坛 Webhook — 新问题 → SEO 候选；含联系方式 → 询盘草稿；采纳答案 → Wiki 草稿。 · 函数:11 |
| `backend/app/services/founder_wechat_service.py` | 116 | 创始人微信唯一绑定校验。 · 函数:9 |
| `backend/app/services/gdpr_compliance.py` | 221 | GDPR 合规服务 — FIX-46 · 类:DataSubjectRequest,RequestStatus,GDPRComplianceService |
| `backend/app/services/gdpr_compliance_service.py` | 41 | 出海数据合规与 GDPR 隐私治理服务模块。 · 类:GDPRComplianceService |
| `backend/app/services/geo/geo_writing_policy.py` | 382 | GEO 写作策略 v3 — Princeton 引用战术 + arXiv 2026 最新研究 + 去 AI 味。 · 类:ContentQualityScore · 函数:10 |
| `backend/app/services/geo/headless_rank_probe_service.py` | 288 | Headless 排名探针 — 外置 Sidecar（Playwright/Browser Use）或显式 dev stub。 · 函数:11 · ⚑DEGRADED |
| `backend/app/services/geo/multi_engine_rank_registry.py` | 183 | 多流量入口排名注册表 — 百度 / 豆包 / 360 / 大模型 / 出海搜索 分轨探测。 · 类:TrafficEngine · 函数:6 |
| `backend/app/services/geo/platform_discovery_service.py` | 100 | 平台发现与扩展 — 对照 catalog / live 适配器，持续拉高 GEO 覆盖面。 · 函数:5 |
| `backend/app/services/geo/platform_rank_registry.py` | 130 | 平台 × GEO 排名权重注册表 — 排名优先准则下的发布顺序。 · 类:PlatformRankProfile · 函数:4 |
| `backend/app/services/geo/public_tech_reference_service.py` | 131 | 公开技术资料引用 — 国标/专利摘要等脱敏改写，供 GEO 内容注入可验证参数。 · 函数:4 |
| `backend/app/services/geo/tavily_search.py` | 107 | Tavily 外网 AI/SEO 新闻搜索（RADAR-09）。 · 函数:3 |
| `backend/app/services/geo/tech_radar_fetch.py` | 743 | GEO 技术雷达 v2 — 定时抓取 GEO/SEO 最新论文、论坛、白帽技术、开源工具。 · 类:RadarSource,RadarItem · 函数:12 · ⚑STUB |
| `backend/app/services/geo/tech_radar_reports_service.py` | 53 | RADAR-06/08：技术雷达 Markdown 日报索引。 · 函数:3 |
| `backend/app/services/geo_agents.py` | 422 | GEO Agents — 竞品追踪 + 技术雷达 + 定时调度 · 类:CompetitorTarget,TechSource,MonitorResult,ScanResult,CompetitorMonitorAgent,TechRadarAgent · 函数:4 · ⚑STUB |
| `backend/app/services/geo_alert_service.py` | 480 | GEO Alert Service - 预警服务层（SQLAlchemy 版本） · 类:AlertRuleEngine,GeoAlertService |
| `backend/app/services/geo_engine_service.py` | 551 | GEO 引擎 — 多模型收录与「推荐位」探测。 · 类:GEOEngine |
| `backend/app/services/geo_lead_service.py` | 129 | GEO Lead Service - 询盘统计服务（从sourcechain-geo-engine合并） · 类:GeoLeadService · 函数:3 · ⚑DEGRADED |
| `backend/app/services/geo_rag_evaluator.py` | 175 | GEO RAG 内容质量评估器 · 类:EvaluationResult,GEORAGEvaluator · 函数:1 |
| `backend/app/services/geo_rank_guard.py` | 184 | GEO Rank Guard — 发布前五维质量门禁 · 类:GuardMetrics,GuardResult,GEORankGuard · 函数:1 |
| `backend/app/services/geo_rank_guard_probe.py` | 133 | GEO Rank Guard 探针 — 司令部 / Celery / Hermes 告警共用。 · 函数:5 |
| `backend/app/services/globalization_service.py` | 267 | 全球化多语言服务 · 类:GlobalizationService |
| `backend/app/services/goodjob/__init__.py` | 1 | GoodJob 附属桥服务（批次 B：customer_pool 投影 + 单证委派）。 |
| `backend/app/services/goodjob/customer_pool_projection.py` | 104 | customer_pool 投影同步 · UJ 真相 → GoodJob 工作副本. · 函数:7 |
| `backend/app/services/goodjob/trade_document_bridge.py` | 104 | trade-documents 桥 · 单证生成委派 GoodJob（批次 B）. · 函数:5 |
| `backend/app/services/growth_loop_service.py` | 39 | 外贸全自动化获客闭环引擎 (Growth Loop Engine)。 · 类:GrowthLoopEngine |
| `backend/app/services/growth_services.py` | 321 | 推荐奖励机制 + 客户成功体系 — FIX-49/50 · 类:ReferralStatus,ReferralService,HealthScoreTier,CustomerSuccessService |
| `backend/app/services/growth_tools_service.py` | 510 | 三大增长内置工具 — 热门词库 / 内容质检 / AI 引流监测。 · 函数:14 |
| `backend/app/services/hermes/__init__.py` | 1 | Hermes — 内部插件平台（对外品牌：旺财插件市场）。 |
| `backend/app/services/hermes/a2a_skill_marketplace_service.py` | 591 | Hermes A2A 技能市场 — Brief→ECC→部门路由 沉底为可调用 Agent 技能。 · 函数:19 |
| `backend/app/services/hermes/agency/__init__.py` | 13 | Hermes 内嵌 agency-orchestrator 专家角色库。 |
| `backend/app/services/hermes/agency/llm_router.py` | 639 | agency-orchestrator 10 provider / 7 免 Key — Hermes LLM 路由（对齐 ao factory）。 · 类:AgencyLlmConfig · 函数:19 · ⚑DEGRADED |
| `backend/app/services/hermes/agency/orchestrator_bridge.py` | 385 | Hermes × agency-orchestrator — 专家角色库编排桥接。 · 函数:9 · ⚑DEGRADED |
| `backend/app/services/hermes/agency/provider_setup.py` | 240 | Hermes agency LLM — 服务器/bootstrap 安装计划（非交互部分可脚本化）。 · 函数:3 |
| `backend/app/services/hermes/agency/role_loader.py` | 131 | agency-orchestrator 角色库加载 — 产品内嵌 agency-agents 中文专家人格。 · 函数:5 |
| `backend/app/services/hermes/agency/workflow_runner.py` | 380 | agency-orchestrator YAML 工作流执行 — Hermes 驱动的 Python DAG 引擎。 · 函数:13 · ⚑MOCK/STUB/DEGRADED |
| `backend/app/services/hermes/alert_dispatcher.py` | 376 | Hermes 运维告警 — 飞书 Webhook（巡站 / 技术雷达 / 异常）。 · 函数:13 · ⚑DEPRECATED |
| `backend/app/services/hermes/anysearch_probe_service.py` | 165 | AnySearch 外网探测 — Hermes 研究员 hourly / 批量脚本共用。 · 函数:5 |
| `backend/app/services/hermes/brand_audit_service.py` | 196 | COMP-02 品牌抽检：扫描租户/落地页可见文案是否泄露禁词。 · 函数:6 |
| `backend/app/services/hermes/brand_guard.py` | 94 | 对外文案脱敏：禁止第三方 Agent 产品商标进入用户可见字段。 · 函数:2 |
| `backend/app/services/hermes/browser_companion.py` | 81 | 浏览器伴侣插件 — 本地 Chrome/Edge 扩展，不进服务端执行。 · 函数:4 |
| `backend/app/services/hermes/command_center.py` | 460 | L0 超管司令部 — 聚合 Hermes / DeerFlow / SEO / 视频 Worker 态势（只读）。 · 函数:16 |
| `backend/app/services/hermes/command_center_cache.py` | 262 | 司令部快照缓存 — Redis + Stale-While-Revalidate + 云端后台预热。 · 类:CommandCenterPrewarmScheduler · 函数:10 |
| `backend/app/services/hermes/companion_launch.py` | 145 | 优丁平台专属 · 浏览器伴侣唤起（内容仅来自本平台任务，不可独立外发）。 · 类:CompanionLaunchError · 函数:4 |
| `backend/app/services/hermes/consistency_harness_service.py` | 320 | 一致性控制服务 (Consistency Harness) · 类:ConsistencyHarnessService |
| `backend/app/services/hermes/content_knowledge_graph_service.py` | 438 | 内容知识图谱服务 (Content Knowledge Graph) · 类:ContentKnowledgeGraphService |
| `backend/app/services/hermes/daily_autonomous_cycle.py` | 638 | 每日自主运营闭环 — 串联所有步骤。 · 类:StepResult,DailyAutonomousCycleScheduler · 函数:13 |
| `backend/app/services/hermes/daily_rank_ops.py` | 309 | Hermes 每日排名攻坚 — 多引擎 probe + 战术雷达 + ECC 评审 + 回归告警。 · 函数:9 |
| `backend/app/services/hermes/deerflow_ops_service.py` | 93 | DeerFlow 超管运维：全平台队列分页 + SLO 指标。 · 函数:2 |
| `backend/app/services/hermes/ecc_expert_panel.py` | 379 | Hermes ECC 专家人格评审 — 对齐 docs/技术栈-智能体-MCP-调度表，只读测试、不装依赖。 · 类:EccExpert · 函数:12 · ⚑DEGRADED/DEPRECATED |
| `backend/app/services/hermes/executors/__init__.py` | 23 | Hermes Executor Plugins Package. |
| `backend/app/services/hermes/executors/accio_executor.py` | 164 | Accio Executor Plugin for Hermes — 销售飞轮（接真实服务）。 · 类:AccioExecutor · ⚑MOCK/STUB |
| `backend/app/services/hermes/executors/base.py` | 121 | Base Executor Contract for Hermes Orchestration. · 类:ExecutorContext,BaseExecutor,ExecutorRegistry |
| `backend/app/services/hermes/executors/content_executor.py` | 127 | Content Executor Plugin — 内容页创建与发布。 · 类:ContentExecutor · 函数:1 · ⚑DEGRADED |
| `backend/app/services/hermes/executors/deerflow_executor.py` | 112 | DeerFlow Executor Plugin for Hermes Orchestration. · 类:DeerflowExecutor |
| `backend/app/services/hermes/executors/egress_executor.py` | 112 | Egress Executor Plugin — 静态 IP 槽位分配 + 指纹环境。 · 类:EgressExecutor |
| `backend/app/services/hermes/executors/goodjob_crm_executor.py` | 171 | GoodJob CRM Executor — 接真实 HTTP 桥（不再返回硬编码假单证）。 · 类:GoodJobCrmExecutor · ⚑MOCK/STUB |
| `backend/app/services/hermes/executors/nurture_executor.py` | 134 | Nurture Executor Plugin — 多平台账号养护（养号）。 · 类:NurtureExecutor |
| `backend/app/services/hermes/executors/publish_executor.py` | 289 | Publish Executor Plugin — 多平台内容分发。 · 类:PublishExecutor |
| `backend/app/services/hermes/executors/site_builder_executor.py` | 162 | Site Builder Executor Plugin for Hermes Orchestration. · 类:SiteBuilderExecutor · ⚑MOCK/DEGRADED |
| `backend/app/services/hermes/executors/trade_ai_agent_executor.py` | 186 | Trade AI Agent Executor — 接真实适配器（不再返回假数据）。 · 类:TradeAiAgentExecutor · ⚑MOCK |
| `backend/app/services/hermes/expert_execution_registry.py` | 1324 | 专家执行注册表 — 让专家真正执行专职工作。 · 函数:60 |
| `backend/app/services/hermes/expert_inspection_registry.py` | 1540 | 专家巡检注册表 — 基于 ECC (Everything Claude Code) 真实技能体系实现专家功能。 · 函数:37 |
| `backend/app/services/hermes/flywheel_workflow.py` | 305 | Hermes 卖货飞轮闭环 — 研究 → 找客 → 编排（内部调度，对外脱敏）。 · 函数:6 |
| `backend/app/services/hermes/github_ecosystem_scout_service.py` | 520 | GitHub 生态侦察 — 代用户翻找开源项目，映射系统短板，推送 PM Inbox（不自动安装）。 · 函数:21 · ⚑STUB |
| `backend/app/services/hermes/greedy_agency_orchestrator_service.py` | 396 | Hermes 财迷疯 × agency-agents-zh — 专家库编排（SaaS 内嵌 220+ 角色）。 · 函数:15 · ⚑DEGRADED |
| `backend/app/services/hermes/greedy_avatar_constitution.py` | 180 | 财迷疯分身宪法（摸金校尉）— 与 SaaS Hermes 维护宪法隔离。 · 类:GreedyAvatarViolation · 函数:5 · ⚑MOCK |
| `backend/app/services/hermes/greedy_contest_memory_service.py` | 1011 | 摸金校尉 · 挣钱大赛 + 专家记忆 — 持续盈利者不下线，越赛越有 experience。 · 函数:35 · ⚑DEGRADED |
| `backend/app/services/hermes/greedy_cumulative_personality_service.py` | 365 | 全球累计（周/月/年）+ 摸金打江山人格（羞耻感·奋发图强·比上次更强）。 · 函数:13 · ⚑DEGRADED |
| `backend/app/services/hermes/greedy_endurance_scheduler.py` | 129 | 7×24 持久耐力赛调度 — 每小时检查 30 天擂台是否满期并轮转。 · 类:GreedyEnduranceScheduler |
| `backend/app/services/hermes/greedy_hub_service.py` | 89 | 摸金校尉总控 Hub — 一次拉取累计/大赛/耐力/闭环/队列/生存脉搏。 · 函数:1 |
| `backend/app/services/hermes/greedy_production_readiness_service.py` | 323 | 摸金校尉 · 生产就绪检查 + 平台自营租户 bootstrap。 · 函数:9 · ⚑MOCK/STUB/DEGRADED |
| `backend/app/services/hermes/greedy_project_board_service.py` | 497 | 挣钱项目看板 — 从大赛轮次、专家归因收入、L4 审核历史聚合，禁止写死假数。 · 函数:9 |
| `backend/app/services/hermes/greedy_publish_queue_service.py` | 262 | L4 发布队列人工审核 — 通过/驳回 + 审核历史。 · 函数:9 · ⚑DEGRADED |
| `backend/app/services/hermes/greedy_revenue_loop_scheduler.py` | 184 | 摸金校尉 · 搞钱闭环日调度 — 与 SaaS Hermes 巡站调度隔离。 · 类:GreedyRevenueLoopScheduler |
| `backend/app/services/hermes/greedy_revenue_loop_service.py` | 358 | 财迷疯 · 摸金校尉 — 搞钱商业闭环（调研→编排→生产→发出→卖出跟踪→收款 KPI）。 · 函数:12 |
| `backend/app/services/hermes/greedy_survival_digest_scheduler.py` | 149 | 摸金校尉 · Survival 周报调度 — 每周一推送飞书（全球累计 + 人格 + 大赛）。 · 类:GreedySurvivalDigestScheduler |
| `backend/app/services/hermes/greedy_survival_digest_service.py` | 161 | 摸金校尉 · Survival 周报 — 飞书推送（全球累计 + 人格 + 大赛 Top5）。 · 函数:4 |
| `backend/app/services/hermes/greedy_survival_publish_service.py` | 195 | 摸金校尉 L4 审核通过 → ContentMaster + PublishTask 真发。 · 函数:5 · ⚑DEGRADED |
| `backend/app/services/hermes/harness_gateway.py` | 120 | DeepSeek Harness Gateway —— 最外层意图入口（接真实拆解器）。 · 类:HarnessGateway · 函数:1 · ⚑MOCK/STUB |
| `backend/app/services/hermes/hermes_ai_lanes_service.py` | 58 | RADAR-07 / AI-03：Hermes ops vs 租户 customer AI 场景分流快照。 · 函数:1 |
| `backend/app/services/hermes/hermes_continuous_iteration_service.py` | 430 | Hermes 持续迭代闭环 — 宪法 + DeerFlow + 研究员 + 营销/各部门 + ECC。 · 函数:16 · ⚑DEGRADED |
| `backend/app/services/hermes/hermes_mcp_server.py` | 43 | Hermes MCP Server. · 类:GeneratePlanToolInput,HermesMCPServer |
| `backend/app/services/hermes/hermes_rank_first_constitution.py` | 51 | Hermes 存在第一准则 — 排名效果优先于一切运维动作。 · 函数:1 |
| `backend/app/services/hermes/install_service.py` | 150 | 租户 Hermes 插件安装 / 启用。 · 函数:5 |
| `backend/app/services/hermes/learning_harness_service.py` | 391 | 学习更新服务 (Learning Harness) · 类:LearningHarnessService |
| `backend/app/services/hermes/maintenance_constitution.py` | 121 | Hermes 巡站维护宪法 — 底层写死：只维护、不破坏。 · 类:HermesMaintenanceViolation · 函数:3 |
| `backend/app/services/hermes/marketing_anysearch_workflow_service.py` | 389 | Hermes 营销 Lane — AnySearch 数字产品/智能体变现深度拆解与工作流编排。 · 函数:11 |
| `backend/app/services/hermes/ops_access.py` | 26 | Hermes 运维 API 访问门控 — L0 超管专用，租户不可见。 · 函数:2 |
| `backend/app/services/hermes/ops_autopilot.py` | 193 | Hermes 运维自动驾驶 — 巡站 + 技术雷达 + 自愈 + 飞书通知。 · 函数:4 · ⚑DEGRADED |
| `backend/app/services/hermes/planner_service.py` | 403 | Hermes 拆解器（Planner）—— 意图 → 任务图。 · 函数:11 · ⚑STUB/DEGRADED |
| `backend/app/services/hermes/platform_survival_service.py` | 364 | Hermes 平台生存基金 — 财迷疯真钱账本（仅超管收款，与租户账单隔离）。 · 函数:11 |
| `backend/app/services/hermes/prompt_harness_service.py` | 500 | 统一 Prompt 构建管理服务 (Prompt Harness) · 类:PromptHarnessService |
| `backend/app/services/hermes/publish_history_aggregate.py` | 81 | 超管统一发布历史：SEO 图文 + 视频矩阵。 · 函数:1 |
| `backend/app/services/hermes/registry.py` | 125 | Hermes 插件注册表 — 对内完整目录，对外经 marketplace 脱敏。 · 函数:6 |
| `backend/app/services/hermes/research_brief_service.py` | 450 | 外贸研究员 — 只读信号 → ResearchBrief JSON（违宪动作禁止自动执行）。 · 函数:14 |
| `backend/app/services/hermes/role_economics_service.py` | 269 | 211 专家变现契约 — 每位角色须有赚钱路径，否则不得摸金上场。 · 函数:9 |
| `backend/app/services/hermes/runtime.py` | 513 | Hermes 插件运行时 — 统一执行入口。 · 类:HermesPluginError · 函数:9 |
| `backend/app/services/hermes/safe_remediation.py` | 146 | Hermes 安全自愈 — 仅白名单动作，违宪即拒绝。 · 函数:3 |
| `backend/app/services/hermes/scoring_harness_service.py` | 362 | 评分分发服务 (Scoring Harness) · 类:ScoringHarnessService |
| `backend/app/services/hermes/site_build_workflow.py` | 205 | Hermes 智能建站工作流 — ECC 专家流水线 + 设计技能约束。 · 函数:5 |
| `backend/app/services/hermes/site_builder_ecc_pipeline.py` | 301 | Hermes 建站 ECC 专家流水线 — 美工/文案/视觉营销/美学 UI，非裸 LLM。 · 函数:10 |
| `backend/app/services/hermes/site_cta_audit.py` | 43 | 生成站双 CTA + 24h 询盘承诺抽检（western-inquiry-conversion）。 · 函数:1 |
| `backend/app/services/hermes/site_design_guard.py` | 75 | 租户建站设计 manifest 与设计门禁（供 Hermes 流水线复用，避免循环 import）。 · 函数:3 |
| `backend/app/services/hermes/site_patrol_scheduler.py` | 193 | Hermes 7×24 巡站调度 — 只读维护，间隔可配置。 · 类:HermesSitePatrolScheduler · 函数:1 |
| `backend/app/services/hermes/site_patrol_service.py` | 606 | Hermes 7×24 巡站维护 — 只读探测 + 建议，不执行破坏性操作。 · 函数:18 · ⚑DEGRADED |
| `backend/app/services/hermes/site_patrol_store.py` | 131 | Hermes 巡站快照持久化（仅单键 SystemSetting）。 · 函数:5 |
| `backend/app/services/hermes/task_control_supervisor.py` | 416 | Hermes Task Control Supervisor. · 函数:6 · ⚑DEGRADED |
| `backend/app/services/hermes/tech_radar_markdown_export.py` | 49 | RADAR-08：技术雷达 Markdown 日报导出。 · 函数:2 |
| `backend/app/services/hermes/tech_validation.py` | 123 | Hermes 对抓取技术候选做安全验证（不安装、不改依赖）。 · 函数:4 · ⚑DEPRECATED |
| `backend/app/services/hermes/templates/outreach_scenario.py` | 53 | B2B Outreach and Lead Gen Scenario Template. · 函数:1 |
| `backend/app/services/hermes/templates/site_build_scenario.py` | 51 | Site Build and Distribution Scenario Template. · 函数:1 · ⚑DEGRADED |
| `backend/app/services/hermes/video_matrix_workflow.py` | 300 | Hermes 视频矩阵真发编排 — 预检 → 分发 → 验真汇总。 · 函数:5 |
| `backend/app/services/hermes/worldfirst_webhook_service.py` | 231 | 万里汇 WorldFirst Webhook → 财迷疯 survival 台账（摸金校尉 L6 自动收款）。 · 函数:8 |
| `backend/app/services/hermes/write_boundary_audit_service.py` | 126 | ARCH-03：Hermes 写库边界静态审计（只读扫描）。 · 函数:6 |
| `backend/app/services/hub_urls.py` | 48 | 总站枢纽 URL 构建 · 函数:3 |
| `backend/app/services/im_channel_webhook_service.py` | 36 | 七步⑤：企微 / 抖音私信 → 统一询盘入库（框架 webhook 入口）。 · 函数:1 |
| `backend/app/services/im_locale_service.py` | 325 | IM 渠道多语言文案与访客解析（12 语种）。 · 类:ResolvedIMChannel · 函数:7 |
| `backend/app/services/industry_pattern_service.py` | 353 | 跨租户行业模式学习服务 — 行业匿名聚合 + 战术推荐。 · 类:IndustryInsight,IndustryInsightService · 函数:2 · 表:industry_insights |
| `backend/app/services/inquiries_portal_service.py` | 61 | 询盘入口聚合 — 统一说明 v1 / v2 / unified 路径。 · 类:InquiriesPortalService · ⚑DEPRECATED |
| `backend/app/services/inquiries_unified_service.py` | 502 | 询盘 v1 / v2 / unified 统一序列化与列表。 · 类:InquiriesUnifiedService · 函数:2 · ⚑DEPRECATED |
| `backend/app/services/inquiry_assignment_audit_service.py` | 303 | 询盘负责人变更 — 结构化审计（operation_logs）。 · 函数:9 |
| `backend/app/services/inquiry_lead_assignment_service.py` | 216 | 平台落地页线索 — 自动分配销售 + 飞书通知。 · 函数:6 |
| `backend/app/services/inquiry_push_service.py` | 70 | 新询盘 → Push 通知商家（APP-1b 生产链路）。 · 函数:2 |
| `backend/app/services/inquiry_weekly_service.py` | 64 | 租户询盘周报 — P0-5 honest 报表（数字可为 0，不可假）。 · 函数:2 |
| `backend/app/services/integrations_status_service.py` | 137 | 双栈集成状态 — FastAPI 主库 + SEO 矩阵 + 可选 Node seo-backend。 · 函数:3 · ⚑MOCK/DEGRADED |
| `backend/app/services/invoice_application_service.py` | 546 | 开票申请合规校验与业务逻辑。 · 类:InvoiceApplicationError,InvoiceApplicationService · 函数:3 |
| `backend/app/services/invoice_pdf_service.py` | 136 | P1-08：租户账单简易 PDF（无第三方依赖）。 · 函数:3 |
| `backend/app/services/journey_health_service.py` | 220 | 租户旅程健康度 — PM / 数据 / 用研可读的缺口诊断（非 mock 分数）。 · 函数:7 · ⚑MOCK |
| `backend/app/services/jtbd_site_service.py` | 269 | SITE-JTBD-01 · B2B 建站思维层（与 frontend industryPresets.ts 对齐）。 · 函数:5 |
| `backend/app/services/keyword_tracker.py` | 246 | 关键词排名追踪服务 - Phase 4 · 类:KeywordData,KeywordTracker · 函数:1 |
| `backend/app/services/knowledge_ingestion.py` | 344 | 知识库自动沉淀服务 · 类:KnowledgeIngestionService |
| `backend/app/services/knowledge_service.py` | 490 | 建材行业知识库 - RAG检索服务 · 类:KnowledgeService |
| `backend/app/services/lab_site_editor_service.py` | 103 | FE-11 站点编辑器试点 — 草稿读写（租户 settings 或用户级文件兜底） · 函数:4 |
| `backend/app/services/langchain_service.py` | 245 | LangChain 服务层 — 模型分发、会话管理、流式对话、知识库 RAG · 类:SessionManager · 函数:5 · ⚑DEGRADED |
| `backend/app/services/license_service.py` | 192 | 设备指纹 + 授权码 + 套餐订单 服务（P1-5）。 · 函数:6 |
| `backend/app/services/logistics_access.py` | 29 | 物流模块 — 租户成员订单可见性。 · 函数:1 |
| `backend/app/services/logistics_dashboard_service.py` | 129 | 物流看板 — 基于真实订单聚合（P1-09 / P2-06）。 · 函数:2 |
| `backend/app/services/logistics_provider.py` | 154 | 物流轨迹第三方适配（快递100 / 沙箱）。 · 函数:4 · ⚑DEGRADED |
| `backend/app/services/logistics_tracking_service.py` | 96 | 物流轨迹查询与订单回填。 · 函数:4 |
| `backend/app/services/matching_engine/__init__.py` | 21 | Product Finder 匹配引擎包。 |
| `backend/app/services/matching_engine/engine.py` | 554 | Product Finder 匹配引擎（纯函数，不依赖 FastAPI / SQLAlchemy）。 · 类:MatchingEngine · 函数:15 |
| `backend/app/services/matching_engine/schemas.py` | 96 | Product Finder 匹配引擎 — 请求 / 响应 Pydantic 模型。 · 类:ProductMatchRequest,DimensionScores,MatchItem,RejectedItem,MatchResponse |
| `backend/app/services/matrix_admin_bridge.py` | 173 | SEO 矩阵 admin_users 只读校验：MySQL（生产）与 SQLite（本地）双模式，供统一登录使用。 · 函数:7 |
| `backend/app/services/media/platform_title_adapt.py` | 34 | VID-11：多平台标题/描述长度适配。 · 函数:1 |
| `backend/app/services/media_cleanup_scheduler.py` | 116 | 视频成品定时清理调度。 · 类:MediaCleanupScheduler |
| `backend/app/services/media_cloud_upload_service.py` | 316 | 渲染完成后异步上云：酷播（国内播放）+ R2（海外发布）。 · 函数:15 |
| `backend/app/services/media_cuplayer_service.py` | 128 | 酷播云（保利威点播）官方上传接口。 · 类:CuplayerUploadError · 函数:4 |
| `backend/app/services/media_factory_service.py` | 602 | 多媒体工厂业务逻辑。 · 函数:18 · ⚑DEGRADED |
| `backend/app/services/media_guest_service.py` | 59 | 未登录访客视频任务归属：guest_token → tenant_id。 · 函数:3 |
| `backend/app/services/media_lenslink_service.py` | 144 | 棱束链（S3 兼容）灾备上传。 · 类:MediaLenslinkError · 函数:8 |
| `backend/app/services/media_publish_service.py` | 264 | 多媒体工厂 → 多平台发布（带 video_url，不破坏 SEO 正文）。 · 函数:6 |
| `backend/app/services/media_qiniu_service.py` | 115 | 七牛云 Kodo — 国内产品图存储（S3 类对象存储 + CDN 域名）。 · 类:MediaQiniuError · 函数:5 |
| `backend/app/services/media_r2_service.py` | 164 | Cloudflare R2（S3 兼容）上传与预签名。 · 类:MediaR2Error · 函数:10 |
| `backend/app/services/media_render_worker.py` | 200 | 多媒体工厂渲染 worker：queued → rendering → done/failed。 · 函数:7 · ⚑MOCK |
| `backend/app/services/media_retention_service.py` | 275 | 视频成品保留：预览 TTL、下载/发布 handoff、文件清理。 · 函数:13 |
| `backend/app/services/media_seo_service.py` | 159 | 视频任务 SEO / GEO 增强：独立 VideoObject，不覆盖文章页既有 Schema。 · 函数:4 |
| `backend/app/services/media_tenant_traffic_service.py` | 327 | 视频 → 租户官网流量：落地页、UTM、结构化数据、GEO 要点。 · 函数:14 |
| `backend/app/services/media_video_edit_service.py` | 358 | 视频剪辑与调试（ffmpeg + 脚本重渲）。 · 函数:12 |
| `backend/app/services/minio_service.py` | 267 | MinIO对象存储服务 — 租户隔离增强 · 类:MinioService · 函数:3 |
| `backend/app/services/model_gateway/__init__.py` | 55 | Model Gateway — 轮16 重构（总纲 §4.6）。 · 函数:1 |
| `backend/app/services/model_gateway/capability.py` | 57 | 能力标签（总纲 §4.6）：reasoning/coding/vision/writing/translation/structured_output/cheap/fast。 · 函数:1 |
| `backend/app/services/model_gateway/gateway.py` | 154 | Model Gateway 门面（总纲 §4.6）。 · 类:ModelGateway · 函数:2 · ⚑MOCK/DEGRADED |
| `backend/app/services/model_gateway/ledger.py` | 184 | 成本记账（总纲 §4.6）：每次 LLM 调用写 model_call_ledger，可汇总至 token_ledger。 · 类:CostLedger · 函数:3 |
| `backend/app/services/model_gateway/router.py` | 156 | 能力路由：required_capabilities + 四维信号 → ai_engine 场景 tier。 · 类:ModelRouter · 函数:5 · ⚑DEGRADED |
| `backend/app/services/moss_auto_clip_pipeline.py` | 202 | MOSS-VL AI 智能剪辑自动化执行流水线（已挂载 SEO/GEO/AAO 排名优化引擎）。 · 类:RenderedClipArtifact,MossAutoClipPipeline · ⚑DEGRADED |
| `backend/app/services/moss_clip_and_publish_workflow.py` | 100 | MOSS-VL AI 剪辑与一键分发联动工作流（集成 SEO/GEO/AAO 排名自动增强）。 · 类:PublishDispatchResult,MossClipAndPublishWorkflow |
| `backend/app/services/moss_vl/__init__.py` | 20 | OpenMOSS / MOSS-VL 完整多模态开源引擎包。 |
| `backend/app/services/moss_vl/hot_reload_manager.py` | 286 | MOSS-VL 官方仓库追踪、双缓冲热更新与版本回滚管理器。 · 类:MossVersionSnapshot,MossRuntimeInstance,MossHotReloadManager · ⚑DEGRADED |
| `backend/app/services/moss_vl/model_loader.py` | 80 | MOSS-VL 官方模型权重加载器与量化支持。 · 类:MossVLModelLoader · ⚑MOCK |
| `backend/app/services/moss_vl/offline_inference.py` | 111 | MOSS-VL 官方离线视频全景推理引擎。 · 类:DenseEventAnnotation,OfflineInferenceEngine |
| `backend/app/services/moss_vl/realtime_session.py` | 127 | MOSS-VL-Realtime 官方实时流式会话 API。 · 类:StreamFrame,StreamMessage,MossRealtimeSession · 函数:1 |
| `backend/app/services/moss_vl/repo_syncer.py` | 116 | MOSS-VL 官方开源仓库自动化同步与环境检测工具。 · 类:MossRepoSyncer |
| `backend/app/services/moss_vl/xrope_spatial_temporal.py` | 64 | XRoPE (Cross-attention Rotary Position Embedding) 时空三维统一位置编码器。 · 类:SpatiotemporalCoordinate,XRoPEEmbedding |
| `backend/app/services/moss_vl_service.py` | 274 | MOSS-VL 时空多模态视频大模型服务总中枢（支持动态热更新与回滚）。 · 类:VideoSceneInfo,HighlightClipCandidate,VisualSubtitleItem,MossVLService · ⚑MOCK |
| `backend/app/services/n8n/__init__.py` | 25 | n8n 集成服务模块。 |
| `backend/app/services/n8n/trigger.py` | 290 | n8n 工作流触发器。 · 类:N8nTriggerService · 函数:1 |
| `backend/app/services/n8n/webhook.py` | 287 | n8n Webhook 接收服务。 · 类:N8nWebhookService · 函数:1 |
| `backend/app/services/n8n/workflow_registry.py` | 311 | n8n 工作流注册表。 · 类:WorkflowRecord,WorkflowRegistry · 函数:3 · ⚑STUB |
| `backend/app/services/nurture_execution_scheduler.py` | 248 | 养号全链路调度器 — 互动执行 + 定时发布 + 状态升级 + 规则计划。 · 类:NurtureExecutionScheduler |
| `backend/app/services/nurture_execution_worker.py` | 288 | 养号执行 Worker — 通过 AiToEarn API 自动执行点赞/评论/关注。 · 类:_UnsupportedAction · 函数:12 |
| `backend/app/services/nvidia_catalog_service.py` | 336 | NVIDIA NIM 模型目录：按业务场景分类（推理 / 文章 / 视频等）。 · 类:ModelEntry · 函数:4 |
| `backend/app/services/nvidia_customer_probe_scheduler.py` | 186 | 英伟达客户可用模型定时探测：默认每日 1:00 / 12:00 / 20:00（北京时间）。 · 类:NvidiaCustomerProbeScheduler · 函数:2 |
| `backend/app/services/nvidia_customer_probe_service.py` | 90 | 英伟达客户侧可用模型探测（卖货副驾 / 旺财插件场景）。 · 函数:3 |
| `backend/app/services/nvidia_customer_probe_store.py` | 65 | 英伟达客户可用模型探测快照（system_settings）。 · 函数:3 |
| `backend/app/services/nvidia_scenario_health_service.py` | 205 | NVIDIA 场景模型健康探测（chat / Cosmos infer）。 · 函数:6 · ⚑MOCK |
| `backend/app/services/nvidia_scenario_service.py` | 301 | NVIDIA 按业务场景选择/切换模型（持久化到 ai_model_configs）。 · 函数:8 |
| `backend/app/services/oauth_binding_service.py` | 111 | 第三方账号绑定（已登录用户）。 · 函数:4 |
| `backend/app/services/oauth_login.py` | 666 | 第三方 OAuth 登录：授权 URL 生成与 code 换身份。 · 函数:17 · ⚑STUB |
| `backend/app/services/omnichannel_support_service.py` | 37 | 海外多渠道智能客服 Agent (WhatsApp / LiveChat Widget)。 · 类:OmnichannelSupportService |
| `backend/app/services/onboarding_autopilot_job.py` | 156 | 注册后后台 autopilot — 0 等待进向导。 · 函数:6 |
| `backend/app/services/onboarding_autopilot_service.py` | 385 | 一键开业 — Time-to-Value 自动编排（Hermes → 旺财 → 首篇草稿）。 · 函数:9 |
| `backend/app/services/onboarding_chain_service.py` | 342 | Onboarding 全链：注册 → Hermes 建站 → 旺财预览 → 发布首篇。 · 函数:11 |
| `backend/app/services/onboarding_external_accounts.py` | 367 | 开户第三方账号 / 云存储 — 注册与实名流程编排（平台代开 vs 客户自备）。 · 函数:9 |
| `backend/app/services/onboarding_im_contacts_service.py` | 141 | 开户指引 — 即时通讯联系方式写入官网 contact 页（挂件读取，非旺财 Trade Q&A）。 · 函数:4 |
| `backend/app/services/onboarding_platform_service.py` | 161 | 开户向导 — 首个平台绑定（内嵌 OAuth/Cookie，不跳转菜单）。 · 函数:3 |
| `backend/app/services/onboarding_progress_service.py` | 798 | 开户待办六步 — 真实进度判定（对齐 client-dashboard-bento-spec §3） · 函数:24 · ⚑MOCK |
| `backend/app/services/onboarding_publish_service.py` | 232 | 开户首篇 — SEO 引用种子 + GeneratedContent + PublishTask 真入队。 · 函数:5 |
| `backend/app/services/onboarding_service.py` | 255 | 租户入驻引导服务 — 3步入驻 + 示例数据 + 成就系统 · 函数:4 |
| `backend/app/services/ops_autopilot_scheduler.py` | 134 | 开发环境运维自动驾驶 — 周期性健康探针，无需 Owner 开口。 · 类:OpsAutopilotScheduler |
| `backend/app/services/ops_backup_service.py` | 58 | 运维备份（SQLite 文件 + 元数据快照）。 · 函数:3 |
| `backend/app/services/ops_expert_autonomy_service.py` | 606 | 专家自治：自动修补（小事）+ 站会总结 + 通知 Owner（大事）。 · 函数:21 · ⚑MOCK |
| `backend/app/services/ops_readiness_alert_service.py` | 100 | 生产就绪失败时推送运维告警（飞书 Webhook）。 · 函数:2 |
| `backend/app/services/orchestrator/__init__.py` | 5 | 商业闭环编排器 — 串联从产品输入到成交的完整链路。 |
| `backend/app/services/orchestrator/commercial_loop.py` | 285 | 商业闭环编排器。 · 类:CommercialLoopOrchestrator · ⚑STUB/DEGRADED |
| `backend/app/services/order_addon_service.py` | 221 | Token 加购 — 支付成功后充值 Token（幂等按 order_no）。 · 函数:11 |
| `backend/app/services/order_payment_sync_service.py` | 71 | B2B 订单支付状态联动。 · 函数:2 |
| `backend/app/services/outreach_batch_compensate_service.py` | 138 | 批量外联补偿服务 —— ORCH-19 修复 · 函数:5 |
| `backend/app/services/paperclip/__init__.py` | 0 |  |
| `backend/app/services/paperclip/approval_gate.py` | 338 | Paperclip 审批门服务。 · 函数:14 |
| `backend/app/services/paperclip/budget_guard.py` | 234 | Paperclip 预算控制服务。 · 函数:7 |
| `backend/app/services/paperclip/goal_chain.py` | 332 | Paperclip 目标对齐链服务。 · 函数:11 |
| `backend/app/services/paperclip/heartbeat_engine.py` | 497 | Paperclip 心跳调度引擎。 · 类:PaperclipHeartbeatEngine · 函数:8 · ⚑DEGRADED |
| `backend/app/services/paperclip/orchestrator.py` | 996 | Paperclip 核心编排服务。 · 函数:30 |
| `backend/app/services/paperclip/tenant_context.py` | 362 | Paperclip 租户业务上下文 — 聚合产品/视频/询盘/行业数据供 220 个 Agent 使用。 · 函数:9 |
| `backend/app/services/payment_balance_service.py` | 268 | 余额支付接入服务 — FEAT-余额支付 · 类:BalancePaymentResult,BalancePreviewResult · 函数:3 |
| `backend/app/services/payment_compensation_service.py` | 152 | 支付权益发放补偿任务巡检服务 · 类:CompensationReprocessService · 函数:1 |
| `backend/app/services/payment_ops_audit_service.py` | 238 | 支付运维操作审计 — 探针 / 证书刷新 / staging 自检等落库。 · 函数:7 |
| `backend/app/services/payment_ops_service.py` | 738 | 支付运维 — 渠道状态与微信平台证书缓存（超管/运维）。 · 函数:22 · ⚑MOCK |
| `backend/app/services/payment_pkg/__init__.py` | 16 | 支付服务子包（单一职责拆分） |
| `backend/app/services/payment_pkg/payment_service_impl.py` | 785 | 通用支付服务（对接订单模型） · 类:PaymentService · ⚑MOCK/DEGRADED |
| `backend/app/services/payment_pkg/verify_flags.py` | 21 | 支付回调验签严格模式 — 单一权威判定。 · 函数:1 |
| `backend/app/services/payment_pkg/wechat_pay.py` | 235 | 微信支付服务（Native 扫码支付 + 回调验签 + 退款） · 类:WeChatPayService · ⚑MOCK/STUB |
| `backend/app/services/payment_service.py` | 983 | 支付服务 - 支付订单管理 + 微信支付 Native 模式（扫码支付） · 类:WeChatPayService,PaymentService · ⚑MOCK/STUB/DEGRADED |
| `backend/app/services/paypal_pay_service.py` | 83 | PayPal 国际支付服务模块。 · 类:PayPalPayService |
| `backend/app/services/performance_monitor.py` | 199 | 性能监控服务 - 追踪API响应时间和系统性能指标 · 类:PerformanceMetric,PerformanceMonitor · ⚑DEGRADED |
| `backend/app/services/pilot_rehearsal_service.py` | 109 | 保温厂试点：HTTPS 演示域与七步②彩排检查。 · 函数:4 |
| `backend/app/services/pipeline/__init__.py` | 6 | 四链路强制流水线（总纲 §6：双关卡与四链路加固）。 |
| `backend/app/services/pipeline/chains.py` | 156 | 四链路业务侧关卡接入（总纲 §6.4/§6.6：文章/视频/邮件/多平台分发）。 · 类:ChainGateReport · 函数:3 |
| `backend/app/services/pipeline/gates/__init__.py` | 1 | 双关卡（总纲 §6.4-1/2）：清洗关（CleanseGate）与复核关（ReviewGate）。 |
| `backend/app/services/pipeline/gates/cleanse.py` | 162 | 清洗关卡 CleanseGate（总纲 §6.4-1）。 · 类:CleanseIssue,CleanseReport,CleanseGate · 函数:4 · ⚑MOCK/STUB |
| `backend/app/services/pipeline/gates/review.py` | 132 | 复核关卡 ReviewGate（总纲 §6.4-2）。 · 类:ReviewVerdict,ReviewGate · 函数:2 · ⚑STUB |
| `backend/app/services/pipeline/state_machine.py` | 103 | 流水线状态机（总纲 §6.5：11 态）。 · 类:InvalidTransition · 函数:3 |
| `backend/app/services/pipeline/wiring.py` | 171 | Pipeline S3 接线（总纲 §6.4 / V1.7 待办）：存量质量件注册入双关卡。 · 函数:6 |
| `backend/app/services/plan_gate_service.py` | 164 | Plan Gate — 套餐功能校验（BE-04） · 函数:7 |
| `backend/app/services/platform_account_service.py` | 240 | 租户级平台账号：列表、绑定 upsert、媒体发布解析。 · 函数:8 |
| `backend/app/services/platform_alignment_service.py` | 54 | P1-10：40 平台 catalog 与 DB 对齐检查。 · 函数:2 |
| `backend/app/services/platform_catalog.py` | 257 | 40 平台主数据目录（国内 20 + 海外 20）。 · 函数:5 |
| `backend/app/services/platform_storage_provision_service.py` | 494 | 平台级产品图存储（七牛 / R2）开通、探测与验收 — 运维自动化。 · 类:QiniuCredentials,R2Credentials · 函数:13 · ⚑MOCK/DEGRADED |
| `backend/app/services/platform_sync_service.py` | 230 | 客户新增平台 → 超管审计、默认养号模板、指纹模板（客户无感）。 · 函数:7 |
| `backend/app/services/platforms/__init__.py` | 17 |  |
| `backend/app/services/platforms/baijiahao.py` | 398 | 百度百家号发布适配器 — 真实对接百家号开放平台 API。 · 类:BaijiahaoPublisher,BaijiahaoPublisherAdapter · 函数:1 |
| `backend/app/services/platforms/csdn.py` | 296 | CSDN 发布适配器 — 真实对接 CSDN 博客 API。 · 类:CSDNPublisher,CSDNPublisherAdapter · 函数:1 |
| `backend/app/services/platforms/toutiao.py` | 393 | 今日头条发布适配器 — 真实对接头条号开放平台 API。 · 类:ToutiaoPublisher,ToutiaoPublisherAdapter · 函数:1 |
| `backend/app/services/platforms/wechat.py` | 293 | 微信公众号发布适配器 —— 真实对接微信公众平台 API · 类:WeChatPublisher,WeChatPublisherAdapter |
| `backend/app/services/platforms/weibo.py` | 449 | 微博发布适配器 — 真实对接微博开放平台 API。 · 类:WeiboPublisher,WeiboPublisherAdapter · 函数:1 |
| `backend/app/services/platforms/xiaohongshu.py` | 371 | 小红书发布适配器 — 真实对接小红书创作者平台 API。 · 类:XiaohongshuPublisher,XiaohongshuPublisherAdapter · 函数:1 |
| `backend/app/services/platforms/zhihu.py` | 323 | 知乎发布适配器 — 真实对接知乎专栏 API。 · 类:ZhihuPublisher,ZhihuPublisherAdapter · 函数:1 |
| `backend/app/services/policy/__init__.py` | 5 | Policy Engine 包（总纲 §3.1/§6.6 P2；轮20）。 |
| `backend/app/services/policy/engine.py` | 250 | Policy Engine：统一策略裁决（总纲 §3.1/§7.2/§6.6 P2；轮20）。 · 类:PolicyDecision,PolicyEngine · 函数:1 |
| `backend/app/services/product_content_ai_service.py` | 168 | 产品页 AI 生成/润色 — 走 NVIDIA NIM 场景模型（invoke_llm）。 · 函数:4 · ⚑MOCK |
| `backend/app/services/product_image_storage_service.py` | 458 | 产品图片空间 — 国内（七牛）/ 国外（R2）分轨存储。 · 函数:19 |
| `backend/app/services/product_service.py` | 405 | 产品服务层 · 类:CategoryService,ProductService,ProductDocumentService |
| `backend/app/services/production_readiness_service.py` | 900 | 生产上线就绪检查（Sprint I）。 · 类:ReadinessCheck,ReadinessReport · 函数:20 · ⚑MOCK |
| `backend/app/services/prospect_scorer.py` | 221 | 潜客线索 4 维评分服务（匹配度 / 邮箱可信度 / 证据完整度 / 联系人完整度）。 · 类:ProspectScorer · 函数:6 |
| `backend/app/services/provisioning_service.py` | 128 | 支付成功后自动开户 / 续费 · 类:ProvisioningService |
| `backend/app/services/publish_capability_registry.py` | 288 | 发布能力注册表 — 多 Worker 真发，禁止假成功。 · 函数:7 · ⚑MOCK/DEGRADED |
| `backend/app/services/publish_dispatch_service.py` | 338 | SEO 矩阵图文发布：平台适配器 + PublishService 异步回退。 · 类:SeoPublishService,PublishDispatchService · 函数:4 · ⚑STUB |
| `backend/app/services/publish_queue_service.py` | 99 | 发布队列生产化：统计、僵死恢复、失败重试。 · 函数:3 |
| `backend/app/services/publish_readiness_service.py` | 86 | 发布就绪总览 — 建站 / IP 槽位 / 平台绑号，供内容分发中心使用。 · 函数:1 |
| `backend/app/services/publish_result_notify_service.py` | 82 | 矩阵发布结果通知 — 飞书 / Slack Webhook（诚实：仅汇报验真结果）。 · 函数:3 |
| `backend/app/services/publish_service.py` | 1211 | Publish Service - handles content publishing to various platforms. · 类:BasePublisher,UnimplementedPublisher,WeChatPublisher,ToutiaoPublisher,ZhihuPublisher,FacebookPublisher,InstagramPublisher,TwitterPublisher · 函数:1 · ⚑STUB |
| `backend/app/services/publish_workers/__init__.py` | 10 | 多平台视频发布 Worker — SAU / biliup / 小红书 MCP / AiToEarn 分层。 |
| `backend/app/services/publish_workers/biliup_worker.py` | 111 | biliup CLI Worker — B站专用，可解析 BV 回执。 · 函数:3 |
| `backend/app/services/publish_workers/dual_line.py` | 118 | 双线发布 — 主路（SAU/专用 Worker）+ 备路（AiToEarn）同时部署，主败备上。 · 函数:5 · ⚑DEGRADED |
| `backend/app/services/publish_workers/media_fetch.py` | 97 | 将云视频 URL 拉到 Worker 本地路径（SAU / xhs-mcp 需要本地文件）。 · 函数:4 |
| `backend/app/services/publish_workers/sau_sidecar.py` | 174 | SAU HTTP Sidecar 客户端 — 远程 Worker 机执行 Playwright 上传。 · 函数:7 |
| `backend/app/services/publish_workers/sau_worker.py` | 402 | social-auto-upload CLI Worker — 抖音/快手/B站/小红书/视频号。 · 函数:12 |
| `backend/app/services/publish_workers/tier_router.py` | 141 | 发布分层路由 — 集 SAU / biliup / xhs-mcp / 原生 / AiToEarn。 · 函数:6 |
| `backend/app/services/publish_workers/verify.py` | 81 | 发布后验真 — 无 platform URL/ID 一律不算成功。 · 函数:3 |
| `backend/app/services/publish_workers/xhs_mcp_worker.py` | 114 | xiaohongshu-mcp HTTP Worker — 小红书视频真发。 · 函数:3 |
| `backend/app/services/push_notification_service.py` | 156 | 出海计 Push — FCM Legacy HTTP（配置 FCM_SERVER_KEY 后真推送）。 · 函数:6 |
| `backend/app/services/rag_pricing_guard.py` | 106 | 租户 RAG 销售话术 — 禁止脱离授权区间报价。 · 类:PricingGuardResult · 函数:2 |
| `backend/app/services/rank_checker.py` | 643 | 真实的搜索引擎排名查询服务 · 类:RankResult,CheckResult,BaiduChecker,GoogleChecker,BingChecker,RankChecker · 函数:4 · ⚑MOCK/DEGRADED |
| `backend/app/services/rank_scheduler.py` | 194 | 排名定时任务调度服务 · 类:RankScheduler · ⚑MOCK |
| `backend/app/services/referral_redeem_service.py` | 102 | 现金券线下核销 — 超管确认已兑付。 · 函数:3 |
| `backend/app/services/referral_reward_service.py` | 90 | P1-06：裂变奖励类型（Token / 现金券 / 免费月 / 套餐升级）。 · 函数:3 |
| `backend/app/services/referral_service.py` | 174 | 客户裂变推荐系统服务 · 类:ReferralService |
| `backend/app/services/refund_service.py` | 527 | 退款服务 — 通用退款入口，按支付通道分发退款请求。 · 类:RefundResult,RefundService · ⚑STUB |
| `backend/app/services/registry/__init__.py` | 55 | 能力注册表服务包（轮17）。 |
| `backend/app/services/registry/common.py` | 50 | 注册表公共工具：JSON 安全解析、状态校验、唯一性帮助。 · 函数:5 |
| `backend/app/services/registry/data_source_service.py` | 146 | 数据源合规评审服务（轮17-6）。 · 类:DataSourceNotFoundError,DataSourceConflictError,DataSourceService · 函数:1 |
| `backend/app/services/registry/matrix.py` | 123 | Skill 运行态 × 发布态 映射矩阵（轮17-5）。 · 类:RunStatus,PublishStatus · 函数:4 |
| `backend/app/services/registry/mcp_service.py` | 365 | MCP 注册表服务（轮17-3；轮19 扩展 connector-manifest 字段）。 · 类:McpNotFoundError,McpConflictError,McpService · 函数:4 |
| `backend/app/services/registry/permissions.py` | 113 | Permissions 权限矩阵（轮17-8）。 · 类:Permission · 函数:4 · ⚑DEGRADED |
| `backend/app/services/registry/plugin_service.py` | 173 | Plugin 注册表服务（轮17-4）。 · 类:PluginNotFoundError,PluginConflictError,PluginService · 函数:1 |
| `backend/app/services/registry/skill_base.py` | 233 | Skill 运行时基类（移植自 Trade AI Agent `app/core/skill_base.py`，MIT，保留出处）。 · 类:SkillStatus,BaseSkill,SkillRegistry · 函数:2 |
| `backend/app/services/registry/skill_pack_loader.py` | 367 | 技能包扫描解析器 —— 把磁盘上的 SKILL.md 技能包变成编排可消费的索引。 · 类:SkillPackEntry · 函数:8 · ⚑DEGRADED |
| `backend/app/services/registry/skill_service.py` | 575 | Skill 注册表服务（轮17-1/17-2）。 · 类:SkillNotFoundError,SkillConflictError,IllegalTransitionError,SkillService · 函数:7 · ⚑MOCK |
| `backend/app/services/registry/tenant_toggle.py` | 87 | 租户能力开关（轮17-7）。 · 类:TenantToggleService · 函数:1 |
| `backend/app/services/rfq_service.py` | 167 | RFQ 评分服务 — 确定性规则，不可由 LLM 覆盖。 · 类:RFQService · 函数:2 |
| `backend/app/services/rum_metrics_service.py` | 142 | 浏览器 RUM 采集与 Rank Guard 快照联动。 · 函数:4 |
| `backend/app/services/sales_channel_rehearsal_service.py` | 59 | 七步⑤ 本地/租户彩排 — 5a 入站、5b 企微推送、5c 评论入库。 · 函数:3 · ⚑MOCK |
| `backend/app/services/sales_push_service.py` | 238 | Lane P · 询盘/社媒互动 → 租户企微推送编排。 · 函数:5 |
| `backend/app/services/scenario_health_scheduler.py` | 166 | 场景模型健康定时巡检。 · 类:ScenarioHealthScheduler · 函数:1 |
| `backend/app/services/scenario_health_store.py` | 65 | 场景健康检查结果持久化（system_settings）。 · 函数:3 |
| `backend/app/services/scheduled_publish_retry_service.py` | 94 | ScheduledPublish 重试服务 —— ORCH-12 修复 · 函数:3 |
| `backend/app/services/scheduler_leader.py` | 202 | Distributed scheduler leader lock - Redis SET NX. · 类:_LockState · 函数:6 |
| `backend/app/services/schema_generator.py` | 480 | 类:SchemaGenerator · ⚑STUB |
| `backend/app/services/security_auditor.py` | 488 | 安全审计服务 - OWASP TOP 10漏洞扫描与检测（AI驱动） · 类:SecurityIssue,SecurityAuditor |
| `backend/app/services/security_event_service.py` | 190 | 成果保护：高价值安全事件写入 operation_logs（供鉴定与追溯）。 · 函数:5 |
| `backend/app/services/seo/inclusion_check_service.py` | 188 | SEO 收录复检 — 供 API 与 Celery 共用。 · 函数:5 |
| `backend/app/services/seo/inclusion_probe.py` | 144 | 搜索引擎收录探测 — Baidu site: 查询（失败可降级 HTTP 探活）。 · 函数:3 · ⚑DEGRADED |
| `backend/app/services/seo/inclusion_probe_cache.py` | 70 | 收录探测 probe_mode 侧车缓存（无 schema 迁移）。 · 函数:3 |
| `backend/app/services/seo/rank_scheduler_ops.py` | 122 | Hermes ops：Rank Scheduler 状态与 keywords 表同步。 · 函数:5 |
| `backend/app/services/seo/seo_matrix_db_health.py` | 82 | SEO-09：独立 SEO 矩阵库连通性探针（司令部健康）。 · 函数:1 |
| `backend/app/services/seo/seo_research_hints_service.py` | 119 | SEO-10：矩阵词/收录关键词 → DeerFlow research_hints。 · 函数:4 |
| `backend/app/services/seo/seo_utm_service.py` | 37 | SEO-11：矩阵发布 URL 追加 UTM 便于 PostHog/流量归因。 · 函数:1 |
| `backend/app/services/seo_analyzer.py` | 224 | 类:SeoAnalyzer |
| `backend/app/services/seo_report_service.py` | 71 | SEO 报告 HTML 导出（可浏览器打印为 PDF）。 · 函数:2 |
| `backend/app/services/seven_step_framework_service.py` | 154 | 商用七步主链 — 框架级自动验收（P0 彩排优先）。 · 函数:2 |
| `backend/app/services/site_ai_service.py` | 572 | 租户官网 AI 一键建站：根据产品名生成 site_content 结构。 · 函数:13 · ⚑DEGRADED |
| `backend/app/services/site_audit.py` | 1059 | 类:SiteAuditEngine · 函数:3 |
| `backend/app/services/site_builder/__init__.py` | 5 | 一键建站编排服务 — 端到端站点生成流水线。 |
| `backend/app/services/site_builder/orchestrator.py` | 518 | 一键建站核心编排器。 · 类:SiteBuildError,SiteBuilderOrchestrator · 函数:2 · ⚑DEGRADED |
| `backend/app/services/site_builder/prompts.py` | 141 | 一键建站各步骤 Prompt 模板。 · 函数:4 |
| `backend/app/services/site_content_array_i18n.py` | 392 | site_content CMS 数组字段多语种模板（stats / badges / milestones 等）。 · 函数:15 |
| `backend/app/services/site_content_bridge.py` | 67 | site_content ↔ 旧版 brand 字段桥接（公开站与编辑器兼容）。 · 函数:2 |
| `backend/app/services/site_content_i18n_ai_service.py` | 336 | Hermes · 按租户 site_content 正文 AI 翻译为多语种 i18n。 · 函数:7 |
| `backend/app/services/site_content_i18n_service.py` | 993 | site_content 多语种 i18n 生成 · 建站补全 · 存量租户回填。 · 函数:27 |
| `backend/app/services/site_content_locale_service.py` | 141 | site_content 按访客语言解析 i18n 覆盖层（Hero/About 等正文 + CMS 数组）。 · 函数:4 |
| `backend/app/services/site_l_pro_service.py` | 368 | SITE-DESIGN-01 · L-Pro 模板填槽与发布门禁。 · 函数:11 · ⚑MOCK/DEGRADED |
| `backend/app/services/site_product_assets.py` | 113 | 客户产品图 ↔ site_content 挂接（客户只提供产品名与白底图，不生成装饰图）。 · 函数:2 |
| `backend/app/services/social_interaction_service.py` | 510 | Lane I · 社媒评论/私信 → 意向识别 → 谈单草稿 → 可验证发送。 · 函数:17 · ⚑MOCK |
| `backend/app/services/social_nurture_service.py` | 936 | 海外社交媒体养号周期状态机 — 持久化 + 智能频控 + 平台规则联动。 · 函数:20 |
| `backend/app/services/ssl_certificate_service.py` | 257 | 租户独立域 SSL 申请状态机（mock / HTTP 委托）。 · 函数:9 · ⚑MOCK |
| `backend/app/services/stripe_pay_service.py` | 126 | Stripe 国际支付服务模块 - 支持 Checkout Session、Webhook 验签、多币种与 Token 充值联动。 · 类:StripePayService |
| `backend/app/services/stripe_service.py` | 352 | Stripe 支付集成骨架 — 轻量 httpx 直调 REST API，不强依赖 stripe SDK。 · 函数:13 · ⚑MOCK |
| `backend/app/services/super_admin_path_audit.py` | 85 | P0-08：前端 super-admin 引用与 FastAPI 挂载路径对齐审计。 · 函数:4 |
| `backend/app/services/talking_stick/__init__.py` | 25 | Talking-Stick 漏洞挖掘系统 |
| `backend/app/services/talking_stick/agents/__init__.py` | 11 | Talking-Stick Agent模块 |
| `backend/app/services/talking_stick/agents/audit_agent.py` | 210 | Talking-Stick 审计Agent · 类:AuditAgent |
| `backend/app/services/talking_stick/agents/base_agent.py` | 88 | Talking-Stick Agent 基类 · 类:BaseAgent · ⚑STUB |
| `backend/app/services/talking_stick/agents/recon_agent.py` | 229 | Talking-Stick 侦察Agent · 类:ReconAgent |
| `backend/app/services/talking_stick/agents/verify_agent.py` | 575 | Talking-Stick 验证Agent · 类:VerifyAgent · ⚑MOCK/STUB |
| `backend/app/services/talking_stick/config.py` | 122 | Talking-Stick 配置管理模块 · 类:ModelConfig,FileLockConfig,OutputConfig,TalkingStickConfig,ConfigManager |
| `backend/app/services/talking_stick/file_lock.py` | 153 | Talking-Stick 文件锁机制 · 类:LockInfo,FileLock |
| `backend/app/services/talking_stick/models/__init__.py` | 14 | Talking-Stick 数据模型模块 |
| `backend/app/services/talking_stick/models/fix.py` | 125 | Talking-Stick 修复方案数据模型 · 类:POC,FixSuggestion,VerificationResult,VerificationOutput |
| `backend/app/services/talking_stick/models/scan_result.py` | 125 | Talking-Stick 扫描结果数据模型 · 类:RiskFile,DependencyInfo,ScanSummary,ScanResult |
| `backend/app/services/talking_stick/models/vulnerability.py` | 84 | Talking-Stick 漏洞数据模型 · 类:Vulnerability,AuditResult |
| `backend/app/services/talking_stick/report_generator.py` | 258 | Talking-Stick 报告生成器 · 类:ReportGenerator |
| `backend/app/services/talking_stick/scheduler.py` | 220 | Talking-Stick 调度器 · 类:Scheduler |
| `backend/app/services/talking_stick/task_queue.py` | 136 | Talking-Stick 任务队列 · 类:TaskStatus,Task,TaskQueue |
| `backend/app/services/talking_stick/utils/__init__.py` | 10 | Talking-Stick 工具模块 |
| `backend/app/services/talking_stick/utils/dependency_parser.py` | 165 | Talking-Stick 依赖解析工具 · 类:DependencyFile,DependencyParser · ⚑STUB |
| `backend/app/services/talking_stick/utils/file_scanner.py` | 168 | Talking-Stick 文件扫描工具 · 类:FileInfo,FileScanner |
| `backend/app/services/talking_stick/utils/rule_engine.py` | 317 | Talking-Stick 规则引擎 · 类:DetectionRule,RuleEngine · ⚑MOCK |
| `backend/app/services/tasks/__init__.py` | 0 |  |
| `backend/app/services/tasks/deerflow_bridge.py` | 155 | DeerFlow → ai_tasks 影子双写桥（总纲 §4.6-1 收编过渡；轮24-A 首批调用方）。 · 类:DeerflowTaskBridge · 函数:4 · ⚑DEGRADED |
| `backend/app/services/tasks/hermes_task_bridge.py` | 354 | ai_tasks → Hermes 编排桥（打通中央断点；总纲 §4.6 / 轮24 后续）。 · 类:HermesNodeExecutionError · 函数:7 |
| `backend/app/services/tasks/paperclip_bridge.py` | 189 | Paperclip → ai_tasks 影子双写桥（总纲 §4.6-1 收编过渡第 2 迭代；轮24-B）。 · 类:PaperclipTaskBridge · 函数:4 · ⚑DEGRADED |
| `backend/app/services/tasks/task_control.py` | 583 | 统一任务控制面服务（总纲 §4.6-1/§4.6-2 / §8 082；轮23 任务端接线）。 · 类:TaskControlError,TaskNotFound,InvalidTaskTransition,QuotaGateDenied,TaskControlService · 函数:3 |
| `backend/app/services/technical_qna_service.py` | 151 | Technical Q&A — 基于批准知识库的带引用技术问答。 · 函数:5 |
| `backend/app/services/tenant_aitoearn_slot_service.py` | 315 | 租户 AiToEarn 槽位 — 一客户一组矩阵号，与池内其他租户隔离。 · 函数:12 |
| `backend/app/services/tenant_lifecycle_service.py` | 113 | 租户订阅生命周期：到期冻结、试用结束处理。 · 类:TenantLifecycleService |
| `backend/app/services/tenant_llms_txt_service.py` | 219 | 租户级 llms.txt / llms-full.txt — 从 site_content 生成 AI 可读索引。 · 函数:9 |
| `backend/app/services/tenant_onboarding_service.py` | 528 | 租户开户一站式编排：验证码、AI 场景、云存储路径、平台账号槽位。 · 函数:15 · ⚑STUB |
| `backend/app/services/tenant_product_context.py` | 63 | 租户主营产品上下文 — 注册 / Hermes / 旺财 / 蓝海 单一来源。 · 函数:3 |
| `backend/app/services/tenant_product_profile_service.py` | 415 | 租户产品画像 — 产品库优先 · 产业带 · 可选联网调研（开发信/建站共用）。 · 类:ProductProfileRequiredError · 函数:15 · ⚑MOCK |
| `backend/app/services/tenant_renewal_notify_service.py` | 214 | 租户到期续费提醒 — 飞书 + 邮件，幂等按到期日去重。 · 类:TenantRenewalNotifyService · 函数:7 |
| `backend/app/services/tenant_scenario_service.py` | 196 | 租户级 AI 场景模型覆盖（存于 tenant.settings.ai_scenario_overrides）。 · 函数:7 |
| `backend/app/services/tenant_service.py` | 364 | SaaS多租户服务层 · 类:TenantPlanService,TenantService |
| `backend/app/services/tenant_settings_service.py` | 47 | 租户 settings JSON 解析（P1-05 等）。 · 函数:3 |
| `backend/app/services/tenant_site_persistence.py` | 69 | 租户官网 site_content 持久化。 · 函数:2 |
| `backend/app/services/tenant_wangcai_service.py` | 84 | 旺财统一入口 — 公开站与开户向导必须同源。 · 函数:2 · ⚑DEGRADED |
| `backend/app/services/tenant_wecom_config_service.py` | 251 | 租户企微推送配置 — 客户填写自己的 Corp / Agent / 销售 UserID。 · 类:TenantWecomCredentials · 函数:8 · ⚑MOCK/DEGRADED |
| `backend/app/services/token_service.py` | 189 | 租户 Token 配额与账本 · 类:InsufficientTokenError,TokenService |
| `backend/app/services/trace/__init__.py` | 23 | 统一 Trace / 经验飞轮接线（总纲 §4.6-7 / §6.6 P3）。 |
| `backend/app/services/trace/publish_gate.py` | 233 | Canary 发布门禁（总纲 §1.3 第4条 / §6.6 P3 / E14）。 · 类:PublishGate · 函数:2 |
| `backend/app/services/trace/terminal_hook.py` | 237 | 终态钩子 — 任务终态接线至经验飞轮（总纲 §4.6-7 / §6.6 P3）。 · 函数:4 |
| `backend/app/services/trace/trace_service.py` | 320 | 统一 Trace 服务 — 链式追踪的写入/读取与记分卡聚合（总纲 §4.6-7 / §8 085_traces）。 · 类:TaskTraceService · 函数:2 |
| `backend/app/services/trade_intel_commercial_service.py` | 53 | 出海参谋 M2 — 商业海关 API 适配层（可配置外部数据源）。 · 函数:1 · ⚑DEGRADED |
| `backend/app/services/trade_intel_comtrade_client.py` | 120 | UN Comtrade 公开 API — 中国出口按 HS 章别拉取目的国贸易额。 · 函数:5 |
| `backend/app/services/trade_intel_customs_service.py` | 65 | AI-M1：海关公开统计试点数据（带来源标注，非实时报关 API）。 · 函数:3 |
| `backend/app/services/trade_intel_data.py` | 365 | 出海参谋 JSON 数据加载（M0 矩阵 / M1 海关 / 市场数据源）。 · 函数:15 |
| `backend/app/services/trade_intel_refresh_service.py` | 295 | 出海参谋 M1 — 定时从 UN Comtrade 刷新海关公开统计 JSON。 · 函数:12 · ⚑DEGRADED |
| `backend/app/services/trade_intel_scheduler.py` | 188 | 出海参谋海关数据 — 每周定时从 Comtrade 刷新。 · 类:TradeIntelScheduler |
| `backend/app/services/trade_intel_seed.py` | 56 | 将 M0 内置矩阵写入 trade_country_category（幂等）。 · 函数:1 |
| `backend/app/services/trade_intel_service.py` | 443 | 出海参谋 M0 — 品类×国家规则矩阵（可解释、可溯源）。 · 类:FeasibilityResult · 函数:11 · ⚑DEGRADED |
| `backend/app/services/trade_platform_meta.py` | 115 | 外贸平台分类元数据 — 注册 / 开户指引展示用。 · 函数:2 |
| `backend/app/services/traffic_analytics_service.py` | 686 | 流量看板：埋点落库、日 UV/PV、点击排行、询盘/电话归因。 · 类:TrafficAnalyticsService · 函数:4 |
| `backend/app/services/tts_synthesis_service.py` | 112 | TTS 配音合成 — 开发显式 mock；生产无上游时 503。 · 函数:4 · ⚑MOCK |
| `backend/app/services/ubrain/__init__.py` | 3 |  |
| `backend/app/services/ubrain/accio_gap_constants.py` | 42 | Accio gap 技能 ID（避免 catalog ↔ handlers 循环导入）。 |
| `backend/app/services/ubrain/accio_gap_handlers.py` | 314 | Accio 对标 gap 技能 — 预览载荷 + 带 DB 上下文真执行。 · 函数:10 |
| `backend/app/services/ubrain/accio_sales_service.py` | 781 | AccioWork 卖货核心：找客、开发信、谈单草稿（画像级 + 人审发送）。 · 函数:15 |
| `backend/app/services/ubrain/accio_skill_catalog.py` | 116 | AccioWork 39+ 技能包对标目录（本系统实现状态）。 · 函数:6 |
| `backend/app/services/ubrain/action_audit_service.py` | 241 | Accio A5：UBrain / 对外动作审计（不含真实 SMTP 外发本身）。 · 函数:7 |
| `backend/app/services/ubrain/ai_email_generator.py` | 385 | AI 开发信生成 — FIX-48 · 类:EmailTemplate,AIEmailGenerator · 函数:1 · ⚑MOCK/DEGRADED |
| `backend/app/services/ubrain/ai_find_customer_sidecar.py` | 437 | AI Hunter 找客旁路 — 对接 xiongQvQ/AI_Find_Customer 式 Sidecar HTTP API。 · 函数:12 · ⚑MOCK/DEGRADED |
| `backend/app/services/ubrain/brand_guard_bff.py` | 20 | UB-06：飞轮 BFF 层统一脱敏序列化。 · 函数:1 |
| `backend/app/services/ubrain/channel_status.py` | 113 | FIX-5: Prospect channel availability service. · 类:ChannelInfo · 函数:9 · ⚑MOCK |
| `backend/app/services/ubrain/chat_context_service.py` | 134 | UBrain 对话上下文：经营快照 + 记忆，供 general LLM 与智能路由使用。 · 函数:4 |
| `backend/app/services/ubrain/code_quality_service.py` | 410 | 代码质量服务 — FIX-70~73 · 类:FrontendConfigGenerator,TypeComplianceReport,TypeComplianceTracker,CodeReviewResult,AutomatedCodeReviewEngine,SonarQubeIntegration |
| `backend/app/services/ubrain/commercial_os_bridge.py` | 751 | DeerFlow + AccioWork 商业 OS 飞轮 — 记忆 / 编排 / 反馈（可接 Mem0、n8n）。 · 函数:17 |
| `backend/app/services/ubrain/content_draft_service.py` | 97 | UBrain-X：将 lead_content_pack 选题写入 ContentMaster 草稿（人审后发布）。 · 函数:2 |
| `backend/app/services/ubrain/dedup_engine.py` | 305 | 线索去重引擎 —— 统一模型的核心组件 · 类:DedupEngine · 函数:5 |
| `backend/app/services/ubrain/deerflow_brief_templates_service.py` | 140 | DeerFlow 租户 Research Brief 预制模板（Hermes×AnySearch 研究沉淀）。 · 函数:5 |
| `backend/app/services/ubrain/deerflow_job_service.py` | 536 | DeerFlow 任务队列：入队、执行、轮询（Phase 1 进程内执行，可接 cron）。 · 函数:17 · ⚑DEGRADED |
| `backend/app/services/ubrain/deerflow_research_service.py` | 340 | DeerFlow 风格深度研究 — Planner / Researcher / Reviewer / Writer → Research Brief。 · 函数:7 |
| `backend/app/services/ubrain/deerflow_scheduled_service.py` | 421 | DeerFlow 定时更新 — 套餐门控入队 + 分 lane 队列消费。 · 函数:11 · ⚑DEGRADED |
| `backend/app/services/ubrain/deerflow_scheduler.py` | 178 | DeerFlow 定时调度 — 每日市场研究 + 与 Hermes 运维循环联动。 · 类:DeerflowScheduler |
| `backend/app/services/ubrain/deerflow_sidecar.py` | 271 | 官方 DeerFlow 2.0 旁路：可选 HTTP 研究服务，失败则回退本机 Lite。 · 函数:10 · ⚑DEGRADED |
| `backend/app/services/ubrain/deerflow_tenant_quota.py` | 163 | DeerFlow 租户套餐/配额 — 定时市场研究仅对符合条件的租户。 · 函数:7 |
| `backend/app/services/ubrain/domain_email_extractor_sidecar.py` | 205 | 官网域名邮箱 enrichment Sidecar — AI Hunter 后处理，须 source_url。 · 函数:7 · ⚑MOCK/DEGRADED |
| `backend/app/services/ubrain/drip_sequence_service.py` | 411 | 邮件序列 Drip Campaign — FIX-44 · 类:SequenceTrigger,SequenceStep,DripSequence,DripSequenceService |
| `backend/app/services/ubrain/email_outreach_service.py` | 476 | 邮件外联服务 —— 状态机 + 幂等 + 追踪 · 类:EmailOutreachService · 函数:14 |
| `backend/app/services/ubrain/email_quality_service.py` | 1113 | 开发信质量评估 + A/B 测试 + 获客流程标准化 — FIX-58 & FIX-59 · 类:EmailQualityDimension,QualityDimensionScore,EmailQualityReport,EmailQualityEvaluator,ABTestVariant,ABTestConfig,ABTestResult,ABTestEngine · ⚑STUB |
| `backend/app/services/ubrain/email_queue_service.py` | 999 | 邮件发送队列 + 数据飞轮 + 安全加密 + AI 安全 — FIX-62 ~ FIX-65 · 类:EmailQueueStatus,EmailQueueItem,EmailSendQueue,DataFlywheelStage,FlywheelInsight,DataFlywheelEngine,EncryptionAlgorithm,EncryptedField · ⚑MOCK/DEGRADED |
| `backend/app/services/ubrain/email_send_service.py` | 192 | 零成本邮件发送服务 · 类:EmailSendResult,EmailMessage,EmailSendService · 函数:4 · ⚑DEGRADED |
| `backend/app/services/ubrain/email_tracking_service.py` | 234 | 邮件追踪服务 — FIX-47 · 类:EmailTrackingService · 函数:1 |
| `backend/app/services/ubrain/email_verification_service.py` | 220 | 零成本邮箱验证服务 — 无需付费 API · 类:EmailVerificationResult,EmailVerificationService · 函数:4 |
| `backend/app/services/ubrain/embedding_service.py` | 258 | Embedding Service - 文本向量生成服务 · 类:EmbeddingService · 函数:1 · ⚑DEGRADED |
| `backend/app/services/ubrain/export_feasibility_reply.py` | 311 | 出口可行性回复：避免重复提问时机械复读同一模板。 · 函数:8 |
| `backend/app/services/ubrain/flywheel_integrations.py` | 178 | P2 外挂槽位：Mem0 双写、PostHog 埋点、n8n 状态（未配置则 no-op）。 · 函数:8 · ⚑STUB |
| `backend/app/services/ubrain/follow_up_engine.py` | 769 | 智能 Follow-up 策略引擎 — FIX-57 · 类:FollowUpStage,FollowUpChannel,FollowUpTrigger,FollowUpOutcome,FollowUpAction,FollowUpSequence,IntelligentFollowUpEngine |
| `backend/app/services/ubrain/general_smart_reply.py` | 569 | 无 LLM 时的卖货助手智能回复：并列多种策略，结合经营快照给出可执行建议。 · 函数:16 · ⚑DEGRADED |
| `backend/app/services/ubrain/geo_content_matrix_service.py` | 731 | GEO/SEO 内容矩阵 — 借鉴 agency-orchestrator seo-content-matrix + content-pipeline DAG。 · 函数:21 · ⚑DEGRADED |
| `backend/app/services/ubrain/gmssl_crypto_service.py` | 482 | 国密算法服务 — FIX-13: GmSSL 认证库替换 · 类:SM3,SM4,GmSSLCryptoResult,GmSSLCryptoService |
| `backend/app/services/ubrain/google_prospect_service.py` | 524 | Google 搜索客户开发服务 — 通过 Google 搜索引擎地毯式开发海外客户。 · 函数:11 · ⚑MOCK/DEGRADED |
| `backend/app/services/ubrain/hunter_service.py` | 1070 | Hunter.io / Apollo.io 付费 API 集成 — FIX-53 · 类:EmailConfidence,VerificationStatus,ApolloPersonSeniority,HunterEmail,HunterDomainResult,ApolloPerson,EmailCache,HunterClient · ⚑DEGRADED |
| `backend/app/services/ubrain/imap_inquiry_sidecar.py` | 149 | 只读 IMAP 询盘收取 Sidecar — mymailclaw 对标，禁止 SMTP 自动发信。 · 函数:5 · ⚑MOCK/DEGRADED |
| `backend/app/services/ubrain/inquiry_context_service.py` | 325 | Accio A2/A3/A4：租户真实询盘上下文 → 草稿、评分与经营快照。 · 函数:12 |
| `backend/app/services/ubrain/inquiry_discovery_service.py` | 65 | Discovery 教练 — 新询盘结构化追问（MOQ / 目的港 / 规格）。 · 函数:3 |
| `backend/app/services/ubrain/inquiry_intel_service.py` | 72 | 询盘智能 enrichment — 意向分 + Discovery 追问（列表/详情共用）。 · 函数:3 |
| `backend/app/services/ubrain/inquiry_scoring_service.py` | 78 | 询盘意向评分 — 副驾 inquiry_score 与公开询盘创建共用。 · 函数:1 |
| `backend/app/services/ubrain/knowledge_graph_service.py` | 734 | Knowledge Graph Service - Neo4j 知识图谱服务 · 类:KnowledgeGraphService · 函数:1 · ⚑DEGRADED |
| `backend/app/services/ubrain/lead_csv_service.py` | 268 | 获客CSV导入导出 — FIX-38 · 类:LeadCSVService,LeadCSVValidator |
| `backend/app/services/ubrain/lead_processing_pipeline.py` | 429 | 线索处理 Pipeline（责任链模式） — FIX-35 · 类:PipelineStatus,LeadContext,LeadHandler,NormalizeHandler,DedupHandler,VerifyHandler,ScoreHandler,EnrichHandler · 函数:2 |
| `backend/app/services/ubrain/lead_scoring_engine.py` | 294 | 线索评分引擎 v2 — FIX-36 · 类:LeadGrade,LeadScoringEngine · 函数:1 |
| `backend/app/services/ubrain/lead_search_engine.py` | 268 | 线索搜索引擎 — FIX-61 · 类:SearchHit,InvertedIndex,LeadSearchEngine · ⚑STUB/DEGRADED |
| `backend/app/services/ubrain/lead_search_task.py` | 220 | 获客搜索异步任务 —— 后台执行 + 进度推送 · 类:TaskStatus,LeadSearchTask · 函数:5 · ⚑STUB |
| `backend/app/services/ubrain/linkedin_decision_maker_sidecar.py` | 149 | LinkedIn 决策人 enrichment Sidecar — P3 restricted，须 evidence_url + 人工核实。 · 函数:5 · ⚑MOCK/DEGRADED |
| `backend/app/services/ubrain/linkedin_prospect_service.py` | 298 | LinkedIn 外贸客户开发服务 — 从 LinkedIn 挖掘 B2B 决策人。 · 函数:5 |
| `backend/app/services/ubrain/linkedin_sales_navigator_service.py` | 1017 | LinkedIn Sales Navigator API 正式接入 — FIX-55 · 类:LinkedInSeniority,LinkedInCompanySize,LinkedInIndustry,LinkedInPerson,LinkedInCompany,LinkedInSearchResult,LinkedInSalesNavigatorClient,LinkedInDecisionMakerService · ⚑STUB |
| `backend/app/services/ubrain/llm_assist_reply.py` | 191 | 预制模板 + 大模型 API 辅助润色 — 财旺通用对话层。 · 函数:6 · ⚑DEGRADED |
| `backend/app/services/ubrain/matrix_publish_bootstrap.py` | 163 | 矩阵发布零配置引导 — 自动补平台、占位账号、内容母版草稿。 · 函数:4 · ⚑MOCK/STUB/DEGRADED |
| `backend/app/services/ubrain/matrix_publish_service.py` | 298 | 矩阵发布 — 计划预览、PublishTask 创建、视频真发统一入口。 · 函数:8 · ⚑STUB/DEGRADED |
| `backend/app/services/ubrain/mem0_batch_sync_service.py` | 65 | INT-03：Mem0 洞察批量双写（超管触发 · 未配置则 no-op）。 · 函数:2 |
| `backend/app/services/ubrain/orchestrator.py` | 1605 | UBrain v1 — 意图识别 + 工具调用（走现有 API 数据或 M0 规则）。 · 类:UBrainOrchestrator · ⚑DEGRADED |
| `backend/app/services/ubrain/outreach_deliverability_service.py` | 412 | 开发信可达性 — 质量评分、垃圾箱风险、发送窗口（研究员×PM 契约）。 · 函数:10 · ⚑DEGRADED |
| `backend/app/services/ubrain/p2_enhancement_service.py` | 727 | P2 增强服务 — 完成剩余 19 项 · 类:ChannelAggregatorService,PredictiveAcquisitionEngine,MCPAcquisitionToolkit,DatabasePartitioningService,MultiRegionDeploymentService,ServerlessMigrationService,CostOptimizationService,AICodeReviewService |
| `backend/app/services/ubrain/paid_ads_creative_service.py` | 112 | 付费广告创意 — 结构化变体 + 可选 AI 增强。 · 函数:2 |
| `backend/app/services/ubrain/performance_optimization_service.py` | 499 | 性能优化服务 — FIX-66~69 · 类:MessagePriority,AsyncMessage,AsyncMessageBus,CDNCacheConfig,CloudflareCDNService,NginxConfigGenerator,TraceSpan,ObservabilityService |
| `backend/app/services/ubrain/pro_research_terms_service.py` | 56 | COMP-03：Pro 定时市场研究服务条款（租户可见 · 已脱敏）。 · 函数:1 |
| `backend/app/services/ubrain/product_commercial_service.py` | 545 | 产品商业化服务 — FIX-74~81 · 类:AgentTier,AgentSystemService,TemplateMarketplaceService,IndustrySolutionService,ManagedServiceService,WhiteLabelService,CustomerSuccessService,GrowthEngineService |
| `backend/app/services/ubrain/prospect_export_service.py` | 100 | 采购商候选导出 — CSV（人工核实后跟进）。 · 函数:2 |
| `backend/app/services/ubrain/prospect_research_engine.py` | 827 | RAG 客户洞察 + 定制化开发信 — FIX-56 · 类:CompanyGrowthSignal,InsightCategory,EmailTone,CompanyInsight,ProspectResearch,PersonalizedEmail,WebResearchTool,ProspectResearchEngine |
| `backend/app/services/ubrain/quality_gate_service.py` | 79 | DF-13：研究质量门 — 低分自动重跑（限频）。 · 函数:2 |
| `backend/app/services/ubrain/quora_prospect_service.py` | 266 | Quora 外贸客户开发服务 — 从 Quora 问答平台挖掘采购需求。 · 函数:4 |
| `backend/app/services/ubrain/reddit_prospect_service.py` | 254 | Reddit 外贸客户开发服务 — 从 Reddit 社区挖掘潜在采购商线索。 · 函数:5 |
| `backend/app/services/ubrain/reply_templates.py` | 172 | 财旺/UBrain 预制回复模板 — 事实与指令骨架；口语润色由 LLM assist 完成。 · 函数:9 |
| `backend/app/services/ubrain/search_strategy_builder.py` | 632 | AI 辅助搜索策略构建器 — FIX-60 · 类:SearchPlatform,SearchIntent,SearchQuery,SearchStrategy,SearchStrategyBuilder |
| `backend/app/services/ubrain/skill_audit_service.py` | 256 | 技能安全审核服务 — 参考 CocoLoop BSS安全扫描体系。 · 函数:6 |
| `backend/app/services/ubrain/super_agent_bridge.py` | 632 | AccioWork 原生桥 — 无 ai_engine 包时使用 UBrain 卖货服务。 · 类:NativeAccioWorkEngine · 函数:1 · ⚑DEGRADED |
| `backend/app/services/ubrain/team_rbac_service.py` | 82 | 租户团队 RBAC 快照 — 角色权限矩阵（ROLE_PERMISSIONS + 超管 DB 角色）。 · 函数:2 |
| `backend/app/services/ubrain/tenant_memory_service.py` | 196 | 租户副驾记忆 — Accio「越用越智能」底座。 · 函数:5 |
| `backend/app/services/ubrain/tiktok_prospect_service.py` | 250 | TikTok 外贸客户开发服务 — 从 TikTok 短视频挖掘采购需求。 · 函数:4 |
| `backend/app/services/ubrain/ubrain_decision_tracker.py` | 327 | UBrain AI Agent 决策追踪服务 · 类:UBrainDecisionTracker |
| `backend/app/services/ubrain/vector_search_service.py` | 659 | Vector Search Service - Qdrant 向量检索服务 · 类:VectorSearchService · 函数:1 · ⚑DEGRADED |
| `backend/app/services/ubrain/website_email_scraper.py` | 247 | 零成本网站邮箱抓取服务 — 从目标公司网站提取邮箱 · 类:ScrapedEmail,WebsiteEmailResult,WebsiteEmailScraper · 函数:6 |
| `backend/app/services/ubrain/whatsapp_business_service.py` | 1095 | WhatsApp Business Cloud API 正式接入 — FIX-54 · 类:WhatsAppMessageType,WhatsAppMessageStatus,WhatsAppTemplateCategory,WhatsAppTemplateStatus,WhatsAppLanguage,WhatsAppTemplate,WhatsAppMessage,WhatsAppIncomingMessage |
| `backend/app/services/ubrain/whatsapp_prospect_service.py` | 706 | WhatsApp 外贸客户开发服务 — 参考 whatsfinds.com 获客模式。 · 函数:16 · ⚑MOCK/DEGRADED |
| `backend/app/services/ubrain/zero_trust_service.py` | 320 | 零信任安全架构服务 — FIX-14 · 类:TrustLevel,RiskLevel,DeviceContext,AccessContext,TrustDecision,ZeroTrustEngine,ZeroTrustMiddleware · ⚑STUB |
| `backend/app/services/unified_admin_login.py` | 92 | 主站 users 与 SEO 矩阵 admin_users 的统一登录解析（不丢数据、可签发同一 JWT）。 · 函数:1 |
| `backend/app/services/unified_geo_score_service.py` | 307 | 统一 GEO 评分口径 — unified-geo-v1（合并 AEO / Optimizer / Engine / AI Search）。 · 函数:8 · ⚑DEGRADED |
| `backend/app/services/user_service.py` | 188 | 用户服务层 · 类:UserService |
| `backend/app/services/user_wallet_service.py` | 489 | 用户钱包服务（WALLET-SVC） · 类:WalletTxResult,WalletSummary,WalletUnavailableError · 函数:13 · ⚑DEGRADED |
| `backend/app/services/vault/__init__.py` | 23 | 凭证库包（总纲 §8 迁移 087；轮20）。 |
| `backend/app/services/vault/credential_service.py` | 373 | 凭证库服务（总纲 §3.1/§8 迁移 087；轮20）。 · 类:VaultError,CredentialNotFoundError,CredentialRevokedError,GrantDeniedError,CredentialVaultService · 函数:6 |
| `backend/app/services/vault/crypto.py` | 134 | 凭证库加密层（总纲 §3.1/§8 迁移 087；轮20）。 · 类:VaultCryptoError,AadMismatchError · 函数:6 · ⚑DEGRADED |
| `backend/app/services/video_bind_hub_service.py` | 195 | 视频发布绑定中枢 — 登录优丁后一次入口绑号（含 AiToEarn 同步）。 · 函数:4 |
| `backend/app/services/video_publish_orchestrator.py` | 478 | Hermes 编排的视频真发 — 多 Worker 链式尝试 + 强制验真 + 养号频控。 · 函数:11 |
| `backend/app/services/video_publish_router.py` | 509 | 统一视频发布口 — Hermes 双线编排：主路 SAU + 备路 AiToEarn + 强制验真。 · 函数:14 |
| `backend/app/services/video_seo_geo_aao_optimizer.py` | 202 | 视频 SEO / GEO / AAO 综合排名优化引擎。 · 类:SeoVideoMetadata,GeoEngineMetadata,AaoAlgorithmMetadata,FullRankingOptimizationPack,VideoSeoGeoAaoOptimizer |
| `backend/app/services/visitor_locale_service.py` | 939 | 访客 IP / 请求头 → 国家与语言；外贸站与旺财 UI 随地域自动切换。 · 函数:15 · ⚑MOCK |
| `backend/app/services/wangcai/__init__.py` | 7 | 旺财租户前台智能助手链路增强（总纲 §7A / 实施指南 N1-N8）。 · ⚑DEGRADED |
| `backend/app/services/wangcai/intent.py` | 245 | 旺财 N1 意图识别层（实施指南 §1，总纲 §7A 阶段 1）。 · 类:IntentResult,IntentDef · 函数:4 · ⚑DEGRADED |
| `backend/app/services/wangcai/knowledge.py` | 205 | 旺财 N2 知识检索层（实施指南 §2，阶段一：SQL 关键词起步）。 · 类:KnowledgeHit,RetrievalResult,KnowledgeRetriever · 函数:4 |
| `backend/app/services/wangcai/llm.py` | 213 | 旺财 N4 LLM 调用层（实施指南 §4，总纲 §7A 阶段 2）。 · 类:DraftAnswer,WangcaiLLM · 函数:4 · ⚑MOCK/DEGRADED |
| `backend/app/services/wangcai/memory.py` | 177 | 旺财 N3 上下文记忆层（实施指南 §3）。 · 类:Turn,SessionRecord,ContextWindow,SessionStore,InMemorySessionStore · 函数:2 |
| `backend/app/services/wangcai/persistence.py` | 233 | 旺财 N3/N7 持久化接线（迁移 094：wangcai_sessions + wangcai_qa_log，轮14）。 · 类:DbSessionStore · 函数:1 · ⚑DEGRADED |
| `backend/app/services/wangcai/router.py` | 420 | WangcaiRouter 总编排（实施指南 §0.1 链路；阶段 1 收口，不依赖 LLM 可上线）。 · 类:WangcaiRouter · 函数:7 · ⚑MOCK/DEGRADED |
| `backend/app/services/wangcai_reply_locale.py` | 68 | 旺财贸易问答回复 — 按访客语言加标题/脚注包装（数据层可仍为英文）。 · 函数:1 |
| `backend/app/services/wangcai_trade_service.py` | 550 | 公开站旺财 — 海关/出口问答（不暴露 Hermes/Agent 品牌）。 · 函数:13 |
| `backend/app/services/wechat_pay_v3.py` | 299 | 微信支付 API v3 — Native 下单与回调解密（配置齐全时走真实接口）。 · 类:WeChatPayV3Config,WeChatPayV3Client · 函数:3 · ⚑MOCK |
| `backend/app/services/wechat_platform_cert_service.py` | 192 | 微信支付平台证书 — 按 serial 缓存，验签失败时刷新一次。 · 类:WeChatPlatformCertStore · 函数:4 |
| `backend/app/services/wecom_push_service.py` | 173 | Lane P · 企业微信推送（租户自有凭证 + 群机器人）。 · 函数:4 |
| `backend/app/services/workflow_canvas_service.py` | 50 | 类:WorkflowCanvasService |
| `backend/app/tasks/__init__.py` | 0 |  |
| `backend/app/tasks/billing_tasks.py` | 29 | 轮22：计量周期汇总任务（总纲 §4.6-8：Celery beat 汇总进现有计费）。 · 函数:1 |
| `backend/app/tasks/celery_app.py` | 90 |  |
| `backend/app/tasks/cross_border_tasks.py` | 48 | 跨境语言桥 Celery 任务。 · 函数:2 |
| `backend/app/tasks/deerflow_tasks.py` | 203 | DeerFlow 执行引擎 Celery 任务。 · 函数:3 |
| `backend/app/tasks/geo_tasks.py` | 109 | GEO Celery 任务 — 技术雷达 / Rank Guard / 竞品监控。 · 函数:5 |
| `backend/app/tasks/ops_scheduler_tasks.py` | 433 | 函数:26 |
| `backend/app/tasks/orchestration_tasks.py` | 35 | 编排任务消费（ai_tasks → Hermes 桥的 Celery 入口）。 · 函数:1 |
| `backend/app/tasks/publish_tasks.py` | 119 | Publish task definitions and enqueue functions. · 函数:6 |
| `backend/app/tasks/scheduled_publish_worker.py` | 122 | 定时发布调度器 — 借鉴 AiToEarn enqueue-publishing-task scheduler。 · 函数:3 |
| `backend/app/tasks/seo_tasks.py` | 162 | 函数:5 |
| `backend/app/tasks/trade_intel_tasks.py` | 32 | Celery — 出海参谋海关数据定时刷新。 · 函数:1 |
| `backend/app/tasks/ubrain_tasks.py` | 95 | UBrain / DeerFlow Celery 任务。 · 函数:3 |
| `backend/app/workers/__init__.py` | 6 |  |
| `backend/app/workers/publish_worker.py` | 285 | ARQ Worker for publishing tasks. · 函数:9 |