# 后端测试 backend/tests

> 根目录：`C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix\backend\tests` · **58 个文件** · 后端测试

| 文件 | 行 | 摘要 · 符号 · 标记 |
|---|---:|---|
| `backend/tests/__init__.py` | 0 |  |
| `backend/tests/annex_ticket_cross_lang.py` | 131 | 跨语言票据协议兼容验证：UJ（Python HS256）↔ GoodJob（Node crypto）。 · 函数:2 |
| `backend/tests/annex_ticket_verify.py` | 243 | 附属统一登录票据协议验证（垫片模式）：UJ 签发 → 附属回调校验全链。 · 函数:5 |
| `backend/tests/api_helpers.py` | 58 | 与 /api/v1 统一 APIResponse 及 axios 解包约定对齐的测试辅助。 · 函数:7 |
| `backend/tests/browser_runtime_extra_write_verify.py` | 363 | 轮 25-F 写动作扩展（drag/upload/keyboard）验证（不触碰真实 Playwright）。 · 类:_FakeSettings · 函数:18 · ⚑MOCK/STUB |
| `backend/tests/browser_runtime_policy_real_verify.py` | 396 | 轮 25-E PolicyEngine 真接入 验证（不触碰真实 Playwright / DB）。 · 类:_FakeSettings,_FakePolicyDecision,_FakePolicyEngine · 函数:13 · ⚑MOCK/STUB/DEGRADED |
| `backend/tests/browser_runtime_real_verify.py` | 329 | 轮25-C Browser Runtime 真实 Playwright 接入 内存 + 真浏览器双路径验证。 · 类:_FakeSettings · 函数:6 · ⚑MOCK/DEGRADED |
| `backend/tests/browser_runtime_skeleton_verify.py` | 365 | 轮25-B Browser Runtime 骨架 内存验证（不触碰真实 Playwright）。 · 类:_FakeSettings · 函数:6 · ⚑MOCK/DEGRADED/DEPRECATED |
| `backend/tests/browser_runtime_write_verify.py` | 455 | 轮25-D Browser Runtime 写动作扩展 fill/click/submit 验证。 · 类:_FakeSettings · 函数:6 · ⚑MOCK/DEGRADED |
| `backend/tests/conftest.py` | 329 | 测试体系基础 — FIX-52 · 类:LeadFactory,EmailOutreachFactory,TestHealthEndpoint,TestLeadScoring,TestDripSequence,TestEventBus,TestPipeline · 函数:7 |
| `backend/tests/goodjob_bridge_verify.py` | 292 | 批次 B 隔离冒烟测试（垫片模式）：UJ 侧 GoodJob 桥全链验证。 · 类:FakeTransport · 函数:5 · ⚑MOCK |
| `backend/tests/helpers/qa_bff_bootstrap.py` | 147 | QA 三壳 BFF 冒烟 — 共享 TestClient 自举（in-memory DB） · 函数:6 |
| `backend/tests/idor_tenant_isolation_verify.py` | 192 | IDOR / 多租户隔离 运行时哨兵（ADR-002 方案 1，T02 tracer + T09 门禁雏形）。 · 函数:4 |
| `backend/tests/integration/test_core_chain.py` | 102 | 核心链路集成测试。 · 函数:10 · ⚑MOCK |
| `backend/tests/meter_reconcile_verify.py` | 302 | 轮22 MeterEvent 埋点 + 财务对账 内存 SQLite 全流程验证（不触碰真实 DB）。 · 类:_Base,_FakeSettings,_TenantType,TenantShim · 函数:6 · 表:tenants · ⚑MOCK |
| `backend/tests/model_gateway_router_verify.py` | 135 | Model Gateway 四维评分路由验证（垫片模式，仅标准库）。 · 函数:3 · ⚑DEGRADED |
| `backend/tests/pre_launch_canary_smoke.py` | 311 | 启用前冒烟 5/25/50/100% 灰度（上线前检查单 §F，路线图最后 1 站）。 · 函数:6 |
| `backend/tests/registry_verify.py` | 480 | 轮17 注册表服务 内存 SQLite 全流程验证脚本（不触碰真实 DB）。 · 类:_Base,_TenantShim · 函数:4 · 表:tenants |
| `backend/tests/rls_pilot_verify.py` | 312 | 轮 25-A RLS 试点 验证（不依赖真 PG）。 · 类:_FakeSettings · 函数:14 · ⚑MOCK |
| `backend/tests/rls_real_pg_verify.py` | 251 | ⚑MOCK |
| `backend/tests/role_grants_verify.py` | 222 | 生产角色映射 + ALTER DEFAULT PRIVILEGES 真实 PostgreSQL 验证。 · 函数:3 |
| `backend/tests/stress_generation_verify.py` | 156 | 压测脚本：租户文章生成 + 视频生成 + 智能体编排（真实 LLM 网关）。 · 函数:8 |
| `backend/tests/system_upgrade_verify.py` | 166 | 系统升级专项验证（建议 1、2、3 综合断言） · 类:TestSystemUpgrades · 函数:1 · ⚑MOCK/DEGRADED |
| `backend/tests/task_caller_wire_verify.py` | 389 | 轮24-A DeerFlow→ai_tasks 影子双写 + 双记账防护 内存 SQLite 验证（不触碰真实 DB）。 · 类:_Base,_FakeSettings,_TenantType,TenantShim,UserShim,_FakeJob · 函数:6 · 表:tenants,users · ⚑MOCK |
| `backend/tests/task_chain_verify.py` | 596 | 轮23 任务端接线 内存 SQLite 全流程验证（不触碰真实 DB）。 · 类:_Base,_FakeSettings,_TenantType,_StubEngine,TenantShim · 函数:7 · 表:tenants · ⚑MOCK |
| `backend/tests/task_paperclip_wire_verify.py` | 410 | 轮24-B Paperclip→ai_tasks 影子双写 + deerflow 去重裁决 内存 SQLite 验证。 · 类:_Base,_FakeSettings,_TenantType,TenantShim,UserShim,_FakeTask · 函数:7 · 表:tenants,users · ⚑MOCK/DEGRADED |
| `backend/tests/test_aeos_full_loop_dag.py` | 240 | AEOS v1.0 Full Closed-Loop Integration Test. · 函数:4 |
| `backend/tests/test_api/conftest.py` | 173 | pytest configuration for test_api · 类:_WrappedResponse,_AutoUnwrapClient · 函数:4 |
| `backend/tests/test_circuit_breaker.py` | 155 | 类:TestCircuitBreaker · ⚑MOCK/DEGRADED |
| `backend/tests/test_hermes_dag_p0.py` | 150 | Unit test for Phase P0: Hermes TaskGraph DAG Dispatcher & JsonPath Data Bus. · 类:FakeTestExecutor · 函数:2 · ⚑MOCK/DEGRADED |
| `backend/tests/test_layer_marker.py` | 39 | 函数:4 |
| `backend/tests/test_structured_logging.py` | 79 | 类:TestStructuredLogging |
| `backend/tests/trace_evolution_verify.py` | 385 | 轮21 Trace/Experience/Evolution 接线内存 SQLite 验证脚本（不触碰真实 DB）。 · 类:_Base,_FakeSettings,TenantShim,AiTaskShim · 函数:6 · 表:tenants,ai_tasks · ⚑MOCK |
| `backend/tests/unit/test_advance_plan_approval_input.py` | 138 | advance_plan 闸门顺序回归测试（不连真库）。 · 函数:7 · ⚑MOCK |
| `backend/tests/unit/test_ai_site_multimodal.py` | 50 | AI 独立站与多模态营销单元测试。 · 函数:3 |
| `backend/tests/unit/test_auth_routes.py` | 308 | 认证路由单元测试 — login / refresh / logout / change-password / email-code · 类:TestLogin,TestRefreshToken,TestLogout,TestChangePassword,TestSendEmailCode,TestLoginByEmail · 函数:2 · ⚑MOCK |
| `backend/tests/unit/test_deerflow_executor_contract.py` | 111 | DeerFlow 适配器契约回归测试（不连真库）。 · 函数:8 · ⚑MOCK |
| `backend/tests/unit/test_ecommerce_crawlers_sidecar.py` | 104 | 函数:8 |
| `backend/tests/unit/test_ecommerce_crawlers_smart.py` | 44 | ECommerceCrawlers smart layer tests. · 函数:4 |
| `backend/tests/unit/test_growth_and_support.py` | 31 | 获客闭环与海外客服单元测试。 · 函数:2 |
| `backend/tests/unit/test_hermes_bridge_failure_terminal.py` | 150 | 编排链桥的失败落态回归测试（不连真库，全部用假 DB）。 · 函数:8 · ⚑MOCK |
| `backend/tests/unit/test_hermes_publish_detail_roundtrip.py` | 226 | 分发结果回写编排链的回归测试（不连真库，全部假 DB）。 · 类:_StubExecutor · 函数:11 · ⚑MOCK |
| `backend/tests/unit/test_international_payments.py` | 84 | 跨境支付与出海合规单元测试。 · 函数:4 · ⚑MOCK |
| `backend/tests/unit/test_moss_vl_clip_publish.py` | 125 | MOSS-VL AI 智能剪辑与一键分发单元测试。 · 类:TestMossVLClipPublish |
| `backend/tests/unit/test_moss_vl_full_capabilities.py` | 93 | MOSS-VL 官方开源完整能力深度测试套件。 · 类:TestMossVLFullCapabilities |
| `backend/tests/unit/test_moss_vl_hot_reload_rollback.py` | 102 | MOSS-VL 官方追踪、热更新与回滚单元测试套件。 · 类:TestMossVLHotReloadRollback |
| `backend/tests/unit/test_moss_vl_repo_integration.py` | 52 | MOSS-VL 官方整仓物理集成与联动测试套件。 · 类:TestMossVLRepoIntegration |
| `backend/tests/unit/test_moss_vl_seo_geo_aao.py` | 101 | SEO / GEO / AAO 排名优化引擎与 MOSS-VL 联动单元测试。 · 类:TestMossVlSeoGeoAao |
| `backend/tests/unit/test_orders.py` | 214 | 类:TestCreateOrder,TestGetOrder,TestListOrders,TestUpdateOrderStatus,TestUpdateOrderPaymentStatus,TestUpdateOrderTracking · 函数:2 · ⚑MOCK |
| `backend/tests/unit/test_payment_balance_service.py` | 184 | 余额支付服务单元测试 — preview / pay / 边界条件 · 类:TestPreviewBalancePayment,TestPayOrderWithBalance,TestWalletTxToDict · ⚑MOCK |
| `backend/tests/unit/test_payment_routes.py` | 259 | 支付路由单元测试 — create / notify / orders / mock-pay · 类:TestCreatePayment,TestCreateNativePayment,TestPaymentNotify,TestListPaymentOrders,TestGetPaymentOrder,TestMockPay,TestPaymentChannelsStatus,TestListPlans · 函数:2 · ⚑MOCK |
| `backend/tests/unit/test_payment_service.py` | 168 | 支付服务 API 单元测试 — WeChatPayService / PaymentService / 验签 / 幂等 · 类:TestWeChatPayService,TestPaymentService · ⚑MOCK |
| `backend/tests/unit/test_publish_executor_three_way.py` | 226 | 分发执行器「三分法」回归测试（不连真库，全部假发布服务）。 · 类:_FakePublishService · 函数:12 · ⚑MOCK/DEGRADED |
| `backend/tests/unit/test_token_service.py` | 266 | Token 服务单元测试 — 配额、扣减、充值、暂停/恢复 · 类:TestBalance,TestEnsureCanConsume,TestConsume,TestCredit,TestSettingsIO · 函数:2 · ⚑MOCK |
| `backend/tests/unit/test_user_action_analytics_sidecar.py` | 25 | UserActionAnalyzePlatform sidecar tests. · 函数:3 |
| `backend/tests/unit/test_workflow_canvas.py` | 68 | 函数:4 |
| `backend/tests/vault_policy_verify.py` | 593 | 轮20 Vault + Policy Engine 内存 SQLite 全流程验证脚本（不触碰真实 DB）。 · 类:_Base,_FakeSettings,TenantShim,UserShim,DeerflowJobShim · 函数:5 · 表:tenants,users,deerflow_jobs · ⚑MOCK/DEGRADED |
| `backend/tests/wallet_user_rls_verify.py` | 199 | wallet 两表 user_id 维度 RLS 真实 PostgreSQL 隔离验证（轮 25-A 补齐专项）。 · 函数:3 · ⚑MOCK |