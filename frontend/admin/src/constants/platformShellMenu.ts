/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** Platform 超管侧栏菜单 SSOT — 与 check-nav-routes / Nav Kernel 对齐 */
import type { ShellMenuGroup } from '@/types/shellNav';
import { PLATFORM_OPS_ALWAYS_VISIBLE } from '@/constants/stubVisibility';

export type PlatformMenuNavItem = ShellMenuGroup['children'][number];

/** 司令部运维页（含挣钱大赛）— admin 角色也保留，不随「超级管理工具」整组隐藏 */
export function getPlatformOpsMenuItems(): PlatformMenuNavItem[] {
  const superGroup = PLATFORM_SHELL_MENU.find((g) => g.title === '超级管理工具');
  if (!superGroup?.children?.length) return [];
  return superGroup.children.filter((item) =>
    PLATFORM_OPS_ALWAYS_VISIBLE.some(
      (p) => item.path === p || item.path.startsWith(`${p}/`),
    ),
  );
}

export const PLATFORM_SHELL_MENU: ShellMenuGroup[] = [
  { title: '总览', children: [
    { name:'Dashboard',path:'/dashboard',title:'数据看板',icon:'DashboardOutlined' },
    { name:'OperationsTrafficBoard',path:'/operations/traffic',title:'流量看板',icon:'LineChartOutlined' },
  ]},
  { title: '业务管理', children: [
    // 功能域（无特权）：与其它业务项同级，非「附属执行台」
    { name:'SocialOutreach',path:'/sales/customer-finder',title:'社媒拓客',icon:'GlobalOutlined' },
    { name:'TradeFulfillment',path:'/admin/queues/fulfillment',title:'外贸履约',icon:'CarryOutOutlined' },
    { name:'Products',path:'/products',title:'产品管理',icon:'ShoppingOutlined' },
    { name:'VideoSpace',path:'/admin/video-space',title:'视频空间',icon:'VideoCameraOutlined' },
    { name:'Categories',path:'/products/categories',title:'分类管理',icon:'FolderOpenOutlined' },
    { name:'Content',path:'/content',title:'文章内容',icon:'FileOutlined' },
    { name:'Cases',path:'/cases',title:'案例展示',icon:'PictureOutlined' },
    { name:'News',path:'/news',title:'新闻动态',icon:'ReadOutlined' },
    // 功能域菜单（无特权）：与其它业务项同级，非「附属执行台」
  ]},
  { title: '客户线索', children: [
    { name:'Inquiries',path:'/inquiries',title:'询盘留言',icon:'MessageOutlined' },
  ]},
  { title: '智能销售', children: [
    { name:'Sales',path:'/sales/dashboard',title:'销售工作台',icon:'DashboardOutlined' },
    { name:'CustomerFinder',path:'/sales/customer-finder',title:'客户开发',icon:'UserAddOutlined' },
    { name:'AutoNegotiator',path:'/sales/auto-negotiator',title:'自动谈单',icon:'MessageOutlined' },
    { name:'EmailAutomation',path:'/sales/email-automation',title:'开发信管理',icon:'MailOutlined' },
  ]},
  { title: '网站优化', children: [
    { name:'SEO',path:'/seo',title:'SEO总览',icon:'SearchOutlined' },
    { name:'BuildingWiki',path:'/seo/building-wiki',title:'AI建材百科',icon:'ReadOutlined' },
    { name:'ContentOptimizer',path:'/seo/content-optimizer',title:'AI内容优化',icon:'HighlightOutlined' },
    { name:'KeywordRanking',path:'/seo/keyword-ranking',title:'关键词排名',icon:'LineChartOutlined' },
    { name:'BaiduTools',path:'/seo/baidu-tools',title:'百度站长工具',icon:'SearchOutlined' },
    { name:'SiteAudit',path:'/seo/site-audit',title:'站点体检',icon:'AuditOutlined' },
    { name:'SEOMatrixKeywords',path:'/seo-matrix/keywords',title:'矩阵词管理',icon:'CopyOutlined' },
    { name:'SEOMatrixPublish',path:'/seo-matrix/publish',title:'多平台发布',icon:'SendOutlined' },
  ]},
  { title: '代理中心', children: [
    { name:'AgentPerformance',path:'/agent/performance',title:'业绩看板',icon:'DashboardOutlined' },
    { name:'AgentTrafficBoard',path:'/agent/traffic',title:'流量看板',icon:'LineChartOutlined' },
    { name:'AgentCommission',path:'/agent/commission',title:'佣金管理',icon:'DollarOutlined' },
    { name:'AgentAccountOpening',path:'/agent/account-opening',title:'客户开户',icon:'UserAddOutlined' },
    { name:'AgentDailyReport',path:'/agent/daily-report',title:'经营日报',icon:'FileTextOutlined' },
    { name:'AgentChurnWarning',path:'/agent/churn-warning',title:'流失预警',icon:'AlertOutlined' },
  ]},
  { title: '系统', children: [
    { name:'Users',path:'/users',title:'账户管理',icon:'UserOutlined' },
    { name:'Settings',path:'/settings',title:'系统设置',icon:'SettingOutlined' },
    { name:'AiConfig',path:'/ai-config',title:'AI配置',icon:'ApiOutlined' },
    { name:'RecycleBin',path:'/admin/recycle-bin',title:'回收站',icon:'DeleteOutlined' },
    { name:'Onboarding',path:'/admin/onboarding',title:'入驻引导',icon:'RocketOutlined' },
  ]},
  { title: '呼朋唤友', children: [
    { name:'ReferralDashboard',path:'/referral',title:'我的邀请',icon:'TeamOutlined' },
    { name:'ReferralRules',path:'/referral/rules',title:'活动规则',icon:'FileTextOutlined' },
  ]},
  { title: '获取SaaS服务', children: [
    { name:'TenantRegister',path:'/tenants/register',title:'注册开通',icon:'UserAddOutlined' },
  ]},
  { title: '海外采销', children: [
    { name:'IntlDashboard',path:'/international',title:'采集概览',icon:'DashboardOutlined' },
    { name:'IntlInquiries',path:'/international/inquiries',title:'海外询盘',icon:'MessageOutlined' },
    { name:'IntlSites',path:'/international/sites',title:'目标网站',icon:'GlobalOutlined' },
  ]},
  { title: '财务板块', children: [
    { name:'AdminFinance',path:'/admin/finance',title:'财务概览',icon:'AccountBookOutlined' },
    { name:'AdminFinancePaymentOps',path:'/admin/finance/payment-ops',title:'支付码与接口',icon:'PayCircleOutlined' },
    { name:'AdminFinancePaymentOrders',path:'/admin/finance/payment-orders',title:'租户支付订单',icon:'OrderedListOutlined' },
    { name:'AdminFinanceIpPool',path:'/admin/finance/ip-pool',title:'静态 IP 池',icon:'GlobalOutlined' },
    { name:'AdminFinanceInvoices',path:'/admin/finance/invoices',title:'开票审核',icon:'FileTextOutlined' },
    { name:'AdminFinanceCommissions',path:'/admin/finance/commissions',title:'分润结算',icon:'DollarOutlined' },
    { name:'AdminFinanceCommissionRules',path:'/admin/finance/commission-rules',title:'分润规则',icon:'SettingOutlined' },
  ]},
  { title: '超级管理工具', children: [
    { name:'AdminHub',path:'/admin',title:'超管工作台',icon:'CrownOutlined' },
    { name:'AdminAggregation',path:'/admin/aggregation',title:'数据中心',icon:'BarChartOutlined' },
    { name:'AdminAttribution',path:'/admin/attribution',title:'全链路归因',icon:'FunnelPlotOutlined' },
    { name:'AdminTrafficBoard',path:'/admin/traffic-board',title:'全平台流量',icon:'LineChartOutlined' },
    // --- 治理收口（防孤岛）---
    { name:'AdminHierarchy',path:'/admin/hierarchy',title:'权限层级',icon:'ApartmentOutlined', group:'运维监控' },
    { name:'AdminPlatformRegistry',path:'/admin/platform-registry',title:'平台注册表',icon:'AppstoreOutlined', group:'运维监控' },
    { name:'AdminPlatformZones',path:'/admin/platform-zones',title:'平台分区',icon:'PartitionOutlined', group:'运维监控' },
    { name:'AdminPlatformCredentials',path:'/admin/platform-credentials',title:'平台凭证',icon:'SafetyCertificateOutlined', group:'运维监控' },
    { name:'AdminCapabilityHub',path:'/admin/capability-hub',title:'能力中心',icon:'ThunderboltOutlined', group:'运维监控' },
    { name:'AdminFounderDiag',path:'/admin/founder-diagnostics',title:'创始人诊断',icon:'FundProjectionScreenOutlined', group:'运维监控' },
    // --- 运维监控组 ---
    { name:'SuiteSystem',path:'/admin/system',title:'系统管理',icon:'MonitorOutlined', group:'运维监控' },
    { name:'SystemCommandCenter',path:'/admin/system/command-center',title:'超管司令部',icon:'DashboardOutlined', group:'运维监控' },
    { name:'SystemHealth',path:'/admin/system-health',title:'系统健康压测',icon:'HeartOutlined', group:'运维监控', children: [
      { name:'SystemHealthDash', path:'/admin/system-health', title:'健康看板', icon:'HeartOutlined' },
      { name:'SystemHealthStress', path:'/system-health/stress-test', title:'压测管理', icon:'ThunderboltOutlined' },
      { name:'SystemHealthResource', path:'/system-health/resource-monitor', title:'资源监控', icon:'MonitorOutlined' },
      { name:'SystemHealthBackup', path:'/system-health/backup', title:'备份回滚', icon:'CloudServerOutlined' },
    ]},
    { name:'SystemUsers',path:'/admin/system/users',title:'管理员账号',icon:'UserOutlined', group:'运维监控' },
    { name:'SystemPermissions',path:'/admin/system/permissions',title:'权限码管理',icon:'KeyOutlined', group:'运维监控' },
    { name:'SystemLogs',path:'/admin/system/logs',title:'系统日志',icon:'FileTextOutlined', group:'运维监控' },
    { name:'SystemConfig',path:'/admin/system/config',title:'系统配置',icon:'SettingOutlined', group:'运维监控' },
    { name:'SystemLicense',path:'/admin/system/license',title:'许可与授权',icon:'IdcardOutlined', group:'运维监控' },
    { name:'SystemStorageProvision',path:'/admin/system/storage-provision',title:'存储供给',icon:'CloudServerOutlined', group:'运维监控' },
    { name:'SystemAccountBindings',path:'/admin/system/account-bindings',title:'账号绑定',icon:'LinkOutlined', group:'运维监控' },
    { name:'SystemIntegrations',path:'/admin/system/integrations-stack',title:'集成栈',icon:'ApiOutlined', group:'运维监控' },
    { name:'SystemDeerflowMonitor',path:'/admin/system/deerflow-monitor',title:'DeerFlow 监控',icon:'MonitorOutlined', group:'运维监控' },
    { name:'SystemPublishHistory',path:'/admin/system/publish-history',title:'发布历史',icon:'HistoryOutlined', group:'运维监控' },
    { name:'SystemRankScheduler',path:'/admin/system/rank-scheduler',title:'排名调度',icon:'FieldTimeOutlined', group:'运维监控' },
    { name:'SystemEccHangar',path:'/admin/system/ecc-hangar',title:'ECC 机库',icon:'DeploymentUnitOutlined', group:'运维监控' },
    { name:'SuiteRuntime',path:'/admin/runtime',title:'运行时',icon:'CloudOutlined', group:'运维监控' },
    { name:'SuiteScheduler',path:'/admin/scheduler-hub',title:'调度中心',icon:'CalendarOutlined', group:'运维监控' },
    // --- Paperclip 治理 ---
    { name:'PaperclipDashboard',path:'/admin/paperclip/dashboard',title:'Paperclip 总控',icon:'ClusterOutlined', group:'运维监控' },
    { name:'PaperclipOrgChart',path:'/admin/paperclip/org-chart',title:'组织图谱',icon:'ApartmentOutlined', group:'运维监控' },
    { name:'PaperclipGoals',path:'/admin/paperclip/goals',title:'目标管理',icon:'AimOutlined', group:'运维监控' },
    { name:'PaperclipHeartbeats',path:'/admin/paperclip/heartbeats',title:'心跳巡检',icon:'HeartOutlined', group:'运维监控' },
    { name:'PaperclipApprovals',path:'/admin/paperclip/approvals',title:'Paperclip 审批',icon:'AuditOutlined', group:'运维监控' },
    // --- AI 能力组 ---
    { name:'SuiteAI',path:'/admin/ai-center',title:'AI中心',icon:'ApiOutlined', group:'AI 能力', children: [
      { name:'AICenterDashboard', path:'/admin/ai-center', title:'控制台', icon:'CpuOutlined' },
      { name:'AICenterModels', path:'/admin/ai-center/models', title:'模型管理', icon:'LayersOutlined' },
      { name:'AICenterContent', path:'/admin/ai-center/content', title:'AI内容助手', icon:'EditOutlined' },
      { name:'AICenterAnalytics', path:'/admin/ai-center/analytics', title:'智能分析', icon:'BarChartOutlined' },
      { name:'AICenterLogs', path:'/admin/ai-center/logs', title:'调用日志', icon:'FileTextOutlined' },
      { name:'AICenterProviderSetup', path:'/admin/ai-center/provider-setup', title:'模型配置', icon:'ApiOutlined' },
      { name:'AICenterScenarioModels', path:'/admin/ai-center/scenario-models', title:'场景模型切换', icon:'SwapOutlined' },
      { name:'AICenterArticleGenerator', path:'/admin/ai-center/article-generator', title:'文章生成器', icon:'FileTextOutlined' },
      { name:'AICenterArticleToVideo', path:'/admin/ai-center/article-to-video', title:'文章转视频', icon:'VideoCameraOutlined' },
      { name:'AICenterUsage', path:'/admin/ai-center/usage', title:'用量监控', icon:'BarChartOutlined' },
      { name:'AICenterKnowledge', path:'/admin/ai-center/knowledge', title:'知识库', icon:'ReadOutlined' },
    ]},
    { name:'SuiteAIEngine',path:'/admin/ai-engine',title:'AI 引擎',icon:'RobotOutlined', group:'AI 能力', children: [
      { name:'AIEngineDashboard', path:'/admin/ai-engine', title:'引擎总览', icon:'DashboardOutlined' },
      { name:'AIEngineAnalytics', path:'/admin/ai-engine/analytics', title:'引擎分析', icon:'BarChartOutlined' },
      { name:'AIEngineTasks', path:'/admin/ai-engine/tasks', title:'引擎任务', icon:'OrderedListOutlined' },
      { name:'AIEnginePrompts', path:'/admin/ai-engine/prompts', title:'提示词库', icon:'EditOutlined' },
      { name:'AIEngineModels', path:'/admin/ai-engine/models', title:'引擎模型', icon:'LayersOutlined' },
      { name:'AIEngineTradeIntel', path:'/admin/ai-engine/trade-intel', title:'外贸情报', icon:'GlobalOutlined' },
    ]},
    { name:'AdminEvolution',path:'/admin/evolution',title:'AI 进化引擎',icon:'BulbOutlined', group:'AI 能力' },
    { name:'AdminN8nWorkflows',path:'/admin/n8n/workflows',title:'n8n 工作流',icon:'ApiOutlined', group:'AI 能力' },
    { name:'AdminSitesBuild',path:'/admin/sites/build',title:'一键建站',icon:'RocketOutlined', group:'AI 能力' },
    { name:'AdminDeerflowMonitor',path:'/admin/deerflow/monitor',title:'DeerFlow 监控',icon:'MonitorOutlined', group:'AI 能力' },
    { name:'AgentHubIndex',path:'/agent-hub',title:'智能体协同总览',icon:'RobotOutlined', group:'AI 能力' },
    { name:'AgentHubTaskGraph',path:'/agent-hub/task-graph',title:'任务图谱',icon:'NodeIndexOutlined', group:'AI 能力' },
    { name:'AgentHubOrchestrator',path:'/agent-hub/task-orchestrator',title:'任务编排器',icon:'PartitionOutlined', group:'AI 能力' },
    { name:'AgentHubMcpBridge',path:'/agent-hub/mcp-bridge',title:'MCP 桥接',icon:'ApiOutlined', group:'AI 能力' },
    { name:'AgentHubExecutionReview',path:'/agent-hub/execution-review',title:'执行复核',icon:'AuditOutlined', group:'AI 能力' },
    { name:'GEOEngine',path:'/admin/geo-engine',title:'GEO引擎收录',icon:'SearchOutlined', group:'AI 能力' },
    { name:'TechRadar',path:'/admin/tech-radar',title:'GEO 技术雷达',icon:'RadarChartOutlined', group:'AI 能力' },
    { name:'AgentHub',path:'/agent-hub/dashboard',title:'智能体看板',icon:'DashboardOutlined', group:'AI 能力' },
    // --- SaaS 运营组 ---
    { name:'Tenants',path:'/admin/tenants',title:'SaaS租户',icon:'TeamOutlined', group:'SaaS 运营', children: [
      { name:'TenantDashboard', path:'/admin/tenants', title:'租户总览', icon:'DashboardOutlined' },
      { name:'TenantShowcase', path:'/tenants/product-showcase', title:'产品展示', icon:'ShopOutlined' },
      { name:'TenantPricing', path:'/tenants/pricing', title:'定价方案', icon:'DollarOutlined' },
      { name:'TenantPlans', path:'/tenants/plans', title:'套餐配置', icon:'SettingOutlined' },
      { name:'TenantBilling', path:'/tenants/billing', title:'计费结算', icon:'BankOutlined' },
      { name:'TenantWhiteLabel', path:'/tenants/white-label', title:'白标品牌', icon:'TrophyOutlined' },
      { name:'TenantDomain', path:'/tenants/domain', title:'域名管理', icon:'GlobalOutlined' },
      { name:'SiteEditor', path:'/tenants/site-editor', title:'AI智能建站', icon:'EditOutlined' },
    ]},
    { name:'AgentCapabilities',path:'/admin/system/agent-capabilities',title:'能力划拨',icon:'PartitionOutlined', group:'SaaS 运营' },
    // --- 工具箱组 ---
    { name:'SuiteCode',path:'/admin/code-tools',title:'代码工具',icon:'CodeOutlined', group:'工具箱', children: [
      { name:'CodeToolsHub', path:'/admin/code-tools', title:'工具总览', icon:'CodeOutlined' },
      { name:'CodeToolsGenerator', path:'/admin/code-tools/generator', title:'代码生成', icon:'ThunderboltOutlined' },
      { name:'CodeToolsRefactor', path:'/admin/code-tools/refactor', title:'重构助手', icon:'ToolOutlined' },
      { name:'CodeToolsDebug', path:'/admin/code-tools/debug', title:'调试', icon:'BugOutlined' },
      { name:'CodeToolsFormat', path:'/admin/code-tools/format', title:'格式化', icon:'AlignLeftOutlined' },
      { name:'CodeToolsScanner', path:'/admin/code-tools/scanner', title:'安全扫描', icon:'SafetyOutlined' },
    ]},
    { name:'SuiteFiles',path:'/admin/file-manager',title:'产品图片空间',icon:'PictureOutlined', group:'工具箱' },
    { name:'SuiteSecurity',path:'/admin/security',title:'安全合规',icon:'SecurityScanOutlined', group:'工具箱' },
    { name:'SuiteAutomation',path:'/admin/automation',title:'自动化',icon:'ThunderboltOutlined', group:'工具箱' },
    { name:'SuiteProjects',path:'/admin/projects',title:'项目中心',icon:'FolderOutlined', group:'工具箱' },
    { name:'MediaFactory',path:'/media-factory/dashboard',title:'多媒体工厂',icon:'VideoCameraOutlined', group:'工具箱', children: [
      { name:'MediaFactoryDashboard', path:'/media-factory/dashboard', title:'工厂总览', icon:'DashboardOutlined' },
      { name:'MediaFactoryIndex', path:'/media-factory', title:'媒体库', icon:'PictureOutlined' },
      { name:'MediaFactoryRenderQueue', path:'/media-factory/render-queue', title:'渲染队列', icon:'OrderedListOutlined' },
      { name:'MediaFactoryTts', path:'/media-factory/tts', title:'TTS 配音', icon:'AudioOutlined' },
      { name:'MediaFactoryCharts', path:'/media-factory/charts', title:'媒体图表', icon:'BarChartOutlined' },
    ]},
    { name:'Globalization',path:'/globalization/dashboard',title:'全球化多语言',icon:'TranslationOutlined', group:'工具箱', children: [
      { name:'G11nDashboard', path:'/globalization/dashboard', title:'全球化总览', icon:'GlobalOutlined' },
      { name:'G11nIndex', path:'/globalization', title:'语言工作台', icon:'TranslationOutlined' },
      { name:'G11nTranslator', path:'/globalization/translator', title:'翻译中心', icon:'SwapOutlined' },
      { name:'G11nGlossary', path:'/globalization/glossary', title:'术语表', icon:'BookOutlined' },
      { name:'G11nCulture', path:'/globalization/culture-adapt', title:'文化适配', icon:'ReadOutlined' },
    ]},
    { name:'Logistics',path:'/admin/logistics',title:'智能物流定价',icon:'CarOutlined', group:'工具箱', children: [
      { name:'LogisticsDashboard', path:'/logistics/dashboard', title:'物流总览', icon:'DashboardOutlined' },
      { name:'LogisticsIndexAlias', path:'/admin/logistics', title:'物流工作台', icon:'CarOutlined' },
      { name:'LogisticsFreight', path:'/logistics/freight-calc', title:'运费计算', icon:'CalculatorOutlined' },
      { name:'LogisticsQuotation', path:'/logistics/quotation', title:'报价', icon:'FileTextOutlined' },
      { name:'LogisticsTrack', path:'/logistics/orders-track', title:'订单追踪', icon:'AimOutlined' },
      { name:'LogisticsLbs', path:'/logistics/lbs-routing', title:'路径优化', icon:'NodeIndexOutlined' },
    ]},
    { name:'V2RayProxy',path:'/admin/v2ray',title:'V2RayN代理',icon:'GlobalOutlined', group:'工具箱', children: [
      { name:'V2RayHub', path:'/admin/v2ray', title:'代理总控', icon:'GlobalOutlined' },
      { name:'V2RayServers', path:'/admin/v2ray-legacy/servers', title:'节点管理', icon:'CloudServerOutlined' },
    ]},
    { name:'EdgeCDN',path:'/edge-cdn/dashboard',title:'边缘计算CDN',icon:'CloudServerOutlined', group:'工具箱', children: [
      { name:'CdnDashboard', path:'/edge-cdn/dashboard', title:'CDN 总览', icon:'DashboardOutlined' },
      { name:'CdnIndex', path:'/edge-cdn', title:'加速配置', icon:'CloudServerOutlined' },
      { name:'CdnNodes', path:'/edge-cdn/nodes', title:'边缘节点', icon:'ClusterOutlined' },
      { name:'CdnPreheat', path:'/edge-cdn/preheat', title:'预热', icon:'ThunderboltOutlined' },
      { name:'CdnProtocol', path:'/edge-cdn/protocol', title:'协议优化', icon:'ApiOutlined' },
    ]},
    { name:'Developer',path:'/developer/dashboard',title:'开发者生态',icon:'CodeSandboxOutlined', group:'工具箱', children: [
      { name:'DevDashboard', path:'/developer/dashboard', title:'开发者总览', icon:'DashboardOutlined' },
      { name:'DevIndex', path:'/developer', title:'工作台', icon:'CodeOutlined' },
      { name:'DevLowCode', path:'/developer/low-code', title:'低代码', icon:'AppstoreOutlined' },
      { name:'DevPlugins', path:'/developer/plugins', title:'插件', icon:'ApiOutlined' },
      { name:'DevSdk', path:'/developer/sdk', title:'SDK', icon:'CodeOutlined' },
    ]},
    // --- 摸金校尉组 ---
    { name:'SystemGreedyHub',path:'/admin/system/greedy-hub',title:'摸金校尉总控',icon:'FundProjectionScreenOutlined', group:'摸金校尉' },
    { name:'SystemGreedyCumulative',path:'/admin/system/greedy-cumulative',title:'摸金累计看板',icon:'FundOutlined', group:'摸金校尉' },
    { name:'SystemGreedyContestLeaderboard',path:'/admin/system/greedy-contest-leaderboard',title:'挣钱大赛',icon:'TrophyOutlined', group:'摸金校尉' },
    { name:'SystemGreedyPublishQueue',path:'/admin/system/greedy-publish-queue',title:'L4 发布队列',icon:'SendOutlined', group:'摸金校尉' },
    { name:'SystemSurvivalDashboard',path:'/admin/system/survival-dashboard',title:'Survival 台账',icon:'BankOutlined', group:'摸金校尉' },
    { name:'SystemGreedyExpertMemory',path:'/admin/system/greedy-expert-memory',title:'专家记忆',icon:'ReadOutlined', group:'摸金校尉' },
  ]},
];
