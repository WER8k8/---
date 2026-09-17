/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * FIX-9: 路由拆分引导
 * =====================
 * 本文件 1930 行，建议按角色壳拆分为独立模块：
 *
 *   router/index.ts          ← 仅保留 createRouter + guard（~100 行）
 *   router/routes/admin.ts   ← 超管/平台路由 (/admin/*)
 *   router/routes/client.ts  ← 租户路由 (/client/*)
 *   router/routes/agent.ts   ← 代理路由 (/agent/*)
 *   router/routes/public.ts  ← 公共路由 (login 等)
 *
 * 拆分时注意：
 * - ROLE-SHELL-LOCK-01 硬锁：唯一登录路由 /login，组件 views/login/index.vue
 * - 路由 meta.requiresAuth / meta.role 必须保留
 * - roleShellLock.ts 中的 roleFromAccessToken 决定跳转
 * - 建议每个模块导出 RouteRecordRaw[]，在 index.ts 中 spread 合并
 */

import { createRouter, createWebHistory } from 'vue-router';
import type { RouteRecordRaw } from 'vue-router';
import { useAgentCapabilitiesStore } from '@/stores/agentCapabilities';
import { useAuthStore } from '@/stores/auth';
import {
  normalizeLocationPath,
  resolveCapabilityIdForPath,
} from '@/constants/workbenchPathCapabilities';
import { isClientPathHidden, isPlatformKilledPath, isPlatformPathBlockedInCertMode, resolveClientLabPlanGate, resolveClientPlanGate } from '@/constants/stubVisibility';
import { bffPlanCheck } from '@/api/admin-bff';
import { LOGIN_PATH } from '@/constants/loginPortalCopy';
import {
  decideRoleShellNavigation,
  homePathForRole,
} from '@/constants/roleShellLock';
import { postLoginNavigatePath, roleFromAccessToken } from '@/utils/postLoginNavigation';
import { readStoredAccessToken } from '@/utils/sessionAuth';
import { generatedCrudRoutes } from '@/router/generated-crud-routes';
import TenantSiteEditor from '@/views/tenants/site-editor.vue';

const routes: RouteRecordRaw[] = [
  {
    path: '/login/admin',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: {
      title: '登录',
      requiresAuth: false,
      skipCapabilityGuard: true,
    },
  },
  {
    path: '/login/oauth-callback',
    name: 'OAuthCallback',
    component: () => import('@/views/login/oauth-callback.vue'),
    meta: {
      title: '第三方登录',
      requiresAuth: false,
      skipCapabilityGuard: true,
    },
  },
  {
    path: '/tenants/register',
    name: 'TenantRegister',
    component: () => import('@/views/tenants/register.vue'),
    meta: {
      title: '注册开通',
      requiresAuth: false,
      skipCapabilityGuard: true,
    },
  },
  {
    path: '/landing',
    name: 'Landing',
    component: () => import('@/views/landing/index.vue'),
    meta: {
      title: '官网首页',
      requiresAuth: false,
      skipCapabilityGuard: true,
    },
  },
  {
    path: '/access-denied',
    name: 'AccessDenied',
    component: () => import('@/views/access-denied.vue'),
    meta: {
      title: '无权访问',
      requiresAuth: false,
      skipCapabilityGuard: true,
    },
  },
  // 遗留 UBrain 路径 → 现有功能
  { path: '/skill-center', redirect: '/agent-hub/dashboard' },
  { path: '/invitation', redirect: '/referral' },
  { path: '/conversation', redirect: '/client/assistant' },
  { path: '/home', redirect: '/landing' },
  /** 后台菜单种子 `/admin/seo-matrix` → 实际路由 `/seo-matrix/*` */
  { path: '/admin/seo-matrix', redirect: '/seo-matrix/dashboard' },
  {
    path: '/admin/seo-matrix/:pathMatch(.*)*',
    redirect: (to) => {
      const pm = to.params.pathMatch;
      const tail = Array.isArray(pm) ? pm.filter(Boolean).join('/') : String(pm || '');
      return tail ? `/seo-matrix/${tail}` : '/seo-matrix/dashboard';
    },
  },
  // ========== 租户客户管理后台 ==========
  {
    path: '/client',
    name: 'ClientLayout',
    component: () => import('@/layout/ClientShellLayout.vue'),
    redirect: '/client/today',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'today',
        name: 'ClientToday',
        component: () => import('@/views/client/today-three.vue'),
        meta: { title: '今日三步' },
      },
      { path: 'dashboard', name: 'ClientDashboard', component: () => import('@/views/client/dashboard.vue'), meta: { title: '工作台' } },
      { path: 'annex/trade-ai', name: 'ClientAnnexTradeAi', component: () => import('@/views/annex/AnnexEmbedPage.vue'), meta: { title: 'TradeAI 执行台', annexKey: 'trade-ai' } },
     { path: 'annex/goodjob', name: 'ClientAnnexGoodjob', component: () => import('@/views/annex/AnnexEmbedPage.vue'), meta: { title: 'GoodJob 执行台', annexKey: 'goodjob' } },
      { path: 'annex/goodjob/tickets', name: 'ClientAnnexGoodjobTickets', component: () => import('@/views/annex/AnnexEmbedPage.vue'), meta: { title: 'GoodJob CRM · 票据中心管理', annexKey: 'goodjob', annexModule: 'tickets' } },
      { path: 'annex/goodjob/customers', name: 'ClientAnnexGoodjobCustomers', component: () => import('@/views/annex/AnnexEmbedPage.vue'), meta: { title: 'GoodJob CRM · 客户管理', annexKey: 'goodjob', annexModule: 'customers' } },
     { path: 'traffic', name: 'ClientTrafficBoard', component: () => import('@/views/client/traffic-board.vue'), meta: { title: '流量看板' } },
      { path: 'assistant', name: 'ClientAssistant', component: () => import('@/views/client/assistant.vue'), meta: { title: '卖货智能助手' } },
      { path: 'copilot', name: 'ClientCopilot', component: () => import('@/views/client/copilot.vue'), meta: { title: '卖货飞轮' } },
      {
        path: 'foreign-trade-team',
        name: 'ClientForeignTradeTeam',
        component: () => import('@/views/client/foreign-trade-team.vue'),
        meta: { title: 'AI 外贸团队' },
      },
      {
        path: 'plugin-market',
        name: 'ClientPluginMarket',
        component: () => import('@/views/client/wangcai-plugin-market.vue'),
        meta: { title: '旺财插件市场' },
      },
      {
        path: 'app',
        name: 'ChuhaijiApp',
        component: () => import('@/views/client/chuhaiji-app.vue'),
        meta: { title: '出海计', appShell: true },
      },
      { path: 'onboarding', name: 'ClientOnboarding', component: () => import('@/views/client/onboarding.vue'), meta: { title: '开通向导' } },
      { path: 'site-editor', name: 'ClientSiteEditor', component: TenantSiteEditor, meta: { title: '可视化建站' } },
      {
        path: 'product-images',
        name: 'ClientProductImages',
        component: () => import('@/views/admin/file-manager/overview.vue'),
        meta: { title: '产品图片空间', productImageSpaceMode: true },
      },
      {
        path: 'video-space',
        name: 'ClientVideoSpace',
        component: () => import('@/views/admin/file-manager/overview.vue'),
        meta: { title: '视频空间', videoSpaceMode: true },
      },
      { path: 'image-space', redirect: '/client/product-images' },
      { path: 'videos', redirect: '/client/video-space' },
      { path: 'products', name: 'ClientProducts', component: () => import('@/views/products/index.vue'), meta: { title: '产品管理' } },
      // 产品编辑/分类挂在 client 子树：tenant 角色守卫只放行 /client 前缀，
      // 根级 /products/edit/:id 会被 decideRoleShellNavigation 弹回工作台
      { path: 'products/edit/:id', name: 'ClientProductEdit', component: () => import('@/views/products/edit.vue'), meta: { title: '编辑产品' } },
      { path: 'products/categories', name: 'ClientProductCategories', component: () => import('@/views/products/categories.vue'), meta: { title: '分类管理' } },
      { path: 'inquiries', name: 'ClientInquiries', component: () => import('@/views/inquiries/index.vue'), meta: { title: '询盘管理' } },
      { path: 'egress', name: 'ClientEgress', component: () => import('@/views/client/egress.vue'), meta: { title: 'IP 槽位' } },
      { path: 'referral', name: 'ClientReferral', component: () => import('@/views/client/referral.vue'), meta: { title: '邀请好友' } },
      { path: 'content', name: 'ClientContent', component: () => import('@/views/content/index.vue'), meta: { title: '内容管理' } },
      { path: 'seo', name: 'ClientSEO', component: () => import('@/views/seo/index.vue'), meta: { title: 'SEO优化' } },
      { path: 'invoices', name: 'ClientInvoices', component: () => import('@/views/client/invoices.vue'), meta: { title: '开票申请' } },
      {
        path: 'tokens',
        name: 'ClientTokens',
        component: () => import('@/views/client/tokens.vue'),
        meta: { title: 'AI 流量充值' },
      },
      {
        path: 'distribute',
        name: 'ClientContentDistribute',
        component: () => import('@/views/client/content-distribute.vue'),
        meta: { title: '内容分发中心' },
      },
      {
        path: 'cross-platform',
        name: 'ClientCrossPlatformDashboard',
        component: () => import('@/views/cross-platform/dashboard.vue'),
        meta: { title: '跨平台数据看板' },
      },
      {
        path: 'engage',
        name: 'ClientAitoearnEngage',
        component: () => import('@/views/client/aitoearn-engage.vue'),
        meta: { title: '评论互动' },
      },
      {
        path: 'video-overseas',
        name: 'ClientVideoOverseas',
        component: () => import('@/views/client/video-overseas.vue'),
        meta: { title: '中文片出海' },
      },
      {
        path: 'video-studio',
        name: 'ClientVideoStudio',
        component: () => import('@/views/client/video-studio.vue'),
        meta: { title: '全媒体剪辑台' },
      },
      {
        path: 'video-editor/fly-cut',
        name: 'ClientVideoEditorFlyCut',
        component: () => import('@/views/client/video-editor-embed.vue'),
        meta: { title: 'Fly-Cut 剪辑', editorId: 'fly_cut' },
      },
      {
        path: 'video-editor/opencut',
        name: 'ClientVideoEditorOpenCut',
        component: () => import('@/views/client/video-editor-embed.vue'),
        meta: { title: 'OpenCut 剪辑', editorId: 'opencut' },
      },
      {
        path: 'product-candidates',
        name: 'ClientProductCandidates',
        component: () => import('@/views/client/product-candidates.vue'),
        meta: { title: '产业带产品候选' },
      },
      {
        path: 'publish',
        name: 'ClientUnifiedPublish',
        component: () => import('@/views/publish/unified.vue'),
        meta: { title: 'GEO 统一发布台' },
      },
      { path: 'ai-scenarios', name: 'ClientAiScenarios', component: () => import('@/views/client/ai-scenarios.vue'), meta: { title: 'AI 场景模型' } },
      { path: 'workspace/prospecting', name: 'ProspectingWorkspace', component: () => import('@/views/workspace/ProspectingWorkspace.vue'), meta: { title: '搜客执行台' } },
      { path: 'workspace/outreach', name: 'OutreachEditor', component: () => import('@/views/workspace/OutreachEditor.vue'), meta: { title: '写信工作台' } },
      { path: 'email-campaigns', name: 'ClientEmailCampaigns', component: () => import('@/views/sales/EmailAutomation.vue'), meta: { title: '邮件营销' } },
      { path: 'workspace/skills', name: 'SkillConsole', component: () => import('@/views/workspace/SkillConsole.vue'), meta: { title: 'AI 技能台' } },
      { path: 'skills', name: 'ClientSkillsMarket', component: () => import('@/views/client/skills-market.vue'), meta: { title: 'Meoo专属技能' } },
      { path: 'explore', name: 'ClientTemplatesExplore', component: () => import('@/views/client/templates-explore.vue'), meta: { title: '创意社区与模板' } },
      { path: 'ai-config', name: 'ClientAiConfig', component: () => import('@/views/client/ai-config.vue'), meta: { title: 'AI 配置' } },
      {
        path: 'trade-tools',
        name: 'ClientTradeTools',
        component: () => import('@/views/client/trade-tools.vue'),
        meta: { title: '外贸工具指南' },
      },
      {
        path: 'billing',
        name: 'ClientBilling',
        component: () => import('@/views/client/billing.vue'),
        meta: { title: '套餐续费' },
      },
      {
        path: 'plan-gate',
        name: 'ClientPlanGate',
        component: () => import('@/views/client/plan-gate.vue'),
        meta: { title: '升级套餐', skipCapabilityGuard: true },
      },
      {
        path: 'queues/inquiries',
        name: 'ClientInquiryQueue',
        component: () => import('@/views/client/queues/inquiries.vue'),
        meta: { title: '询盘队列' },
      },
      {
        path: 'geo-visibility',
        name: 'ClientGeoVisibility',
        component: () => import('@/views/client/geo-visibility.vue'),
        meta: { title: 'GEO 可见性' },
      },
      {
        path: 'queues/publish',
        name: 'ClientPublishQueue',
        component: () => import('@/views/client/queues/publish.vue'),
        meta: { title: '发布队列' },
      },
      {
        path: 'queues/fulfillment',
        name: 'ClientFulfillmentQueue',
        component: () => import('@/views/client/queues/fulfillment.vue'),
        meta: { title: '履约队列' },
      },
      {
        path: 'site-editor-lab',
        name: 'ClientSiteEditorLab',
        component: () => import('@/views/client/site-editor-lab.vue'),
        meta: { title: '站点编辑器试点' },
      },
      ...generatedCrudRoutes,
      {
        path: 'seo-publish',
        name: 'ClientSeoPublish',
        component: () => import('@/views/seo-matrix/publish.vue'),
        meta: { title: '平台绑定与发布' },
      },
      {
        path: 'video-bind',
        redirect: { path: 'distribute', query: { focus: 'bind' } },
      },
      {
        path: 'media-factory',
        name: 'ClientMediaFactory',
        component: () => import('@/views/media-factory/dashboard.vue'),
        meta: { title: '视频工厂' },
      },
      {
        path: 'article-to-video',
        name: 'ClientArticleToVideo',
        component: () => import('@/views/admin/ai-center/article-to-video.vue'),
        meta: { title: '文章转视频' },
      },
      { path: 'settings', name: 'ClientSettings', component: () => import('@/views/system/settings.vue'), meta: { title: '系统设置' } },
    ],
  },
  // ========== 客户登录（独立页面，用客户端布局） ==========
  {
    path: '/client/login',
    redirect: LOGIN_PATH,
  },
  {
    path: '/login/agent',
    redirect: LOGIN_PATH,
  },
  {
    path: '/login/partner',
    redirect: LOGIN_PATH,
  },
  {
    path: '/login/platform',
    redirect: LOGIN_PATH,
  },
  // ========== 省代独立壳（L2） ==========
  {
    path: '/partner',
    name: 'PartnerShellLayout',
    component: () => import('@/layout/index.vue'),
    redirect: '/partner/performance',
    meta: { requiresAuth: true, partnerShell: true },
    children: [
      { path: 'performance', name: 'PartnerPerformance', component: () => import('@/views/partner/performance.vue'), meta: { title: '省代看板', partnerShell: true } },
      { path: 'traffic', name: 'PartnerTrafficBoard', component: () => import('@/views/agent/traffic-board.vue'), meta: { title: '流量看板', partnerShell: true } },
      { path: 'commission', name: 'PartnerCommission', component: () => import('@/views/agent/commission.vue'), meta: { title: '佣金管理', partnerShell: true } },
      { path: 'account-opening', name: 'PartnerAccountOpening', component: () => import('@/views/agent/account-opening.vue'), meta: { title: '客户开户', partnerShell: true } },
      { path: 'daily-report', name: 'PartnerDailyReport', component: () => import('@/views/agent/daily-report.vue'), meta: { title: '经营日报', partnerShell: true } },
      { path: 'churn-warning', name: 'PartnerChurnWarning', component: () => import('@/views/agent/churn-warning.vue'), meta: { title: '流失预警', partnerShell: true } },
    ],
  },
  // ========== 市代独立壳（L3） ==========
  {
    path: '/agent',
    name: 'AgentShellLayout',
    component: () => import('@/layout/index.vue'),
    redirect: '/agent/performance',
    meta: { requiresAuth: true, agentShell: true },
    children: [
      { path: 'performance', name: 'AgentPerformance', component: () => import('@/views/agent/performance.vue'), meta: { title: '业绩看板', agentShell: true } },
      { path: 'traffic', name: 'AgentTrafficBoard', component: () => import('@/views/agent/traffic-board.vue'), meta: { title: '流量看板', agentShell: true } },
      { path: 'commission', name: 'AgentCommission', component: () => import('@/views/agent/commission.vue'), meta: { title: '佣金管理', agentShell: true } },
      { path: 'account-opening', name: 'AgentAccountOpening', component: () => import('@/views/agent/account-opening.vue'), meta: { title: '客户开户', agentShell: true } },
      { path: 'daily-report', name: 'AgentDailyReport', component: () => import('@/views/agent/daily-report.vue'), meta: { title: '经营日报', agentShell: true } },
      { path: 'churn-warning', name: 'AgentChurnWarning', component: () => import('@/views/agent/churn-warning.vue'), meta: { title: '流失预警', agentShell: true } },
    ],
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layout/index.vue'),
    redirect: '/admin',
    meta: { requiresAuth: false },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '数据概览', icon: 'DashboardOutlined' },
      },
      // ========== 仪表盘模板展示 ==========
      {
        path: 'templates',
        name: 'TemplateGallery',
        component: () => import('@/views/templates/index.vue'),
        meta: { title: '仪表盘模板', icon: 'LayoutOutlined' },
      },
      {
        path: 'templates/data-cockpit',
        name: 'TemplateDataCockpit',
        component: () => import('@/views/templates/dashboard-data-cockpit.vue'),
        meta: { title: '数据驾驶舱', icon: 'DashboardOutlined' },
      },
      {
        path: 'templates/enterprise',
        name: 'TemplateEnterprise',
        component: () => import('@/views/templates/dashboard-enterprise.vue'),
        meta: { title: '企业后台实战', icon: 'DashboardOutlined' },
      },
      {
        path: 'templates/tencent',
        name: 'TemplateTencent',
        component: () => import('@/views/templates/dashboard-tencent.vue'),
        meta: { title: '大厂极简风', icon: 'DashboardOutlined' },
      },
      {
        path: 'templates/saas',
        name: 'TemplateSaaS',
        component: () => import('@/views/templates/dashboard-saas.vue'),
        meta: { title: 'SaaS系统风', icon: 'DashboardOutlined' },
      },
      {
        path: 'templates/data-screen',
        name: 'TemplateDataScreen',
        component: () => import('@/views/templates/dashboard-data-screen.vue'),
        meta: { title: '数据大屏', icon: 'DashboardOutlined' },
      },
      // ========== 运营管理员（admin 角色）功能 ==========
      {
        path: 'admin/dashboard',
        name: 'AdminDashboardPage',
        component: () => import('@/views/admin/dashboard.vue'),
        meta: { title: '运营看板', icon: 'DashboardOutlined' },
      },
      {
        path: 'admin/tenants',
        name: 'AdminTenantsPage',
        component: () => import('@/views/tenants/dashboard.vue'),
        meta: { title: '租户管理', icon: 'TeamOutlined' },
      },
      // ========== 超级管理员功能模块 ==========
      {
        path: 'admin',
        name: 'Admin',
        component: () => import('@/views/admin/layout.vue'),
        meta: { title: '超级管理员', icon: 'CrownOutlined' },
        children: [
          {
            path: '',
            name: 'AdminDashboard',
            component: () => import('@/views/admin/index.vue'),
            meta: { title: '功能总览', icon: 'DashboardOutlined' },
          },
          {
            path: 'platform-zones',
            name: 'AdminPlatformZones',
            component: () => import('@/views/admin/platform-zones.vue'),
            meta: { title: '三区治理', icon: 'AppstoreOutlined' },
          },
          {
            path: 'platform-registry',
            name: 'AdminPlatformRegistry',
            component: () => import('@/views/admin/platform-registry.vue'),
            meta: { title: '平台来源审计', icon: 'GlobalOutlined' },
          },
          {
            path: 'platform-credentials',
            name: 'AdminPlatformCredentials',
            component: () => import('@/views/admin/platform-credentials.vue'),
            meta: { title: '平台凭证', icon: 'KeyOutlined' },
          },
          // 附属执行台（SYSTEM-LOCK-02 第⑤⑥子系统）：路径必须与
          // constants/annexModules.ts 的 adminPath 及 platformShellMenu 的菜单项一致，
          // 即 /admin/annex/*。此前误挂在 system 子级下（实际解析成
          // /admin/system/annex/*），导致菜单点进去渲染 NotFound「无入口」。
          {
            path: 'annex/trade-ai',
            name: 'AnnexTradeAi',
            component: () => import('@/views/annex/AnnexEmbedPage.vue'),
            meta: { title: 'TradeAI 执行台', group: 'biz', icon: 'ThunderboltOutlined', annexKey: 'trade-ai' },
          },
          {
            path: 'annex/goodjob',
            name: 'AnnexGoodjob',
            component: () => import('@/views/annex/AnnexEmbedPage.vue'),
            meta: { title: 'GoodJob 执行台', group: 'biz', icon: 'GlobalOutlined', annexKey: 'goodjob' },
          },
          {
            path: 'annex/goodjob/tickets',
            name: 'AnnexGoodjobTickets',
            component: () => import('@/views/annex/AnnexEmbedPage.vue'),
            meta: { title: 'GoodJob CRM · 票据中心管理', group: 'biz', icon: 'GlobalOutlined', annexKey: 'goodjob', annexModule: 'tickets' },
          },
          {
            path: 'annex/goodjob/customers',
            name: 'AnnexGoodjobCustomers',
            component: () => import('@/views/annex/AnnexEmbedPage.vue'),
            meta: { title: 'GoodJob CRM · 客户管理', group: 'biz', icon: 'GlobalOutlined', annexKey: 'goodjob', annexModule: 'customers' },
          },
          {
            path: 'demo-rehearsal',
            name: 'AdminDemoRehearsal',
            component: () => import('@/views/admin/demo-rehearsal.vue'),
            meta: { title: '七步彩排', icon: 'PlayCircleOutlined' },
          },
          {
            path: 'capability-hub',
            name: 'AdminCapabilityHub',
            component: () => import('@/views/admin/capability-hub.vue'),
            meta: { title: '能力导航', icon: 'PartitionOutlined' },
          },
          {
            path: 'aggregation',
            name: 'AdminAggregation',
            component: () => import('@/views/admin/aggregation.vue'),
            meta: { title: '数据中心', icon: 'BarChartOutlined' },
          },
          {
            path: 'traffic-board',
            name: 'AdminTrafficBoard',
            component: () => import('@/views/admin/traffic-board.vue'),
            meta: { title: '流量看板', icon: 'LineChartOutlined' },
          },
          {
            path: 'founder-diagnostics',
            name: 'AdminFounderDiagnostics',
            component: () => import('@/views/admin/founder-diagnostics.vue'),
            meta: { title: '创始人诊断', icon: 'SafetyCertificateOutlined' },
          },
          {
            path: 'attribution',
            name: 'AdminAttribution',
            component: () => import('@/views/admin/attribution/index.vue'),
            meta: { title: '全链路归因', icon: 'FunnelPlotOutlined' },
          },
          {
            path: 'finance',
            name: 'AdminFinance',
            component: () => import('@/views/admin/finance/index.vue'),
            meta: { title: '财务中台', icon: 'AccountBookOutlined' },
          },
          {
            path: 'finance/invoices',
            name: 'AdminFinanceInvoices',
            component: () => import('@/views/admin/finance/invoice-applications.vue'),
            meta: { title: '开票审核', icon: 'FileTextOutlined' },
          },
          {
            path: 'finance/commissions',
            name: 'AdminFinanceCommissions',
            component: () => import('@/views/admin/finance/commissions.vue'),
            meta: { title: '分润结算', icon: 'MoneyCollectOutlined' },
          },
          {
            path: 'finance/commission-rules',
            name: 'AdminFinanceCommissionRules',
            component: () => import('@/views/admin/finance/commission-rules.vue'),
            meta: { title: '分润规则', icon: 'PercentageOutlined' },
          },
          {
            path: 'finance/payment-ops',
            name: 'AdminFinancePaymentOps',
            component: () => import('@/views/admin/finance/payment-ops.vue'),
            meta: { title: '支付码与接口', icon: 'PayCircleOutlined' },
          },
          {
            path: 'finance/payment-orders',
            name: 'AdminFinancePaymentOrders',
            component: () => import('@/views/admin/finance/payment-orders.vue'),
            meta: { title: '租户支付订单', icon: 'OrderedListOutlined' },
          },
          {
            path: 'finance/ip-pool',
            name: 'AdminFinanceIpPool',
            component: () => import('@/views/admin/finance/ip-pool.vue'),
            meta: { title: '静态 IP 池', icon: 'GlobalOutlined' },
          },
          // 层级管理模块
          {
            path: 'hierarchy',
            name: 'AdminHierarchy',
            component: () => import('@/views/admin/hierarchy/index.vue'),
            meta: { title: '层级管理', group: 'core', icon: 'AppstoreOutlined' },
          },
          // 回收站
          {
            path: 'recycle-bin',
            name: 'AdminRecycleBin',
            component: () => import('@/views/admin/recycle-bin/index.vue'),
            meta: { title: '回收站', icon: 'DeleteOutlined' },
          },
          // GEO 技术雷达
          {
            path: 'tech-radar',
            name: 'AdminTechRadar',
            component: () => import('@/views/admin/tech-radar/index.vue'),
            meta: { title: 'GEO 技术雷达', icon: 'RadarChartOutlined' },
          },
          // 入驻引导
          {
            path: 'onboarding',
            name: 'AdminOnboarding',
            component: () => import('@/views/admin/onboarding/index.vue'),
            meta: { title: '入驻引导', icon: 'RocketOutlined' },
          },
          // 系统管理模块
          {
            path: 'system',
            name: 'AdminSystem',
            component: () => import('@/views/admin/system/index.vue'),
            meta: { title: '系统管理', icon: 'SettingsOutlined' },
            children: [
              {
                path: '',
                name: 'SystemOverview',
                component: () => import('@/views/admin/system/overview.vue'),
                meta: { title: '系统概览', group: 'core', icon: 'MonitorOutlined' },
              },
              {
                path: 'users',
                name: 'SystemUsers',
                component: () => import('@/views/admin/system/users.vue'),
                meta: { title: '用户管理', group: 'core', icon: 'UserOutlined' },
              },
              {
                path: 'permissions',
                name: 'SystemPermissions',
                component: () => import('@/views/admin/system/permissions.vue'),
                meta: { title: '权限管理', group: 'core', icon: 'LockOutlined' },
              },
              {
                path: 'agent-capabilities',
                name: 'SystemAgentCapabilities',
                component: () => import('@/views/admin/system/agent-capabilities.vue'),
                meta: { title: '代理能力划拨', group: 'biz', icon: 'PartitionOutlined', skipCapabilityGuard: true },
              },
              {
                path: 'logs',
                name: 'SystemLogs',
                component: () => import('@/views/admin/system/logs.vue'),
                meta: { title: '系统日志', group: 'ops', icon: 'FileTextOutlined' },
              },
              {
                path: 'config',
                name: 'SystemConfig',
                component: () => import('@/views/admin/system/config.vue'),
                meta: { title: '系统配置', group: 'core', icon: 'WrenchOutlined' },
              },
              {
                path: 'account-bindings',
                name: 'SystemAccountBindings',
                component: () => import('@/views/admin/system/account-bindings.vue'),
                meta: { title: '账号绑定', group: 'biz', icon: 'LinkOutlined' },
              },
              {
                path: 'integrations-stack',
                name: 'SystemIntegrationsStack',
                component: () => import('@/views/admin/system/integrations-stack.vue'),
                meta: { title: '集成栈', group: 'biz', icon: 'ApiOutlined' },
              },
              {
                path: 'license',
                name: 'SystemLicense',
                component: () => import('@/views/admin/system/license.vue'),
                meta: { title: '许可证管理', group: 'biz', icon: 'KeyOutlined' },
              },
              {
                path: 'storage-provision',
                name: 'SystemStorageProvision',
                component: () => import('@/views/admin/system/storage-provision.vue'),
                meta: { title: '存储开通', group: 'ops', icon: 'CloudUploadOutlined' },
              },
              {
                path: 'progress-board',
                name: 'SystemProgressBoard',
                component: () => import('@/views/admin/system/progress-board.vue'),
                meta: { title: '开发进度', group: 'dev', icon: 'BarChartOutlined' },
              },
              {
                path: 'command-center',
                name: 'SystemCommandCenter',
                component: () => import('@/views/admin/system/command-center.vue'),
                meta: { title: '超管司令部', group: 'dev', icon: 'DashboardOutlined' },
              },
              {
                path: 'ecc-hangar',
                name: 'SystemEccHangar',
                component: () => import('@/views/admin/system/ecc-hangar.vue'),
                meta: { title: 'ECC 专家机库', group: 'dev', icon: 'TeamOutlined' },
              },
              {
                path: 'deerflow-monitor',
                name: 'SystemDeerflowMonitor',
                component: () => import('@/views/admin/system/deerflow-monitor.vue'),
                meta: { title: 'DeerFlow 队列', group: 'ops', icon: 'ClusterOutlined' },
              },
              {
                path: 'publish-history',
                name: 'SystemPublishHistory',
                component: () => import('@/views/admin/system/publish-history.vue'),
                meta: { title: '统一发布历史', group: 'ops', icon: 'HistoryOutlined' },
              },
              {
                path: 'rank-scheduler',
                name: 'SystemRankScheduler',
                component: () => import('@/views/admin/system/rank-scheduler.vue'),
                meta: { title: 'Rank Scheduler', group: 'dev', icon: 'LineChartOutlined' },
              },
              {
                path: 'greedy-hub',
                name: 'SystemGreedyHub',
                component: () => import('@/views/admin/system/greedy-hub.vue'),
                meta: { title: '摸金校尉总控', group: 'game', icon: 'FundProjectionScreenOutlined' },
              },
              {
                path: 'greedy-cumulative',
                name: 'SystemGreedyCumulative',
                component: () => import('@/views/admin/system/greedy-cumulative.vue'),
                meta: { title: '摸金累计看板', group: 'game', icon: 'FundOutlined' },
              },
              {
                path: 'greedy-contest-leaderboard',
                name: 'SystemGreedyContestLeaderboard',
                component: () => import('@/views/admin/system/greedy-contest-leaderboard.vue'),
                meta: { title: '挣钱大赛', group: 'game', icon: 'TrophyOutlined' },
              },
              {
                path: 'greedy-publish-queue',
                name: 'SystemGreedyPublishQueue',
                component: () => import('@/views/admin/system/greedy-publish-queue.vue'),
                meta: { title: 'L4 发布队列', group: 'game', icon: 'SendOutlined' },
              },
              {
                path: 'survival-dashboard',
                name: 'SystemSurvivalDashboard',
                component: () => import('@/views/admin/system/survival-dashboard.vue'),
                meta: { title: 'Survival 台账', group: 'game', icon: 'BankOutlined' },
              },
              {
                path: 'greedy-expert-memory',
                name: 'SystemGreedyExpertMemory',
                component: () => import('@/views/admin/system/greedy-expert-memory.vue'),
                meta: { title: '专家记忆', group: 'game', icon: 'ReadOutlined' },
              },
              {
                path: 'paperclip-dashboard',
                name: 'PaperclipDashboard',
                component: () => import('@/views/admin/paperclip/dashboard.vue'),
                meta: { title: 'Agent 编排总控', group: 'orchestration', icon: 'ApartmentOutlined' },
              },
              {
                path: 'paperclip-org-chart',
                name: 'PaperclipOrgChart',
                component: () => import('@/views/admin/paperclip/org-chart.vue'),
                meta: { title: '组织架构', group: 'orchestration', icon: 'ClusterOutlined' },
              },
              {
                path: 'paperclip-goals',
                name: 'PaperclipGoals',
                component: () => import('@/views/admin/paperclip/goals.vue'),
                meta: { title: '目标管理', group: 'orchestration', icon: 'AimOutlined' },
              },
              {
                path: 'paperclip-heartbeats',
                name: 'PaperclipHeartbeats',
                component: () => import('@/views/admin/paperclip/heartbeats.vue'),
                meta: { title: '心跳监控', group: 'ops', icon: 'HeartOutlined' },
              },
              {
                path: 'paperclip-approvals',
                name: 'PaperclipApprovals',
                component: () => import('@/views/admin/paperclip/approvals.vue'),
                meta: { title: '审批管理', group: 'orchestration', icon: 'AuditOutlined' },
              },
              {
                path: 'ops-wrap',
                name: 'SystemOpsWrap',
                component: () => import('@/views/admin/system/ops-wrap.vue'),
                meta: { title: '运维批处理', group: 'ops', icon: 'ThunderboltOutlined' },
              },
            ],
          },
          // AI中心模块（统一AI功能入口）
          {
            path: 'ai-center',
            name: 'AdminAICenter',
            component: () => import('@/views/admin/ai-center/index.vue'),
            meta: { title: 'AI中心', icon: 'BrainOutlined' },
            children: [
              {
                path: '',
                name: 'AICenterDashboard',
                component: () => import('@/views/admin/ai-center/dashboard.vue'),
                meta: { title: '控制台', group: 'core', icon: 'CpuOutlined' },
              },
              {
                path: 'models',
                name: 'AICenterModels',
                component: () => import('@/views/admin/ai-center/models.vue'),
                meta: { title: '模型管理', group: 'core', icon: 'LayersOutlined' },
              },
              {
                path: 'content',
                name: 'AICenterContent',
                component: () => import('@/views/admin/ai-center/content.vue'),
                meta: { title: 'AI内容助手', group: 'content', icon: 'EditOutlined' },
              },
              {
                path: 'analytics',
                name: 'AICenterAnalytics',
                component: () => import('@/views/admin/ai-center/analytics.vue'),
                meta: { title: '智能分析', group: 'analytics', icon: 'BarChartOutlined' },
              },
              {
                path: 'logs',
                name: 'AICenterLogs',
                component: () => import('@/views/admin/ai-center/logs.vue'),
                meta: { title: '调用日志', group: 'ops', icon: 'FileTextOutlined' },
              },
              {
                path: 'provider-setup',
                name: 'AICenterProviderSetup',
                component: () => import('@/views/admin/ai-center/provider-setup.vue'),
                meta: { title: '模型配置', icon: 'ApiOutlined' },
              },
              {
                path: 'scenario-models',
                name: 'AICenterScenarioModels',
                component: () => import('@/views/admin/ai-center/scenario-models.vue'),
                meta: { title: '场景模型切换', icon: 'SwapOutlined' },
              },
              {
                path: 'usage',
                name: 'AICenterUsage',
                component: () => import('@/views/admin/ai-center/usage.vue'),
                meta: { title: '用量监控', group: 'analytics', icon: 'BarChartOutlined' },
              },
              {
                path: 'knowledge',
                name: 'AICenterKnowledge',
                component: () => import('@/views/admin/ai-center/knowledge.vue'),
                meta: { title: '知识库', group: 'content', icon: 'ReadOutlined' },
              },
              {
                path: 'article-generator',
                name: 'AICenterArticleGenerator',
                component: () => import('@/views/admin/ai-center/article-generator.vue'),
                meta: { title: '文章生成器', group: 'content', icon: 'FileTextOutlined' },
              },
              {
                path: 'article-to-video',
                name: 'AICenterArticleToVideo',
                component: () => import('@/views/admin/ai-center/article-to-video.vue'),
                meta: { title: '文章转视频', group: 'content', icon: 'VideoCameraOutlined' },
              },
              {
                path: 'browser-companion',
                name: 'AICenterBrowserCompanion',
                component: () => import('@/views/admin/ai-center/browser-companion-bridge.vue'),
                meta: { title: '浏览器伴侣工作台', icon: 'ChromeOutlined' },
              },
              {
                path: 'skill-store',
                name: 'AICenterSkillStore',
                component: () => import('@/views/ai-center/skill-store.vue'),
                meta: { title: '技能商店', group: 'tools', icon: 'ShopOutlined' },
              },
            ],
          },
          // AI 引擎（超管套件页面，对齐菜单 /admin/ai-engine）
          {
            path: 'ai-engine',
            name: 'AdminAIEngine',
            component: () => import('@/views/admin/ai-engine/index.vue'),
            meta: { title: 'AI引擎', icon: 'ApiOutlined' },
            children: [
              {
                path: '',
                name: 'AIEngineOverview',
                component: () => import('@/views/admin/ai-engine/overview.vue'),
                meta: { title: 'AI引擎概览', icon: 'ApiOutlined' },
              },
              {
                path: 'analytics',
                name: 'AIEngineAnalytics',
                component: () => import('@/views/admin/ai-engine/analytics.vue'),
                meta: { title: 'AI分析', icon: 'BarChartOutlined' },
              },
              {
                path: 'tasks',
                name: 'AIEngineTasks',
                component: () => import('@/views/admin/ai-engine/tasks.vue'),
                meta: { title: '任务看板', icon: 'UnorderedListOutlined' },
              },
              {
                path: 'prompts',
                name: 'AIEnginePrompts',
                component: () => import('@/views/admin/ai-engine/prompts.vue'),
                meta: { title: '提示词', icon: 'EditOutlined' },
              },
              {
                path: 'models',
                name: 'AIEngineModels',
                component: () => import('@/views/admin/ai-engine/models.vue'),
                meta: { title: '模型', icon: 'LayersOutlined' },
              },
              {
                path: 'trade-intel',
                name: 'AIEngineTradeIntel',
                component: () => import('@/views/admin/ai-engine/trade-intel.vue'),
                meta: { title: '出海参谋', icon: 'GlobalOutlined' },
              },
            ],
          },
          // GEO 引擎：各大模型关键词收录
          {
            path: 'geo-engine',
            name: 'AdminGEOEngine',
            component: () => import('@/views/admin/geo-engine/index.vue'),
            meta: { title: 'GEO引擎模型收录', icon: 'SearchOutlined' },
          },
          // 静态 IP 槽位（原 V2Ray 入口已重定向，内部运维见 /admin/v2ray-legacy）
          {
            path: 'v2ray',
            redirect: '/admin/finance/ip-pool',
          },
          {
            path: 'egress',
            redirect: '/admin/finance/ip-pool',
          },
          {
            path: 'v2ray-legacy',
            name: 'AdminV2RayLegacy',
            component: () => import('@/views/admin/v2ray/index.vue'),
            meta: { title: 'V2Ray运维(内部)', icon: 'GlobalOutlined', hideInMenu: true },
            children: [
              { path: '', name: 'V2RayLegacyRoot', redirect: '/admin/v2ray-legacy/servers' },
              {
                path: 'servers', name: 'V2RayServers',
                component: () => import('@/views/admin/v2ray/servers.vue'),
                meta: { title: '服务器配置' },
              },
            ],
          },
          // 代码工具模块
          {
            path: 'code-tools',
            name: 'AdminCodeTools',
            component: () => import('@/views/admin/code-tools/index.vue'),
            meta: { title: '代码工具', icon: 'CodeOutlined' },
            children: [
              {
                path: '',
                name: 'CodeToolsOverview',
                component: () => import('@/views/admin/code-tools/overview.vue'),
                meta: { title: '工具概览', icon: 'ToolsOutlined' },
              },
              {
                path: 'generator',
                name: 'CodeGenerator',
                component: () => import('@/views/admin/code-tools/generator.vue'),
                meta: { title: '代码生成', icon: 'SparklesOutlined' },
              },
              {
                path: 'refactor',
                name: 'CodeRefactor',
                component: () => import('@/views/admin/code-tools/refactor.vue'),
                meta: { title: '代码重构', icon: 'RepeatOutlined' },
              },
              {
                path: 'debug',
                name: 'CodeDebug',
                component: () => import('@/views/admin/code-tools/debug.vue'),
                meta: { title: '代码调试', icon: 'BugOutlined' },
              },
              {
                path: 'format',
                name: 'CodeFormat',
                component: () => import('@/views/admin/code-tools/format.vue'),
                meta: { title: '代码格式化', icon: 'AlignLeftOutlined' },
              },
              {
                path: 'scanner',
                name: 'CodeScanner',
                component: () => import('@/views/admin/code-tools/scanner.vue'),
                meta: { title: '代码扫描', icon: 'SearchOutlined' },
              },
              {
                path: 'review',
                name: 'CodeReview',
                component: () => import('@/views/admin/code-tools/review.vue'),
                meta: { title: '代码审查', icon: 'FileSearchOutlined' },
              },
              /** 历史/文案别名，避免按钮跳 404 */
              { path: 'editor', redirect: '/admin/code-tools/format' },
              { path: 'bug-fix', redirect: '/admin/code-tools/debug' },
              { path: 'translate', redirect: '/admin/code-tools/refactor' },
              { path: 'generate', redirect: '/admin/code-tools/generator' },
            ],
          },
          // 产品图片空间（超管 · 文件/图片上传）
          {
            path: 'file-manager',
            name: 'AdminFileManager',
            component: () => import('@/views/admin/file-manager/index.vue'),
            meta: { title: '产品图片空间', icon: 'PictureOutlined', productImageSpaceMode: true },
            children: [
              {
                path: '',
                name: 'FileManagerOverview',
                component: () => import('@/views/admin/file-manager/overview.vue'),
                meta: { title: '产品图片空间', icon: 'PictureOutlined', productImageSpaceMode: true },
              },
              {
                path: 'scan',
                name: 'FileScan',
                component: () => import('@/views/admin/file-manager/scan.vue'),
                meta: { title: '文件扫描', icon: 'SearchOutlined' },
              },
              {
                path: 'search',
                name: 'FileSearch',
                component: () => import('@/views/admin/file-manager/search.vue'),
                meta: { title: '全局检索', icon: 'DatabaseOutlined' },
              },
              {
                path: 'history',
                name: 'FileHistory',
                component: () => import('@/views/admin/file-manager/history.vue'),
                meta: { title: '历史记录', icon: 'HistoryOutlined' },
              },
            ],
          },
          { path: 'media-library', redirect: '/admin/file-manager' },
          { path: 'image-space', redirect: '/admin/file-manager' },
          {
            path: 'video-space',
            name: 'AdminVideoSpace',
            component: () => import('@/views/admin/file-manager/overview.vue'),
            meta: { title: '视频空间', icon: 'VideoCameraOutlined', videoSpaceMode: true },
          },
          { path: 'video-library', redirect: '/admin/video-space' },
          // 安全合规模块
          {
            path: 'security',
            name: 'AdminSecurity',
            component: () => import('@/views/admin/security/index.vue'),
            meta: { title: '安全合规', icon: 'ShieldOutlined' },
            children: [
              {
                path: '',
                name: 'SecurityOverview',
                component: () => import('@/views/admin/security/overview.vue'),
                meta: { title: '安全概览', icon: 'SecurityScanOutlined' },
              },
              {
                path: 'vulnerability',
                name: 'SecurityVulnerability',
                component: () => import('@/views/admin/security/vulnerability.vue'),
                meta: { title: '漏洞扫描', icon: 'AlertTriangleOutlined' },
              },
              {
                path: 'audit',
                name: 'SecurityAudit',
                component: () => import('@/views/admin/security/audit.vue'),
                meta: { title: '安全审计', icon: 'FileSearchOutlined' },
              },
              {
                path: 'compliance',
                name: 'SecurityCompliance',
                component: () => import('@/views/admin/security/compliance.vue'),
                meta: { title: '合规检查', icon: 'CheckCircleOutlined' },
              },
            ],
          },
          // 自动化模块
          {
            path: 'automation',
            name: 'AdminAutomation',
            component: () => import('@/views/admin/automation/index.vue'),
            meta: { title: '自动化', icon: 'ZapOutlined' },
            children: [
              {
                path: '',
                name: 'AutomationOverview',
                component: () => import('@/views/admin/automation/overview.vue'),
                meta: { title: '自动化概览', icon: 'TimerOutlined' },
              },
              {
                path: 'scripts',
                name: 'AutomationScripts',
                component: () => import('@/views/admin/automation/scripts.vue'),
                meta: { title: '脚本管理', icon: 'PlayCircleOutlined' },
              },
              {
                path: 'scheduler',
                name: 'AutomationScheduler',
                component: () => import('@/views/admin/automation/scheduler.vue'),
                meta: { title: '任务调度', icon: 'CalendarOutlined' },
              },
              {
                path: 'workflows',
                name: 'AutomationWorkflows',
                component: () => import('@/views/admin/automation/workflows.vue'),
                meta: { title: '工作流', icon: 'GitBranchOutlined' },
              },
            ],
          },
          {
            path: 'projects',
            name: 'AdminProjects',
            component: () => import('@/views/admin/projects/index.vue'),
            meta: { title: '项目中心', icon: 'FolderOutlined' },
            children: [
              {
                path: '',
                name: 'ProjectsOverview',
                component: () => import('@/views/admin/projects/overview.vue'),
                meta: { title: '项目概览', icon: 'AppstoreOutlined' },
              },
            ],
          },
          {
            path: 'runtime',
            name: 'AdminRuntime',
            component: () => import('@/views/admin/runtime/index.vue'),
            meta: { title: '运行时', icon: 'CloudOutlined' },
            children: [
              {
                path: '',
                name: 'RuntimeOverview',
                component: () => import('@/views/admin/runtime/overview.vue'),
                meta: { title: '运行概览', icon: 'MonitorOutlined' },
              },
            ],
          },
          {
            path: 'scheduler-hub',
            name: 'AdminSchedulerHub',
            component: () => import('@/views/admin/scheduler/index.vue'),
            meta: { title: '调度中心', icon: 'CalendarOutlined' },
            children: [
              {
                path: '',
                name: 'SchedulerHubOverview',
                component: () => import('@/views/admin/scheduler/overview.vue'),
                meta: { title: '调度概览', icon: 'ClockCircleOutlined' },
              },
            ],
          },
        ],
      },
      // ========== SEO矩阵系统 ==========
      {
        path: 'seo-matrix',
        name: 'SEOMatrix',
        component: () => import('@/views/seo-matrix/index.vue'),
        redirect: { name: 'SEOMatrixDashboard' },
        meta: { title: 'SEO矩阵系统', icon: 'GridOutlined' },
        children: [
          {
            path: 'dashboard',
            name: 'SEOMatrixDashboard',
            component: () => import('@/views/seo-matrix/dashboard.vue'),
            meta: { title: '数据看板', icon: 'DashboardOutlined' },
          },
          {
            path: 'settings',
            name: 'SEOMatrixSettings',
            component: () => import('@/views/seo-matrix/settings.vue'),
            meta: { title: '系统设置', icon: 'SettingsOutlined' },
          },
          {
            path: 'regions',
            name: 'SEOMatrixRegions',
            component: () => import('@/views/seo-matrix/regions.vue'),
            meta: { title: '地域词库', icon: 'MapOutlined' },
          },
          {
            path: 'keywords',
            name: 'SEOMatrixKeywords',
            component: () => import('@/views/seo-matrix/keywords.vue'),
            meta: { title: '关键词管理', icon: 'SearchOutlined' },
          },
          {
            path: 'content',
            name: 'SEOMatrixContent',
            component: () => import('@/views/seo-matrix/content.vue'),
            meta: { title: '文案生成', icon: 'FileTextOutlined' },
          },
          {
            path: 'publish',
            name: 'SEOMatrixPublish',
            component: () => import('@/views/seo-matrix/publish.vue'),
            meta: { title: '多平台分发', icon: 'SendOutlined' },
          },
          {
            path: 'inclusion',
            name: 'SEOMatrixInclusion',
            component: () => import('@/views/seo-matrix/inclusion.vue'),
            meta: { title: '收录监控', icon: 'EyeOutlined' },
          },
          {
            path: 'growth-tools',
            name: 'SEOMatrixGrowthTools',
            component: () => import('@/views/seo-matrix/growth-tools.vue'),
            meta: { title: '增长工具', icon: 'ToolOutlined' },
          },
        ],
      },
      // ========== 原有业务模块 ==========
      {
        path: 'products',
        name: 'Products',
        component: () => import('@/views/products/index.vue'),
        meta: { title: '产品管理', icon: 'PackageOutlined' },
      },
      {
        path: 'products/edit/:id',
        name: 'ProductEdit',
        component: () => import('@/views/products/edit.vue'),
        meta: { title: '编辑产品', hidden: true },
      },
      {
        path: 'products/categories',
        name: 'Categories',
        component: () => import('@/views/products/categories.vue'),
        meta: { title: '分类管理', icon: 'FolderOpenOutlined' },
      },
      {
        path: 'seo',
        name: 'SEO',
        component: () => import('@/views/seo/index.vue'),
        meta: { title: 'SEO概览', icon: 'SearchOutlined' },
      },
      {
        path: 'seo/llms-txt',
        name: 'LLMSTxt',
        component: () => import('@/views/seo/llms-txt.vue'),
        meta: { title: 'LLMs.txt生成', icon: 'FileTextOutlined' },
      },
      {
        path: 'seo/content-optimizer',
        name: 'ContentOptimizer',
        component: () => import('@/views/seo/content-optimizer.vue'),
        meta: { title: 'AI内容优化', icon: 'MagicOutlined' },
      },
      {
        path: 'seo/site-audit',
        name: 'SiteAudit',
        component: () => import('@/views/seo/site-audit.vue'),
        meta: { title: '站点审计', icon: 'AuditOutlined' },
      },
      {
        path: 'seo/batch-seo',
        name: 'BatchSEO',
        component: () => import('@/views/seo/batch-seo.vue'),
        meta: { title: '批量SEO管理', icon: 'CopyOutlined' },
      },
      {
        path: 'seo/schema-markup',
        name: 'SchemaMarkup',
        component: () => import('@/views/seo/schema-markup.vue'),
        meta: { title: 'Schema标记管理', icon: 'CodeOutlined' },
      },
      {
        path: 'seo/eeat',
        name: 'EEAT',
        component: () => import('@/views/seo/eeat.vue'),
        meta: { title: 'EEAT评分管理', icon: 'AwardOutlined' },
      },
      {
        path: 'seo/compliance',
        name: 'Compliance',
        component: () => import('@/views/seo/compliance.vue'),
        meta: { title: '广告法合规审查', icon: 'SafetyOutlined' },
      },
      {
        path: 'seo/keyword-ranking',
        name: 'KeywordRanking',
        component: () => import('@/views/seo/keyword-ranking.vue'),
        meta: { title: '关键词排名追踪', icon: 'RiseOutlined' },
      },
      {
        path: 'seo/baidu-tools',
        name: 'BaiduTools',
        component: () => import('@/views/seo/baidu-tools.vue'),
        meta: { title: '百度站长工具', icon: 'SearchOutlined' },
      },
      {
        path: 'seo/building-wiki',
        name: 'BuildingWiki',
        component: () => import('@/views/seo/building-wiki.vue'),
        meta: { title: 'AI建材百科', icon: 'ReadOutlined' },
      },
      {
        path: 'seo/performance',
        name: 'SEOPerformance',
        component: () => import('@/views/seo/performance.vue'),
        meta: { title: '性能与安全监控', icon: 'DashboardOutlined' },
      },
      {
        path: 'publish/unified',
        name: 'UnifiedPublish',
        component: () => import('@/views/publish/unified.vue'),
        meta: { title: '统一发布台', icon: 'RocketOutlined' },
      },
      {
        path: 'hub',
        name: 'ContentHub',
        component: () => import('@/views/admin/hub/index.vue'),
        meta: { title: '总站枢纽', icon: 'GlobalOutlined' },
      },
      {
        path: 'content',
        name: 'Content',
        component: () => import('@/views/content/index.vue'),
        meta: { title: '内容管理', icon: 'FileOutlined' },
      },
      {
        path: 'content/edit/:id',
        name: 'ContentEdit',
        component: () => import('@/views/content/edit.vue'),
        meta: { title: '编辑内容', hidden: true },
      },
      {
        path: 'cases',
        name: 'Cases',
        component: () => import('@/views/cases/index.vue'),
        meta: { title: '案例管理', icon: 'PictureOutlined' },
      },
      {
        path: 'cases/edit/:id',
        name: 'CaseEdit',
        component: () => import('@/views/cases/edit.vue'),
        meta: { title: '编辑案例', hidden: true },
      },
      {
        path: 'inquiries',
        name: 'Inquiries',
        component: () => import('@/views/inquiries/index.vue'),
        meta: { title: '询盘管理', icon: 'MessageSquareOutlined' },
      },
      {
        path: 'inquiries/im-routing',
        name: 'InquiriesIMRouting',
        component: () => import('@/views/inquiries/im-routing.vue'),
        meta: { title: 'IM 全渠道', icon: 'MessageOutlined', hideInMenu: true },
      },
      // ========== AccioWork 销售模块 ==========
      {
        path: 'sales',
        name: 'Sales',
        component: () => import('@/views/sales/index.vue'),
        redirect: { name: 'SalesDashboard' },
        meta: { title: '销售中心', icon: 'ShopOutlined' },
        children: [
          {
            path: 'dashboard',
            name: 'SalesDashboard',
            component: () => import('@/views/sales/dashboard.vue'),
            meta: { title: '销售工作台', icon: 'DashboardOutlined' },
          },
          {
            path: 'customer-finder',
            name: 'CustomerFinder',
            component: () => import('@/views/sales/CustomerFinder.vue'),
            meta: { title: '客户开发', icon: 'UserAddOutlined' },
          },
          {
            path: 'auto-negotiator',
            name: 'AutoNegotiator',
            component: () => import('@/views/sales/AutoNegotiator.vue'),
            meta: { title: '自动谈单', icon: 'MessageOutlined' },
          },
          {
            path: 'email-automation',
            name: 'EmailAutomation',
            component: () => import('@/views/sales/EmailAutomation.vue'),
            meta: { title: '开发信管理', icon: 'MailOutlined' },
          },
          {
            path: 'opportunities',
            name: 'OpportunityBoard',
            component: () => import('@/views/sales/OpportunityBoard.vue'),
            meta: { title: '销售管道看板', icon: 'FunnelPlotOutlined' },
          },
          {
            path: 'rfqs',
            name: 'RfqPanel',
            component: () => import('@/views/sales/RfqPanel.vue'),
            meta: { title: 'RFQ 需求单', icon: 'FileSearchOutlined' },
          },
          {
            path: 'company-360',
            name: 'CompanyAccount360',
            component: () => import('@/views/sales/CompanyAccount360.vue'),
            meta: { title: 'Company 360', icon: 'GlobalOutlined' },
          },
          {
            path: 'quotes',
            name: 'QuotesPanel',
            component: () => import('@/views/sales/QuotesPanel.vue'),
            meta: { title: '报价管理', icon: 'DollarOutlined' },
          },
          {
            path: 'tasks',
            name: 'SalesTaskCenter',
            component: () => import('@/views/sales/SalesTaskCenter.vue'),
            meta: { title: '销售任务中心', icon: 'CheckSquareOutlined' },
          },
        ],
      },
      {
        path: 'news',
        name: 'News',
        component: () => import('@/views/news/index.vue'),
        meta: { title: '新闻管理', icon: 'ReadOutlined' },
      },
      {
        path: 'compliance',
        name: 'ComplianceHub',
        component: () => import('@/views/compliance/index.vue'),
        meta: { title: '合规治理', icon: 'SafetyCertificateOutlined' },
      },
      {
        path: 'ai-config',
        name: 'AiConfig',
        component: () => import('@/views/integrations/AiConfig.vue'),
        meta: { title: 'AI配置', icon: 'ApiOutlined' },
      },
      {
        path: 'feishu',
        name: 'Feishu',
        component: () => import('@/views/integrations/Feishu.vue'),
        meta: { title: '飞书集成', icon: 'LinkOutlined' },
      },
      {
        path: 'ab-test',
        name: 'AbTest',
        component: () => import('@/views/experiments/AbTest.vue'),
        meta: { title: 'A/B测试', icon: 'ExperimentOutlined' },
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/system/users.vue'),
        meta: { title: '用户管理', icon: 'UserOutlined' },
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('@/views/system/analytics.vue'),
        meta: { title: '数据分析', icon: 'BarChartOutlined' },
      },
      {
        path: 'operations/traffic',
        name: 'OperationsTrafficBoard',
        component: () => import('@/views/operations/traffic-board.vue'),
        meta: { title: '流量看板', icon: 'LineChartOutlined' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/system/settings.vue'),
        meta: { title: '系统设置', icon: 'SettingOutlined' },
        children: [
          {
            path: '',
            name: 'SettingsMain',
            component: () => import('@/views/system/settings-main.vue'),
            meta: { title: '基本设置', icon: 'SettingOutlined' },
          },
          {
            path: 'drag-module',
            name: 'DragModule',
            component: () => import('@/views/system/drag-module.vue'),
            meta: { title: '自定义拖拽模块', icon: 'SettingOutlined' },
          },
          {
            path: 'effects',
            name: 'Effects',
            component: () => import('@/views/system/effects.vue'),
            meta: { title: '自定义特效组件', icon: 'PictureOutlined' },
          },
        ],
      },
      // ========== 智能体协同中心 ==========
      {
        path: 'agent-hub',
        name: 'AgentHub',
        component: () => import('@/views/agent-hub/index.vue'),
        redirect: { name: 'AgentHubDashboard' },
        meta: { title: '智能体协同', icon: 'RobotOutlined' },
        children: [
          {
            path: 'dashboard',
            name: 'AgentHubDashboard',
            component: () => import('@/views/agent-hub/dashboard.vue'),
            meta: { title: '协同看板', icon: 'DashboardOutlined' },
          },
          {
            path: 'mcp-bridge',
            name: 'MCPBridge',
            component: () => import('@/views/agent-hub/mcp-bridge.vue'),
            meta: { title: 'MCP桥接', icon: 'ApiOutlined' },
          },
          {
            path: 'task-orchestrator',
            name: 'TaskOrchestrator',
            component: () => import('@/views/agent-hub/task-orchestrator.vue'),
            meta: { title: '任务调度', icon: 'CalendarOutlined' },
          },
          {
            // 统一编排链（AiTask / Hermes 任务图）——区别于上面的 DeerFlow 队列视图
            path: 'task-graph',
            name: 'TaskGraph',
            component: () => import('@/views/agent-hub/task-graph.vue'),
            meta: { title: '任务图', icon: 'PartitionOutlined' },
          },
          {
            path: 'execution-review',
            name: 'ExecutionReview',
            component: () => import('@/views/agent-hub/execution-review.vue'),
            meta: { title: '执行复盘', icon: 'HistoryOutlined' },
          },
        ],
      },
      // ========== 多媒体内容工厂 ==========
      {
        path: 'media-factory',
        name: 'MediaFactory',
        component: () => import('@/views/media-factory/index.vue'),
        redirect: { name: 'MediaFactoryDashboard' },
        meta: { title: '多媒体工厂', icon: 'VideoCameraOutlined' },
        children: [
          {
            path: 'dashboard',
            name: 'MediaFactoryDashboard',
            component: () => import('@/views/media-factory/dashboard.vue'),
            meta: { title: '视频生成', icon: 'VideoCameraOutlined' },
          },
          {
            path: 'tts',
            name: 'TTSStudio',
            component: () => import('@/views/media-factory/tts.vue'),
            meta: { title: 'TTS配音', icon: 'SoundOutlined' },
          },
          {
            path: 'charts',
            name: 'ChartEngine',
            component: () => import('@/views/media-factory/charts.vue'),
            meta: { title: '动态图表', icon: 'LineChartOutlined' },
          },
          {
            path: 'render-queue',
            name: 'RenderQueue',
            component: () => import('@/views/media-factory/render-queue.vue'),
            meta: { title: '渲染队列', icon: 'OrderedListOutlined' },
          },
        ],
      },
      // ========== 全球化与多语言 ==========
      {
        path: 'globalization',
        name: 'Globalization',
        component: () => import('@/views/globalization/index.vue'),
        redirect: { name: 'GlobalizationDashboard' },
        meta: { title: '全球化多语言', icon: 'TranslationOutlined' },
        children: [
          {
            path: 'dashboard',
            name: 'GlobalizationDashboard',
            component: () => import('@/views/globalization/dashboard.vue'),
            meta: { title: '多语言管理', icon: 'TranslationOutlined' },
          },
          {
            path: 'glossary',
            name: 'Glossary',
            component: () => import('@/views/globalization/glossary.vue'),
            meta: { title: '术语库', icon: 'ReadOutlined' },
          },
          {
            path: 'translator',
            name: 'Translator',
            component: () => import('@/views/globalization/translator.vue'),
            meta: { title: '翻译引擎', icon: 'GlobalOutlined' },
          },
          {
            path: 'culture-adapt',
            name: 'CultureAdapt',
            component: () => import('@/views/globalization/culture-adapt.vue'),
            meta: { title: '文化适配', icon: 'EnvironmentOutlined' },
          },
        ],
      },
      // ========== 智能物流与定价 ==========
      {
        path: 'logistics',
        name: 'Logistics',
        component: () => import('@/views/logistics/index.vue'),
        redirect: { name: 'LogisticsDashboard' },
        meta: { title: '智能物流定价', icon: 'CarOutlined' },
        children: [
          {
            path: 'dashboard',
            name: 'LogisticsDashboard',
            component: () => import('@/views/logistics/dashboard.vue'),
            meta: { title: '物流看板', icon: 'CarOutlined' },
          },
          {
            path: 'lbs-routing',
            name: 'LBSRouting',
            component: () => import('@/views/logistics/lbs-routing.vue'),
            meta: { title: 'LBS测距', icon: 'EnvironmentOutlined' },
          },
          {
            path: 'freight-calc',
            name: 'FreightCalc',
            component: () => import('@/views/logistics/freight-calc.vue'),
            meta: { title: '运费精算', icon: 'DollarOutlined' },
          },
          {
            path: 'quotation',
            name: 'Quotation',
            component: () => import('@/views/logistics/quotation.vue'),
            meta: { title: '报价单生成', icon: 'FileTextOutlined' },
          },
          {
            path: 'orders-track',
            name: 'LogisticsOrdersTrack',
            component: () => import('@/views/logistics/orders-track.vue'),
            meta: { title: '订单运单回填', icon: 'ContainerOutlined' },
          },
        ],
      },
      // ========== 系统健康与压测 ==========
      {
        path: 'system-health',
        name: 'SystemHealth',
        component: () => import('@/views/system-health/index.vue'),
        redirect: { name: 'SystemHealthDashboard' },
        meta: { title: '系统健康压测', icon: 'HeartOutlined' },
        children: [
          {
            path: 'dashboard',
            name: 'SystemHealthDashboard',
            component: () => import('@/views/system-health/dashboard.vue'),
            meta: { title: '健康看板', icon: 'HeartOutlined' },
          },
          {
            path: 'stress-test',
            name: 'StressTest',
            component: () => import('@/views/system-health/stress-test.vue'),
            meta: { title: '压测管理', icon: 'ThunderboltOutlined' },
          },
          {
            path: 'resource-monitor',
            name: 'ResourceMonitor',
            component: () => import('@/views/system-health/resource-monitor.vue'),
            meta: { title: '资源监控', icon: 'MonitorOutlined' },
          },
          {
            path: 'backup',
            name: 'BackupRestore',
            component: () => import('@/views/system-health/backup.vue'),
            meta: { title: '备份回滚', icon: 'CloudServerOutlined' },
          },
        ],
      },
      // ========== AI深度学习与自我进化 ==========
      {
        path: 'ai-learning',
        name: 'AILearning',
        component: () => import('@/views/ai-learning/index.vue'),
        redirect: { name: 'AILearningDashboard' },
        meta: { title: 'AI深度学习', icon: 'BulbOutlined' },
        children: [
          {
            path: 'dashboard',
            name: 'AILearningDashboard',
            component: () => import('@/views/ai-learning/dashboard.vue'),
            meta: { title: '学习看板', icon: 'BulbOutlined' },
          },
          {
            path: 'behavior',
            name: 'BehaviorAnalysis',
            component: () => import('@/views/ai-learning/behavior.vue'),
            meta: { title: '行为分析', icon: 'RadarChartOutlined' },
          },
          {
            path: 'conversion-funnel',
            name: 'ConversionFunnel',
            component: () => import('@/views/ai-learning/conversion-funnel.vue'),
            meta: { title: '转化漏斗', icon: 'FallOutlined' },
          },
          {
            path: 'auto-ab-test',
            name: 'AutoABTest',
            component: () => import('@/views/ai-learning/auto-ab-test.vue'),
            meta: { title: 'A/B自动化', icon: 'ExperimentOutlined' },
          },
        ],
      },
      // ========== 客户裂变推荐系统 ==========
      {
        path: 'referral',
        name: 'Referral',
        component: () => import('@/views/referral/index.vue'),
        meta: { title: '呼朋唤友', icon: 'TeamOutlined' },
        children: [
          {
            path: '',
            name: 'ReferralDashboard',
            component: () => import('@/views/referral/dashboard.vue'),
            meta: { title: '我的邀请', icon: 'DashboardOutlined' },
          },
          {
            path: 'rules',
            name: 'ReferralRules',
            component: () => import('@/views/referral/rules.vue'),
            meta: { title: '活动规则', icon: 'FileTextOutlined' },
          },
          {
            path: 'redemption',
            name: 'ReferralRedemption',
            component: () => import('@/views/referral/redemption-admin.vue'),
            meta: { title: '现金券核销', icon: 'AuditOutlined' },
          },
        ],
      },
      // ========== SaaS租户与商业化 ==========
      {
        path: 'tenants',
        name: 'Tenants',
        component: () => import('@/views/tenants/index.vue'),
        redirect: { name: 'TenantsDashboard' },
        meta: { title: 'SaaS租户', icon: 'TeamOutlined' },
        children: [
          {
            path: 'dashboard',
            name: 'TenantsDashboard',
            component: () => import('@/views/tenants/dashboard.vue'),
            meta: { title: '租户管理', icon: 'TeamOutlined' },
          },
          {
            path: 'product-showcase',
            name: 'TenantProductShowcase',
            component: () => import('@/views/tenants/product-showcase.vue'),
            meta: { title: '产品展示', icon: 'ShopOutlined' },
          },
          {
            path: 'pricing',
            redirect: { name: 'TenantPlans' },
          },
          {
            path: 'plans',
            name: 'TenantPlans',
            component: () => import('@/views/tenants/pricing.vue'),
            meta: { title: '套餐配置', icon: 'ShopOutlined' },
          },
          {
            path: 'plans/manage',
            name: 'TenantPlansManage',
            component: () => import('@/views/tenants/plans.vue'),
            meta: { title: '套餐配额编辑', icon: 'SettingOutlined' },
          },
          {
            path: 'billing',
            name: 'TenantBilling',
            component: () => import('@/views/tenants/billing.vue'),
            meta: { title: '计费结算', icon: 'BankOutlined' },
          },
          {
            path: 'white-label',
            name: 'WhiteLabel',
            component: () => import('@/views/tenants/white-label.vue'),
            meta: { title: '白标品牌', icon: 'TrophyOutlined' },
          },
          {
            path: 'domain',
            name: 'TenantDomain',
            component: () => import('@/views/tenants/domain.vue'),
            meta: { title: '域名管理', icon: 'GlobalOutlined' },
          },
          {
            path: 'site-editor',
            name: 'SiteEditor',
            component: TenantSiteEditor,
            meta: { title: 'AI智能建站', icon: 'EditOutlined' },
          },
        ],
      },
      // ========== 认知智能与知识图谱 ==========
      {
        path: 'cognitive',
        name: 'Cognitive',
        component: () => import('@/views/cognitive/index.vue'),
        redirect: { name: 'CognitiveDashboard' },
        meta: { title: '认知智能', icon: 'NodeIndexOutlined' },
        children: [
          {
            path: 'dashboard',
            name: 'CognitiveDashboard',
            component: () => import('@/views/cognitive/dashboard.vue'),
            meta: { title: '知识图谱', icon: 'NodeIndexOutlined' },
          },
          {
            path: 'qa-engine',
            name: 'QAEngine',
            component: () => import('@/views/cognitive/qa-engine.vue'),
            meta: { title: '智能问答', icon: 'MessageOutlined' },
          },
          {
            path: 'expert-system',
            name: 'ExpertSystem',
            component: () => import('@/views/cognitive/expert-system.vue'),
            meta: { title: '专家系统', icon: 'RobotOutlined' },
          },
          {
            path: 'semantic-index',
            name: 'SemanticIndex',
            component: () => import('@/views/cognitive/semantic-index.vue'),
            meta: { title: '语义索引', icon: 'SearchOutlined' },
          },
        ],
      },
      // ========== 边缘计算与CDN ==========
      {
        path: 'edge-cdn',
        name: 'EdgeCDN',
        component: () => import('@/views/edge-cdn/index.vue'),
        redirect: { name: 'EdgeCDNDashboard' },
        meta: { title: '边缘计算CDN', icon: 'CloudServerOutlined' },
        children: [
          {
            path: 'dashboard',
            name: 'EdgeCDNDashboard',
            component: () => import('@/views/edge-cdn/dashboard.vue'),
            meta: { title: 'CDN管理', icon: 'CloudServerOutlined' },
          },
          {
            path: 'nodes',
            name: 'EdgeNodes',
            component: () => import('@/views/edge-cdn/nodes.vue'),
            meta: { title: '边缘节点', icon: 'DeploymentUnitOutlined' },
          },
          {
            path: 'preheat',
            name: 'ContentPreheat',
            component: () => import('@/views/edge-cdn/preheat.vue'),
            meta: { title: '内容预热', icon: 'GatewayOutlined' },
          },
          {
            path: 'protocol',
            name: 'ProtocolOpt',
            component: () => import('@/views/edge-cdn/protocol.vue'),
            meta: { title: '协议优化', icon: 'BlockOutlined' },
          },
        ],
      },
      // ========== 开发者生态与低代码 ==========
      {
        path: 'developer',
        name: 'Developer',
        component: () => import('@/views/developer/index.vue'),
        redirect: { name: 'DeveloperDashboard' },
        meta: { title: '开发者生态', icon: 'CodeSandboxOutlined' },
        children: [
          {
            path: 'dashboard',
            name: 'DeveloperDashboard',
            component: () => import('@/views/developer/dashboard.vue'),
            meta: { title: 'API网关', icon: 'CodeSandboxOutlined' },
          },
          {
            path: 'sdk',
            name: 'SDKManager',
            component: () => import('@/views/developer/sdk.vue'),
            meta: { title: 'SDK管理', icon: 'ProjectOutlined' },
          },
          {
            path: 'low-code',
            name: 'LowCode',
            component: () => import('@/views/developer/low-code.vue'),
            meta: { title: '低代码平台', icon: 'BuildOutlined' },
          },
          {
            path: 'plugins',
            name: 'PluginMarket',
            component: () => import('@/views/developer/plugins.vue'),
            meta: { title: '插件市场', icon: 'AppstoreOutlined' },
          },
        ],
      },
      // ========== 国际询盘采集 ==========
      {
        path: 'international',
        name: 'International',
        component: () => import('@/views/international/index.vue'),
        meta: { title: '国际订单采集', icon: 'GlobalOutlined' },
        children: [
          { path: '', name: 'InternationalDashboard', component: () => import('@/views/international/dashboard.vue'), meta: { title: '采集概览', icon: 'DashboardOutlined' } },
          { path: 'inquiries', name: 'InternationalInquiries', component: () => import('@/views/inquiries/index.vue'), meta: { title: '海外询盘', icon: 'MessageOutlined' } },
          { path: 'sites', name: 'InternationalSites', component: () => import('@/views/international/sites.vue'), meta: { title: '目标网站', icon: 'GlobalOutlined' } },
        ],
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面不存在', requiresAuth: false },
  },
];

const router = createRouter({
  history: createWebHistory('/'),
  routes,
});

function resolvePostLoginRedirect(raw: unknown, role: string | undefined): string {
  return postLoginNavigatePath(raw, role);
}

router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore();
  await auth.ensureAuthInitialized();
  if (auth.token == null) {
    auth.token = readStoredAccessToken();
  }

  const loc = normalizeLocationPath(to.path);

  if (loc === '/access-denied') {
    next();
    return;
  }

  const loginPaths = new Set(['/login', '/login/oauth-callback', '/tenants/register', '/client/login']);

  if (loginPaths.has(normalizeLocationPath(to.path))) {
    if (auth.isAuthenticated) {
      const role = auth.currentRole ?? roleFromAccessToken(auth.token);
      next({
        path: resolvePostLoginRedirect(to.query.redirect, role),
        replace: true,
      });
      return;
    }
    next();
    return;
  }

  if (!auth.isAuthenticated) {
    next({ path: '/login', query: { redirect: to.fullPath }, replace: true });
    return;
  }

  const shellDecision = decideRoleShellNavigation(to.path, auth.currentRole);
  if (shellDecision.type === 'logout') {
    await auth.logout();
    next({
      path: LOGIN_PATH,
      query: { redirect: shellDecision.redirectPath },
      replace: true,
    });
    return;
  }
  if (shellDecision.type === 'redirect') {
    next({ path: shellDecision.path, query: to.query, hash: to.hash, replace: true });
    return;
  }

  if (isPlatformKilledPath(loc)) {
    const platformRoles = new Set(['super_admin', 'admin']);
    if (platformRoles.has(auth.currentRole || '')) {
      next({ path: homePathForRole(auth.currentRole), replace: true });
      return;
    }
    next({ path: '/access-denied', query: { from: to.fullPath, reason: 'route_killed' }, replace: true });
    return;
  }

  const platformRoles = new Set(['super_admin', 'admin']);

  if (platformRoles.has(auth.currentRole || '')) {
    if (isPlatformPathBlockedInCertMode(loc)) {
      next({ path: '/admin', replace: true });
      return;
    }
  }

  if (auth.currentRole === 'tenant_admin') {
    if (isClientPathHidden(loc)) {
      next({ path: '/client/today', replace: true });
      return;
    }
    const onboardingSkipPaths = [
      '/client/onboarding',
      '/client/site-editor',
      '/client/plan-gate',
      '/access-denied',
    ];
    if (
      localStorage.getItem('tenant_onboarding_pending') === '1' &&
      !onboardingSkipPaths.some((p) => loc === p || loc.startsWith(`${p}/`))
    ) {
      next({ path: '/client/onboarding', replace: true });
      return;
    }
    const gateFeature = resolveClientPlanGate(loc) ?? resolveClientLabPlanGate(loc);
    if (gateFeature && !loc.startsWith('/client/plan-gate')) {
      // 修复：守卫只按 feature 黑名单拦截会把已满足套餐的租户也拦在 plan-gate
      //（gate 页拿到 allowed=true 后 replace 回原路径又被守卫弹回 → 死循环）。
      // 先问后端 BFF 裁决（BE-04 服务端同源），allowed 直接放行。
      try {
        const verdict = await bffPlanCheck(gateFeature);
        if (!verdict?.allowed) {
          next({ path: '/client/plan-gate', query: { feature: gateFeature, from: to.fullPath }, replace: true });
          return;
        }
      } catch {
        // BFF 不可达时保守处理：仍跳 plan-gate 展示升级 CTA（离线降级语义）
        next({ path: '/client/plan-gate', query: { feature: gateFeature, from: to.fullPath }, replace: true });
        return;
      }
    }
  }

  // 能力守卫：无权限时跳明确提示页，避免静默回首页像「点不动」
  if (!to.meta?.skipCapabilityGuard) {
    const capId = resolveCapabilityIdForPath(loc);
    if (capId && !platformRoles.has(auth.currentRole || '')) {
      const capStore = useAgentCapabilitiesStore();
      if (!capStore.canAccess(capId)) {
        next({ path: '/access-denied', query: { from: to.fullPath }, replace: true });
        return;
      }
    }
  }

  next();
});

router.onError((error, to) => {
  const msg = error?.message || String(error);
  if (
    /Failed to fetch dynamically imported module|Importing a module script failed|Loading chunk .* failed/i.test(
      msg
    )
  ) {
    window.location.assign(to.fullPath);
  }
});

export default router;
