# AI Global Growth OS — 完整开发计划 V1.0

> **项目定位**：以 DeepSeek Harness + Hermes 双层智能编排为核心，构建"产品输入 → 官网生成 → 内容生成 → 多平台分发 → SEO/GEO/AEO → AI获客 → 开发信 → CRM → 成交 → 经验沉淀 → 持续进化"的企业级 AI 商业操作系统。
>
> **核心原则**：模型无关、组件可插拔、租户数据隔离、任务异步化、执行可追踪、失败可恢复、经验可沉淀、版本可升级。

---

## 一、项目总览

### 1.1 系统定位

**ANY PRODUCT / ANY INDUSTRY / ANY COUNTRY / ANY MARKETING CHANNEL / ANY BUSINESS MODEL**

客户只需：产品图片 + 产品资料 + 自然语言需求，系统自动完成从产品理解到成交的全链路。

### 1.2 最终商业闭环

```
产品图片/自然语言 → DeepSeek Harness → Hermes → ECC/Skills/MCP → Agent团队 → DeerFlow深度执行 → n8n自动化 → Browser Runtime → AI官网 → SEO/GEO/AEO → 全球内容分发 → 流量 → Lead → CRM → AI销售 → 成交 → 经验沉淀 → Evolution Engine → 系统进化
```

### 1.3 七种商业模式

| 模式 | 说明 |
|------|------|
| Subscription | SaaS订阅 |
| Usage | 按次付费 |
| Credits | 积分制 |
| API | API调用 |
| Affiliate | 联盟推广 |
| Lead Generation | 线索销售 |
| Advertising | 广告变现 |

---

## 二、技术架构总览

### 2.1 技术栈

| 层级 | 技术选型 |
|------|----------|
| 前端 | Next.js + TypeScript |
| 后端 | Python 3.12 + FastAPI + Pydantic v2 |
| ORM | SQLAlchemy 2.x |
| 数据库 | PostgreSQL 16+ (pgvector) |
| 缓存/队列 | Redis 7+ |
| 对象存储 | S3-compatible / MinIO |
| 可观测性 | OpenTelemetry |
| 测试 | pytest + mypy + ruff |
| 部署 | Docker Compose → K8s |

### 2.2 架构分层

```
┌─────────────────────────────────────────────────────────────┐
│                     Experience Engine                        │
│              (Observes everything, evolves system)           │
└────────────────────┬────────────────────────────────────────┘
                     │ Feedback loops
┌────────────────────▼────────────────────────────────────────┐
│                      Revenue OS                              │
│         (Orchestrates marketing → sales → revenue)           │
└────┬─────────┬──────────┬──────────┬───────────┬───────────┘
     │         │          │          │           │
┌────▼───┐ ┌──▼─────┐ ┌──▼────┐ ┌──▼──────┐ ┌──▼──────┐
│Website │ │  SEO   │ │ Dist. │ │  Lead   │ │   CRM   │
│  Gen   │ │ /GEO   │ │Engine │ │  Gen    │ │ AI Sales│
└────┬───┘ └──┬─────┘ └──┬────┘ └──┬──────┘ └──┬──────┘
     │        │          │          │           │
     └────────┴──────────┴──────────┴───────────┘
                     │
            ┌────────▼───────────┐
            │   Browser Runtime  │
            │    + n8n + DeerFlow│
            └────────┬───────────┘
                     │
            ┌────────▼───────────┐
            │   Agent System     │
            │  (AI orchestration)│
            └────────┬───────────┘
                     │
         ┌───────────┼───────────┐
    ┌────▼────┐ ┌────▼────┐ ┌───▼──────┐
    │ Plugins │ │   MCP   │ │  Skills  │
    └────┬────┘ └────┬────┘ └───┬──────┘
         └───────────┴───────────┘
                     │
            ┌────────▼───────────┐
            │        ECC         │
            │ (Execution Context)│
            └────────────────────┘
```

---

## 三、开发阶段与里程碑

### 第一阶段：底座工程（TASK-001 ~ TASK-013）

**目标**：搭建可运行的系统骨架，跑通"创建租户 → 上传产品 → 创建AI任务 → Hermes调度 → Harness执行 → 生成Trace → 任务完成"完整链路。

#### TASK-001：项目初始化

| 项目 | 内容 |
|------|------|
| 目标 | 搭建项目骨架，FastAPI健康检查通过 |
| 交付 | FastAPI项目结构、pyproject.toml、Makefile、基础配置 |
| 验收 | `GET /health` 返回 `{"status": "ok"}` |

#### TASK-002：多租户系统

| 项目 | 内容 |
|------|------|
| 目标 | 实现Tenant/User/Workspace数据模型与RLS隔离 |
| 交付 | tenants, users, tenant_users, workspaces表 + RLS策略 |
| 验收 | Tenant A数据对Tenant B不可见 |

#### TASK-003：企业私有数据空间

| 项目 | 内容 |
|------|------|
| 目标 | 实现对象存储隔离与资产管理 |
| 交付 | assets表、S3 key规范、上传/下载API |
| 验收 | 文件按tenant_id隔离，Agent无法跨租户访问 |

#### TASK-004：统一事件总线

| 项目 | 内容 |
|------|------|
| 目标 | 实现基于Redis Streams的事件系统 |
| 交付 | EventEnvelope定义、events:global stream、发布/订阅API |
| 验收 | 事件正确发布到stream，消费者可接收 |

#### TASK-005：Outbox模式

| 项目 | 内容 |
|------|------|
| 目标 | 实现数据库与事件发布的一致性 |
| 交付 | outbox_events表、Worker轮询发布、重试机制 |
| 验收 | 业务写入后事件最终一致发布 |

#### TASK-006：认证系统

| 项目 | 内容 |
|------|------|
| 目标 | 实现JWT认证与Session管理 |
| 交付 | 登录/注册API、JWT中间件、Token刷新 |
| 验收 | 未认证请求返回401 |

#### TASK-007：RBAC权限

| 项目 | 内容 |
|------|------|
| 目标 | 实现基于角色的权限控制 |
| 交付 | roles, permissions表、require_permission装饰器 |
| 验收 | 不同角色访问受保护资源正确允许/拒绝 |

#### TASK-008：Task Schema

| 项目 | 内容 |
|------|------|
| 目标 | 定义任务数据模型与约束 |
| 交付 | tasks表、预算字段、DAG支持(parent_task_id) |
| 验收 | 任务CRUD正常，预算字段验证生效 |

#### TASK-009：Task状态机

| 项目 | 内容 |
|------|------|
| 目标 | 实现任务生命周期状态管理 |
| 交付 | 状态定义、转移规则、非法转移拦截 |
| 验收 | 状态按规则流转，非法转移返回TASK_INVALID_STATE |

#### TASK-010：Harness Adapter

| 项目 | 内容 |
|------|------|
| 目标 | 定义DeepSeek Harness统一接口 |
| 交付 | HarnessRuntime Protocol、DeepSeekHarnessAdapter、MockHarness |
| 验收 | 通过Contract Test，Mock可替换真实实现 |

#### TASK-011：Hermes Adapter

| 项目 | 内容 |
|------|------|
| 目标 | 定义内部调度中心接口 |
| 交付 | HermesOrchestrator Protocol、Plan版本化、MockHermes |
| 验收 | Plan生成与Dispatch流程可测试 |

#### TASK-012：Model Gateway

| 项目 | 内容 |
|------|------|
| 目标 | 实现模型无关的调用层 |
| 交付 | ModelAdapter Protocol、ModelGateway、Router、Fallback |
| 验收 | 主模型故障时自动切换到备选模型 |

#### TASK-013：Trace系统

| 项目 | 内容 |
|------|------|
| 目标 | 实现全链路追踪与成本记录 |
| 交付 | traces, trace_spans, model_usage表、OpenTelemetry集成 |
| 验收 | 每个任务拥有完整Trace，Token成本准确记录 |

#### 第一阶段验收清单

- [ ] 项目启动成功
- [ ] PostgreSQL/Redis/MinIO连接正常
- [ ] 创建Tenant/User/Workspace
- [ ] RBAC权限生效
- [ ] 多租户隔离测试通过
- [ ] 资产上传/下载
- [ ] Event写入与Outbox发布
- [ ] Task创建/状态流转
- [ ] 幂等性验证
- [ ] 重试/超时机制
- [ ] Budget Guard触发
- [ ] Harness/Hermes/Mock E2E跑通
- [ ] Trace完整记录
- [ ] 安全测试通过

---

### 第二阶段：智能能力层（TASK-014 ~ TASK-018）

**目标**：构建ECC企业经验中心、Skill技能系统、MCP工具连接、Plugin插件生态、Agent智能员工。

#### TASK-014：ECC 企业经验智能中心

| 项目 | 内容 |
|------|------|
| 目标 | 建立企业AI知识大脑 |
| 核心 | 产品知识 + 行业经验 + 营销策略 + SOP + 成功案例 |
| 数据库 | ecc_knowledge, ecc_sop, ecc_domain_rules, ecc_strategy_memory |
| 技术 | PostgreSQL + pgvector + Embedding + Rerank |
| API | POST /api/ecc/search — 经验检索 |
| 验收 | 输入任务描述，返回相关经验与SOP |

#### TASK-015：Skill 技能系统

| 项目 | 内容 |
|------|------|
| 目标 | 把经验封装成可调用能力 |
| 结构 | metadata.yaml + prompt.md + workflow.json + tools.json |
| 数据库 | skills表（id, name, version, input_schema, output_schema, prompt） |
| 示例 | seo_writer, b2b_email, product_description, youtube_script |
| 能力 | 热更新、版本管理、企业私有Skill |
| API | POST /skill/run — 执行技能 |
| 验收 | 输入产品参数，输出SEO文章/开发信 |

#### TASK-016：MCP 工具连接层

| 项目 | 内容 |
|------|------|
| 目标 | 让Agent连接外部世界 |
| 架构 | Agent → MCP Router → Google/CRM/Payment/Browser/Database |
| 数据库 | mcp_servers表（id, name, endpoint, auth, status） |
| 标准 | 每个MCP提供manifest.json |
| 验收 | Agent可通过MCP调用Google Search/CRM等外部服务 |

#### TASK-017：Plugin 插件系统

| 项目 | 内容 |
|------|------|
| 目标 | 实现"一切皆插件" |
| 类型 | Content/SEO/Video/Browser/Industry/Payment Plugin |
| 生命周期 | Install → Verify → Load → Execute → Monitor → Update |
| 安全 | 沙箱运行、权限控制、独立升级 |
| 验收 | 插件可动态安装/卸载/升级，不影响系统运行 |

#### TASK-018：Agent 智能员工系统

| 项目 | 内容 |
|------|------|
| 目标 | 创建AI员工团队 |
| 角色 | CEO/Marketing/SEO/Sales/Research/Customer Agent |
| 数据库 | agents表（id, tenant_id, name, role, skills, memory_id） |
| 流程 | 用户任务 → Hermes → Agent Planner → Skill选择 → MCP调用 → 执行 → 反馈 |
| API | POST /agent/run — 启动Agent |
| 验收 | Agent可自主规划并执行复杂任务 |

---

### 第三阶段：商业执行层（TASK-019 ~ TASK-023）

**目标**：实现DeerFlow深度执行、n8n自动化、Browser Runtime、AI官网生成、SEO/GEO/AEO优化。

#### TASK-019：DeerFlow 深度执行引擎

| 项目 | 内容 |
|------|------|
| 目标 | 复杂任务执行Agent Runtime |
| 模块 | Task Planner、Executor、Reviewer、Memory Agent |
| 沙箱 | 每租户独立Docker环境 |
| 状态机 | CREATED → PLANNING → EXECUTING → REVIEW → WAIT_HUMAN → DONE |
| 数据库 | deerflow_tasks表 |
| 验收 | 输入产品资料，自动拆解并执行多步骤任务 |

#### TASK-020：n8n 自动化编排

| 项目 | 内容 |
|------|------|
| 目标 | 事件触发 + 外部连接 + 自动化流程 |
| 架构 | Event → n8n → Webhook → Hermes → Agent |
| 场景 | 产品创建→自动建站、新内容→自动分发、Lead→通知销售 |
| 验收 | 事件触发后自动执行后续业务流程 |

#### TASK-021：Browser Runtime

| 项目 | 内容 |
|------|------|
| 目标 | 解决无API平台的自动化 |
| 能力 | 登录、搜索、填写、上传、发布、监控 |
| 技术 | Playwright + Cookie隔离 + Tenant Sandbox |
| 安全 | 域名白名单、操作权限、Human-in-the-loop |
| 验收 | 可自动登录第三方平台并执行操作 |

#### TASK-022：AI Website Generator

| 项目 | 内容 |
|------|------|
| 目标 | 客户上传产品图片+一句话 → 生成品牌官网 |
| 输入 | 产品图片 + 产品参数 + 目标市场 |
| 输出 | 首页、产品页、案例页、博客、FAQ、询盘页、多语言 |
| 流程 | Vision → Product Extraction → Market Analysis → Persona → Brand → Structure → Copy → SEO → UI → Preview → Publish |
| 验收 | 10分钟内生成完整可部署的B2B官网 |

#### TASK-023：SEO/GEO/AEO Engine

| 项目 | 内容 |
|------|------|
| 目标 | 同时优化三种搜索可见性 |
| SEO | 关键词、Title、Meta、文章、内链、Schema |
| GEO | AI搜索引用内容、ChatGPT/Perplexity优化 |
| AEO | FAQ、问答结构、结构化答案 |
| 验收 | 生成内容在SEO/GEO/AEO评分均>80 |

---

### 第四阶段：业务闭环层（TASK-024 ~ TASK-031）

**目标**：实现内容生产、全球分发、Lead获取、CRM、AI销售、收入系统、进化引擎。

#### TASK-024：内容生产系统

| 项目 | 内容 |
|------|------|
| 输入 | 产品资料 |
| 输出 | 文章、视频脚本、图片、社媒帖子、邮件、广告素材 |
| 数据库 | content_assets, content_versions, content_publications |
| 验收 | 一个产品自动生成20+种内容资产 |

#### TASK-025：全球分发系统

| 项目 | 内容 |
|------|------|
| 渠道 | 官网、YouTube、LinkedIn、Facebook、论坛、博客、行业平台 |
| 策略 | 官方API优先 → 合法自动化 → 人工审批 |
| 接口 | DistributionChannel统一接口（validate/publish/status/analytics） |
| 验收 | 内容自动发布到至少5个渠道 |

#### TASK-026：Lead Generation

| 项目 | 内容 |
|------|------|
| 目标 | AI主动寻找客户 |
| 流程 | 目标市场 → 企业数据库 → 客户筛选 → 价值评分 → 销售线索 |
| 评分 | Company Fit + Product Fit + Intent + Engagement + Budget + Geography |
| 分级 | 0-30 Cold / 31-60 Warm / 61-80 MQL / 81-100 SQL |
| 验收 | 自动生成合格Lead并评分 |

#### TASK-027：CRM系统

| 项目 | 内容 |
|------|------|
| 流程 | Lead → MQL → SQL → Opportunity → Deal |
| AI能力 | 分类、跟进、提醒、预测成交概率 |
| 数据库 | leads, contacts, accounts, opportunities, deals |
| 验收 | Lead自动进入正确销售阶段 |

#### TASK-028：AI Sales Agent

| 项目 | 内容 |
|------|------|
| 能力 | 研究客户、生成开发信、发送、回复分析、持续跟进 |
| 合规 | unsubscribe、consregional compliance、sending limits |
| 验收 | 自动生成个性化开发信并处理回复 |

#### TASK-029：Revenue OS

| 项目 | 内容 |
|------|------|
| 目标 | 商业收入操作系统 |
| 连接 | 流量 → Lead → 销售 → 成交 → 续费 → 扩展 |
| 监控 | CAC、LTV、ROI、转化率 |
| 数据库 | billing_accounts, subscriptions, meter_events, invoices |
| 验收 | 七种商业模式统一计费 |

#### TASK-030：Experience Engine

| 项目 | 内容 |
|------|------|
| 目标 | 用户体验学习系统 |
| 记录 | 用户行为、成功路径、失败路径、转化路径 |
| 输出 | Experience Memory |
| 验收 | 每次任务后自动沉淀经验 |

#### TASK-031：Evolution Engine

| 项目 | 内容 |
|------|------|
| 目标 | 最终进化层，系统越用越聪明 |
| 流程 | 数据 → 经验 → Skill优化 → SOP优化 → Agent优化 → 成功率提升 |
| 安全 | Draft → Evaluation → Canary → Approved → Production |
| 验收 | 系统自动发现改进点并安全部署 |

---

## 四、MVP开发顺序

### MVP-1：产品理解 + 官网生成（4-6周）

```
多租户 + 产品上传 + 图片识别 + 自然语言任务 + Harness Adapter + Hermes Adapter + ECC + DeerFlow Adapter
```

**验收标准**：上传产品 → AI理解 → 自动生成官网

### MVP-2：SEO内容资产（3-4周）

```
SEO + GEO + AEO + 内容生成
```

**验收标准**：产品 → 官网 → 搜索内容资产

### MVP-3：自动分发（3-4周）

```
N8N + 多平台发布
```

**验收标准**：官网 → 内容 → 自动分发

### MVP-4：获客闭环（4-6周）

```
Lead + Lead Scoring + CRM + AI开发信
```

**验收标准**：流量 → 客户 → 销售

### MVP-5：商业化（2-3周）

```
Billing + Subscription + Usage + Credits
```

**验收标准**：开始收费

### MVP-6：智能进化（持续）

```
Experience Engine + Evolution Engine
```

**验收标准**：企业私有智能中心形成

---

## 五、代码仓库结构

```
ai-growth-os/
├── apps/
│   ├── api/                    # FastAPI主服务
│   ├── worker/                 # 异步任务Worker
│   ├── scheduler/              # 定时任务调度
│   └── web/                    # Next.js前端
├── services/
│   ├── identity/               # 认证服务
│   ├── tenant/                 # 租户服务
│   ├── task/                   # 任务服务
│   ├── orchestration/          # 编排服务
│   ├── trace/                  # 追踪服务
│   ├── model/                  # 模型网关
│   ├── ecc/                    # 企业经验中心
│   ├── skill/                  # 技能系统
│   ├── mcp/                    # MCP连接层
│   ├── plugin/                 # 插件系统
│   ├── agent/                  # Agent管理
│   ├── product/                # 产品智能
│   ├── website/                # 官网生成
│   ├── content/                # 内容工厂
│   ├── marketing/              # 营销引擎
│   ├── distribution/           # 分发系统
│   ├── lead/                   # 线索获取
│   ├── crm/                    # CRM系统
│   ├── sales/                  # AI销售
│   ├── billing/                # 计费系统
│   ├── analytics/              # 数据分析
│   ├── knowledge/              # 知识管理
│   └── evolution/              # 进化引擎
├── orchestration/
│   ├── harness/                # Harness适配器
│   ├── hermes/                 # Hermes适配器
│   ├── ecc/                    # ECC核心
│   ├── deerflow/               # DeerFlow适配器
│   ├── n8n/                    # N8N适配器
│   └── accio/                  # 浏览器执行器
├── infrastructure/
│   ├── postgres/               # 数据库配置
│   ├── redis/                  # Redis配置
│   ├── object-storage/         # 对象存储
│   ├── vector-db/              # 向量数据库
│   ├── message-queue/          # 消息队列
│   └── observability/          # 可观测性
├── packages/
│   ├── contracts/              # 共享契约
│   ├── events/                 # 事件定义
│   ├── security/               # 安全工具
│   ├── logging/                # 日志工具
│   └── sdk/                    # 客户端SDK
├── migrations/                 # 数据库迁移
├── tests/
│   ├── unit/                   # 单元测试
│   ├── integration/            # 集成测试
│   ├── e2e/                    # 端到端测试
│   ├── security/               # 安全测试
│   └── benchmark/              # 性能测试
└── docs/
    ├── architecture/           # 架构文档
    ├── api/                    # API文档
    ├── plugins/                # 插件文档
    ├── skills/                 # 技能文档
    ├── agents/                 # Agent文档
    └── deployment/             # 部署文档
```

---

## 六、开发规范

### 6.1 Codex硬性规则

| 规则 | 说明 |
|------|------|
| Rule 1 | 任何第三方AI Runtime必须Adapter化 |
| Rule 2 | 所有业务数据必须tenant_id隔离 |
| Rule 3 | 所有Agent任务必须可追踪 |
| Rule 4 | 所有长任务必须支持恢复 |
| Rule 5 | 所有Tool必须拥有权限 |
| Rule 6 | 所有模型调用必须记录成本 |
| Rule 7 | 所有Agent必须限制最大执行次数 |
| Rule 8 | 所有Skill必须版本化 |
| Rule 9 | 所有经验进入知识库前必须经过评估 |
| Rule 10 | AI不得直接修改生产核心配置 |
| Rule 11 | 官方组件升级不能要求重写业务层 |
| Rule 12 | 任何一个组件故障不得导致整个SaaS停摆 |

### 6.2 每个TASK交付格式

```
TASK-ID:
Implemented:
Files changed:
Database migrations:
API changes:
Tests:
Security checks:
Known issues:
Rollback plan:
PASS / FAIL:
```

### 6.3 每完成一个TASK必须执行

1. 编码
2. 单元测试
3. 集成测试
4. 类型检查
5. Lint
6. 安全检查
7. Docker构建
8. API测试
9. 多租户隔离测试
10. 记录变更

---

## 七、Docker Compose开发环境

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: growth_os
      POSTGRES_USER: growth
      POSTGRES_PASSWORD: growth_dev_password
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]

  redis:
    image: redis:7
    ports: ["6379:6379"]

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: minio_dev_password
    ports: ["9000:9000", "9001:9001"]
    volumes: [minio_data:/data]

  api:
    build:
      context: .
      dockerfile: infrastructure/docker/api.Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://growth:growth_dev_password@postgres:5432/growth_os
      REDIS_URL: redis://redis:6379/0
    depends_on: [postgres, redis, minio]
    ports: ["8000:8000"]

  worker:
    build:
      context: .
      dockerfile: infrastructure/docker/worker.Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://growth:growth_dev_password@postgres:5432/growth_os
      REDIS_URL: redis://redis:6379/0
    depends_on: [postgres, redis]

volumes:
  postgres_data:
  minio_data:
```

---

## 八、安全体系

### 8.1 多租户隔离

| 层级 | 机制 |
|------|------|
| API层 | TenantContext注入 |
| Repository层 | 自动过滤tenant_id |
| Database层 | Row Level Security |
| Object Storage | Key前缀隔离 |
| Cache | Key前缀隔离 |
| Event | tenant_id字段 |
| Trace | tenant_id字段 |
| Runtime | Session隔离 |

### 8.2 权限模型

```
platform_admin > tenant_owner > tenant_admin > manager > member > viewer
```

权限格式：`resource.action`（如 `task.create`, `asset.delete`）

### 8.3 Agent执行安全链

```
Agent → Tool Request → Authorization → Policy → Quota/Budget → Runtime → Sandbox → Result
```

禁止：Agent → raw shell / raw database / other tenant filesystem / unscoped browser

---

## 九、可靠性设计

### 9.1 任务保障

| 机制 | 说明 |
|------|------|
| timeout | 默认1800秒 |
| retry | 1s/2s/4s/8s/16s 指数退避 + jitter |
| backoff | 指数退避 |
| idempotency | Idempotency-Key支持 |
| checkpoint | 断点保存 |
| resume | 断点恢复 |
| dead-letter | 超过重试上限进入DLQ |

### 9.2 故障转移

```
Retry → Model Fallback → Skill Fallback → Template Fallback → Human Approval → Failed
```

### 9.3 熔断器

| 组件 | 状态 |
|------|------|
| Harness | CLOSED / OPEN / HALF_OPEN |
| Hermes | CLOSED / OPEN / HALF_OPEN |
| Model Provider | CLOSED / OPEN / HALF_OPEN |
| DeerFlow | CLOSED / OPEN / HALF_OPEN |
| N8N | CLOSED / OPEN / HALF_OPEN |
| Browser Runtime | CLOSED / OPEN / HALF_OPEN |

---

## 十、可观测性

### 10.1 OpenTelemetry字段

```
service.name, service.version, tenant.id, task.id, trace.id, span.id, component, operation
```

### 10.2 核心指标

| 指标 | 说明 |
|------|------|
| task_success_rate | 任务成功率 |
| agent_success_rate | Agent成功率 |
| runtime_error_rate | 运行时错误率 |
| fallback_rate | 降级率 |
| avg_task_latency | 平均任务延迟 |
| avg_task_cost | 平均任务成本 |
| llm_error_rate | LLM错误率 |

### 10.3 Health/Ready

```
GET /health    # 存活检查
GET /ready     # 就绪检查（PostgreSQL/Redis/MinIO/Harness/Model Gateway）
```

---

## 十一、开发时间线（估算）

| 阶段 | 任务范围 | 预估时间 | 里程碑 |
|------|----------|----------|--------|
| 第一阶段 | TASK-001~013 | 6-8周 | 底座跑通，E2E链路验证 |
| 第二阶段 | TASK-014~018 | 4-6周 | 智能能力层完成 |
| 第三阶段 | TASK-019~023 | 6-8周 | 商业执行层完成 |
| 第四阶段 | TASK-024~031 | 8-10周 | 业务闭环完成 |
| **总计** | **TASK-001~031** | **24-32周** | **完整系统上线** |

---

## 十二、最终验收标准

### 12.1 核心链路验收

```
创建Tenant → 创建User → 上传Product → 创建Project → 创建AI Task → Hermes收到Task → Harness创建Runtime → Model Router选择模型 → Agent执行 → 生成Trace → 保存结果 → 任务Completed
```

### 12.2 商业闭环验收

```
客户一句自然语言 + 产品图片 → AI建站 → 内容/视频 → SEO/GEO/AEO → 多平台分发 → 获客 → Lead → CRM → 开发信 → 促单 → 成交 → 数据沉淀 → AI进化
```

### 12.3 多租户安全验收

- Tenant A创建Asset A → Tenant B读取 → DENY
- Tenant A创建Task A → Tenant B查询 → DENY
- Tenant A的Runtime session → Tenant B复用 → DENY

覆盖：API层 + Repository层 + Database RLS + Object Storage + Cache + Event + Trace + Runtime

---

## 十三、最终工程原则

> **技术可以持续变化，业务底座不能被绑定。**

```
Model替换 → Runtime更新 → Skill热更新 → Plugin增加 → MCP增加 → DeerFlow升级 → N8N升级 → Browser Runtime替换
                    ↓
Control Plane不变 / Domain Model不变 / Tenant不变 / CRM不变 / Revenue不变 / Experience不变
```

系统最终追求：

```
一次正确设计底座 → 持续接入新模型 → 持续接入新Agent → 持续接入新Skill → 持续接入新MCP → 持续接入新Plugin → 持续积累真实业务结果 → 持续增强企业私有智能中心
```

---

> **这就是 AI Global Growth OS / 企业私有智能中心的完整开发计划。**
> 
> 客户只需要把产品交给系统，再告诉AI想卖到哪里、卖给谁，系统自动生成官网、内容、视频并进行全球分发，通过SEO/GEO/AEO获取流量和客户，再利用AI拓客、开发信和CRM推动成交；每一次执行和成交又反过来沉淀为企业私有经验，让系统越用越懂企业、越用越聪明、越用越简单。
