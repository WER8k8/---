# ADR-001: 租户身份归一（tenant_id 为唯一租户维度）

- **状态**：已采纳（2026-09-05）
- **裁决来源**：2026-09-05 全量审计 P0-4「租户身份双轨制」（`audit/2026-09-05-20维交付审计报告.md` 维度 3）
- **冲突裁决**：本 ADR 依据总纲多租户红线精神制定；与总纲冲突处以总纲为准并回改本 ADR。

## 1. 背景与问题

项目由多个模型协作编写，形成了两套并存的"身份维度"：

| 体系 | 表 | 含义 |
|---|---|---|
| `tenant_id`（租户维度） | rfqs / opportunities / campaigns / companies / projects / ai_tasks / meter_events / content 等 | SaaS 租户边界，RLS 蓝图以此为主键（`app/db/rls_policies.py` 以 `tenant_id = current_setting('app.current_tenant_id')` 断言） |
| `merchant_id` / `buyer_id`（用户维度） | orders / quotes | 交易对手的用户外键 |
| 无租户列 | products | 平台全局目录（B2B 商城语义下商品曾被视为公共池） |

后果：RLS 蓝图无法覆盖三张核心商业表；跨租户隔离完全依赖应用层人工过滤纪律；审计越权测试无法系统性覆盖。

## 2. 决策

1. **`tenant_id` 是唯一租户维度**。所有业务表逐步收敛到 tenant_id 体系。
2. **`merchant_id` / `buyer_id` 保留**，语义收窄为"交易对手用户外键"，不再承担租户边界职责。
3. **products / orders / quotes 补 `tenant_id` 列**（迁移 `102_tenant_unification_columns`，nullable + 索引）：
   - nullable 是刻意决策：存量数据不背书租户归属，避免凭空填错租户；
   - 写入方（RFQ 转报价、报价转订单、产品创建/导入）在新代码中必须显式提供 tenant_id；
   - 非空约束与回填在独立后续迁移中完成（需先按 merchant → 所属租户的映射回填并人审抽样）。
4. **RLS 启用路径不变**：`RLS_PILOT_ENABLED`（默认关）+ `RLS_PILOT_TABLES` 逐步扩表；会话注入链路已存在（TenantMiddleware → OTel context → engine begin 事件 → `SET LOCAL app.current_tenant_id`，见 `app/core/database.py:_setup_rls_event_listener`），本 ADR 不新增开关。
5. **查询过滤纪律**：在这三张表的列表/详情端点改造为强制 `tenant_id` 过滤前，先以本 ADR 第 3 条的写入补值为准；端点过滤改造按端点逐个评审（涉及商城"公共商品池"语义的产品端点需产品裁决，不在本 ADR 范围）。

## 3. 验证记录（2026-09-05 实测）

- 迁移图：单 head `102_tenant_unification_columns`（alembic ScriptDirectory 官方确认）
- 存量库路径：create_all(200 表) → stamp 101 → upgrade 102 → 三表 `tenant_id` 列 + `ix_*_tenant_id` 索引全就位，幂等重跑 no-op
- ORM 对齐：Product/Order/Quote 模型已加 `tenant_id`（nullable + index）
- 说明：全链 001→102 仅在 PG 可跑（旧迁移 022 用 JSONB，SQLite 不可渲染，属既有设计）；SQLite 开发库走 create_all + 条件迁移路径，与 101 既有实践一致。

## 4. 后续工作（不在本次范围）

| 项 | 触发条件 |
|---|---|
| 回填迁移（tenant_id 非空 + 数据回填） | 写入方全部补真值后 |
| 三表端点强制租户过滤改造 | 回填完成后逐端点评审 |
| RLS_PILOT_TABLES 扩表到 products/orders/quotes | PG 环境下双租户穿透验证通过后 |
| 商城公共商品池语义裁决 | 产品层决策（多租户商品目录 vs 平台公共目录） |
