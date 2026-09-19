/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * 导航路由注册表 - 单一数据源
 * 所有导航菜单项的 key 到路由路径映射都在此定义
 * 路由壳统一由 layout/index.vue + YdProSidebar.vue 消费，保持单一映射配置
 */

export interface NavRoute {
  key: string;
  path: string;
  label: string;
  icon?: string;
  children?: NavRoute[];
}

export const NAV_ROUTE_MAP: Record<string, string> = {
  // 基础路由
  'home': '/admin',
  'conversation': '/client/assistant',
  'skill-center': '/agent-hub/dashboard',
  'auto-negotiate': '/sales/auto-negotiator',
  'deep-research': '/agent-hub/task-orchestrator',
  'customer-analysis': '/agent-hub/execution-review',
  'analytics': '/analytics',
  'invitation': '/referral',
  
  // 常用路由映射
  'dashboard': '/dashboard',
  'admin-dashboard': '/admin/dashboard',
  'tenants': '/admin/tenants',
  'platform-zones': '/admin/platform-zones',
  
  // 总览模块
  'dashboard-data': '/dashboard',
  'operations-traffic': '/operations/traffic',
  
  // 业务管理模块
  'products': '/products',
  'categories': '/products/categories',
  'content': '/content',
  'cases': '/cases',
  'news': '/news',
  
  // 客户线索模块
  'inquiries': '/inquiries',
  
  // 销售模块
  'sales': '/sales/dashboard',
  'customer-finder': '/sales/customer-finder',
  'email-automation': '/sales/email-automation',
  
  // SEO模块
  'seo': '/seo',
  'building-wiki': '/seo/building-wiki',
  'content-optimizer': '/seo/content-optimizer',
  'keyword-ranking': '/seo/keyword-ranking',
  'baidu-tools': '/seo/baidu-tools',
  'site-audit': '/seo/site-audit',
  'seo-matrix-keywords': '/seo-matrix/keywords',
  'seo-matrix-publish': '/seo-matrix/publish',
  
  // 代理中心模块
  'agent-performance': '/agent/performance',
  'agent-traffic': '/agent/traffic',
  'agent-commission': '/agent/commission',
  'agent-account-opening': '/agent/account-opening',
  'agent-daily-report': '/agent/daily-report',
  'agent-churn-warning': '/agent/churn-warning',
  
  // 系统模块
  'users': '/users',
  'settings': '/settings',
  'ai-config': '/ai-config',
  
  // 呼朋唤友模块
  'referral': '/referral',
  'referral-rules': '/referral/rules',
  
  // 海外采销模块
  'international': '/international',
  'international-inquiries': '/international/inquiries',
  'international-sites': '/international/sites',
  
  // 超级管理工具模块
  'admin-hub': '/admin',
  'admin-aggregation': '/admin/aggregation',
  'admin-traffic-board': '/admin/traffic-board',
  'admin-system': '/admin/system',
  'admin-agent-capabilities': '/admin/system/agent-capabilities',
  'admin-ai-center': '/admin/ai-center',
  'admin-code': '/admin/code-tools',
  'admin-files': '/admin/file-manager',
  'admin-security': '/admin/security',
  'admin-automation': '/admin/automation',
  'admin-projects': '/admin/projects',
  'admin-runtime': '/admin/runtime',
  'admin-scheduler': '/admin/scheduler-hub',
  'admin-geo-engine': '/admin/geo-engine',
  'admin-v2ray': '/admin/v2ray',
  'admin-annex-trade-ai': '/admin/annex/trade-ai',
  'admin-annex-goodjob': '/admin/annex/goodjob',
  'client-hermes-tasks': '/client/tasks',
  'admin-agent-hub': '/agent-hub/dashboard',
  'admin-media-factory': '/media-factory/dashboard',
  'admin-globalization': '/globalization/dashboard',
  'admin-logistics': '/logistics/dashboard',
  'admin-system-health': '/system-health/dashboard',
  'admin-tenants': '/tenants/dashboard',
  'admin-cognitive': '/cognitive/dashboard',
  'admin-edge-cdn': '/edge-cdn/dashboard',
  'admin-developer': '/developer/dashboard',
  
  // AI中心子菜单
  'ai-center-dashboard': '/admin/ai-center',
  'ai-center-models': '/admin/ai-center/models',
  'ai-center-content': '/admin/ai-center/content',
  'ai-center-analytics': '/admin/ai-center/analytics',
  'ai-center-logs': '/admin/ai-center/logs',
  'ai-center-provider-setup': '/admin/ai-center/provider-setup',
  'ai-center-scenario-models': '/admin/ai-center/scenario-models',
  'ai-center-article-generator': '/admin/ai-center/article-generator',
  'ai-center-article-to-video': '/admin/ai-center/article-to-video',
  'ai-center-usage': '/admin/ai-center/usage',
  'ai-center-knowledge': '/admin/ai-center/knowledge',
  
  // 租户管理子菜单
  'tenant-dashboard': '/tenants/dashboard',
  'tenant-showcase': '/tenants/product-showcase',
  'tenant-pricing': '/tenants/pricing',
  'tenant-plans': '/tenants/plans',
  'tenant-billing': '/tenants/billing',
  'tenant-white-label': '/tenants/white-label',
  'tenant-domain': '/tenants/domain',
  'tenant-site-editor': '/tenants/site-editor',
  
  // 租户 Client 壳模块
  'client-dashboard': '/client/dashboard',
  'client-traffic': '/client/traffic',
  'client-onboarding': '/client/onboarding',
  'client-site-editor': '/client/site-editor',
  'client-product-images': '/client/product-images',
  'client-video-space': '/client/video-space',
  'client-inquiries': '/client/inquiries',
  'client-referral': '/client/referral',
  'client-products': '/client/products',
  'client-content': '/client/content',
  'client-seo': '/client/seo',
  'client-seo-publish': '/client/seo-publish',
  'client-distribute': '/client/distribute',
  'client-cross-platform': '/client/cross-platform',
  'client-publish': '/client/publish',
  'client-billing': '/client/billing',
  'client-invoices': '/client/invoices',
  'client-tokens': '/client/tokens',
  'client-settings': '/client/settings',
  'client-queues-inquiries': '/client/queues/inquiries',
  'client-queues-publish': '/client/queues/publish',
  'client-queues-fulfillment': '/client/queues/fulfillment',
};

export const NAV_PATH_TO_KEY_MAP: Record<string, string> = Object.entries(NAV_ROUTE_MAP)
  .reduce((acc, [key, path]) => {
    acc[path] = key;
    return acc;
  }, {} as Record<string, string>);

export function getRouteFromKey(key: string): string | undefined {
  return NAV_ROUTE_MAP[key];
}

export function getKeyFromPath(path: string): string | undefined {
  return NAV_PATH_TO_KEY_MAP[path];
}

export function isValidNavKey(key: string): boolean {
  return key in NAV_ROUTE_MAP;
}

export function isValidNavPath(path: string): boolean {
  return path in NAV_PATH_TO_KEY_MAP;
}

export const ALL_NAV_KEYS = Object.keys(NAV_ROUTE_MAP);
export const ALL_NAV_PATHS = Object.values(NAV_ROUTE_MAP);

if (import.meta.env.DEV) {
  console.log('[NavRouteRegistry] 导航路由注册表已加载', {
    keys: ALL_NAV_KEYS,
    paths: ALL_NAV_PATHS,
  });
}