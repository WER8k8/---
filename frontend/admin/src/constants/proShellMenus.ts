/**
 * YoudingProLayout · Client / Partner / Agent 侧栏菜单（一壳三 accent）
 * @see docs/youding-omni-pro-design-LOCKED.md P2
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
      { name: 'ClientInquiries', path: '/client/inquiries', title: '询盘管理', icon: 'MessageOutlined' },
      { name: 'ClientAcquisitionOps', path: '/client/acquisition-ops', title: '获客作战台', icon: 'AimOutlined' },
      { name: 'ClientInquiryQueue', path: '/client/queues/inquiries', title: '询盘队列', icon: 'OrderedListOutlined' },
      { name: 'ClientEmailCampaigns', path: '/client/email-campaigns', title: '邮件营销', icon: 'MailOutlined' },
      { name: 'ClientTradeTools', path: '/client/trade-tools', title: '外贸工具指南', icon: 'QuestionCircleOutlined' },
      { name: 'ClientReferral', path: '/client/referral', title: '邀请好友', icon: 'TeamOutlined' },
    ],
  },
  {
    title: '商品与内容',
    children: [
      { name: 'ClientProducts', path: '/client/products', title: '产品管理', icon: 'ShoppingOutlined' },
      { name: 'ClientContent', path: '/client/content', title: '内容管理', icon: 'FileOutlined' },
      { name: 'ClientSEO', path: '/client/seo', title: 'SEO 优化', icon: 'SearchOutlined' },
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
    title: '履约与账户',
    children: [
      { name: 'ClientFulfillmentQueue', path: '/client/queues/fulfillment', title: '履约队列', icon: 'CarryOutOutlined' },
      { name: 'ClientBilling', path: '/client/billing', title: '套餐续费', icon: 'AccountBookOutlined' },
      { name: 'ClientInvoices', path: '/client/invoices', title: '开票申请', icon: 'FileTextOutlined' },
      { name: 'ClientTokens', path: '/client/tokens', title: 'AI 流量充值', icon: 'ThunderboltOutlined' },
      { name: 'ClientEgress', path: '/client/egress', title: '出口 IP', icon: 'GlobalOutlined' },
      { name: 'ClientSettings', path: '/client/settings', title: '系统设置', icon: 'SettingOutlined' },
    ],
  },
  {
    title: '附属执行台',
    children: [
      { name: 'ClientAnnexTradeAi', path: '/client/annex/trade-ai', title: 'TradeAI 执行台', icon: 'ThunderboltOutlined' },
      { name: 'ClientAnnexGoodjob', path: '/client/annex/goodjob', title: 'GoodJob 执行台', icon: 'GlobalOutlined' },
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
export const CLIENT_PRIMARY_SHELL_PATHS = [
  '/client/today',
  '/client/inquiries',
  '/client/products',
  '/client/distribute',
  '/client/billing',
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
