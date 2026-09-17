/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { unwrapFetchedJson } from '@/api';
import { apiFetch } from './fetchWrapper';

export async function sendEmailLoginCode(email: string): Promise<{
  message: string;
  expires_in: number;
  dev_code?: string;
}> {
  const { data: raw, status } = await apiFetch('/auth/send-email-code', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
  const safeRaw = raw ?? {};
  if (status < 200 || status >= 300) {
    const msg =
      typeof (safeRaw as { message?: string }).message === 'string'
        ? (safeRaw as { message: string }).message
        : '发送验证码失败';
    throw new Error(msg);
  }
  if (safeRaw && typeof safeRaw === 'object' && 'code' in safeRaw && (safeRaw as { code: number }).code !== 0) {
    throw new Error((safeRaw as { message?: string }).message || '发送验证码失败');
  }
  return unwrapFetchedJson(safeRaw);
}

export async function loginByEmail(email: string, code: string): Promise<{
  access_token: string;
  refresh_token?: string;
}> {
  const { data: raw, status } = await apiFetch('/auth/login-by-email', {
    method: 'POST',
    body: JSON.stringify({ email, code }),
  });
  const safeRaw = raw ?? {};
  if (status < 200 || status >= 300) {
    throw new Error('验证码无效或已过期');
  }
  if (safeRaw && typeof safeRaw === 'object' && 'code' in safeRaw && (safeRaw as { code: number }).code !== 0) {
    throw new Error((safeRaw as { message?: string }).message || '登录失败');
  }
  const data = unwrapFetchedJson<{
    access_token: string;
    refresh_token?: string;
  }>(safeRaw);
  if (!data?.access_token) {
    throw new Error('登录失败');
  }
  return data;
}
