/**
 * Admin BFF 客户端
 *
 * 边界：
 * - 只访问 /api/v1/admin-bff/*（UAC 契约）
 * - 复用项目 normalizeApiSuccessBody，不重复造 axios 轮子
 * - FIX-22: Token 通过 HttpOnly Cookie 自动发送，无需手动附加 Authorization Header
 */
import axios, { type AxiosInstance } from 'axios';

import { normalizeApiSuccessBody } from '@/api/index';

import type {
  UacLoginResult,
  UacMenuRoute,
  UacPermissionBundle,
  UacTenantSearchHit,
  UacUserInfo,
} from './admin-bff.types';
import { BFF_BASE_URL } from './admin-bff.types';

function createBffClient(): AxiosInstance {
  const client = axios.create({
    baseURL: BFF_BASE_URL,
    timeout: 30_000,
    // FIX-22: 发送 Cookie（HttpOnly access_token 自动携带）
    withCredentials: true,
  });

  client.interceptors.response.use((res) => {
    const body = res.data;
    if (body && typeof body === 'object' && typeof (body as { code?: number }).code === 'number') {
      const code = (body as { code: number }).code;
      if (code !== 0) {
        const message = (body as { message?: string }).message || 'BFF 请求失败';
        return Promise.reject(new Error(message));
      }
    }
    return { ...res, data: normalizeApiSuccessBody(body as Record<string, unknown>) };
  });

  return client;
}

const bff = createBffClient();

export async function bffLogin(username: string, password: string): Promise<UacLoginResult> {
  const res = await bff.post('/auth/login', { username, password });
  const data = res.data as {
    accessToken?: string;
    refreshToken?: string;
  };
  return {
    accessToken: data.accessToken ?? '',
    refreshToken: data.refreshToken,
  };
}

export async function bffUserInfo(): Promise<UacUserInfo> {
  const res = await bff.get('/user/info');
  return res.data as UacUserInfo;
}

export async function bffLogout(): Promise<void> {
  await bff.post('/logout');
}

export async function bffMenuRoutes(): Promise<UacMenuRoute[]> {
  const res = await bff.get('/menu/routes');
  return res.data as UacMenuRoute[];
}

export async function bffPermissions(): Promise<UacPermissionBundle> {
  const res = await bff.get('/menu/permissions');
  return res.data as UacPermissionBundle;
}

export async function bffTenantSearch(code: string): Promise<UacTenantSearchHit[]> {
  const res = await bff.get('/auth/tenant/search', { params: { code } });
  return res.data as UacTenantSearchHit[];
}

export async function bffPlanCheck(feature: string) {
  const res = await bff.get('/plan/check', { params: { feature } });
  return res.data as {
    allowed: boolean;
    cta_copy?: string;
    current_plan_name?: string;
    required_plan_name?: string;
  };
}

export type SiteEditorDraft = {
  title: string;
  hero: string;
  locale: string;
  showCta: boolean;
  brandName?: string;
  aboutText?: string;
  contactPhone?: string;
  contactEmail?: string;
  ctaLabel?: string;
  primaryPromise?: string;
  inquiryHook?: string;
  stage1Title?: string;
  stage1Desc?: string;
  stage2Title?: string;
  stage2Desc?: string;
  stage3Title?: string;
  stage3Desc?: string;
  stage4Title?: string;
  stage4Desc?: string;
  knowledge1Title?: string;
  knowledge1Hook?: string;
  knowledge2Title?: string;
  knowledge2Hook?: string;
  knowledge3Title?: string;
  knowledge3Hook?: string;
};

export async function bffSiteEditorDraftGet(): Promise<SiteEditorDraft> {
  return bff.get('/lab/site-editor') as Promise<SiteEditorDraft>;
}

export async function bffSiteEditorDraftSave(draft: SiteEditorDraft): Promise<SiteEditorDraft> {
  return bff.put('/lab/site-editor', draft) as Promise<SiteEditorDraft>;
}

export default bff;
