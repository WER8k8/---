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
    { name:'Products',path:'/products',title:'产品管理',icon:'ShoppingOutlined' },
    { name:'ProductImages',path:'/admin/file-manager',title:'产品图片空间',icon:'PictureOutlined' },
    { name:'VideoSpace',path:'/admin/video-space',title:'视频空间',icon:'VideoCameraOutlined' },
    { name:'Categories',path:'/products/categories',title:'分类管理',icon:'FolderOpenOutlined' },
    { name:'Content',path:'/content',title:'文章内容',icon:'FileOutlined' },
    { name:'Cases',path:'/cases',title:'案例展示',icon:'PictureOutlined' },
    { name:'News',path:'/news',title:'新闻动态',icon:'ReadOutlined' },
  ]},
  { title: '附属执行台', children: [
    { name:'AnnexTradeAi',path:'/admin/annex/trade-ai',title:'TradeAI 执行台',icon:'ThunderboltOutlined' },
    { name:'AnnexGoodjob',path:'/admin/annex/goodjob',title:'GoodJob 执行台',icon:'GlobalOutlined' },
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
    // --- 运维监控组 ---
    { name:'SuiteSystem',path:'/admin/system',title:'系统管理',icon:'MonitorOutlined', group:'运维监控' },
    { name:'SystemCommandCenter',path:'/admin/system/command-center',title:'超管司令部',icon:'DashboardOutlined', group:'运维监控' },
    { name:'SystemHealth',path:'/system-health/dashboard',title:'系统健康压测',icon:'HeartOutlined', group:'运维监控' },
    { name:'SuiteRuntime',path:'/admin/runtime',title:'运行时',icon:'CloudOutlined', group:'运维监控' },
    { name:'SuiteScheduler',path:'/admin/scheduler-hub',title:'调度中心',icon:'CalendarOutlined', group:'运维监控' },
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
    { name:'GEOEngine',path:'/admin/geo-engine',title:'GEO引擎收录',icon:'SearchOutlined', group:'AI 能力' },
    { name:'TechRadar',path:'/admin/tech-radar',title:'GEO 技术雷达',icon:'RadarChartOutlined', group:'AI 能力' },
    { name:'AgentHub',path:'/agent-hub/dashboard',title:'智能体协同',icon:'RobotOutlined', group:'AI 能力' },
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
    { name:'SuiteCode',path:'/admin/code-tools',title:'代码工具',icon:'CodeOutlined', group:'工具箱' },
    { name:'SuiteFiles',path:'/admin/file-manager',title:'产品图片空间',icon:'PictureOutlined', group:'工具箱' },
    { name:'SuiteSecurity',path:'/admin/security',title:'安全合规',icon:'SecurityScanOutlined', group:'工具箱' },
    { name:'SuiteAutomation',path:'/admin/automation',title:'自动化',icon:'ThunderboltOutlined', group:'工具箱' },
    { name:'SuiteProjects',path:'/admin/projects',title:'项目中心',icon:'FolderOutlined', group:'工具箱' },
    { name:'MediaFactory',path:'/media-factory/dashboard',title:'多媒体工厂',icon:'VideoCameraOutlined', group:'工具箱' },
    { name:'Globalization',path:'/globalization/dashboard',title:'全球化多语言',icon:'TranslationOutlined', group:'工具箱' },
    { name:'Logistics',path:'/logistics/dashboard',title:'智能物流定价',icon:'CarOutlined', group:'工具箱' },
    { name:'V2RayProxy',path:'/admin/v2ray',title:'V2RayN代理',icon:'GlobalOutlined', group:'工具箱' },
    { name:'EdgeCDN',path:'/edge-cdn/dashboard',title:'边缘计算CDN',icon:'CloudServerOutlined', group:'工具箱' },
    { name:'Developer',path:'/developer/dashboard',title:'开发者生态',icon:'CodeSandboxOutlined', group:'工具箱' },
    // --- 摸金校尉组 ---
    { name:'SystemGreedyHub',path:'/admin/system/greedy-hub',title:'摸金校尉总控',icon:'FundProjectionScreenOutlined', group:'摸金校尉' },
    { name:'SystemGreedyCumulative',path:'/admin/system/greedy-cumulative',title:'摸金累计看板',icon:'FundOutlined', group:'摸金校尉' },
    { name:'SystemGreedyContestLeaderboard',path:'/admin/system/greedy-contest-leaderboard',title:'挣钱大赛',icon:'TrophyOutlined', group:'摸金校尉' },
    { name:'SystemGreedyPublishQueue',path:'/admin/system/greedy-publish-queue',title:'L4 发布队列',icon:'SendOutlined', group:'摸金校尉' },
    { name:'SystemSurvivalDashboard',path:'/admin/system/survival-dashboard',title:'Survival 台账',icon:'BankOutlined', group:'摸金校尉' },
    { name:'SystemGreedyExpertMemory',path:'/admin/system/greedy-expert-memory',title:'专家记忆',icon:'ReadOutlined', group:'摸金校尉' },
  ]},
];
