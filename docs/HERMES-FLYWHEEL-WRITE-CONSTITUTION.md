# Hermes 运维宪法 vs 飞轮写库边界（ARCH-03）

## 原则

| 层 | 可写库 | 可自动执行 |
|----|--------|------------|
| **Hermes ops** | 仅快照/审计（巡站、雷达、Rank Guard） | 白名单自愈：缓存刷新、场景健康重探 |
| **DeerFlow / Accio** | 洞察、找客、编排、job 队列 | 研究入队；**不**自动外发邮件/改价 |
| **UBrain 客面** | 记忆、询盘、草稿 | 长任务异步入队 |

## Code Review 清单

- [ ] 新增 `/hermes/ops/*` 路由须 `ops_access.is_ops_admin`
- [ ] 租户路由不得 import `ops_autopilot.run_full_ops_cycle` 同步飞轮
- [ ] `video_matrix` 须 `human_confirmed=true` 才真发
- [ ] 收录/排名探测只读，不写 PublishTask 状态为已发布
- [ ] 告警仅 notify，不触发 deploy/delete/pricing

## 机器审计（Sprint 9）

```powershell
python scripts/arch-03-write-boundary-audit.py
# 或 GET /hermes/ops/write-boundary-audit（超管）
```

检查项：租户 API 不含 ops_autopilot 直调 · Hermes `/ops/*` 均 `_ops_gate` · 品牌中间件覆盖 client/BFF 前缀。
## 引用

- `maintenance_constitution.py` · `safe_remediation.py` · `brand_guard.py`
