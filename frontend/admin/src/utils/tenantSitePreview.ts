/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { buildTenantPreviewUrl } from '../../../utils/tenant-preview-domain';

/** 租户「我的网站」链接：开发走 Nuxt 预览，生产走 SaaS 子域 */
export function resolveTenantSiteUrl(tenantDomain: string, backendSiteUrl?: string): string {
  const domain = String(tenantDomain || '').trim();
  if (import.meta.env.DEV && domain) {
    return buildTenantPreviewUrl(domain);
  }
  const fromApi = String(backendSiteUrl || '').trim();
  if (fromApi) return fromApi;
  if (domain) return buildTenantPreviewUrl(domain);
  return '';
}
