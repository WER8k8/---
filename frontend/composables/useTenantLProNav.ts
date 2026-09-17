/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** L-Pro 租户站路径导航 */

export type TenantLProNavKey =
  | 'home'
  | 'products'
  | 'about'
  | 'solutions'
  | 'downloads'
  | 'contact';

export const TENANT_L_PRO_PATHS: Record<TenantLProNavKey, string> = {
  home: '/tenant',
  products: '/tenant/products',
  about: '/tenant/about',
  solutions: '/tenant/solutions',
  downloads: '/tenant/downloads',
  contact: '/tenant/contact',
};

export function tenantProductDetailPath(slug: string): string {
  return `/tenant/products/${encodeURIComponent(slug)}`;
}

export function tenantProductsCategoryQuery(slug: string): string {
  return `${TENANT_L_PRO_PATHS.products}?category=${encodeURIComponent(slug)}`;
}

export interface TenantLProNavItem {
  key: TenantLProNavKey;
  label: string;
  href: string;
}

export function buildTenantLProNavItems(
  tSite: (key: string, vars?: Record<string, string>) => string,
  opts?: { hasSolutions?: boolean; hasDownloads?: boolean },
): TenantLProNavItem[] {
  const items: TenantLProNavItem[] = [
    { key: 'home', label: tSite('nav_home'), href: TENANT_L_PRO_PATHS.home },
    { key: 'products', label: tSite('nav_products'), href: TENANT_L_PRO_PATHS.products },
  ];
  if (opts?.hasSolutions) {
    items.push({ key: 'solutions', label: tSite('nav_solutions'), href: TENANT_L_PRO_PATHS.solutions });
  }
  items.push({ key: 'about', label: tSite('nav_about'), href: TENANT_L_PRO_PATHS.about });
  if (opts?.hasDownloads) {
    items.push({ key: 'downloads', label: tSite('nav_downloads'), href: TENANT_L_PRO_PATHS.downloads });
  }
  items.push({ key: 'contact', label: tSite('nav_contact'), href: TENANT_L_PRO_PATHS.contact });
  return items;
}
