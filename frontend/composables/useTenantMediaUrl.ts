/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** 租户站媒体 URL — /uploads 走 Nuxt→API 代理，避免指到 :3000 无文件 */
export function useTenantMediaUrl() {
  const config = useRuntimeConfig();
  const apiHost = computed(() =>
    String(config.public.apiHost || 'http://127.0.0.1:8001').replace(/\/$/, ''),
  );

  function resolveMediaUrl(url: string): string {
    if (!url) return '';
    if (url.startsWith('http') || url.startsWith('data:')) return url;
    const path = url.startsWith('/') ? url : `/${url}`;

    if (path.startsWith('/uploads/') || path.startsWith('/static/')) {
      // 浏览器：同源相对路径，由 nuxt devProxy / 生产反代转发到 API
      if (import.meta.client) return path;
      // SSR：img src 仍用相对路径，首屏 HTML 由浏览器在同源加载
      return path;
    }

    if (import.meta.client) {
      return `${window.location.origin}${path}`;
    }
    const host = apiHost.value;
    return host ? `${host}${path}` : path;
  }

  return { resolveMediaUrl };
}
