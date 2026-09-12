/**
 * ROLE-SHELL-LOCK-01 · 租户 / 平台超管 / 代理（含省代）登录后壳隔离
 *
 * 契约：.project/role-shell-lock.json
 *
 * 与 LOGIN-LOCK-01 分工：
 * - LOGIN-LOCK-01：唯一登录页 /login（入口）
 * - ROLE-SHELL-LOCK-01：JWT 角色 → 允许路由前缀、首页、跨壳策略、工作标签分桶
 */

import type { ShellMode } from '@/constants/proShellMenus';
import { certPathAllowed, isCertInspectionMode, isPlatformKilledPath } from '@/constants/stubVisibility';
import { normalizeLocationPath } from '@/constants/workbenchPathCapabilities';

export const ROLE_SHELL_LOCK_ID = 'ROLE-SHELL-LOCK-01';

export type RoleShellTier = 'platform' | 'tenant' | 'partner' | 'agent';

export type RoleShellNavDecision =
  | { type: 'continue' }
  | { type: 'redirect'; path: string }
  | { type: 'logout'; redirectPath: string };

export const LEGACY_WORKTAB_STORAGE_KEY = 'uj-worktabs-v1';

const WORKTAB_KEYS: Record<RoleShellTier, string> = {
  platform: 'uj-worktabs-platform-v1',
  tenant: 'uj-worktabs-client-v1',
  partner: 'uj-worktabs-partner-v1',
  agent: 'uj-worktabs-agent-v1',
};

const TENANT_LEGACY_REDIRECTS: Record<string, string> = {
  '/seo-matrix/publish': '/client/seo-publish',
  '/media-factory': '/client/media-factory',
  '/media-factory/dashboard': '/client/media-factory',
  '/admin/ai-center/article-to-video': '/client/article-to-video',
  '/admin/video-space': '/client/video-space',
  '/admin/file-manager': '/client/product-images',
  '/tenants/billing': '/client/billing',
  '/tenants/pricing': '/client/billing',
};

const PLATFORM_LEGACY_REDIRECTS: Record<string, string> = {
  '/client/video-space': '/admin/video-space',
  '/client/product-images': '/admin/file-manager',
};

const PARTNER_FROM_AGENT: Record<string, string> = {
  '/agent/performance': '/partner/performance',
  '/agent/traffic': '/partner/traffic',
  '/agent/commission': '/partner/commission',
  '/agent/account-opening': '/partner/account-opening',
  '/agent/daily-report': '/partner/daily-report',
  '/agent/churn-warning': '/partner/churn-warning',
};

const AGENT_BLOCKED_PREFIXES = [
  '/admin',
  '/partner',
  '/agent-hub',
  '/admin/geo-engine',
  '/admin/code-tools',
];

const PUBLIC_AUTH_PATHS = new Set([
  '/login',
  '/login/oauth-callback',
  '/tenants/register',
  '/client/login',
]);

export function resolveRoleShellTier(role: string | null | undefined): RoleShellTier {
  const r = String(role || '').toLowerCase();
  if (r === 'tenant_admin') return 'tenant';
  if (r === 'l2') return 'partner';
  if (r === 'l3' || r === 'agent' || r === 'sales') return 'agent';
  return 'platform';
}

export function shellModeForTier(tier: RoleShellTier): ShellMode {
  switch (tier) {
    case 'tenant':
      return 'client';
    case 'partner':
      return 'partner';
    case 'agent':
      return 'agent';
    default:
      return 'platform';
  }
}

export function homePathForRole(role: string | null | undefined): string {
  switch (resolveRoleShellTier(role)) {
    case 'tenant':
      return '/client/today';
    case 'partner':
      return '/partner/performance';
    case 'agent':
      return '/agent/performance';
    default:
      return '/admin';
  }
}

export function workTabStorageKeyForRole(role: string | null | undefined): string {
  return WORKTAB_KEYS[resolveRoleShellTier(role)];
}

export function resolveLegacyPathForRole(
  path: string,
  role: string | null | undefined,
): string | null {
  const p = normalizeLocationPath(path);
  const tier = resolveRoleShellTier(role);
  if (tier === 'tenant') return TENANT_LEGACY_REDIRECTS[p] ?? null;
  if (tier === 'partner' && p.startsWith('/agent')) {
    return PARTNER_FROM_AGENT[p] ?? '/partner/performance';
  }
  if (tier === 'platform' && !isCertInspectionMode()) {
    return PLATFORM_LEGACY_REDIRECTS[p] ?? null;
  }
  return null;
}

export function isPathAllowedForRoleTier(
  path: string,
  role: string | null | undefined,
  opts?: { certMode?: boolean },
): boolean {
  const p = normalizeLocationPath(path);
  if (p === '/access-denied') return true;
  const cert = opts?.certMode ?? isCertInspectionMode();
  const tier = resolveRoleShellTier(role);

  switch (tier) {
    case 'tenant':
      return p.startsWith('/client');
    case 'partner':
      return p.startsWith('/partner');
    case 'agent':
      return p.startsWith('/agent');
    case 'platform':
      if (p.startsWith('/partner')) return false;
      if (p.startsWith('/client')) {
        return cert && certPathAllowed(p);
      }
      return true;
    default:
      return true;
  }
}

function isPublicAuthPath(path: string): boolean {
  return PUBLIC_AUTH_PATHS.has(normalizeLocationPath(path));
}

export function decideRoleShellNavigation(
  path: string,
  role: string | null | undefined,
): RoleShellNavDecision {
  const loc = normalizeLocationPath(path);

  if (isPublicAuthPath(loc)) {
    return { type: 'continue' };
  }

  const legacy = resolveLegacyPathForRole(loc, role);
  if (legacy) {
    return { type: 'redirect', path: legacy };
  }

  if (isPathAllowedForRoleTier(loc, role)) {
    return { type: 'continue' };
  }

  const tier = resolveRoleShellTier(role);

  if (tier === 'tenant' && loc.startsWith('/admin')) {
    return { type: 'logout', redirectPath: loc };
  }

  if (tier === 'agent') {
    if (AGENT_BLOCKED_PREFIXES.some((pre) => loc.startsWith(pre))) {
      return { type: 'redirect', path: '/agent/performance' };
    }
    return { type: 'redirect', path: '/agent/performance' };
  }

  if (tier === 'partner') {
    return { type: 'redirect', path: '/partner/performance' };
  }

  return { type: 'redirect', path: homePathForRole(role) };
}

export function resolveLoginTarget(
  rawRedirect: unknown,
  role: string | null | undefined,
): string {
  const fallback = homePathForRole(role);
  const v = Array.isArray(rawRedirect) ? rawRedirect[0] : rawRedirect;
  if (typeof v !== 'string') return fallback;
  const t = v.trim();
  if (!t.startsWith('/') || t.startsWith('//') || t.startsWith('/login')) return fallback;

  const legacy = resolveLegacyPathForRole(t, role);
  const candidate = legacy ?? normalizeLocationPath(t);
  if (isPlatformKilledPath(candidate)) return fallback;
  if (isPathAllowedForRoleTier(candidate, role)) return candidate;
  return fallback;
}

export function resolveWorkTabNavigatePath(
  path: string,
  shell: ShellMode,
  role?: string,
): string {
  const mapped = resolveLegacyPathForRole(path, role);
  if (mapped) return mapped;

  const p = normalizeLocationPath(path);
  if (isPlatformKilledPath(p)) return homePathForRole(role);
  const tier = resolveRoleShellTier(role);

  if (tier === 'tenant' || shell === 'client') {
    return TENANT_LEGACY_REDIRECTS[p] ?? p;
  }
  if ((tier === 'platform' || shell === 'platform') && !isCertInspectionMode()) {
    return PLATFORM_LEGACY_REDIRECTS[p] ?? p;
  }
  return p;
}

export const PLATFORM_MEDIA_LEGACY_REDIRECTS = { ...PLATFORM_LEGACY_REDIRECTS };

export function isTenantLoginIntent(rawRedirect: unknown): boolean {
  const v = Array.isArray(rawRedirect) ? rawRedirect[0] : rawRedirect;
  if (typeof v !== 'string') return false;
  return v.trim().startsWith('/client');
}
