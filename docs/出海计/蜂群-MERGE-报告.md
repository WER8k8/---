# 蜂群 MERGE 报告（断点续作 · 2026-05-28）

## 看板

| 包 | 状态 | 说明 |
|----|------|------|
| W0-VERIFY | ✅ | [`蜂群-W0-VERIFY-报告.md`](./蜂群-W0-VERIFY-报告.md) |
| W1-ACCIO | ✅ | 四 gap MVP → HTTP 200 |
| W2-FRONT | ✅ | 实验室菜单 + Nuxt 8001 |
| W3-EGRESS | ✅ | 模型 + `030_add_egress_and_browser_profile_tables.py` + 单测 |
| MERGE | ✅ | 本报告 |

## 验收证据

```text
pytest tests/unit -q  →  304 passed  (2026-05-28 断点续跑)
test_commercial_os_webhook.py  →  7 passed（含 4× gap MVP 200）
```

## W1 代码落点

| 文件 | 作用 |
|------|------|
| `backend/app/services/ubrain/accio_gap_constants.py` | 四技能 ID |
| `backend/app/services/ubrain/accio_gap_handlers.py` | MVP 业务载荷 |
| `backend/app/api/v1/routes/ubrain_commercial_os.py` | `/gap/{id}` 200 |
| `backend/app/data/accio_skill_catalog.json` | 四技能 `partial` |
| `frontend/admin/src/views/client/copilot.vue` | 去掉「501 占位」引导 |

## W2 代码落点

| 文件 | 作用 |
|------|------|
| `frontend/admin/src/layout/index.vue` | `labPaths` 扩展（认知/边缘/CDN/V2Ray 等默认隐藏） |
| `frontend/nuxt.config.ts` | `apiHost` / dev proxy → **8001** |
| `frontend/pages/logistics/index.vue` | 已用 `useApiV1Url`（无需再改） |

## JSON 本轮勾选

`docs/dev-sprint-all-in-one.json` → **done**：

- T-P0-08、T-P0-13  
- T-ACCIO-1～5、T-MENU-1、T-V2RAY  

（W0 此前已勾：T-P0-01、02、05、07、12）

## 仍开放（蜂群外）

- T-P0-14 询盘仅 unified 入口  
- S0 菜单定稿、S3 Postgres/Celery、G1～G7、PM 签字项  
