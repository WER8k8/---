/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
export function clearAuthSessionLocal(): void {
  try {
    sessionStorage.removeItem('admin_token')
    sessionStorage.removeItem('admin_refresh_token')
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_refresh_token')
  } catch {
    /* ignore */
  }
}

export function handleUnauthorized(options?: { force?: boolean; skipServerLogout?: boolean }): void {
  clearAuthSessionLocal()
  if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
    const redirect = encodeURIComponent(window.location.pathname + window.location.search)
    window.location.href = `/login?redirect=${redirect}`
  }
}

export const SESSION_KICKED_FLAG = 'auth_session_kicked'
export const SESSION_KICKED_MESSAGE = '账号已在其他设备登录，请重新登录'

type DetailLike = {
  error_code?: unknown
  message?: unknown
  detail?: unknown
}

function readErrorCode(payload: unknown): string | null {
  if (!payload || typeof payload !== 'object') return null
  const body = payload as DetailLike
  if (typeof body.error_code === 'string' && body.error_code) return body.error_code
  const detail = body.detail
  if (detail && typeof detail === 'object') {
    const nested = detail as DetailLike
    if (typeof nested.error_code === 'string' && nested.error_code) return nested.error_code
  }
  // FastAPI 默认 / 旧 handler 可能把 dict detail 序列化进 message 字符串
  const haystacks: unknown[] = [detail, body.message]
  for (const h of haystacks) {
    if (typeof h === 'string' && h.includes('SESSION_REPLACED')) return 'SESSION_REPLACED'
  }
  return null
}

/** 判断 API 错误体是否为「会话被顶替」 */
export function isSessionReplacedPayload(payload: unknown): boolean {
  return readErrorCode(payload) === 'SESSION_REPLACED'
}

export function markSessionKicked(): void {
  try {
    sessionStorage.setItem(SESSION_KICKED_FLAG, '1')
  } catch {
    /* ignore */
  }
}

export function consumeSessionKickedMessage(): string | null {
  try {
    if (sessionStorage.getItem(SESSION_KICKED_FLAG) !== '1') return null
    sessionStorage.removeItem(SESSION_KICKED_FLAG)
    return SESSION_KICKED_MESSAGE
  } catch {
    return null
  }
}

export function redirectToLoginAfterKick(): void {
  markSessionKicked()
  clearAuthSessionLocal()
  handleUnauthorized({ force: true, skipServerLogout: false })
}
