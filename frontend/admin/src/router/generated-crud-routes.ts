/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** AUTO-GENERATED · BJ-03 · do not edit by hand */
import type { RouteRecordRaw } from 'vue-router';

export const generatedCrudRoutes: RouteRecordRaw[] = [
  {
    path: 'generated/inquiries',
    name: 'GeneratedInquiriesList',
    component: () => import('@/views/_generated/InquiriesList.vue'),
    meta: { title: '询盘管理（生成）', skipCapabilityGuard: true },
  },
  {
    path: 'generated/products',
    name: 'GeneratedProductsList',
    component: () => import('@/views/_generated/ProductsList.vue'),
    meta: { title: '产品管理（生成）', skipCapabilityGuard: true },
  },
  {
    path: 'generated/content',
    name: 'GeneratedContentList',
    component: () => import('@/views/_generated/ContentList.vue'),
    meta: { title: '内容管理（生成）', skipCapabilityGuard: true },
  },
  {
    path: 'generated/news',
    name: 'GeneratedNewsList',
    component: () => import('@/views/_generated/NewsList.vue'),
    meta: { title: '新闻管理（生成）', skipCapabilityGuard: true },
  },
  {
    path: 'generated/payment',
    name: 'GeneratedPaymentList',
    component: () => import('@/views/_generated/PaymentList.vue'),
    meta: { title: '支付管理（生成）', skipCapabilityGuard: true },
  },
  {
    path: 'generated/users',
    name: 'GeneratedUsersList',
    component: () => import('@/views/_generated/UsersList.vue'),
    meta: { title: '用户管理（生成）', skipCapabilityGuard: true },
  },
  {
    path: 'generated/analytics',
    name: 'GeneratedAnalyticsList',
    component: () => import('@/views/_generated/AnalyticsList.vue'),
    meta: { title: '数据分析（生成）', skipCapabilityGuard: true },
  },
  {
    path: 'generated/settings',
    name: 'GeneratedSettingsList',
    component: () => import('@/views/_generated/SettingsList.vue'),
    meta: { title: '系统设置（生成）', skipCapabilityGuard: true },
  },
  {
    path: 'generated/seo',
    name: 'GeneratedSeoList',
    component: () => import('@/views/_generated/SeoList.vue'),
    meta: { title: 'SEO优化（生成）', skipCapabilityGuard: true },
  },
  {
    path: 'generated/compliance',
    name: 'GeneratedComplianceList',
    component: () => import('@/views/_generated/ComplianceList.vue'),
    meta: { title: '合规审计（生成）', skipCapabilityGuard: true },
  },
  {
    path: 'generated/agent-hub',
    name: 'GeneratedAgentHubList',
    component: () => import('@/views/_generated/AgentHubList.vue'),
    meta: { title: '智能体协同（生成）', skipCapabilityGuard: true },
  },
  {
    path: 'generated/ab-test',
    name: 'GeneratedAbTestList',
    component: () => import('@/views/_generated/AbTestList.vue'),
    meta: { title: 'A/B测试（生成）', skipCapabilityGuard: true },
  },
];
