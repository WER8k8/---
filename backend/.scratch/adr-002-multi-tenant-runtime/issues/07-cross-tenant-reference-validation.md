# 07 — 跨租户对象引用入参校验

**What to build:** 创建/更新资源时若引用了他租户对象（如报价引用他租户 RFQ、订单引用他租户产品、任务引用他租户资源），统一拦截。这是 IDOR 的另一半：过滤读之外，还要挡住"用他租户 id 建关联"。可复用现成 `agent_portal_service.assert_tenant_in_scope` 语义。

**Blocked by:** 02（确立 scope_tenant/assert 归属判定 helper）

**Status:** ready-for-agent

- [ ] 抽象 `assert_tenant_in_scope(obj_id, model, current_user)` 共享校验
- [ ] 交易类创建端点（quote/order/task/campaign 关联 rfq/company/product）接入：引用对象须同租户（平台级引用公共池除外，按 ADR-001 §4 商城语义裁决）
- [ ] 补越权用例：以租户 A 身份引用 B 的 rfq 建 quote → 被拒
- [ ] 与 products 公共池语义边界一致（待 T08/产品裁决明确哪些跨租户引用合法）
