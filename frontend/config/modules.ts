/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
export interface ModuleConfig {
  id: string;
  name: string;
  icon: string;
  path: string;
  roles: string[];
  children?: ModuleConfig[];
}

export const ADMIN_MODULES: ModuleConfig[] = [
  {
    id: 'dashboard',
    name: '仪表盘',
    icon: 'LayoutDashboard',
    path: '/admin',
    roles: ['super_admin', 'admin', 'editor', 'sales', 'viewer'],
  },
  {
    id: 'products',
    name: '产品管理',
    icon: 'Package',
    path: '/admin/products',
    roles: ['super_admin', 'admin', 'editor'],
    children: [
      {
        id: 'products-list',
        name: '产品列表',
        path: '/admin/products',
        roles: ['super_admin', 'admin', 'editor'],
      },
      {
        id: 'products-categories',
        name: '分类管理',
        path: '/admin/products/categories',
        roles: ['super_admin', 'admin', 'editor'],
      },
      {
        id: 'products-edit',
        name: '编辑产品',
        path: '/admin/products/edit/:id',
        roles: ['super_admin', 'admin', 'editor'],
      },
    ],
  },
  {
    id: 'cases',
    name: '案例管理',
    icon: 'Building2',
    path: '/admin/cases',
    roles: ['super_admin', 'admin', 'editor'],
    children: [
      {
        id: 'cases-list',
        name: '案例列表',
        path: '/admin/cases',
        roles: ['super_admin', 'admin', 'editor'],
      },
      {
        id: 'cases-edit',
        name: '编辑案例',
        path: '/admin/cases/edit/:id',
        roles: ['super_admin', 'admin', 'editor'],
      },
    ],
  },
  {
    id: 'content',
    name: '内容管理',
    icon: 'FileText',
    path: '/admin/content',
    roles: ['super_admin', 'admin', 'editor'],
    children: [
      {
        id: 'content-list',
        name: '内容列表',
        path: '/admin/content',
        roles: ['super_admin', 'admin', 'editor'],
      },
      {
        id: 'content-edit',
        name: '编辑内容',
        path: '/admin/content/edit/:id',
        roles: ['super_admin', 'admin', 'editor'],
      },
    ],
  },
  {
    id: 'news',
    name: '新闻管理',
    icon: 'Newspaper',
    path: '/admin/news',
    roles: ['super_admin', 'admin', 'editor'],
  },
  {
    id: 'inquiries',
    name: '询盘管理',
    icon: 'Mail',
    path: '/admin/inquiries',
    roles: ['super_admin', 'admin', 'sales'],
  },
  {
    id: 'seo',
    name: 'SEO优化',
    icon: 'Search',
    path: '/admin/seo',
    roles: ['super_admin', 'admin', 'editor'],
    children: [
      {
        id: 'seo-dashboard',
        name: 'SEO概览',
        path: '/admin/seo',
        roles: ['super_admin', 'admin', 'editor'],
      },
      {
        id: 'seo-content-optimizer',
        name: '内容优化',
        path: '/admin/seo/content-optimizer',
        roles: ['super_admin', 'admin', 'editor'],
      },
      {
        id: 'seo-batch',
        name: '批量优化',
        path: '/admin/seo/batch-seo',
        roles: ['super_admin', 'admin', 'editor'],
      },
      {
        id: 'seo-llms-txt',
        name: 'LLMs.txt',
        path: '/admin/seo/llms-txt',
        roles: ['super_admin', 'admin'],
      },
      {
        id: 'seo-schema',
        name: 'Schema标记',
        path: '/admin/seo/schema-markup',
        roles: ['super_admin', 'admin', 'editor'],
      },
      {
        id: 'seo-audit',
        name: '站点审计',
        path: '/admin/seo/site-audit',
        roles: ['super_admin', 'admin'],
      },
    ],
  },
  {
    id: 'analytics',
    name: '数据分析',
    icon: 'BarChart3',
    path: '/admin/analytics',
    roles: ['super_admin', 'admin'],
  },
  {
    id: 'ai',
    name: 'AI配置',
    icon: 'Brain',
    path: '/admin/ai',
    roles: ['super_admin', 'admin'],
  },
  {
    id: 'users',
    name: '用户管理',
    icon: 'Users',
    path: '/admin/users',
    roles: ['super_admin'],
  },
  {
    id: 'settings',
    name: '系统设置',
    icon: 'Settings',
    path: '/admin/settings',
    roles: ['super_admin', 'admin'],
  },
];

export const ROLE_LABELS: Record<string, string> = {
  super_admin: '超级管理员',
  admin: '管理员',
  editor: '编辑',
  sales: '销售',
  viewer: '访客',
};

export function getUserModules(role: string): ModuleConfig[] {
  return ADMIN_MODULES.filter((module) => module.roles.includes(role));
}

export function hasAccessToModule(role: string, moduleId: string): boolean {
  const module = ADMIN_MODULES.find((m) => m.id === moduleId);
  return module ? module.roles.includes(role) : false;
}
