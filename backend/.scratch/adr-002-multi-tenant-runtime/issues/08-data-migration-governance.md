# 08 — 数据迁移治理：存量回填 + 归档孤儿列清理

**What to build:** 两件事，均**依赖 ADR-001 产品裁决**方可定稿：
1. 存量 `users.tenant_id` 回填：历史用户多无明确租户归属（当前无映射源）——需产品给出归属规则（按 company/invite 关系？按域名？人工指派？）后写回填迁移。orders/quotes/products.tenant_id 回填同此。
2. 归档孤儿漂移列清理：app 库（youding_dev，归档线 stamp 080）里存在 worktree 模型无定义的列（如 products.fob_price、若干 Float 统计列），在绿色部署链修复（P0-B）后统一 reconcile。

**Blocked by:** 需 ADR-001 商城语义 + ADR-002 用户归属规则拍板（无代码 blocker，但有决策 blocker）

**Status:** needs-decision（决策未定前不排期实现）

- [ ] 产品确认：租户用户归属映射规则（决定 1 的回填可行性）
- [ ] 产品确认：products 公共池 vs 多租户目录（决定 T07 合法跨租户引用边界 + 本票 products.tenant_id 回填）
- [ ] 裁决后：写回填迁移 + 孤儿列 reconcile 迁移，纳入绿色部署链（与 P0-B 修复协同）
