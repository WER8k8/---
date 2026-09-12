# 全量执行计划（2026-09-05 冲刺）—— 状态终版

> 执行结果：M3/M4/M5/M7/M8/M9 全部完成并验证；M1/M2 完成调研+定位+安全网，正式立项为工程票（不可在无 git worktree 里一次性安全 sweep）；M6 经读 docstring 判定为产品语义决策撤回（Project="公开项目/招标情报"，与商城公共池同性质）。

## 状态
- M1 ❌→**立项 ticket 10**：greenfield 链在 PG 的 ID 分裂根因已精确定位（001 ID_TYPE=uuid vs 4188869502e0 tenants.id=硬 varchar；users.id=uuid）→ 需 VCS + canonical(建议 uuid) + 全迁移 sweep + 重建。安全网快照在 `_archive/snapshot-backend-preM1-20260905/`（3889 文件）。
- M2 ❌→**随 M1**：RLS 机制已证（uj_test 65/0 含 role_grants 20/0）；app_rw 角色已在 youding_dev 建好（D2 就绪）；FORCE cutover 待 M1 后干净库+非空数据。
- M3 ✅ 迁移 104（orders/quotes 经 UserTenant 回填；单 head=104；you库 quotes 2/2 回填）。
- M4 ✅ quotes get/list 加 auth+租户隔离（**注意：quotes 属 v1 根"死层"，未挂载——见 M5 发现**）。
- M5 ✅ **重大发现：`app/api/v1/*.py` 根层 31 个文件全部未挂载（只有 routes/ 自动发现是活的）**——quotes/deerflow/evolution/chat/n8n 等全是死层，路由收敛(C组)由此有实锤。deerflow 16 处大小写笔误已修（F821 清零）。
- M6 ❌撤回（读 docstring：Project="公开项目/招标情报"，疑似共享池；与商城语义同一产品决策）。
- M7 ✅ i18n 脚手架（app/core/i18n.py：目录+t()+resolve_locale；auth 登录接入；实测 zh 原样/en 英文）。
- M8 ✅ ruff F401+F541 自动修 680 处（F811 有行为风险跳过）；1101→681 项；回归 21/21 绿。
- M9 ✅ compileall 0 错、回归 21/21 rc=0、IDOR 哨兵 A1–A5 真 PG PASS exit0。

## 剩余（全部已立票/待决策）
- ticket 10（M1/M2，需 VCS+canonical 确认）｜quotes-from-rfq 真挂载后 A5 才是 403 而非 404（本轮已把死层事实纠正进报告）｜D0 并入 M5 发现（死层收敛决策）｜C 组商城/i18n 全量化/存量归属=产品决策。

## M1 P0-B 迁移链 ID 类型统一（canonical = UUID）★基石
- 根因：迁移硬编码 String(36) 建 id/PK/FK，模型用 UUID_TYPE；greenfield 里 tenants.id=varchar、users.id=uuid 自身不一致 → 17+ 迁移外键 DatatypeMismatch。
- canonical 判定：模型 Mapped[str] + 活库 youding_dev（create_all）users.id/tenants.id 均 uuid → 统一为**原生 UUID**（as_uuid=False）。
- 步骤：加 `alembic_migrations/_compat.uuid_col()` → 修 foundational 迁移里 tenants/users 及各 String(36) PK → sweep 所有 `sa.String(36)` 作 id/PK/FK 处 → 空库 greenfield `upgrade heads` 001→head 跑通为止（迭代验证）。

## M2 T05 RLS 运行时强制（M1 后干净库上端到端）
- 新库 uj_rls_check 用 greenfield 建 → 建 app_rw 非属主角色 → ENABLE+FORCE RLS 全 tenant 表 → seed 双租户数据 → 验证非属主只见本租户；IDOR 哨兵 PG 模式 D1/D2 转绿。
- 交付 app_rw cutover 脚本 + runbook；不销毁 youding_dev（保留，cutover 留发布窗）。

## M3 orders/quotes.tenant_id 回填（经 UserTenant 可解，此前误判"无解"）
- 迁移 104：`UPDATE orders/quotes SET tenant_id = <merchant 的 active UserTenant 租户>`（可推导部分）；无法推导留 NULL + 审计。products 因商城语义留决策。

## M4 quotes/leads secure-by-default 鉴权+隔离
- list_quotes/get_quote 现无 auth 且裸 dict → 加 get_current_user + tenant_can_access + 统一包络；leads 列表（若有）按 UserTenant 作用域。

## M5 deerflow D0 裁决并落地
- 查 deerflow 功能是否他处已服务：是→删孤儿文件+修集成测试；否→挂载 + 修 16 F821（DeerFlowJob 等）。

## M6 project.tenant_id（CRM 明确属租户）
- 迁移 + 模型加列 + project 列表/详情接 scope（此前因无列跳过，现补）。

## M7 i18n 后端脚手架（奠基，非 1000+ churn）
- app/core/i18n：消息目录(en/zh) + t(key) + Accept-Language 解析依赖；error_response 支持 key；迁移代表性一批 message，其余按模块增量。

## M8 lint 安全自动修（快照兜底后）
- ruff --fix F541/F811/F401（非 __init__）→ 每类后跑回归；F821 剩余逐点。

## M9 终验 + 文档
- 全量回归 21 套 + 3 PG RLS + IDOR 门禁（PG 模式全绿）+ 绿色链 greenfield 绿；更新 ADR/tickets/报告/记忆。

## 顺序 & 并行
M1 先行（解锁 M2/M3 greenfield）。M4/M5/M6/M7 相互独立，M1 后并行。M8 最后（大面积改后统一回归）。M9 收口。

## 出界（真产品决策，不硬做）
商城"公共池 vs 多租户目录"的最终商业语义、user 存量无映射用户的归属规则 → 留 ADR-001/ticket 8 决策位，代码侧用可推导部分推进。
