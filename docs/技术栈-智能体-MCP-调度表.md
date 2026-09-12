# 技术栈 · 智能体 · MCP 调度表

> 先判 **混合模式场景**：`docs/混合模式-场景抉择表.md`（`04-hybrid-mode-scenarios.mdc`）  
> 再执行质量底线：`.cursor/rules/03-plan-tech-ecc-minimal.mdc`

## 原则

1. **先规划** — 目标 / 边界 / 验收  
2. **按技术派工** — 不默认 222 人全流程  
3. **MCP 当脚手架** — 未配置不调用  
4. **最小实现 + ECC 质检** — 见规则 `03-plan-tech-ecc-minimal.mdc`

## 调度表

| 场景 | 主角色 | ECC | MCP |
|------|--------|-----|-----|
| FastAPI API/服务 | `insulation-backend-developer` | `planner` → `tdd-guide` → `code-reviewer` | codegraph、postgres |
| 架构决策 | `insulation-backend-architect` | `architect` | codegraph |
| Vue 管理端 | `frontend-architect` | `typescript-reviewer` | cursor-ide-browser |
| Nuxt 租户站 | `fullstack-developer` | `typescript-reviewer` | browser |
| 数据库 | `insulation-database-architect` | `database-reviewer` | postgres |
| 安全/支付 | `insulation-backend-security-expert` | `security-reviewer` | — |
| QA/E2E | `testing-reality-checker` | `e2e-runner` | playwright |
| 运维/Worker | `insulation-devops-engineer` | — | cloudflare |
| 飞书通知 | `insulation-operations-engineer` | — | feishu / lark-cli |
| 产品/文档 | `insulation-material-product-manager` | `doc-updater` | — |

## 验收命令（本仓库常用）

```powershell
cd backend
$env:JWT_SECRET_KEY="test-"+("x"*32)
python -m pytest tests/unit/test_sprint_*.py -q
cd ..
python scripts/check_mounted_routes.py
python scripts/dev_progress.py
```

## 蜂群并行（多 Agent）

| 岗位 | 灵码 ID | 路径独占 |
|------|---------|----------|
| 指挥 | `architecture-commander` | 拆包、合并、禁区 |
| 后端包 | `insulation-backend-developer` | `backend/` |
| 管理端包 | `frontend-architect` | `frontend/admin/` |
| 租户站包 | `fullstack-developer` | `frontend/pages/` |
| DB | `insulation-database-architect` | 迁移 **串行** |

- 规则：`.lingma/rules/swarm-parallel-dev.md`  
- 工作流：`workflows/swarm-parallel-dev.yaml`  
- Cursor：`dispatching-parallel-agents` + Task 并行子 agent  

**推荐**：先 `[S]` 定 API 契约 → `[P]` backend ∥ admin → 指挥合并 `routes/__init__.py` → ECC。

## 反模式

- 同一功能 `/foo`、`/foo-v2`、`/foo/unified` 三套实现  
- 未跑测试即声称完成  
- 为单个字段新建 5 个 service 文件  
- 虚构已连接的 MCP  
- 多 agent 同时改同一热点文件  
