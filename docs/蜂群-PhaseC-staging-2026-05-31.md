# Phase C · Staging 送检 — 2026-05-31

> P0–P13 商业闭环 + 严验签公网 notify 已完成。本节为 **GB25000 Phase C** 与蜂群剩余项。

## 已完成（本节）

| 项 | 交付 |
|----|------|
| W45 层级节点写 API | `POST/PUT/DELETE /api/v1/agent-tree/nodes` |
| 前端层级管理 | `/admin/hierarchy` 增删改对接 API |
| 单元测试 | `tests/unit/test_agent_tree_crud.py` |

## 待办（需 Docker / PM）

| 项 | 命令 / 阻塞 |
|----|-------------|
| staging preflight 0 fail | ✅ `scripts/run-staging-preflight-auto.ps1` PASS |
| Locust 1000 | 本地 smoke 50u/30s 已完成；正式 1000 需 staging 服务器 |
| 72h 可靠性 | 5 分钟 smoke PASS；正式 72h 需运维监控 |
| PM 签字 | `l3-signoff.json`、12 模块截图 |

## 本地验证

```powershell
cd backend
python -m pytest tests/unit/test_agent_tree_crud.py -q
```

管理端：`/admin/hierarchy` — 超管登录后添加/编辑/停用节点。
