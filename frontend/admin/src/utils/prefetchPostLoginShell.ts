/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * 登录后首屏壳懒加载预热：避免 dev 下 Vite 首次编译 layout 导致 router.replace 长时间挂起、登录钮一直转圈。
 */
import { resolveRoleShellTier } from '@/constants/roleShellLock';
import { isTenantLoginIntent } from '@/constants/loginPortalCopy';

function prefetchModule(loader: () => Promise<unknown>): void {
  void loader().catch(() => undefined);
}

/** 登录页挂载时按 redirect 意图预热（不阻塞 UI） */
export function prefetchLoginShellChunks(rawRedirect: unknown): void {
  prefetchModule(() => import('@/layout/index.vue'));

  if (isTenantLoginIntent(rawRedirect)) {
    prefetchModule(() => import('@/layout/ClientShellLayout.vue'));
    prefetchModule(() => import('@/views/client/today-three.vue'));
    return;
  }

  const v = Array.isArray(rawRedirect) ? rawRedirect[0] : rawRedirect;
  if (typeof v === 'string') {
    const t = v.trim();
    if (t.startsWith('/agent')) {
      prefetchModule(() => import('@/views/agent/performance.vue'));
      return;
    }
    if (t.startsWith('/partner')) {
      prefetchModule(() => import('@/views/partner/performance.vue'));
      return;
    }
  }

  prefetchModule(() => import('@/views/admin/layout.vue'));
  prefetchModule(() => import('@/views/admin/index.vue'));
}

/** 登录成功后按 JWT 角色再补一轮预热 */
export function prefetchShellForRole(role: string | null | undefined): void {
  prefetchModule(() => import('@/layout/index.vue'));

  switch (resolveRoleShellTier(role)) {
    case 'tenant':
      prefetchModule(() => import('@/layout/ClientShellLayout.vue'));
      prefetchModule(() => import('@/views/client/today-three.vue'));
      break;
    case 'partner':
      prefetchModule(() => import('@/views/partner/performance.vue'));
      break;
    case 'agent':
      prefetchModule(() => import('@/views/agent/performance.vue'));
      break;
    default:
      prefetchModule(() => import('@/views/admin/layout.vue'));
      prefetchModule(() => import('@/views/admin/index.vue'));
      break;
  }
}
