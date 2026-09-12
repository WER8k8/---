# 出海营销 SaaS · 全架构思维导图

> **版本**: v2.0
> **日期**: 2026-07-20
> **说明**: 整合 Admin 外壳四层模型、UBrain 超级智能体、Hermes 插件平台、Paperclip Agent 编排的完整架构视图

---

## 架构思维导图

```mermaid
mindmap
  root((出海营销 SaaS 全架构))
    用户接入层
      前端界面
        Web UI
          Nuxt.js 3 SSR
          Vue 3 + TypeScript
          Tailwind CSS
          Shadcn/ui 组件库
        微信小程序
        API 接口
      三角色壳层
        平台超管 /admin
          薄荷绿主题
          租户管理
          AI 中心
          财务面板
        租户 /client
          蓝色主题
          工作台
          询盘管理
          产品中心
        代理 /agent
          青绿色主题
          业绩统计
          佣金管理
          开户管理
      统一外壳 YoudingProLayout
        侧栏导航
        顶栏工具
        标签页管理
        主题切换
      菜单总表 platformShellMenu
        导航算法 shellNavKernel
        高亮规则
        标签页显示
    AI 智能体层
      UBrain 决策中枢
        意图解析器
        任务编排器
        效果追踪器
        Agent 调度中心
          Research Agent
          Execute Agent
          Analyze Agent
      DeerFlow 深度研究引擎
        多Agent协同
        动态任务编排
        多模态处理
        溯源验证
        工具调用生态
          Tavily搜索
          SerpAPI搜索
          Jina Reader
          Python代码解释器
        研究报告输出
          选品报告
          市场洞察
          竞品分析
      AccioWork 电商执行引擎
        选品技能
          智能选品
          以图搜品
          以词找厂
        建站技能
          一键建站
          SEO优化
          多语言支持
        营销技能
          广告生成
          社媒日历
          EDM营销
        供应链技能
          供应商匹配
          合规检查
          物流追踪
      Paperclip Agent 编排层
        组织架构 OrgChart
          CEO / CTO / CMO
          Worker / Reviewer
        心跳调度引擎
          240分钟间隔
          Redis分布式锁
          防重复调度
        预算控制 Budget Guard
          月度积分预算
          已用积分统计
          超支预警
        目标对齐链
          Mission / Project / Task
          层级关联
          进度追踪
        审批门 Approval Gate
          人审确认
          敏感步骤拦截
          审计记录
    平台服务层
      Hermes 插件平台
        旺财插件市场 /client/plugin-market
          市场目录
          已安装插件
          插件安装/启用/执行
        Hermes 插件管理 /api/v1/hermes/plugins
          全量目录
          租户安装表
          插件运行时
        卖货飞轮闭环
          市场研究
          找客画像入库
          编排下一步
          摘要+待确认项
          用户确认发送
          反馈同步
        AI 通道自动对接
          付费通道 paid
          免费 NVIDIA free_nvidia
          自动降级机制
          Token充值流程
      营销专家包 ECC
        营销总控
        SEO专家
        内容专家
        抖音/小红书专家
        合规专家
      线索生成服务
        Reddit线索
        LinkedIn线索
        TikTok线索
        Google搜索
        Quora问答
        WhatsApp号码搜索
    数据与记忆层
      核心数据库
        PostgreSQL
          业务数据
          租户信息
          询盘记录
        Redis
          缓存
          消息队列
          分布式锁
        Qdrant
          向量检索
          嵌入存储
        Neo4j
          知识图谱
          多跳推理
      Mem0 记忆管理层
        用户偏好 短期记忆
        研究历史 中期记忆
        执行结果 长期记忆
      GraphRAG 知识图谱
        供应商→商品→市场→法规→趋势
        关系建模
        可视化
    基础设施层
      API 网关 FastAPI
        JWT 认证
        限流
        路由
        日志监控
      任务队列
        Celery 异步任务
        DeerFlow Jobs 租户任务
        定时调度 07:30 drain
      爬虫引擎
        Playwright
        BeautifulSoup
        网站审计
        Schema标记
      CDN 加速
        Cloudflare
        阿里云CDN
        静态资源缓存
      部署架构
        Docker Compose
        uvicorn 服务
        多实例部署
        Redis Leader选举
```

---

## 架构分层说明

### 第一层：用户接入层
负责用户与系统的交互入口，包含前端界面、三角色壳层和统一外壳框架。核心原则是「菜单只认一份总表」，避免导航错乱。

### 第二层：AI 智能体层
系统的智能核心，包含四个引擎：
- **UBrain**：决策中枢，负责意图解析和任务编排
- **DeerFlow**：深度研究引擎，基于 LangGraph 多 Agent 协作
- **AccioWork**：电商执行引擎，提供 39+ 专业技能包
- **Paperclip**：Agent 编排层，管理组织架构、心跳调度、预算控制

### 第三层：平台服务层
支撑业务运行的核心服务，包括：
- **Hermes**：插件平台和卖货飞轮闭环
- **ECC**：营销专家包（约 12 个角色 prompt）
- **线索生成**：多渠道外贸线索获取

### 第四层：数据与记忆层
负责数据存储和智能记忆：
- **核心数据库**：PostgreSQL、Redis、Qdrant、Neo4j
- **Mem0 记忆**：短期/中期/长期记忆管理
- **GraphRAG**：知识图谱构建与推理

### 第五层：基础设施层
系统运行的基础支撑：
- **API 网关**：FastAPI 认证、限流、路由
- **任务队列**：Celery、DeerFlow Jobs
- **爬虫引擎**：Playwright、BeautifulSoup
- **CDN 加速**：静态资源分发
- **部署架构**：Docker Compose 多实例

---

## 关键数据流

### 研究 → 执行闭环
```
用户需求 → UBrain意图解析 → DeerFlow深度研究 → 研究报告
    ↓
UBrain指令生成 → AccioWork电商执行 → 效果回流 → 优化研究模型
```

### 卖货飞轮
```
① 市场研究 → ② 找客画像入库 → ③ 编排下一步 → ④ 返回副驾待确认
    ↓
⑤ 用户确认发送 → ⑥ 反馈同步 → ⑦ 下一轮循环
```

### AI 通道对接
```
注册开通 → provision_tenant_ai_connect(nvidia)
    ↓
选择大模型平台 → 写入ai_connect → 降级免费NVIDIA
    ↓
Token充值成功 → apply_token_addon → 接通所选平台
```

---

## 技术选型汇总

| 层级 | 技术 | 用途 |
|------|------|------|
| 前端 | Nuxt 3 + Vue 3 + Vite | SSR/SPA 双模式 |
| 后端 | FastAPI + Python 3.11 | API 网关 |
| ORM | SQLAlchemy | 数据库操作 |
| 验证 | Pydantic | 数据验证 |
| 缓存 | Redis 7.2.4 | 缓存/队列/锁 |
| 向量 | Qdrant | 向量检索 |
| 图谱 | Neo4j | 知识图谱 |
| 工作流 | LangGraph | 多 Agent 编排 |
| 爬虫 | Playwright | 浏览器自动化 |
| 队列 | Celery | 异步任务 |
| 组件 | Ant Design Vue 4.x | 后台 UI |
| 样式 | Tailwind CSS | 样式框架 |

---

## 图标映射

| 架构组件 | 图标名称 | 图标组件 |
|----------|----------|----------|
| UBrain | BrainOutlined | ExperimentOutlined |
| DeerFlow | ClusterOutlined | CloudServerOutlined |
| AccioWork | CarryOutOutlined | CarryOutOutlined |
| Paperclip | ApartmentOutlined | TeamOutlined |
| Hermes | RocketOutlined | RocketOutlined |
| 旺财 | TrophyOutlined | TrophyOutlined |
| AI 引擎 | ApiOutlined | ApiOutlined |
| 数据库 | DatabaseOutlined | DatabaseOutlined |
| 缓存 | CloudOutlined | CloudOutlined |
| 爬虫 | SpiderOutlined | BugOutlined |
| 调度器 | CalendarOutlined | CalendarOutlined |
| 飞轮 | SyncOutlined | SyncOutlined |

---

## 相关文档

- [Admin 架构从零说明](ADMIN-ARCHITECTURE-从零说明.md)
- [UBrain 超级智能体架构](UBRAIN_SUPER_AGENT_ARCHITECTURE.md)
- [Hermes 飞轮架构](HERMES-FLYWHEEL-ARCHITECTURE-v1.md)
- [项目概述与架构](0-项目概述与架构.md)
- [图标映射常量](/frontend/admin/src/constants/antIconMap.ts)
- [图标目录常量](/frontend/admin/src/constants/iconCatalog.ts)