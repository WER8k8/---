# 09 — IDOR 哨兵翻正为隔离门禁（verify/gate）

**What to build:** 把 `tests/idor_tenant_isolation_verify`（现为诊断型、恒 exit 0、记录缺口）升级为**断言型隔离门禁**：C1 RLS 生效 / C2 app 非超主 / C3 列表不跨租户 / C4 详情不跨租户全部 PASS，且覆盖 T03 推广后的多资源；存在失败即 exit 1，纳入回归套件与发布前检查。这是 ADR-002 方案 1 的**完成定义**。

**Blocked by:** 03（app 层过滤铺全）、05（RLS FORCE + 非超主角色）、07（引用校验）

**Status:** ready-for-agent

- [ ] 哨兵退出码改为按隔离结果判定（全 PASS→0，有缺口→1）
- [ ] 扩展用例覆盖 rfq/quote/opportunity/campaign/company/lead 等资源的列表+详情双租户穿透
- [ ] 并入 `tests/*_verify.py` 回归清单，全套绿基线更新（768 → 新基线含本票）
- [ ] 发布前检查文档/脚本引用本门禁（对应 20 维报告"灰度门槛"）
