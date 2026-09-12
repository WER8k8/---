/** 仅客户端解析 JWT payload，不做签名校验（与后端校验分离） */

const KNOWN_JWT_ROLES = new Set([
  'super_admin',
  'admin',
  'tenant_admin',
  'editor',
  'sales',
  'viewer',
  'l2',
  'l3',
  'agent',
]);

/** 从 JWT payload 取账号角色：优先 `role`，否则从 `scopes` 中取首个已知角色（兼容旧 access token）。 */
export function jwtRoleFromPayload(payload: Record<string, unknown> | null | undefined): unknown {
  if (!payload) return undefined;
  if (typeof payload.role === 'string') return payload.role;
  const scopes = payload.scopes;
  if (Array.isArray(scopes)) {
    for (const s of scopes) {
      if (typeof s === 'string' && KNOWN_JWT_ROLES.has(s)) return s;
    }
  }
  return undefined;
}

export function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split('.');
    if (parts.length < 2) return null;
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=');
    const json = atob(padded);
    return JSON.parse(json) as Record<string, unknown>;
  } catch {
    return null;
  }
}

/** 与 backend `User.role` / JWT `role` 对齐，映射到代理会话 L1–L5 */
export function mapJwtRoleToAgentLevelId(role: unknown): string {
  const r = typeof role === 'string' ? role : '';
  const table: Record<string, string> = {
    super_admin: 'L1',
    admin: 'L1',
    editor: 'L3',
    sales: 'L4',
    viewer: 'L5',
  };
  return table[r] ?? 'L1';
}

/**
 * 基于 payload `exp` 判断是否过期（不做签名校验）。
 * - 无法解析的 token 视为过期，便于清理脏数据。
 * - 无 `exp` 字段视为未过期（兼容非标准 JWT）。
 */
export function isJwtExpired(token: string, skewSeconds = 30): boolean {
  const p = decodeJwtPayload(token);
  if (!p) return true;
  const exp = p.exp;
  if (typeof exp !== 'number' || !Number.isFinite(exp)) return false;
  const now = Date.now() / 1000;
  return now >= exp - skewSeconds;
}
