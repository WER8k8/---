import { unwrapFetchedJson } from '@/api';
import { apiFetch } from './fetchWrapper';
import type { OAuthProvider } from '@/api/oauth';

export type OAuthBindingRow = {
  provider: OAuthProvider;
  provider_id_masked: string;
  created_at: string | null;
};

export async function fetchOAuthBindings(): Promise<OAuthBindingRow[]> {
  const { data: raw, status } = await apiFetch('/auth/oauth/bindings');
  const safeRaw = raw ?? {};
  if (status < 200 || status >= 300) {
    throw new Error((safeRaw as { message?: string }).message || '加载绑定失败');
  }
  return unwrapFetchedJson<OAuthBindingRow[]>(safeRaw) ?? [];
}

export async function bindOAuthAccount(provider: OAuthProvider, code: string): Promise<void> {
  const { data: raw, status } = await apiFetch('/auth/oauth/bind', {
    method: 'POST',
    body: JSON.stringify({ provider, code }),
  });
  const safeRaw = raw ?? {};
  if (status < 200 || status >= 300 || (safeRaw as { code?: number }).code !== 0) {
    throw new Error((safeRaw as { message?: string }).message || '绑定失败');
  }
}

export async function unbindOAuthAccount(provider: OAuthProvider): Promise<void> {
  const { data: raw, status } = await apiFetch(`/auth/oauth/bindings/${provider}`, {
    method: 'DELETE',
  });
  const safeRaw = raw ?? {};
  if (status < 200 || status >= 300 || (safeRaw as { code?: number }).code !== 0) {
    throw new Error((safeRaw as { message?: string }).message || '解绑失败');
  }
}
