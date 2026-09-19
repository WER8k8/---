# 智能驱动链路 · 手动测试流程（Hermes / AEOS）

> 对象：优丁 `main` 上的 **任务面智能驱动**（非 SQL、非暗驱）  
> 原则：像业务员一样在优丁发起任务；观察响应时间、任务中心、错误语义  
> 脚本：`scripts/hermes-drive-chain-manual-e2e.ps1`

---

## 0. 测试前检查（环境）

| # | 步骤 | 期望 |
|---|------|------|
| E1 | 后端 `GET /api/v1/health` | 200 |
| E2 | `GET /api/v1/health/ready` | db/redis ok |
| E3 | 后台 `:5173/`、官网 `:3000/`、任务中心 API 可访问 | 200 |
| E4 | 租户/管理员可登录 | token 正常 |

---

## 1. 场景总表（智能驱动）

| ID | 业务场景 | 手动入口（概念） | API 模拟 | L1 模板 | 成功标准 | 流畅标准 |
|----|----------|------------------|----------|---------|----------|----------|
| S1 | **履约 PI / 七步** | 履约队列→一键履约 | `POST /orchestration/golden-path/fulfillment` | `_fulfillment_graph` | `source=L1`，含 goodjob 节点 | 派发 < 5s；详情可查 |
| S2 | **社媒拓客 WhatsApp** | 社媒拓客→一键触达 | `POST /orchestration/golden-path/outreach` | `_social_outreach_graph` | `trade_ai_agent` 节点 | 同上；无 Key 诚实 failed |
| S3 | **询盘转化** | 询盘→跟进转化 | `POST /orchestration/tasks/from-intent` intent=`询盘转化` | `_inquiry_convert_graph` | L1 + inquiry 节点 | < 5s |
| S4 | **产品上架** | 商品→AI 上架 | intent=`产品上架` | `_product_launch_graph` | product/media/seo 等节点 | < 5s |
| S5 | **市场分析** | 经营→市场分析 | intent=`市场分析` | `_research_analysis_graph` | research 节点 | < 5s |
| S6 | **线索搜索** | 拓客→找线索 | intent=`找线索` | `_lead_generation_graph` | lead/billing 等 | < 5s |
| S7 | **网页取证** | 工具→取证 | intent=`网页取证` | `_browser_evidence_graph` | browser 节点 | < 5s |
| S8 | **智能助手** | UBrain 问答 | intent=`智能助手` | `_ubrain_assistant_graph` | ubrain/ai_engine | < 5s |
| S9 | **AEOS 体检** | 系统体检 | intent=`系统体检` | `_aeos_readiness_graph` | multi-core 节点 | < 5s |
| S10 | **账单/钱包** | 账单体检 | intent=`账单体检` | `_billing_ops_graph` | billing 节点 | < 5s |
| S11 | **合规风险** | 制裁筛查 | intent=`合规筛查` | `_risk_compliance_graph` | compliance 节点 | < 5s |
| S12 | **内容获客/SEO** | 内容获客 | intent=`内容获客` | `_knowledge_seo_graph` | seo/content 节点 | < 5s |
| S13 | **招投标** | 招投标 | intent=`招投标` | `_tender_dealer_graph` | tender 节点 | < 5s |
| S14 | **业务机器人** | 全模块机器人 | intent=`业务机器人` | `_module_robot_graph` | module_matrix 等 | < 5s |
| S15 | **任务中心闭环** | Hermes 任务页 | `GET /orchestration/hermes/tasks` | — | 能看到上述 plan | 列表 < 2s |
| S16 | **任务详情** | 点开 plan | `GET .../hermes/tasks/{plan_id}` | — | 节点状态可读 | < 2s |

---

## 2. 手动操作步骤（以 S1 为例）

1. 浏览器打开 `http://127.0.0.1:5173/login`，账号 `tenant` / `tenant123`  
2. 进入 **履约队列** `/client/queues/fulfillment`  
3. 点 **一键履约 · Hermes**  
4. 记录：是否出现 plan_id 提示、耗时（秒）  
5. 自动/手动进入 **Hermes 任务** `/client/tasks?plan=`  
6. 查看：`graph_source` 是否 L1、节点数、各节点 status  
7. 期望错误（合法）：`goodjob_bridge_disabled` 等 **诚实 failed**，而不是假成功  

S2–S14：在驾驶舱/拓客等入口发起，或统一走 `from-intent` API（脚本模拟）。

---

## 3. 观察指标（流畅 / 快速 / 无错）

| 指标 | 达标 | 记录方式 |
|------|------|----------|
| 拆解成功 | `graph_source ∈ {L1_template, L1_hybrid}` | API 响应 |
| 派发 | `dispatched=true` 或任务中心可见 | API |
| 延迟 | 派发接口 P95 **< 5000ms** | 脚本计时 |
| 任务详情 | HTTP 200 且 nodes 可读 | API |
| 业务错误 | 仅允许 **honest failed/not_configured** | 错误文案 |
| 禁止 | 5xx 裸崩、假 success、路由 404 | 失败即记缺陷 |

---

## 4. 缺陷分级

| 级 | 定义 | 处理 |
|----|------|------|
| P0 | 登录失败、health 挂、L1 无法拆解 | 立即修 |
| P1 | 派发/详情 5xx、任务中心看不到 plan | 当轮修 |
| P2 | 延迟 >5s、文案不诚实、归属错误 | 记录并尽量修 |
| P3 | 外部 Key 缺失导致诚实 failed | **非缺陷** |

---

## 5. 回归命令

```powershell
powershell -File scripts/hermes-drive-chain-manual-e2e.ps1
powershell -File scripts/verify_annex_work_mode.py   # 需在 backend 下用 venv python
```
