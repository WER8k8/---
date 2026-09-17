/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** 与 axios / parseApiBody 一致：从 fetch JSON 取出 data 或裸对象 */
export function unwrapFetchedJson<T = unknown>(raw: unknown): T {
  if (raw == null || typeof raw !== 'object') {
    return raw as T;
  }
  const body = raw as Record<string, unknown>;
  if (typeof body.code === 'number' && body.code === 0 && body.data !== undefined) {
    return body.data as T;
  }
  if (body.data !== undefined && !('code' in body)) {
    return body.data as T;
  }
  return raw as T;
}
