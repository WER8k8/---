# WhatsFinds AI 与 YouDing 融合优化分析 — 思维导图报告

> 生成时间：2026-07-20 | 基于官网 https://whatsfinds.com/ 与系统结构探索

```mermaid
mindmap
  root((外贸AI获客<br/>三足鼎立<br/>融合优化))
    GoodJob CRM
      定位[团队销售管理+知识赋能]
      核心[客户/商机/知识库/考试/竞品/案例/问题]
      执行[规则驱动待办+SOP]
      触达[邮件+企微]
      数据权[企业级RBAC]
      亮点[知识-考试-复训闭环/竞品打法卡/案例库/问题复盘]
    WhatsFinds AI
      定位[个人/小团执行工作台]
      核心[用户自带Key/模型/邮箱/数据完全自主]
      执行[4 Agent线性流:搜/像/写/追]
      触达[邮件全链路追踪:像素/点击/回复]
      数据权[用户级完全自主]
      亮点[搜索语法预览/证据链/评分雷达/变量注入/A-B版本/设备授权]
    YouDing 优丁
      定位[GEO/SEO技术平台+内容获客]
      核心[22源雷达+13战术写作+2800县矩阵+收录监控]
      执行[Hermes调度+跨租户学习]
      触达[邮件+询盘归因+自动谈判]
      数据权[多租户隔离+行业知识共享]
      亮点[GEO技术护城河/询盘全链路归因/内容反馈闭环]
    融合策略
      核心洞察[外贸团队不需要更多数据,而需要把自己的Key/模型/邮箱/数据跑通在一个工作台里]
      YouDing提供[高质量种子源+策略大脑+多租户隔离]
      吸收WhatsFinds[工作台交互+Agent编排+用户自带资产]
      产出[GEO驱动的AI外贸工作台:平台+工作台双引擎]
    P0_本周落地
      P0-1[搜索语法实时预览组件]
      P0-2[用户级Key/模型/邮箱配置页]
      P0-3[证据链可视化组件]
      P0-4[评分雷达图组件]
      P0-5[多标签任务栏增强]
    P1_两周内
      P1-1[搜客执行台单页聚合]
      P1-2[AI写信工作台]
      P1-3[邮件追踪像素服务]
      P1-4[画像评分维度拆解]
      P1-5[设备指纹+授权码体系]
    P2_月度规划
      P2-1[Agent化重构Hermes]
      P2-2[跨租户种子源共享]
      P2-3[私有化部署包]
      P2-4[WhatsApp/LinkedIn触达插件]
    终极形态
      上游能力层
        GEO雷达22源
        写作策略13战术
        县域矩阵2800
        收录监控闭环
        跨租户学习
        询盘归因谈判
      执行工作台层
        搜客执行台
        AI写信台
        线索管理台
        邮件追踪台
        用户自带资产配置
      基础设施层
        多租户+设备指纹
        Agent编排总线
        私有化部署包
        多渠道触达插件
```

---

## 📊 核心差异化矩阵 (可视化对比)

```mermaid
quadrantChart
    title 外贸AI获客三产品能力象限
    x-axis 执行层闭环程度 --> 策略/技术深度
    y-axis 数据自主权低 --> 数据自主权高
    quadrant-1 用户自主执行
    quadrant-2 平台级深度+自主
    quadrant-3 平台级深度
    quadrant-4 基础执行
    "WhatsFinds AI": [0.85, 0.9]
    "YouDing 优丁": [0.9, 0.4]
    "GoodJob CRM": [0.6, 0.3]
    "理想融合态": [0.95, 0.85]
```

---

## 🎯 P0-P2 优化路线图甘特图

```mermaid
gantt
    title YouDing 融合 WhatsFinds 优化路线图
    dateFormat  YYYY-MM-DD
    axisFormat  %m/%d
    todayMarker stroke-width:2,stroke:red

    section P0 本周立竿见影
    搜索语法预览组件        :p0-1, 2026-07-21, 2d
    用户级AI配置页          :p0-2, 2026-07-21, 3d
    证据链可视化组件        :p0-3, 2026-07-23, 2d
    评分雷达图组件          :p0-4, 2026-07-23, 1d
    多标签任务栏增强        :p0-5, 2026-07-21, 2d

    section P1 两周补齐短板
    搜客执行台单页聚合      :p1-1, after p0-1, 5d
    AI写信工作台            :p1-2, after p0-2, 5d
    邮件追踪像素服务        :p1-3, 2026-07-28, 5d
    画像评分维度拆解        :p1-4, after p0-4, 3d
    设备指纹+授权码体系     :p1-5, 2026-07-28, 5d

    section P2 月度构建护城河
    Agent化重构Hermes       :p2-1, 2026-08-04, 10d
    跨租户种子源共享        :p2-2, 2026-08-11, 7d
    私有化部署包            :p2-3, 2026-08-18, 7d
    多渠道触达插件          :p2-4, 2026-08-25, 7d
```

---

## 🔄 WhatsFinds 4 Agent 线性流 vs YouDing Hermes 融合架构

```mermaid
flowchart TB
    subgraph WF[WhatsFinds 4 Agent 线性流]
        A1[搜客 Agent<br/>意图拆解+Serper+去重+证据链] --> A2[画像 Agent<br/>爬取+提取+评分4维]
        A2 --> A3[写信 Agent<br/>模版库+变量注入+A/B]
        A3 --> A4[追踪 Agent<br/>像素/点击/回复/分类]
    end

    subgraph YD[YouDing Hermes 调度器]
        B1[GEO雷达 22源] --> B2[策略大脑 13战术]
        B2 --> B3[SEO矩阵 2800县]
        B3 --> B4[收录监控 反馈闭环]
        B4 --> B5[跨租户学习]
        B5 --> B6[询盘归因 谈判]
    end

    subgraph FUSION[融合架构: Agent Protocol 总线]
        direction TB
        C1[统一 AgentProtocol 接口]
        C2[用户自带资产注入<br/>Key/模型/邮箱/数据]
        C3[执行编排层<br/>Hermes -> 4 Agent]
        C4[上游能力注入<br/>GEO种子/策略库/评分引擎]
    end

    A1 -.->|注入 GEO种子源| C4
    A2 -.->|复用 统一评分引擎| C4
    A3 -.->|调用 13战术模版库| C4
    A4 -.->|接入 归因/谈判闭环| C4
    B6 -.->|下发 执行任务| C3
```

---

## 🧩 关键组件清单 (前端新增)

```mermaid
graph TD
    COMP[前端新增组件<br/>frontend/components/whatsfinds/]
    COMP --> UI1[SearchSyntaxPreview.vue<br/>搜索语法实时预览]
    COMP --> UI2[EvidenceChain.vue<br/>证据链时间轴]
    COMP --> UI3[ScoreRadar.vue<br/>评分雷达图 ECharts]
    COMP --> UI4[VariablePicker.vue<br/>写信变量插入器 @唤起]
    COMP --> UI5[OutreachEditor.vue<br/>AI写信工作台 Tiptap]
    COMP --> UI6[EmailVersionTabs.vue<br/>邮件版本对比 Tab]
    COMP --> UI7[EmailPreviewModal.vue<br/>发送前渲染预览]
    COMP --> UI8[TrackingPixelGenerator.vue<br/>像素生成/嵌入]
    COMP --> UI9[DeviceFingerprintBanner.vue<br/>未授权顶栏提示]
    COMP --> UI10[LicenseActivationForm.vue<br/>授权码激活表单]

    PAGE[页面路由新增]
    PAGE --> PG1[/workspace/prospecting<br/>搜客执行台单页]
    PAGE --> PG2[/workspace/outreach<br/>AI写信工作台]
    PAGE --> PG3[/admin/ai-provider-config<br/>用户级AI配置]
    PAGE --> PG4[/system/license<br/>授权/设备管理]
```

---

## 🗄️ 后端模型/服务/路由清单

```mermaid
graph LR
    MODEL[新增模型 models/]
    MODEL --> M1[ai_provider_config.py<br/>用户级Key/模型/邮箱]
    MODEL --> M2[prospect_lead.py<br/>潜在客户+evidence_chain]
    MODEL --> M3[email_tracking_event.py<br/>打开/点击/回复事件]
    MODEL --> M4[license_code.py<br/>授权码/设备/订单]
    MODEL --> M5[device_fingerprint.py<br/>设备指纹]

    SVC[新增服务 services/]
    SVC --> S1[search_agent.py<br/>意图拆解+Serper+去重]
    SVC --> S2[profile_agent.py<br/>爬取+提取+4维评分]
    SVC --> S3[write_agent.py<br/>模版库+变量注入+模型]
    SVC --> S4[track_agent.py<br/>像素回调+IMAP+分类]
    SVC --> S5[email_tracking_service.py<br/>像素路由/事件持久化]
    SVC --> S6[license_service.py<br/>激活/续费/设备绑定]
    SVC --> S7[variable_resolver.py<br/>写信变量解析]

    ROUTE[新增路由 api/v1/routes/]
    ROUTE --> R1[workspace_prospecting.py]
    ROUTE --> R2[workspace_outreach.py]
    ROUTE --> R3[email_tracking.py]
    ROUTE --> R4[ai_provider_config.py]
    ROUTE --> R5[license.py]

    PROTO[Agent 协议 agents/]
    PROTO --> P1[agent_protocol.py<br/>统一接口定义]
```

---

## 💡 一页总结：三大核心行动

| 🎯 **核心洞察** | 📦 **融合产出** | 🚀 **下一步** |
|---|---|---|
| 外贸团队要的是**把自己的 Key/模型/邮箱/数据跑通在一个工作台** | **GEO驱动的 AI 外贸工作台**<br/>平台能力 + 执行工作台 双引擎 | **本周**：P0 五项组件并行开发<br/>**两周**：P1 搜客执行台+写信台+追踪像素<br/>**月度**：P2 Agent化重构+私有化部署 |

---

## 📎 附件引用
- 详细分析文档：[WHATSFINDS_AI_ANALYSIS.md](WHATSFINDS_AI_ANALYSIS.md)
- GoodJob CRM 分析：对话历史中已完成
- YouDing 现状基线：对话历史中 80% 覆盖率分析

---

> **使用说明**：此思维导图报告可直接导入 Notion/Obsidian/XMind 等工具，或用 Mermaid Live Editor 渲染交互式图表。