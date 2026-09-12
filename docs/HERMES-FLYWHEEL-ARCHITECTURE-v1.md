# Hermes 插件平台 · 架构总览 v1

> **日期**：2026-06-02  
> **状态**：Hermes 完整插件平台 v1（目录 + 安装态 + 运行时 + 双入口 API）  
> **对外**：**旺财插件市场**（`/client/plugin-market` · `/api/v1/wangcai/plugins/*`）  
> **对内**：**Hermes 插件**（`/api/v1/hermes/plugins/*`）  
> **原则**：用户只见财旺/优丁；**不得**出现 DeerFlow、Accio、UBrain 等第三方商标。

---

## 一、对话结论梳理（优化版）

### 1. 我们要做什么

| 目标 | 说明 |
|------|------|
| **自动赚钱闭环** | 研究 → 找客 → 开发信草稿 → 人审外发 → 询盘回流 → 再研究 |
| **人格 + 执行分层** | 前台财旺（人格）· UBrain（产品大脑）· **Hermes（内部调度）** · 研究/执行引擎（内部代号） |
| **Accio 能力** | 复刻 **工作台形态 + 确认门 + 执行链**，不 1:1 复刻国际站私有数据与自动谈价 |
| **体验** | 规则库无数据 → LLM 补充；重复提问 → 跟进话术，不机械复读 |

### 2. 不能做什么（合规）

- 对外宣传、界面文案、接口字段值中 **禁止**：DeerFlow、Accio、AccioWork、LangGraph、字节、阿里 等商标/对标名。  
- 代码与 **内部文档** 可用研发代号；对外统一 **「市场研究 / 获客执行 / 卖货飞轮」**。  
- 不自动外发邮件/改价/扣款；敏感步骤 **人审**。

### 3. Accio 真实差距（诚实）

| Accio 硬能力 | 本系统现状 |
|--------------|------------|
| 国际站选品/广告/RFQ 数据 | ❌ 无合作 API |
| 7×24 邮箱监测 + 自动回复 | ❌ 未做 |
| SMTP 自动发信 | ❌ 未做（仅草稿 + 确认发送记录） |
| 找客实名列表 | ⚠️ 画像模板入库，非爬虫 |
| 工作台 + 任务卡 | ✅ `/client/copilot` + Hermes 工单 |
| 询盘分级/草稿 | ✅ 规则 + 部分 LLM |

### 4. 三层分工（定案）

```text
用户 → 财旺 UI
         → UBrain（意图、记忆、话术、确认门）— 客户面
              → Hermes（巡站/雷达/告警/队列 drain）— 平台运维，对客户不可见
                   → DeerFlow 队列（研究/飞轮）— 租户业务任务，套餐+配额
                   → Accio 对标（找客/开发信）— 租户业务，人审外发
         → 账本：inquiries / prospects / insights / pipeline_runs
```

**高用量边界（2026-06 PM 定案）**

| 组件 | 客户可见 | 定时行为 |
|------|----------|----------|
| UBrain | 是 | 长任务默认 `async` 入队 |
| Hermes | 否 | 15min 巡站+雷达；`lane=ops` 每轮最多 drain 3 条队列 |
| DeerFlow | 能力名「市场研究」 | 07:30 drain；自动入队仅 `pro/enterprise/flagship` 且 `DEERFLOW_SCHEDULE_AUTO_ENQUEUE_ENABLED=true` |
| 多实例 | — | Redis `scheduler:leader:*` 防重复调度 |

---

## 二、全自动闭环（Hermes `closed_loop_v1`）

```text
① 市场研究（brief + 洞察沉淀）
      ↓
② 找客画像入库（buyer_prospect_leads）
      ↓
③ 编排下一步（开发信等，入队 deerflow_jobs）
      ↓
④ 返回副驾：摘要 + 待确认项（不自动外发）
      ↓
⑤ 用户确认后实际发送（本机邮箱/WhatsApp）
      ↓
⑥ 同步反馈（metrics → research_hints）
      ↓
⑦ 下一轮 ①（用户说「跑一轮飞轮」或定时，后续）
```

**触发方式**

- 副驾按钮：「跑一轮飞轮（研究→找客）」→ `POST /api/v1/hermes/flywheel/run`  
- 对话：「跑一轮市场研究并自动找客」→ UBrain 意图 `flywheel_loop` 转 Hermes  

---

## 三、双入口 API

### 旺财插件市场（租户 / 对外）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/wangcai/plugins/marketplace` | 市场目录（仅 public 插件） |
| GET | `/api/v1/wangcai/plugins/installed` | 本租户已安装 |
| POST | `/api/v1/wangcai/plugins/{id}/install` | 安装 |
| PATCH | `/api/v1/wangcai/plugins/{id}/enabled` | 启用/禁用 |
| POST | `/api/v1/wangcai/plugins/{id}/run` | 执行插件 |

### Hermes 插件（对内 / 运维）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/hermes/plugins/catalog` | 全量目录（含 internal.handler） |
| POST | `/api/v1/hermes/plugins/{id}/run` | 同运行时，不脱敏内部字段 |
| GET | `/api/v1/hermes/tenants/{id}/installs` | 租户安装表 |
| POST | `/api/v1/hermes/flywheel/run` | 兼容：= `sales_flywheel_loop` |

目录源：`backend/app/data/hermes_plugin_catalog.json`  
安装表：`hermes_plugin_installs`（迁移 `039`）

UBrain `/ubrain/chat` 保留；推荐新能力 **先注册插件** 再在市场露出。

---

## 四、AI 通道自动对接（充值 · 免费 NVIDIA · Hermes）

客户**无需自行填写 API Key**。平台在环境变量或超管「模型配置」中维护各厂商 Key；租户侧只选大模型平台并充值流量。

| 时机 | 行为 |
|------|------|
| 注册开通 | `provision_tenant_ai_connect(nvidia)` + Hermes 默认插件包 |
| 选择大模型平台 | 立即写入 `ai_connect`；无付费 Key 则降级免费 NVIDIA |
| Token 充值成功 | `apply_token_addon` → 接通所选平台 + Hermes 插件 |
| 副驾 / Hermes 插件执行前 | `ensure_tenant_ai_connectivity`，无记录则自动挂免费 NVIDIA |

**模式**

- `paid`：所选平台已有平台 Key，卖货副驾与旺财插件走该通道扣流量  
- `free_nvidia`：平台内置英伟达 Key，**功能不断档**；对外说明「有免费额度、哪些模型能用以实时为准、速度偏慢；要想获得更好的体验，请充值」  
- `unavailable`：连 NVIDIA 也未配置（仅运维问题）

**对外 API**

- `GET /api/v1/client/ai-connect` — 副驾/插件市场加载时调用（含自动 ensure）  
- 充值页目录 `GET /api/v1/client/ai-traffic-recharge-catalog` — 含 `experience_hint` / `free_nvidia_notice`

实现：`backend/app/services/ai_traffic_connect_service.py`

**定时探测（生产）**

- 默认 **1:00 / 12:00 / 20:00**（`Asia/Shanghai`）自动 ping 各产品场景绑定的英伟达模型  
- **生产部署自动开启**（`ENVIRONMENT=production`），只需配置 `AI_NVIDIA_API_KEY`；部署后约 20 秒首探  
- 显式关闭：`NVIDIA_CUSTOMER_PROBE_SCHEDULER_ENABLED=false`  
- 快照：`nvidia_customer_model_probe_snapshot`；客户侧通过 `nvidia_probe` 字段查看最近可用项  
- 运维：`POST /api/v1/ops/nvidia-customer-probe/run` 或 `scripts/run_ops_jobs.py --job nvidia-probe`

---

## 五、营销专家包（ECC 瘦身，不进对外文案）

生产保留约 12 个角色 prompt（营销总控、SEO、内容、抖音/小红书、合规等），由 UBrain 路由，**不对用户展示角色 ID**。

---

## 六、验收（4 周）

| 项 | 标准 |
|----|------|
| 闭环 | 一键跑通 ①→③，副驾可见步骤与待确认 |
| 脱敏 | 抽检 API/UI 无禁止商标词 |
| 重复问 | 同国出口问题第 2 次为跟进话术 |
| Accio gap | `skill-catalog` 中 partial/gap 不对外宣称「已复刻阿里」 |

---

## 七、相关文件

- 品牌脱敏：`backend/app/services/hermes/brand_guard.py`  
- 闭环执行：`backend/app/services/hermes/flywheel_workflow.py`  
- AI 通道对接：`backend/app/services/ai_traffic_connect_service.py`  
- Accio 对标目录：`backend/app/data/accio_skill_catalog.json`（**内部**）  
- 历史路线：`docs/出海计/Accio-Work对标与复刻路线.md`
