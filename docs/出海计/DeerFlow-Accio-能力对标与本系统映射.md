# DeerFlow × AccioWork 能力对标 · 本系统映射

> 2026-05-25 · 基于用户对两款「天花板」产品的深度拆解

## 产品铁律（不可擅自改向）

**卖货第一生产力 = 字节系深度研究（DeerFlow）+ 阿里系国际电商执行（AccioWork）能力对标复刻。**

- **主方向**：大厂路线已验证 — **研究望远镜 + 执行卡车 + Brief 结构化串联**；实现可以分阶段，**不得**改成「自研另一套卖货范式」替代这对组合。
- **允许差异**：建材垂直、独立域、40 平台矩阵、三轨计费、人审外发 — 这些是**增强层**，不是替换 DeerFlow/Accio 对标表。
- **禁止**：用演讲/彩排/七步叙事挤掉 Accio 技能包与 Research Brief 主线；未对标项标 `gap`，不删对标项。

---

## 一、一句话定位（本系统）

| 产品 | 官方定位 | 优丁卖货 OS 等价物 |
|------|----------|-------------------|
| **DeerFlow** | 开源多 Agent 深度研究（望远镜） | `deerflow_research_service` + `deerflow_jobs` + **Research Brief JSON** |
| **AccioWork** | 阿里国际电商执行（自动驾驶卡车） | `accio_sales_service` + `/client/copilot` + **技能包目录** |

**组合键**：`Research Brief.accio_actions[]` → 编排层自动 `enqueue` Accio 任务（无需人工复制报告）。

---

## 二、DeerFlow 能力 → 本系统

| DeerFlow 能力 | 本系统 | 状态 |
|---------------|--------|------|
| LangGraph 动态编排 | `Planner` 子任务拆解 `_planner_subtasks` | ✅ 规则版 |
| Researcher / Reviewer / Writer | `build_research_brief` 四阶段 | ✅ |
| Tavily / 网页解析 | — | ⏳ 可 n8n 接外部搜索后 webhook |
| 长程记忆 | `ubrain_research_insights` + Mem0 槽位 | ✅ |
| 溯源与置信度 | `findings[].source` + `confidence` | ✅ |
| 矛盾标注 | `controversies[]` | ✅ 轻量 |
| Human-in-the-loop | `human_in_the_loop.checkpoint_recommended` | ✅ |
| 私有化 / 模型无关 | FastAPI 自托管 + 多模型可接 LLM 层 | ✅ 骨架 |

**产出契约**：`POST /api/v1/ubrain/commercial-os/research-brief`  
或 DeerFlow 任务 `intent=market_research` 返回 `research_brief` 字段。

---

## 三、AccioWork 能力 → 本系统

详见 `GET /api/v1/ubrain/commercial-os/skill-catalog`（`backend/app/data/accio_skill_catalog.json`）。

| Accio 大类 | 本系统已实现（约） | 刻意不做 |
|------------|-------------------|----------|
| 选品/商机 | market_research、find_buyers、blue_ocean | 阿里 10 亿交易暗数据 |
| 建站/上架 | lead_content_pack、geo、matrix（部分） | 30 分钟 Shopify 克隆 |
| 营销 | 开发信、询盘回复、谈单话术 | 站内广告 API 全自动 |
| 供应链 | 询盘分级、物流 API | 1688 自动下单 |
| 企业运营 | 周报、反馈回流、pipeline、RBAC 部分 | 阿里生态一键写回 |

**壁垒说明（对外话术）**：强在 **建材垂直 + 自有独立域 + 40 平台矩阵 + 三轨计费**；不靠复刻国际站私有库。

---

## 四、王炸组合在本系统的数据流

```text
用户：分析东南亚保温市场出口机会
  → DeerFlow Lite：Planner → Researcher(trade_intel) → Reviewer → Writer
  → research_brief.json
       ├─ findings[]（带 source/confidence）
       ├─ controversies[]
       └─ accio_actions[]（结构化 Accio 指令）
  → on_deerflow_job_finished
       ├─ extract_insight（记忆层 / Mem0 等价）
       └─ run_pipeline_after_deerflow（n8n 等价）
  → Accio：find_buyers → outreach_letter_pack → …
  → collect_sales_feedback → research_hints → 下一轮 Researcher
```

---

## 五、与开源组件推荐的对照

| 推荐组件 | 解决断层 | 本系统当前 | 接入方式 |
|----------|----------|------------|----------|
| **Mem0** | 记忆 | `ubrain_research_insights` | `MEM0_API_URL` 双写 |
| **n8n** | 执行搬运 | `pipeline` + webhook | `POST .../commercial-os/webhook` |
| **PostHog** | 反馈 | `feedback_snapshots` | 埋点 → 定时 sync |
| **GraphRAG** | 关系推理 | `entities_json` | P2 同步 Neo4j |
| **Browser Use** | 非 API 平台 | 发布 Worker | P2 |
| **Ragas** | 质量评估 | `quality_score` | P2 接库 |

**优先顺序**（与用户建议一致）：先用好内置飞轮 → 再接 n8n + Mem0。

---

## 六、完整 DeerFlow 旁路部署（可选）

1. 私有化部署 [DeerFlow](https://github.com/bytedance/deer-flow)（字节开源）。  
2. 研究结束 `POST` 本系统 webhook，`event=deerflow_done`，body 含完整 `result` / `brief`。  
3. 本系统只做 **Accio 执行 + 线索账本 + 反馈**，不把深度爬虫放进主站。

---

## 相关文件

- **开发总文档（整合）**：`docs/出海计/商业飞轮OS-开发总文档.md`
- `backend/app/services/ubrain/deerflow_research_service.py`
- `backend/app/services/ubrain/commercial_os_bridge.py`
- `docs/出海计/商业OS飞轮-开源组件对接.md`
