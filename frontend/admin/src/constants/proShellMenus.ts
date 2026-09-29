/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * YoudingProLayout · Client / Partner / Agent 侧栏菜单声明源（一壳三 accent）
 * @see docs/youding-omni-pro-design-LOCKED.md P2
 *
 * 双源收敛约定（2026-09-23 审计 P1-1）：
 * - ClientShellLayout.categorizedNavGroups = 租户壳主栏「唯一真渲染源」
 * - 本文件 CLIENT_SHELL_MENU = 声明/清单源（更多面板、测试、代理/省代壳共用）
 * - CLIENT_PRIMARY_SHELL_PATHS 必须与 categorizedNavGroups 路径集保持一致；
 *   其余 CLIENT_SHELL_MENU 项由 ClientShellLayout「更多功能」面板渲染，禁止再漂移
 */

import { isClientPathHidden, isClientMoreMenuPathVisible, filterShellMenuByCertMode } from '@/constants/stubVisibility';

export interface ProShellNavItem {
  name: string;
  path: string;
  title: string;
  icon: string;
  children?: ProShellNavItem[];
}

export interface ProShellMenuGroup {
  title: string;
  children: ProShellNavItem[];
}

/** 租户 Client 壳菜单 */
export const CLIENT_SHELL_MENU: ProShellMenuGroup[] = [
  {
    title: '经营总览',
    children: [
      { name: 'ClientToday', path: '/client/today', title: '今日三步', icon: 'ThunderboltOutlined' },
      { name: 'ClientDashboard', path: '/client/dashboard', title: '概览', icon: 'DashboardOutlined' },
      { name: 'ClientTrafficBoard', path: '/client/traffic', title: '流量看板', icon: 'LineChartOutlined' },
      { name: 'ClientOnboarding', path: '/client/onboarding', title: '开通向导', icon: 'CarryOutOutlined' },
      { name: 'ClientSiteEditor', path: '/client/site-editor', title: '可视化建站', icon: 'EditOutlined' },
      { name: 'ClientProductImages', path: '/client/product-images', title: '产品图片空间', icon: 'PictureOutlined' },
      { name: 'ClientVideoSpace', path: '/client/video-space', title: '视频空间', icon: 'VideoCameraOutlined' },
    ],
  },
  {
    title: '获客转化',
    children: [
      // 功能域（无特权）：社媒拓客 / 外贸履约 = 普通业务菜单，非附属特权入口
      { name: 'ClientSocialOutreach', path: '/client/trade-tools', title: '社媒拓客', icon: 'GlobalOutlined' },
      { name: 'ClientTradeFulfillment', path: '/client/queues/fulfillment', title: '外贸履约', icon: 'CarryOutOutlined' },
      { name: 'ClientInquiries', path: '/client/inquiries', title: '询盘管理', icon: 'MessageOutlined' },
      { name: 'ClientAcquisitionOps', path: '/client/acquisition-ops', title: '获客作战台', icon: 'AimOutlined' },
      { name: 'ClientInquiryQueue', path: '/client/queues/inquiries', title: '询盘队列', icon: 'OrderedListOutlined' },
      { name: 'ClientEmailCampaigns', path: '/client/email-campaigns', title: '邮件营销', icon: 'MailOutlined' },
      { name: 'ClientTradeTools', path: '/client/trade-tools', title: '外贸工具指南', icon: 'QuestionCircleOutlined' },
      { name: 'ClientForeignTradeTeam', path: '/client/foreign-trade-team', title: 'AI 外贸团队', icon: 'TeamOutlined' },
      { name: 'ClientReferral', path: '/client/referral', title: '邀请好友', icon: 'TeamOutlined' },
    ],
  },
  {
    title: '商品与内容',
    children: [
      { name: 'ClientProducts', path: '/client/products', title: '产品管理', icon: 'ShoppingOutlined' },
      { name: 'ClientContent', path: '/client/content', title: '内容管理', icon: 'FileOutlined' },
      { name: 'ClientSEO', path: '/client/seo', title: 'SEO 优化', icon: 'SearchOutlined' },
      { name: 'ClientKeywordResearch', path: '/client/keyword-research', title: '关键词热度查询', icon: 'RiseOutlined' },
      { name: 'ClientSeoKeywords', path: '/client/seo-keywords', title: '产业带词库', icon: 'TagsOutlined' },
      { name: 'ClientSeoPublish', path: '/client/seo-publish', title: '平台绑定', icon: 'GlobalOutlined' },
      { name: 'ClientPublishQueue', path: '/client/queues/publish', title: '发布队列', icon: 'SendOutlined' },
      { name: 'ClientContentDistribute', path: '/client/distribute', title: '视频分发', icon: 'VideoCameraOutlined' },
      { name: 'ClientAitoearnEngage', path: '/client/engage', title: '评论互动', icon: 'CommentOutlined' },
      { name: 'ClientCrossPlatformDashboard', path: '/client/cross-platform', title: '跨平台数据', icon: 'BarChartOutlined' },
      { name: 'ClientMediaFactory', path: '/client/media-factory', title: '视频工厂', icon: 'VideoCameraOutlined' },
      { name: 'ClientArticleToVideo', path: '/client/article-to-video', title: '文章转视频', icon: 'PlayCircleOutlined' },
      { name: 'ClientAiScenarios', path: '/client/ai-scenarios', title: 'AI 场景', icon: 'ExperimentOutlined' },
    ],
  },
  {
    title: '视频与创意',
    children: [
      { name: 'ClientVideoStudio', path: '/client/video-studio', title: '视频工作室', icon: 'VideoCameraOutlined' },
      { name: 'ClientVideoOverseas', path: '/client/video-overseas', title: '出海视频', icon: 'GlobalOutlined' },
      { name: 'ClientTemplatesExplore', path: '/client/explore', title: '创意社区模板', icon: 'AppstoreOutlined' },
      { name: 'ClientSkillsMarket', path: '/client/skills', title: '专属技能', icon: 'ThunderboltOutlined' },
      { name: 'ClientPluginMarket', path: '/client/plugin-market', title: '旺财插件市场', icon: 'AppstoreOutlined' },
      { name: 'ClientProductCandidates', path: '/client/product-candidates', title: '选品候选', icon: 'ShoppingOutlined' },
    ],
  },
  {
    title: 'AI 协同',
    children: [
      { name: 'ClientAssistant', path: '/client/assistant', title: '卖货智能助手', icon: 'RobotOutlined' },
      { name: 'ClientCopilot', path: '/client/copilot', title: '卖货飞轮', icon: 'NodeIndexOutlined' },
      { name: 'ClientGeoVisibility', path: '/client/geo-visibility', title: 'GEO 可见性', icon: 'SearchOutlined' },
      { name: 'ClientChuhaijiApp', path: '/client/app', title: '出海计应用', icon: 'MobileOutlined' },
    ],
  },
  {
    title: '履约与账户',
    children: [
      { name: 'ClientDocumentMaker', path: '/client/document-maker', title: '制单中心', icon: 'FileTextOutlined' },
      { name: 'ClientFulfillmentQueue', path: '/client/queues/fulfillment', title: '履约队列', icon: 'CarryOutOutlined' },
      // 功能域（无特权）：原 GoodJob → 外贸履约，与其它履约模块同级
      { name: 'ClientHermesTasks', path: '/client/tasks', title: '我的任务', icon: 'NodeIndexOutlined' },
      { name: 'ClientBilling', path: '/client/billing', title: '套餐续费', icon: 'AccountBookOutlined' },
      { name: 'ClientInvoices', path: '/client/invoices', title: '开票申请', icon: 'FileTextOutlined' },
      { name: 'ClientTokens', path: '/client/tokens', title: 'AI 用量充值', icon: 'ThunderboltOutlined' },
      { name: 'ClientEgress', path: '/client/egress', title: '出口 IP', icon: 'GlobalOutlined' },
      { name: 'ClientPlanGate', path: '/client/plan-gate', title: '套餐门槛', icon: 'SafetyCertificateOutlined' },
      { name: 'ClientSettings', path: '/client/settings', title: '系统设置', icon: 'SettingOutlined' },
    ],
  },
];

/** 代理 Agent 壳菜单 */
export const AGENT_SHELL_MENU: ProShellMenuGroup[] = [
  {
    title: '经营总览',
    children: [
      { name: 'AgentPerformance', path: '/agent/performance', title: '业绩看板', icon: 'DashboardOutlined' },
      { name: 'AgentTrafficBoard', path: '/agent/traffic', title: '流量看板', icon: 'LineChartOutlined' },
      { name: 'AgentDailyReport', path: '/agent/daily-report', title: '经营日报', icon: 'FileTextOutlined' },
    ],
  },
  {
    title: '客户增长',
    children: [
      { name: 'AgentAccountOpening', path: '/agent/account-opening', title: '客户开户', icon: 'UserAddOutlined' },
    ],
  },
  {
    title: '结算与风控',
    children: [
      { name: 'AgentCommission', path: '/agent/commission', title: '佣金管理', icon: 'DollarOutlined' },
      { name: 'AgentChurnWarning', path: '/agent/churn-warning', title: '流失预警', icon: 'AlertOutlined' },
    ],
  },
];

/** 省代 Partner 壳菜单 */
export const PARTNER_SHELL_MENU: ProShellMenuGroup[] = [
  {
    title: '省区总览',
    children: [
      { name: 'PartnerPerformance', path: '/partner/performance', title: '省代看板', icon: 'DashboardOutlined' },
      { name: 'PartnerTrafficBoard', path: '/partner/traffic', title: '流量看板', icon: 'LineChartOutlined' },
      { name: 'PartnerDailyReport', path: '/partner/daily-report', title: '经营日报', icon: 'FileTextOutlined' },
    ],
  },
  {
    title: '渠道拓展',
    children: [
      { name: 'PartnerAccountOpening', path: '/partner/account-opening', title: '客户开户', icon: 'UserAddOutlined' },
    ],
  },
  {
    title: '收益与风险',
    children: [
      { name: 'PartnerCommission', path: '/partner/commission', title: '佣金管理', icon: 'DollarOutlined' },
      { name: 'PartnerChurnWarning', path: '/partner/churn-warning', title: '流失预警', icon: 'AlertOutlined' },
    ],
  },
];

function filterHiddenClientItems(groups: ProShellMenuGroup[]): ProShellMenuGroup[] {
  return groups
    .map((g) => ({
      ...g,
      children: g.children.filter((item) => !isClientPathHidden(item.path)),
    }))
    .filter((g) => g.children.length > 0);
}

/** 租户轻量壳 · 主栏固定五项（与 ClientShellLayout 同步） */
export const /** 侧栏主菜单（与 ClientShellLayout.categorizedNavGroups 保持一致，避免双源漂移） */
CLIENT_PRIMARY_SHELL_PATHS = [
  '/client/today',
  '/client/onboarding',
  '/client/dashboard',
  '/client/inquiries',
  '/client/queues/inquiries',
  '/client/acquisition-ops',
  '/client/email-campaigns',
  '/client/keyword-research',
  '/client/site-editor',
  '/client/product-images',
  '/client/video-space',
  '/client/explore',
  '/client/products',
  '/client/content',
  '/client/distribute',
  '/client/cross-platform',
  '/client/document-maker',
  '/client/queues/fulfillment',
  '/client/tasks',
  '/client/billing',
  '/client/tokens',
  '/client/settings',
] as const;

export function getClientShellMenu(): ProShellMenuGroup[] {
  return filterHiddenClientItems(CLIENT_SHELL_MENU);
}

/** 「更多功能」抽屉：剔除主栏 + Stub 矩阵瘦身 */
export function getClientMoreShellMenu(): ProShellMenuGroup[] {
  const primary = new Set<string>(CLIENT_PRIMARY_SHELL_PATHS);
  return filterShellMenuByCertMode(
    getClientShellMenu()
      .map((g) => ({
        ...g,
        children: g.children.filter(
          (item) => !primary.has(item.path) && isClientMoreMenuPathVisible(item.path),
        ),
      }))
      .filter((g) => g.children.length > 0),
  );
}

export function getAgentShellMenu(): ProShellMenuGroup[] {
  return AGENT_SHELL_MENU;
}

export function getPartnerShellMenu(): ProShellMenuGroup[] {
  return PARTNER_SHELL_MENU;
}

export type ShellMode = 'platform' | 'client' | 'agent' | 'partner';

export function resolveShellMode(path: string): ShellMode {
  if (path.startsWith('/client')) return 'client';
  if (path.startsWith('/partner')) return 'partner';
  if (path.startsWith('/agent')) return 'agent';
  return 'platform';
}
