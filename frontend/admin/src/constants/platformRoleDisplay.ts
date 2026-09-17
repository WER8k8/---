/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * 平台侧角色展示 SSOT（用户可见中文，与 JWT role 字段对齐）
 *
 * - super_admin：平台超管，全量侧栏（含挣钱大赛 / 摸金校尉）
 * - admin：运营管理员，生产环境精简侧栏（本地 dev 账号 admin 见 useEffectivePlatformRole）
 */

export type PlatformJwtRole = 'super_admin' | 'admin' | string;

export function platformRoleLabel(role: PlatformJwtRole | null | undefined): string {
  switch (role) {
    case 'super_admin':
      return '平台超管';
    case 'admin':
      return '运营管理员';
    default:
      return role ? String(role) : '未识别角色';
  }
}

export function platformWorkbenchTitle(role: PlatformJwtRole | null | undefined): string {
  switch (role) {
    case 'super_admin':
      return '平台超管工作台';
    case 'admin':
      return '运营管理员工作台';
    default:
      return '平台工作台';
  }
}

/** 本地开发：账号 admin 即平台超管（与 .project/dev-login-accounts.json 一致） */
export function isDevPlatformSuperAccount(username: string | null | undefined): boolean {
  return import.meta.env.DEV && String(username || '').toLowerCase() === 'admin';
}

/** 菜单 / 工作台 / 顶栏统一用的有效平台角色 */
export function effectivePlatformRole(
  jwtRole: string | null | undefined,
  username: string | null | undefined,
): string | undefined {
  if (isDevPlatformSuperAccount(username)) return 'super_admin';
  return jwtRole || undefined;
}
