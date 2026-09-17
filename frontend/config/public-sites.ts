/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * 公网站点三分法 — 代码与文档唯一源
 * 镜像：.project/public-sites.json
 *
 * 改路由/布局前必读，禁止把 SaaS 或租户模板混入 corporate 首页。
 */
export type PublicSiteId = 'corporate-b2b' | 'saas-marketing' | 'tenant-site';

export interface PublicSiteDefinition {
  id: PublicSiteId;
  label: string;
  purpose: string;
  /** Nuxt 公网路径（Admin 独立 SPA 用 adminPath） */
  nuxtPath?: string;
  adminPath?: string;
  layout: string;
  entryFile: string;
  primaryColor: string;
  copyDeck?: string;
  copyModule?: string;
  designReferences?: string[];
  designRefManifest?: string;
  doNotMixWith: PublicSiteId[];
}

export const PUBLIC_SITES: Record<PublicSiteId, PublicSiteDefinition> = {
  'corporate-b2b': {
    id: 'corporate-b2b',
    label: '优丁建材企业官网',
    purpose: '轻集料混凝土 B2B 对外展示与询盘',
    nuxtPath: '/',
    layout: 'default',
    entryFile: 'frontend/pages/index.vue',
    primaryColor: '#1e3a5f',
    doNotMixWith: ['saas-marketing', 'tenant-site'],
  },
  'saas-marketing': {
    id: 'saas-marketing',
    label: '优丁 SaaS 营销官网',
    purpose: '外贸卖家出海工作台 — 卖 SaaS、注册与四门户登录入口',
    nuxtPath: '/platform',
    adminPath: '/landing',
    layout: 'marketing',
    entryFile: 'frontend/pages/platform/index.vue',
    primaryColor: '#2563eb',
    copyDeck: 'docs/marketing/plan-copy-deck.md',
    designReferences: ['https://iproyal.cn/', 'https://asocks.com/en/', 'https://my.asocks.com/'],
    designRefManifest: '.project/saas-design-references.json',
    copyModule: 'frontend/config/platform-marketing-content.ts',
    doNotMixWith: ['corporate-b2b', 'tenant-site'],
  },
  'tenant-site': {
    id: 'tenant-site',
    label: '租户独立站',
    purpose: 'SaaS 租户按域名/子域名的独立 B2B 长页',
    nuxtPath: '/tenant',
    layout: 'tenant-blank',
    entryFile: 'frontend/pages/tenant/index.vue',
    primaryColor: 'tenant-theme',
    doNotMixWith: ['corporate-b2b', 'saas-marketing'],
  },
};

export function getPublicSite(id: PublicSiteId): PublicSiteDefinition {
  return PUBLIC_SITES[id];
}
