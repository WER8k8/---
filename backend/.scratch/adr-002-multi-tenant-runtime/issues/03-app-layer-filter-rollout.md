# 03 — 应用层租户过滤扩展（migrate 批次）

**What to build:** 把 T02 的 scope_tenant 模式推广到其余租户域端点：报价 quotes、商机 opportunities、营销 campaigns、公司 companies、项目 projects、线索 leads 等。每个端点行为与 RFQ 一致：租户用户限本租户、平台级 NULL 看全部。可按域分多个 PR 批次推进（每批 CI 绿）。

**Blocked by:** 02（确立 helper 与 tracer 模式）

**Status:** ready-for-agent

- [ ] 盘点全部带 tenant_id 的列表/详情端点，列 checklist
- [ ] 逐域接入 scope_tenant；无租户上下文的跨租户对象读统一 403/404
- [ ] 每域补一条双租户穿透用例（可扩展现 IDOR 哨兵为多资源）
- [ ] 哨兵 C3/C4 覆盖到这些资源全 PASS
- [ ] 平台管理员看板/全局统计仍可用（NULL 路径回归）
