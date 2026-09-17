/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** 站点主导航（顶栏与移动端抽屉共用） */
export interface SiteNavLink {
  /** i18n 键名，如 'nav.home' */
  label: string;
  to: string;
  /** i18n 键名，如 'nav.allCategories' */
  description?: string;
}

export interface SiteNavItem {
  /** i18n 键名，如 'nav.home' */
  label: string;
  /** 一级入口（含下拉时仍作为默认落地页） */
  to: string;
  children?: SiteNavLink[];
}

export const siteMainNavigation: SiteNavItem[] = [
  { label: 'nav.home', to: '/' },
  {
    label: 'nav.products',
    to: '/products',
    children: [
      { label: 'nav.productList', to: '/products', description: 'nav.allCategories' },
      { label: 'nav.productExamples', to: '/products-example', description: 'nav.typicalScenarios' },
    ],
  },
  { label: 'nav.cases', to: '/cases' },
  {
    label: 'nav.about',
    to: '/about',
    children: [
      { label: 'nav.companyIntro', to: '/about' },
      { label: 'nav.privacy', to: '/privacy' },
      { label: 'nav.terms', to: '/terms' },
    ],
  },
  { label: 'nav.news', to: '/news' },
  { label: 'nav.seoDiagnosis', to: '/seo-diagnosis' },
  { label: 'nav.contact', to: '/contact' },
];

export function navKey(item: SiteNavItem): string {
  return item.to;
}
