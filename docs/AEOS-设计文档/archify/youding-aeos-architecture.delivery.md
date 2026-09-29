# 优丁 YouDing · AEOS 架构图交付清单与验证证据

> 交付日期：2026-09-18 ｜ **更新：2026-09-19**（功能域 + Hermes 任务中心 + **地毯式扫描刷新**）  
> 工具：Archify（JSON IR → 交互式 HTML/SVG）质量标准：`showcase`  
> 更新要点：GoodJob/TradeAI=**无特权功能域**；新增 **Hermes 任务中心 `/client/tasks`**；DSH 可选、默认 L1；GP-A/B 由 Hermes 驱动。

---

## 〇、2026-09-19 地毯式扫描刷新（本轮）

> 数据口径全部**实测**（`probe_scan_landscape.py`，2026-09-19），不引用旧文档数字：

| 项 | 旧口径 | 实测刷新 | 证据 |
|----|--------|----------|------|
| PostgreSQL 表数 | 229+ | **248**（100% 注水） | PG@5433 `information_schema` 实测；alembic head `116_normalize_lead_enum_case` |
| 后端路由模块 | 157 | **159** | `app/api/v1/routes/*.py` 计数 |
| 后端端点 | 1481 | **1496** | 路由文件 `@router.<method>` 计数 |
| Hermes 执行器 | 37 | **37** | `ExecutorRegistry.list_executors()` 实测 |
| 技能表 | 76 | **77**（active 77） | PG `skills` 表 count |
| Agency 资产 | — | 222 roles · 52 workflows | `backend/app/data/` YAML 计数 |
| 六端口 | — | **3000 / 5173 / 8001 / 6379 / 5433 / 5678 全在跑** | socket connect 实测 |

- **IR 变更**：`api` tag→「159 路由 · 1496 端点」；`pg` tag→「248 表 · 100% 注水」；cards 更新为 37/37 执行器全驱动、248/248 表注水、4 大实盘闭环接口、双 Webhook。
- **验证**：validate 0 错误/0 警告 → render → visual-check **ok/status=pass**（四视口全过）。
- **备份**：旧 IR/HTML 留存为 `*.bak-20260919`。

---

## 一、交付产物清单

| # | 产物 | 路径 | 说明 |
|---|------|------|------|
| 1 | **JSON IR 源** | `docs/archify/youding-aeos.architecture.json` | 唯一事实源（含任务中心与功能域标签） |
| 2 | **交互式 HTML** | `docs/archify/youding-aeos-architecture.html` | 4 视图：主链路 / AI 编排 / **黄金路径** / 出站 |
| 3 | 视觉校验 | `*.visual-check.*` | Chrome 自动化证据 |

**打开**：浏览器直接打开 `docs/archify/youding-aeos-architecture.html`。

---

## 二、验证（2026-09-19 重渲）

| 命令 | 结果 |
|------|------|
| `archify validate architecture … --quality showcase` | **ok: true** |
| `archify render architecture … --quality showcase` | **RENDER=0**，HTML ~824KB |
| `ARCHIFY_CHROME=… archify visual-check …` | **ok: true / status: pass**（sha `64751bd9…`） |

## 三、复现

```powershell
$arch = "C:\Users\Administrator\Documents\上线网站开发完成\_external\archify\archify\bin\archify.mjs"
$ws  = "C:\Users\Administrator\Documents\上线网站开发完成"
$env:ARCHIFY_CHROME = "C:\Program Files\Google\Chrome\Application\chrome.exe"
node $arch validate architecture "$ws\docs\archify\youding-aeos.architecture.json" --quality showcase
node $arch render architecture "$ws\docs\archify\youding-aeos.architecture.json" "$ws\docs\archify\youding-aeos-architecture.html" --quality showcase
node $arch visual-check "$ws\docs\archify\youding-aeos-architecture.html" --json
```

> 注：`docs/archify/` 位于**工作区** `上线网站开发完成\docs\`，不在 git worktree 主仓提交树内；改动需单独归档或迁入仓库后再 commit。


> 交付日期：2026-09-18 ｜ 工具：Archify（open-source architecture diagramming，JSON IR → 交互式 HTML/SVG）
> 质量标准：`showcase`（showcase 组合校验 0 错误 / 0 警告）
> 数据口径：AEOS 八子系统架构法典 + 后端运行环境强制索引（PG 15.8 @5433 / Redis @6379 / n8n @5678 / 157 路由 · 1481 端点 / 229 表）

---

## 一、交付产物清单

| # | 产物 | 路径 | 大小 | 说明 |
|---|------|------|------|------|
| 1 | **JSON IR 源文件** | `docs/archify/youding-aeos.architecture.json` | 5.9 KB | 架构图唯一事实源，可版本化、可 diff、可重渲染 |
| 2 | **交互式 HTML 图** | `docs/archify/youding-aeos-architecture.html` | 820 KB | 成品图：3 个视图（主链路 / AI 编排 / 出站分发）、缩放平移、图例、明暗主题 |
| 3 | **组合校验报告（JSON）** | `docs/archify/youding-aeos-architecture.visual-check.json` | 17 KB | 自动化浏览器证据：视口包含 + 可读性 + 截图 全部 pass |
| 4 | **校验联系表（HTML）** | `docs/archify/youding-aeos-architecture.visual-check.html` | 2 KB | 4 张校验截图的联系表，便于人工复核 |
| 5 | 截图 · 1440×900 浅色 | `docs/archify/youding-aeos-architecture.visual-check.1440x900.light.png` | 155 KB | 标准笔记本视口 |
| 6 | 截图 · 1440×900 深色 | `docs/archify/youding-aeos-architecture.visual-check.1440x900.dark.png` | 148 KB | 标准笔记本视口（深色主题） |
| 7 | 截图 · 2048×1320 浅色 | `docs/archify/youding-aeos-architecture.visual-check.2048x1320.light.png` | 190 KB | 大屏/投屏视口 |
| 8 | 截图 · 2048×1320 深色 | `docs/archify/youding-aeos-architecture.visual-check.2048x1320.dark.png` | 181 KB | 大屏/投屏视口（深色主题） |

**首推打开方式**：`docs/archify/youding-aeos-architecture.html`（浏览器直接打开，交互式，可切视图/明暗）。

---

## 二、验证证据（全部实测，非人工声称）

### 2.1 组合校验 `archify validate --quality showcase`

```
ok: true ｜ profile: showcase ｜ status: pass ｜ errors: 0 ｜ warnings: 0
```

| 检查项 | 结果 | 关键指标 |
|--------|:---:|---------|
| 9 项自动检查（single_svg / finite_svg / orthogonal_arrows / label_route_clearance / relationship_crossings / relationship_corridors / container_border_runs / route_rhythm / legend_clearance） | ✅ 全过 | — |
| properCrossings（连线交叉） | ✅ | **0** |
| ambiguousCorridors（歧义走廊） | ✅ | **0** |
| containerBorderRuns（沿边界走线） | ✅ | **0** |
| labelRouteClearanceIssues（标签压线/重叠） | ✅ | **0**（最小间距 5px） |
| desktopReadabilityIssues（桌面可读性） | ✅ | **0** |
| maxBends（单线最大弯折） | ✅ | 2 ≤ 建议上限 2 |
| maxStretch（最长线拉伸比） | ✅ | 1.065 ≤ 建议上限 1.35 |

### 2.2 视觉校验 `archify visual-check`（自动化 Chrome 实测）

```
status: pass ｜ evidenceKind: automated-browser ｜ diagnostics: []
```

| 视口 | 溢出 X | 溢出 Y | 节点文字最小投影 | 要求下限 | 图例/导航坞 | 结论 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|
| 1440×900 | 无 | 无 | 9px | ≥6px | 有 / 有，间距 10.2px ≥ 10px | ✅ |
| 1600×1000 | 无 | 无 | 9px | ≥6px | 有 / 有 | ✅ |
| 1920×1080 | 无 | 无 | 9px | ≥6px | 有 / 有 | ✅ |
| 2048×1320 | 无 | 无 | 9px | ≥6px | 有 / 有 | ✅ |

- 产物 SHA-256：`b7c407192a816b3240c35f3769ef215d3ac9196187c7f994e443b4485473a961`
- 验证用 Chrome：`C:\Program Files\Google\Chrome\Application\chrome.exe`

---

## 三、图内容 ↔ 真相源映射

图内元素全部有据可查，对应本项目权威文档（无杜撰数据）：

| 图内元素 | 内容 | 真相源 |
|---------|------|--------|
| 前端壳 官网 :3000 · 超管 :5173 | 唯一登录 /login | 仓库 AGENTS.md LOGIN-LOCK-01 / 官网启动强制索引 |
| 后端 API FastAPI :8001 · 157 路由 / 1481 端点 | — | capability_ledger 实测（157/157 路由模块连通） |
| L1 认知沙箱 DeepSeek Harness | 意图分解 → DAG Spec | AEOS_MASTER_ARCHITECTURE_SPEC 双层 Agent 拓扑 |
| L2 受控调度 Hermes | 环路拦截 · 4 执行器（Python/Celery/Subagent/Webhook） | AEOS SPEC §DAG Governor；orchestration_selfcheck 19/19 通过、37 执行器 |
| 入站中枢 Site / Calc / BOQ | 建站 · 22 参数核价 | AEOS SPEC 核心观点 1/2 |
| 内容与研报 DeerFlow | 9 意图深研 · EEAT | AEOS SPEC / 11 个工作流 |
| 履约 CRM GoodJob | 外贸 7 步 · PI/单证 | AEOS SPEC 核心观点 4 |
| 社媒拓客 Trade AI Agent | WhatsApp 矩阵 | AEOS SPEC 核心观点 2 ⑤ |
| PostgreSQL :5433 · 229 表 | — | 后端运行环境强制索引 ENV-LOCK-01 |
| Redis :6379 / n8n :5678 | 出站 Webhook site_built / content_pub | 后端运行环境强制索引 |
| 卡片三则 | 入站 / 八子系统 / 出站与计费（SaaS + Token Wallet Guard + 静态 IP 槽位） | AEOS SPEC 核心观点 4 七轨商业计费 |

---

## 四、复现命令（如需重渲染）

```powershell
# 1) 校验 + 组合质量门禁
node "c:\Users\Administrator\Documents\上线网站开发完成\_external\archify\archify\bin\archify.mjs" validate architecture "docs\archify\youding-aeos.architecture.json" --json

# 2) 渲染 HTML（showcase）
node "c:\Users\Administrator\Documents\上线网站开发完成\_external\archify\archify\bin\archify.mjs" render architecture "docs\archify\youding-aeos.architecture.json" "docs\archify\youding-aeos-architecture.html" --quality showcase

# 3) 视觉校验（需本机 Chrome）
node "c:\Users\Administrator\Documents\上线网站开发完成\_external\archify\archify\bin\archify.mjs" visual-check "docs\archify\youding-aeos-architecture.html" --json
```

---

## 五、后续可选扩展（本次未做，按需追加）

1. **外贸七步闭环数据流图**（`dataflow` 类型）：询盘捕获 → 需求核算 → PI → 定金核销 → 生产跟单 → CI/箱单 → 尾款与物流可查，串 GoodJob 履约表；
2. **DAG 编排生命周期图**（`lifecycle` 类型）：L1 意图分解 → L2 拓扑校验（Kahn/Tarjan 环路拦截）→ 四执行器调度 → 证据回写；
3. **部署拓扑图**：PG@5433 / Redis@6379 / n8n@5678 / 前端 3000·5173 / 后端 8001 的物理部署关系。
