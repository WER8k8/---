/**
 * 登录成功后唯一跳转 SSOT（LOGIN-LOCK-01 + ROLE-SHELL-LOCK-01）
 * 登录页、OAuth 回调、router 已登录访问 /login 均须走此函数。
 *
 * 分流依据：后端校验账号密码后 JWT 里的 role（不是前端猜用户名）。
 */
import {
  homePathForRole,
  resolveLoginTarget,
  resolveRoleShellTier,
} from '@/constants/roleShellLock';
import { decodeJwtPayload, jwtRoleFromPayload } from '@/utils/jwtPayload';

export { homePathForRole, resolveLoginTarget };

/** 从刚签发的 access token 解析角色（登录后跳转须用此值） */
export function roleFromAccessToken(token: string | null | undefined): string | undefined {
  if (!token) return undefined;
  const role = jwtRoleFromPayload(decodeJwtPayload(token));
  return typeof role === 'string' ? role : undefined;
}

/** 登录成功 / 已登录访问 /login 时的目标路径 */
export function postLoginNavigatePath(
  rawRedirect: unknown,
  role: string | null | undefined,
): string {
  return resolveLoginTarget(rawRedirect, role);
}

/** 登录成功提示：让用户看见「不同账号 → 不同去向」 */
export function postLoginShellHint(role: string | null | undefined): string {
  switch (resolveRoleShellTier(role)) {
    case 'tenant':
      return '登录成功，正在进入租户工作台…';
    case 'partner':
      return '登录成功，正在进入省代后台…';
    case 'agent':
      return '登录成功，正在进入区域代理后台…';
    default:
      return '登录成功，正在进入平台运营控制台…';
  }
}
