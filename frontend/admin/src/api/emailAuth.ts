/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import axios from '@/api';
import { unwrapFetchedJson } from '@/api';

export async function sendEmailLoginCode(email: string): Promise<{
  message: string;
  expires_in: number;
  dev_code?: string;
}> {
  const res = await axios.post('/auth/send-email-code', { email });
  const raw = res.data;
  if (raw && typeof raw === 'object' && 'code' in raw && (raw as { code: number }).code !== 0) {
    throw new Error((raw as { message?: string }).message || '发送验证码失败');
  }
  return unwrapFetchedJson(raw);
}

export async function loginByEmail(email: string, code: string): Promise<{
  access_token: string;
  refresh_token?: string;
}> {
  const res = await axios.post('/auth/login-by-email', { email, code });
  const raw = res.data;
  if (raw && typeof raw === 'object' && 'code' in raw && (raw as { code: number }).code !== 0) {
    throw new Error((raw as { message?: string }).message || '登录失败');
  }
  const data = unwrapFetchedJson<{
    access_token: string;
    refresh_token?: string;
  }>(raw);
  if (!data?.access_token) {
    throw new Error('登录失败');
  }
  return data;
}
