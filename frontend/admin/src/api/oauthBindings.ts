/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import axios from '@/api';
import { unwrapFetchedJson } from '@/api';
import type { OAuthProvider } from '@/api/oauth';

export type OAuthBindingRow = {
  provider: OAuthProvider;
  provider_id_masked: string;
  created_at: string | null;
};

export async function fetchOAuthBindings(): Promise<OAuthBindingRow[]> {
  const res = await axios.get('/auth/oauth/bindings');
  const raw = res.data;
  return unwrapFetchedJson<OAuthBindingRow[]>(raw) ?? [];
}

export async function bindOAuthAccount(provider: OAuthProvider, code: string): Promise<void> {
  const res = await axios.post('/auth/oauth/bind', { provider, code });
  const raw = res.data;
  if ((raw as { code?: number }).code !== 0) {
    throw new Error((raw as { message?: string }).message || '绑定失败');
  }
}

export async function unbindOAuthAccount(provider: OAuthProvider): Promise<void> {
  const res = await axios.delete(`/auth/oauth/bindings/${provider}`);
  const raw = res.data;
  if ((raw as { code?: number }).code !== 0) {
    throw new Error((raw as { message?: string }).message || '解绑失败');
  }
}
