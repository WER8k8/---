import { apiV1Base } from '@/api/authPaths';
import { unwrapFetchedJson } from '@/api';
import { readStoredAccessToken } from '@/utils/sessionAuth';

function authHeaders(): HeadersInit {
  const token = readStoredAccessToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export type FounderPreflight = {
  gate_mode: 'wechat' | 'token' | 'none';
  founder_debug_enabled: boolean;
  founder_wechat_configured: boolean;
  founder_wechat_locked?: string | null;
  expected_provider_id?: string | null;
  username_is_founder?: boolean;
  oauth_wechat_enabled: boolean;
  wechat_bound: boolean;
  wechat_id_masked: string | null;
  wechat_is_founder: boolean | null;
  gmssl_installed: boolean;
  steps: string[];
  wechat_provider_id_for_env?: string;
  env_line?: string;
  expected_bind_id?: string;
  env_line_real_openid?: string;
};

export type FounderStatus = {
  gate_mode: string;
  founder_debug_enabled: boolean;
  wechat_is_founder: boolean;
  gmssl_installed: boolean;
  environment: string;
  debug_swagger: boolean;
  readiness: {
    ready: boolean;
    score: { pass: number; warn: number; fail: number };
    checks: Array<{ id: string; title: string; status: string; message: string }>;
  };
  hint: string;
};

export type CryptoSelfTest = {
  gmssl_installed: boolean;
  sm3_sample?: string;
  sm4_roundtrip_ok?: boolean;
  sm2_verify_ok?: boolean;
  error?: string;
};

async function founderFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${apiV1Base()}${path}`, {
    ...init,
    headers: { ...authHeaders(), ...(init?.headers || {}) },
  });
  const raw = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(
      typeof (raw as { message?: string }).message === 'string'
        ? (raw as { message: string }).message
        : `请求失败 (${res.status})`
    );
  }
  if (raw && typeof raw === 'object' && 'code' in raw && (raw as { code: number }).code !== 0) {
    throw new Error((raw as { message?: string }).message || '请求失败');
  }
  const data = unwrapFetchedJson<T>(raw);
  if (data === undefined || data === null) {
    throw new Error('无返回数据');
  }
  return data;
}

export function fetchFounderPreflight(): Promise<FounderPreflight> {
  return founderFetch<FounderPreflight>('/founder-ops/preflight');
}

export function fetchFounderStatus(): Promise<FounderStatus> {
  return founderFetch<FounderStatus>('/founder-ops/status');
}

export function fetchFounderCryptoSelfTest(): Promise<CryptoSelfTest> {
  return founderFetch<CryptoSelfTest>('/founder-ops/crypto/self-test');
}

export type ProtectionSummary = {
  founder_wechat_configured: boolean;
  founder_wechat_locked?: string | null;
  export_platform_founder_only: boolean;
  environment: string;
  stats: {
    data_exports_logged: number;
    access_denied_logged: number;
    founder_ops_logged: number;
  };
  claims: string[];
};

export type SecurityEventRow = {
  id: string;
  action: string;
  user_id: string | null;
  resource_id: string | null;
  ip_address: string | null;
  created_at: string | null;
  detail: Record<string, unknown>;
};

export function fetchProtectionSummary(): Promise<ProtectionSummary> {
  return founderFetch<ProtectionSummary>('/founder-ops/protection-summary');
}

export function fetchSecurityEvents(limit = 30): Promise<SecurityEventRow[]> {
  return founderFetch<SecurityEventRow[]>(`/founder-ops/security-events?limit=${limit}`);
}
