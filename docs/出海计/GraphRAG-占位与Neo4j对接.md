# GraphRAG 占位 · Neo4j 对接（P2，蜂群八轮）

> **状态**：仅占位与契约，**不阻塞** D1–D7 飞轮验收。  
> **触发条件**：单租户 `entities_json` 稳定产出且洞察量 > 500 条，或客户明确要求关系推理。

---

## 一、本系统已有数据（无需 GraphRAG 即可跑）

| 来源 | 字段/表 | 用途 |
|------|---------|------|
| DeerFlow Lite / 旁路 | `ubrain_research_insights.entities_json` | 实体、市场、竞品片段 |
| 记忆合并 | `ubrain_tenant_memory.research_hints` | 下一轮 `market_research` 提示 |
| Accio 编排 | `ubrain_pipeline_runs` | 研究→找客→开发信链路 |

GraphRAG 的价值是**跨洞察的关系查询**（例如「某区域买家 ↔ 某产品线」），不是替代上述表。

---

## 二、目标拓扑（占位）

```text
market_research 完成
  → entities_json（PostgreSQL）
  → [P2] graph_sync_worker（定时或 webhook）
  → Neo4j（节点：Market, Product, BuyerPersona, Competitor；边：TARGETS, COMPETES_WITH, MENTIONED_IN）
  → [可选] GraphRAG index 供 DeerFlow 旁路二次检索
```

---

## 三、环境变量（预留，见 `backend/.env.example`）

| 变量 | 说明 |
|------|------|
| `NEO4J_URI` | 例如 `bolt://127.0.0.1:7687` |
| `NEO4J_USER` / `NEO4J_PASSWORD` | 库账号 |
| `GRAPHRAG_SYNC_ENABLED` | `0` 默认关闭；`1` 启用占位 worker |

未配置时：`GET /api/v1/ubrain/commercial-os/status` 的 `integrations.graphrag` 为 `disabled`（与 Mem0/PostHog 同级展示）。

---

## 四、实现切片（后续蜂群，按序）

1. **只读状态**：`flywheel_integrations_status()` 增加 `graphrag: { enabled, neo4j_configured }`。
2. **一次性导入脚本**：`scripts/graphrag-import-entities.ps1` 从 `ubrain_research_insights` 批量 UPSERT Neo4j。
3. **增量 worker**：洞察写入后异步 enqueue（与 `deerflow_job` 审计同级，失败可重试）。
4. **查询 API**：`GET .../commercial-os/graph/neighbors?entity_id=` 供副驾展示（可选）。

**禁止**：在未接 Neo4j 前改 `market_research` 主路径；禁止第三套平行记忆表。

---

## 五、验收（P2）

| 项 | 命令/检查 |
|----|-----------|
| 集成状态 | `GET /commercial-os/status` → `integrations.graphrag` |
| 导入冒烟 | Neo4j Browser 可见 ≥1 租户子图 |
| 单测 | `tests/unit/test_graphrag_integration_stub.py`（仅状态位，不连真库） |

---

## 相关

- `docs/出海计/商业OS飞轮-开源组件对接.md` §二
- `docs/出海计/DeerFlow-旁路部署与回写.md`
- `backend/app/services/ubrain/flywheel_integrations.py`
