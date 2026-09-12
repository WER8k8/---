# PAT-01 · 权利要求 ↔ 现网代码对照表

> 交底书：[`专利/技术交底书-AI多模型调度.md`](../专利/技术交底书-AI多模型调度.md)

| 权利要求要点 | 现网实现 | 路径 / 符号 | 状态 |
|--------------|----------|-------------|------|
| 场景别名归一 | `normalize_scenario` | `services/ai_invocation_service.py` L22–45 | ✅ |
| 场景→模型映射 | `resolve_scenario_model` | `services/nvidia_scenario_service.py` | ✅ |
| 租户级覆盖 | `get_scenario_runtime(tenant_id=…)` | `ai_invocation_service.py` L60–83 | ✅ |
| 失败切换链 | `_fallback_scenarios` + `invoke_llm` 循环 | `ai_invocation_service.py` L48–57, L160–200 | ✅ |
| 配额/用量 | `log_ai_invocation` → `AIConfigService.log_usage` | `ai_invocation_service.py` L86–110 | ✅ |
| 可复现 demo | `scripts/pat-03-failover-demo.py` | 仓库根 `scripts/` | ✅ PAT-03 |

**下一动作**：PAT-02 代理机构检索 · PAT-04 Owner 签字

*PAT-01 · 2026-06-02*
