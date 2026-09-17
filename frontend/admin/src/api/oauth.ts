/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { apiV1Base } from '@/api/authPaths';
import { unwrapFetchedJson } from '@/api';
import { apiFetch } from '@/api/fetchWrapper';

export type OAuthProvider = 'qq' | 'wechat' | 'feishu' | 'dingtalk';

const PROVIDER_LABEL: Record<OAuthProvider, string> = {
  qq: 'QQ',
  wechat: '微信',
  feishu: '飞书',
  dingtalk: '钉钉',
};

export function oauthProviderLabel(p: OAuthProvider): string {
  return PROVIDER_LABEL[p] ?? p;
}

export type OAuthStatePayload = {
  redirect?: string;
  ts?: number;
  provider?: OAuthProvider;
  mode?: 'login' | 'bind';
};

/** 解析登录页写入的 state（与 index.vue 中 btoa(JSON) 对应） */
export function parseOAuthState(state?: string): OAuthStatePayload | null {
  if (!state) return null;
  try {
    const normalized = state.replace(/-/g, '+').replace(/_/g, '/');
    const pad = normalized.padEnd(
      normalized.length + ((4 - (normalized.length % 4)) % 4),
      '='
    );
    return JSON.parse(atob(pad)) as OAuthStatePayload;
  } catch {
    return null;
  }
}

export function resolveOAuthProvider(
  queryProvider: string | undefined,
  state?: string
): OAuthProvider | null {
  const fromQuery = (queryProvider || '').toLowerCase();
  if (fromQuery && fromQuery in PROVIDER_LABEL) {
    return fromQuery as OAuthProvider;
  }
  const parsed = parseOAuthState(state);
  if (parsed?.provider && parsed.provider in PROVIDER_LABEL) {
    return parsed.provider;
  }
  return null;
}

export async function fetchOAuthProvidersStatus(): Promise<{
  providers: Record<OAuthProvider, boolean>;
  dev_bypass?: boolean;
}> {
  const { data: raw } = await apiFetch('/auth/oauth/providers');
  const data = unwrapFetchedJson<{ providers: Record<string, boolean>; dev_bypass?: boolean }>(raw);
  const providers = (data?.providers || {}) as Record<string, boolean>;
  return {
    providers: {
      qq: Boolean(providers.qq),
      wechat: Boolean(providers.wechat),
      feishu: Boolean(providers.feishu),
      dingtalk: Boolean(providers.dingtalk),
    },
    dev_bypass: data?.dev_bypass ?? false,
  };
}

export async function fetchOAuthAuthorizeUrl(
  provider: OAuthProvider,
  state?: string
): Promise<{ authorize_url: string; state: string }> {
  const q = state ? `?state=${encodeURIComponent(state)}` : '';
  const { data: raw, status } = await apiFetch(`/auth/oauth/${provider}/authorize${q}`);
  if (status !== 200) {
    const msg =
      typeof (raw as { message?: string }).message === 'string'
        ? (raw as { message: string }).message
        : `${oauthProviderLabel(provider)} 登录暂不可用`;
    throw new Error(msg);
  }
  if (raw && typeof raw === 'object' && 'code' in raw && (raw as { code: number }).code !== 0) {
    throw new Error((raw as { message?: string }).message || '无法获取授权地址');
  }
  const data = unwrapFetchedJson<{ authorize_url: string; state: string }>(raw);
  if (!data?.authorize_url) throw new Error('无法获取授权地址');
  return data;
}

export async function exchangeThirdPartyLogin(
  provider: OAuthProvider,
  code: string,
  state?: string
): Promise<{
  access_token: string;
  refresh_token?: string;
  user?: { username?: string };
  new_user?: boolean;
}> {
  const res = await fetch(`${apiV1Base()}/auth/third-party-login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, code, state: state ?? null }),
  });
  const raw = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(
      typeof (raw as { message?: string }).message === 'string'
        ? (raw as { message: string }).message
        : '第三方登录失败'
    );
  }
  if (raw && typeof raw === 'object' && 'code' in raw && (raw as { code: number }).code !== 0) {
    throw new Error((raw as { message?: string }).message || '第三方登录失败');
  }
  const data = unwrapFetchedJson<{
    access_token: string;
    refresh_token?: string;
    user?: { username?: string };
    new_user?: boolean;
  }>(raw);
  if (!data?.access_token) throw new Error('登录失败，未返回令牌');
  return data;
}
