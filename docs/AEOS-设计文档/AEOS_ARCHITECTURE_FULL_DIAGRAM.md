# AEOS 全域系统架构全景图

> 生成时间：2026-09-20
> 用途：系统故障排查、链路追踪、架构优化决策
> 涵盖：八大子系统 + 350+资产 + 全数据流 + 细微组件连接

---

## 完整架构全景图

```mermaid
graph TB
    subgraph "用户接入层"
        A1[官网:3000<br/>Vite运行源<br/>暖米白#f5f4f0/砖橙]
        A2[超管后台:5174<br/>Nuxt3开发源<br/>薄荷绿#4a9b8c]
        A3[SEO管理后台:5173<br/>独立Node系统]
        A4[外贸客户<br/>海外买家]
        A5[销售团队<br/>租户用户]
    end

    subgraph "负载均衡与路由层"
        B1[Nginx/本地代理<br/>生产环境:80/443]
        B2[租户中间件<br/>TenantMiddleware<br/>Host子域解析]
        B3[统一登录<br/>resolve_user_for_unified_login<br/>主库↔SEO矩阵JWT同步]
    end

    subgraph "核心控制面 backend:8001"
        C1[FastAPI主服务<br/>uvicorn run.py入口]
        C2[中间件链<br/>CORS/Session/OTel/租户隔离]
        C3[路由自动发现<br/>150模块/1207+端点<br/>/api/v1/*]
        C4[服务层:42个子系统<br/>660+服务模块]
        C5[模型层:93个ORM<br/>229张PostgreSQL表]
    end

    subgraph "AEOS核心编排层"
        D1[DeepSeek Harness<br/>外层认知沙箱<br/>Cordis JSON-RPC<br/>dsh.exe子进程]
        D2[Hermes Control Plane<br/>受控核心面<br/>DAG Supervisor<br/>JsonPath数据总线<br/>Saga补偿机制]
        D3[DAG Governor<br/>拓扑防爆<br/>DFS环路检测<br/>100节点上限]
    end

    subgraph "四大业务执行器"
        E1[Trade AI Agent<br/>全域社媒拓客<br/>WhatsApp中枢<br/>_external/trade-ai-agent]
        E2[DeerFlow<br/>深度研报/内容工厂<br/>9大意图真执行<br/>services/deerflow]
        E3[GoodJob CRM<br/>7步履约/单证工作室<br/>WhatsApp实时翻译<br/>_external/goodjob-crm]
        E4[Site/Calc Engine<br/>独立站/22参数核价<br/>BOQ标书解析<br/>services/calculators]
    end

    subgraph "350+智能资产网络"
        F1[76业务技能<br/>skills/<br/>SKILL.md frontmatter<br/>PostgreSQL skills表]
        F2[276 AgencyZH角色<br/>_external/agency-agents-zh<br/>细分行业专家人设]
        F3[286 ECC工程SOP<br/>_external/ecc<br/>质量工程门禁]
        F4[PSSP组装协议<br/>Persona⊕Skill⊕SOP⊕Context<br/>动态执行体装配]
    end

    subgraph "异步任务与调度"
        G1[Celery分布式队列<br/>18核心任务注册<br/>3队列:celery/deerflow/cross_border]
        G2[Celery Beat调度器<br/>12/12调度项匹配<br/>定时任务触发]
        G3[APScheduler调度器<br/>rank/geo/hermes_patrol<br/>ops_autopilot/daily_cycle]
    end

    subgraph "取证与出站分发"
        H1[Browser Runtime<br/>无头浏览器沙箱<br/>Playwright执行]
        H2[双轨取证系统<br/>Disk JSONL<br/>DB TaskTrace.artifacts]
        H3[n8n工作流引擎<br/>localhost:5678<br/>Docker容器]
        H4[出站Webhook<br/>site-built-notify<br/>content-publish-dispatch]
    end

    subgraph "数据存储层"
        I1[PostgreSQL 15.8<br/>localhost:5433<br/>229表/单head 105]
        I2[Redis 5.0<br/>localhost:6379<br/>缓存/会话/队列]
        I3[MinIO对象存储<br/>9000/9001<br/>文件/图片/单证]
        I4[Qdrant向量库<br/>6333<br/>AI知识库向量]
    end

    subgraph "外部记忆与知识"
        J1[Obsidian第二大脑<br/>NTFS Junction直通<br/>C:\Users\Administrator\Documents\Obsidian Vault]
        J2[工作区记忆<br/>.workbuddy/memory/<br/>跨会话上下文]
        J3[文档中心<br/>00-文档中心/<br/>审计/方案/交付]
    end

    subgraph "外贸7步履约闭环"
        K1[询盘捕获<br/>Inquiry<br/>海外买家RFQ]
        K2[需求核算<br/>BOQ解析<br/>22参数核价]
        K3[形式发票<br/>PI Generator<br/>智能生成PDF/Excel]
        K4[定金核销<br/>支付验证<br/>PAYMENT_STRICT_VERIFY]
        K5[生产跟单<br/>订单跟踪<br/>状态更新]
        K6[发运单证<br/>CI/PL<br/>报关草单/产地证]
        K7[尾款物流<br/>追踪回执<br/>双轨证据链]
    end

    subgraph "SEO/GEO获客副线"
        L1[AI内容生成<br/>内容母版<br/>EEAT优化]
        L2[SEO优化<br/>GEO引擎<br/>Schema标记]
        L3[统一发布台<br/>40+平台分发<br/>Celery worker]
        L4[流量回流<br/>归因分析<br/>询盘转化]
    end

    subgraph "商业计费三轨"
        M1[SaaS订阅<br/>基础/专业/旗舰<br/>年费计费]
        M2[AI Token计量<br/>Token Wallet Guard<br/>实时拦截]
        M3[静态IP槽位<br/>EgressEndpoint<br/>指纹租借]
    end

    %% 主要数据流连接
    A1 -->|HTTP Cookie/Bearer| B1
    A2 -->|HTTP Cookie/Bearer| B1
    A3 -->|HTTP JWT mid| B1
    B1 --> B2
    B2 --> B3
    B3 --> C1

    C1 --> C2
    C2 --> C3
    C3 --> C4
    C4 --> C5

    C4 --> D1
    D1 -->|TaskGraph Spec| D2
    D2 --> D3
    D3 -->|契约分发<br/>hermes_node:executor| E1
    D3 -->|契约分发<br/>hermes_node:executor| E2
    D3 -->|契约分发<br/>hermes_node:executor| E3
    D3 -->|契约分发<br/>hermes_node:executor| E4

    E1 --> F4
    E2 --> F4
    E3 --> F4
    E4 --> F4

    F4 --> F1
    F4 --> F2
    F4 --> F3

    C4 --> G1
    G1 --> G2
    C4 --> G3

    E1 --> H1
    H1 --> H2
    C4 --> H3
    H3 --> H4

    C5 --> I1
    C4 --> I2
    C4 --> I3
    C4 --> I4

    D1 --> J1
    C4 --> J2
    J1 --> J3

    A4 --> K1
    K1 --> K2
    K2 --> K3
    K3 --> K4
    K4 --> K5
    K5 --> K6
    K6 --> K7

    L1 --> L2
    L2 --> L3
    L3 --> L4
    L4 --> K1

    K7 --> M1
    C4 --> M2
    C4 --> M3

    %% 外部系统连接
    E1 -->|社媒API<br/>WhatsApp Business API| 外部社媒平台[(40+社媒平台)]
    E3 -->|Baileys协议<br/>3100 API/5193 UI| WhatsApp[WhatsApp Web]
    H4 -->|Webhook触发| 外部发布平台[(40+发布平台)]
```

---

## 细微组件详细连接图

### 1. Hermes DAG编排核心连接

```mermaid
graph LR
    A[DeepSeek Harness<br/>意图解析] -->|TaskGraph Spec JSON| B[Hermes DAG Supervisor]
    B -->|拓扑防爆<br/>DFS环路检测| C[DAG Governor]
    C -->|通过| D[ExecutorRegistry]
    D -->|JsonPath数据总线| E[accio执行器]
    D -->|JsonPath数据总线| F[deerflow执行器]
    D -->|JsonPath数据总线| G[trade_ai_agent执行器]
    D -->|JsonPath数据总线| H[goodjob_crm执行器]
    E --> I[PSSP组装<br/>Persona⊕Skill⊕SOP]
    F --> I
    G --> I
    H --> I
    I --> J[350+资产库<br/>76技能+276角色+286 SOP]
    J --> K[执行结果反馈]
    K -->|Saga补偿| B
```

### 2. Trade AI Agent内部组件连接

```mermaid
graph TB
    A[社媒爬虫Scraper] -->|潜客数据| B[潜客雷达探测<br/>prospect.scrape]
    B --> C[多通道冷触达<br/>outreach.whatsapp/email]
    C -->|Baileys协议| D[WhatsApp批量外联]
    C -->|SMTP| E[邮件序列发送]
    D --> F[统一收件箱<br/>inbox.classify]
    E --> F
    F -->|LangGraph| G[意图分类器]
    G -->|RFQ/询盘| H[CRM商机建档]
    G -->|Sample Request| I[样品履约流转]
    G -->|General Inquiry| J[AI辅助回复]
    G -->|Opt-Out| K[黑名单终止]
```

### 3. GoodJob CRM履约闭环连接

```mermaid
graph TB
    A[WhatsApp Plugin<br/>Node.js @3100] -->|Baileys协议| B[WhatsApp Web]
    A -->|实时消息| C[双向翻译引擎]
    C -->|买家母语→中文| D[卖家销售端]
    C -->|中文→买家母语| B
    D --> E[CRM 7步漏斗<br/>Inquiry→Fulfillment]
    E --> F[PI Generator<br/>形式发票生成器]
    F -->|PDF/Excel| G[买家签署转款]
    G --> H[支付验证<br/>PAYMENT_STRICT_VERIFY]
    H --> I[Trade Docs Studio<br/>单证工作室]
    I --> J[商业发票CI]
    I --> K[装箱单PL]
    I --> L[报关草单]
    I --> M[产地证草案]
```

### 4. Browser Runtime双轨取证连接

```mermaid
graph TB
    A[Playwright无头沙箱] -->|页面交互| B[网络请求拦截]
    B --> C[状态码记录]
    B --> D[控制台日志]
    B --> E[页面截图]
    C --> F[Disk JSONL<br/>audit.jsonl]
    D --> F
    E --> F
    F --> G[磁盘审计轨]
    C --> H[PostgreSQL<br/>task_traces.artifacts]
    D --> H
    E --> H
    H --> I[数据库快照轨]
    G --> J[审计数据与商机<br/>实体强绑定]
    I --> J
```

### 5. 数据库连接拓扑

```mermaid
graph TB
    A[PostgreSQL 15.8<br/>localhost:5433] -->|229表| B[核心业务表]
    A -->|93个ORM模型| C[backend/app/models]
    B --> D[ai_tasks<br/>Hermes状态机]
    B --> E[inquiries<br/>询盘数据]
    B --> F[companies<br/>公司主数据]
    B --> G[skills<br/>76技能入库]
    B --> H[evolution_experiences<br/>经验进化库]
    B --> I[meter_events<br/>计费事件溯源]
    B --> J[task_traces<br/>执行追踪]
    C --> K[Alembic迁移<br/>单head 105]
```

---

## 缺失的串联环节分析

### 🔴 识别到的关键缺失连接

#### 1. **Trade AI Agent → Hermes 缺少正式适配器**
- **现状**：`AEOS_GLOBAL_SYSTEM_REGISTRY.json` 显示 Trade AI Agent 状态为 `ready_for_adapter`
- **缺失**：缺少 `hermes_node:trade_ai_agent` 的正式适配器实现
- **影响**：无法通过 Hermes DAG 正式调度 Trade AI Agent 的能力
- **建议**：在 `backend/app/services/hermes/executors/` 下创建 `trade_ai_agent_adapter.py`

#### 2. **GoodJob CRM → Hermes 缺少正式适配器**
- **现状**：`AEOS_GLOBAL_SYSTEM_REGISTRY.json` 显示 GoodJob CRM 状态为 `ready_for_adapter`
- **缺失**：缺少 `hermes_node:goodjob_crm` 的正式适配器实现
- **影响**：无法通过 Hermes DAG 正式调度 GoodJob CRM 的履约能力
- **建议**：在 `backend/app/services/hermes/executors/` 下创建 `goodjob_crm_adapter.py`

#### 3. **WhatsApp Plugin → 核心后端 缺少事件总线集成**
- **现状**：WhatsApp Plugin 独立运行在 Node.js @3100，与主后端缺少实时事件同步
- **缺失**：缺少 WebSocket/SSE 事件总线将 WhatsApp 消息实时推送到主后端
- **影响**：CRM 系统无法实时感知 WhatsApp 消息，存在数据同步延迟
- **建议**：实现 WebSocket 服务或使用 Redis Pub/Sub 进行消息同步

#### 4. **Browser Runtime → 证据分析 缺少自动化分析管道**
- **现状**：双轨取证系统收集了证据，但缺少自动化分析
- **缺失**：缺少证据自动分析、异常检测、合规性检查的自动化管道
- **影响**：收集的证据需要人工分析，无法自动发现异常行为
- **建议**：在 `services/browser_runtime/` 下添加 `evidence_analyzer.py`

#### 5. **Experience Engine → 业务决策 缺少反馈闭环**
- **现状**：进化引擎收集了经验数据，但缺少与业务决策的自动反馈
- **缺失**：缺少将进化经验自动应用到业务策略的闭环机制
- **影响**：经验数据无法自动优化业务策略
- **建议**：实现 `services/evolution/feedback_loop.py` 自动应用经验

#### 6. **SEO/GEO内容 → 官网发布 缺少自动化部署**
- **现状**：内容生成和发布分离，缺少自动化部署到官网的流程
- **缺失**：缺少内容自动部署到官网 Vite 运行源的 CI/CD 流程
- **影响**：内容发布需要手动操作，效率低下
- **建议**：实现内容自动部署管道，集成到 n8n 工作流

---

## 建议的优先级修复方案

### P0 (立即修复)
1. **实现 Trade AI Agent Hermes 适配器**
2. **实现 GoodJob CRM Hermes 适配器**
3. **WhatsApp Plugin 事件总线集成**

### P1 (近期修复)
4. **Browser Runtime 证据分析管道**
5. **Experience Engine 反馈闭环**

### P2 (中期优化)
6. **SEO/GEO 内容自动部署**
7. **统一监控告警系统**

---

## 关键端口和服务清单

| 端口 | 服务 | 状态 | 依赖 |
|------|------|------|------|
| 3000 | 官网 (Vite运行源) | 🟢 活跃 | PostgreSQL 5433 |
| 5173 | SEO管理后台 | 🟢 活跃 | MySQL (seo-backend) |
| 5174 | 超管后台 | 🟢 活跃 | PostgreSQL 5433 |
| 5678 | n8n工作流引擎 | 🟢 活跃 | Docker |
| 5433 | PostgreSQL 15.8 | 🟢 活跃 | 原生安装 |
| 6379 | Redis 5.0 | 🟢 活跃 | 原生安装 |
| 3100 | WhatsApp Plugin API | 🟡 待集成 | Node.js |
| 5193 | WhatsApp Plugin UI | 🟡 待集成 | Node.js |
| 8001 | 主后端API | 🟢 活跃 | PostgreSQL + Redis |
| 9000/9001 | MinIO对象存储 | 🟢 活跃 | Docker |
| 6333 | Qdrant向量库 | 🟢 活跃 | 配置项 |

---

## 故障排查决策树

当系统出现问题时，按以下顺序排查：

1. **检查基础服务**：PostgreSQL @5433、Redis @6379、n8n @5678
2. **检查核心后端**：FastAPI @8001 日志、中间件链、租户解析
3. **检查编排层**：Hermes DAG 状态、DAG Governor 日志
4. **检查执行器**：对应执行器的适配器状态、PSSP 组装
5. **检查数据流**：JsonPath 数据总线、Saga 补偿机制
6. **检查取证系统**：Disk JSONL、DB TaskTrace 双轨
7. **检查外部连接**：WhatsApp Plugin、社媒API、发布平台

---

**文档维护**：当架构发生变更时，请及时更新此文档以保持与实际系统的一致性。
