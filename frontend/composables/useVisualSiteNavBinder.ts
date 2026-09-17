/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** 可视化站点多页导航：开发预览时保留 __tenant 查询参数 */

export function bindVisualSiteNavLinks(root: HTMLElement | null | undefined): () => void {
  if (!root || typeof window === 'undefined') return () => {};

  const handlers: Array<{ el: HTMLAnchorElement; fn: (e: Event) => void }> = [];
  const tenantParam = new URLSearchParams(window.location.search).get('__tenant');

  root.querySelectorAll('a[href^="/tenant"]').forEach((node) => {
    const el = node as HTMLAnchorElement;
    const fn = (e: Event) => {
      if (!tenantParam) return;
      e.preventDefault();
      const url = new URL(el.getAttribute('href') || '/tenant', window.location.origin);
      url.searchParams.set('__tenant', tenantParam);
      window.location.assign(url.toString());
    };
    el.addEventListener('click', fn);
    handlers.push({ el, fn });
  });

  return () => {
    handlers.forEach(({ el, fn }) => el.removeEventListener('click', fn));
  };
}
