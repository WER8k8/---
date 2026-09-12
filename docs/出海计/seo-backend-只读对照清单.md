# seo-backend 只读对照清单（T-NODE-1）

**策略**：见 `docs/adr/seo-backend-vs-fastapi.md` — FastAPI 为唯一写入真相源；`seo-backend/` 仅遗留只读。

## 能力对照

| 能力域 | FastAPI `seo_matrix` | Node `seo-backend` | 说明 |
|--------|---------------------|-------------------|------|
| 省市区 | ✅ | ✅（MySQL） | 新数据以 PG/Alembic 为准 |
| 关键词 | ✅ | ✅ | 生成/导入走 FastAPI |
| 内容生成 | ✅ | ✅ | 禁止 Node 新增写 API |
| 发布任务 | ✅ `publish-tasks` | ✅ | 统一发布台在 FastAPI |
| 平台账号 | ✅ | ✅ | |
| 收录监控 | ✅ | ✅ | |
| 风控 | ✅ | ✅ | |

## 自动扫描

```powershell
backend\.venv\Scripts\python.exe scripts\seo-node-parity-check.py
```

产出：`docs/seo-node-parity-latest.json`

## 验收

- [x] 对照表与 ADR 一致
- [x] FastAPI 矩阵路由已挂载（`tests/unit/test_sprint_routes.py`）
- [ ] 生产环境 Node 仅只读连接（运维确认）
