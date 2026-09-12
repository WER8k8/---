import axios, { AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios';
import { getActivePinia } from 'pinia';
import { useAuthStore } from '@/stores/auth';
import { performSilentTokenRefresh } from '@/api/authRefresh';

const baseURL = import.meta.env.VITE_API_BASE || '/api/v1';

/**
 * 灏?FastAPI `APIResponse` 鎴愬姛浣擄紙code=0锛夎浆涓虹鐞嗙鎯敤鐨勬墎骞崇粨鏋勩€? * axios 鎷︽埅鍣ㄤ笌 fetch 鍏辩敤锛涢潪 0 / 闈炰俊灏佸垯鍘熸牱杩斿洖銆? */
export function normalizeApiSuccessBody(body: Record<string, unknown>): unknown {
  if (
    typeof body.code !== 'number' ||
    body.code !== 0 ||
    !('data' in body) ||
    body.data === undefined
  ) {
    return body;
  }

  const inner = body.data as unknown;
  const total = body.total;
  const page = body.page;
  const page_size = body.page_size;
  const hasPageMeta = total != null || page != null || page_size != null;

  if (inner !== null && typeof inner === 'object' && !Array.isArray(inner)) {
    const obj = inner as Record<string, unknown>;
    if ('items' in obj && Array.isArray(obj.items)) {
      return { ...obj };
    }
    return {
      ...obj,
      ...(total != null ? { total } : {}),
      ...(page != null ? { page } : {}),
      ...(page_size != null ? { page_size } : {}),
    };
  }

  if (Array.isArray(inner)) {
    if (hasPageMeta) {
      return {
        items: inner,
        total: (total as number) ?? inner.length,
        ...(page != null ? { page } : {}),
        ...(page_size != null ? { page_size } : {}),
      };
    }
    return inner;
  }

  return inner;
}

/** `fetch` + `await res.json()` 鍚庝笌 axios 涓€鑷寸殑鎵佸钩鍖?*/
export function unwrapFetchedJson<T = unknown>(raw: unknown): T {
  if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
    return normalizeApiSuccessBody(raw as Record<string, unknown>) as T;
  }
  return raw as T;
}

/** 瑙ｆ瀽 FastAPI `APIResponse`锛坈ode=0 涓斿惈 data锛夋垨宸茬敱鎷︽埅鍣ㄦ墎骞冲寲鍚庣殑 body */
export function unwrapApiData<T = unknown>(response: AxiosResponse): T {
  const body = response?.data as Record<string, unknown> | null | undefined;
  if (
    body &&
    typeof body === 'object' &&
    body.code === 0 &&
    'data' in body &&
    body.data !== undefined
  ) {
    return body.data as T;
  }
  return body as T;
}

const api = axios.create({
  baseURL,
  timeout: 30000,
  // FIX-22: 发送 HttpOnly Cookie（自动携带 access_token）
  withCredentials: true,
});

function joinRequestUrl(cfg: InternalAxiosRequestConfig): string {
  const base = (cfg.baseURL ?? '').replace(/\/$/, '');
  let u = cfg.url ?? '';
  if (!/^https?:\/\//i.test(u)) u = u.replace(/^\//, '');
  if (!base) return u ? `/${u}` : '/';
  return u ? `${base}/${u}` : base;
}

/**
 * 后端路由已同时注册 `""` 和 `"/"` 两个路径，`/news` 不带斜杠可直接匹配，
 * 不再需要主动补尾斜杠。旧逻辑反而触发 307 → 跨端口重定向 → 丢失 Authorization → 401。
 * 保留函数签名（请求拦截器仍在调用），但改为直接透传 URL，不再修改。
 */
function withCollectionTrailingSlash(url: string | undefined): string | undefined {
  return url;
}

function redirectToLogin() {
  const full = `${window.location.pathname}${window.location.search || ''}`;
  window.location.assign(`/login?redirect=${encodeURIComponent(full)}`);
}

/** access 澶辨晥涓旀棤娉曠画鏈燂細娓呬細璇濆苟鏁撮〉鍘荤櫥褰曪紙鐧诲綍椤典笉璺宠浆锛?*/
async function hardLogout401() {
  const path = window.location.pathname;
  if (path === '/login') return;
  const pinia = getActivePinia();
  if (pinia) await useAuthStore(pinia).logout();
  else {
    // 清除 sessionStorage 和 localStorage 中的 token
    sessionStorage.removeItem('admin_token');
    sessionStorage.removeItem('admin_refresh_token');
    sessionStorage.removeItem('admin_username');
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_refresh_token');
    localStorage.removeItem('admin_username');
  }
  redirectToLogin();
}

function navigateApiForbidden(fromFullPath: string, cfg?: InternalAxiosRequestConfig) {
  void import('@/router').then((m) => {
    m.default.replace({
      path: '/access-denied',
      query: {
        reason: 'api403',
        from: fromFullPath.slice(0, 500),
        apiPath: String(cfg?.url ?? '').slice(0, 200),
      },
    });
  });
}

function makeBusinessApiError(
  config: InternalAxiosRequestConfig,
  data: unknown,
  code: number,
  message?: string
): AxiosError {
  const msg = message || (code === 401 ? 'Unauthorized' : code === 403 ? 'Forbidden' : 'Error');
  const err = new AxiosError(msg, String(code), { ...config, skipAuthRefresh: true }, undefined, {
    data,
    status: code,
    statusText: msg,
    headers: {},
    config: { ...config, skipAuthRefresh: true },
  } as AxiosResponse);
  return err;
}

api.interceptors.request.use(
  (config) => {
    config.url = withCollectionTrailingSlash(config.url);
    // 与 auth store 保持一致：优先 sessionStorage，回退 localStorage
    const token = (typeof sessionStorage !== 'undefined' ? sessionStorage.getItem('admin_token') : null)
      ?? localStorage.getItem('admin_token');
    // Cookie 认证模式下 token 是哨兵值 'cookie'：不能作为 Bearer 发送，
    // 否则后端 decode("cookie") 失败且 header 优先级高于 cookie，导致 401 踢出会话
    if (token && token !== 'cookie') {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => {
    const raw = response.data;
    if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
      const o = raw as Record<string, unknown>;
      if (typeof o.code === 'number' && o.code !== 0) {
        // FIX: 业务层 403 不再抛异常导致 message.error 弹窗。
        // 返回空数据对象让调用方正常渲染（空列表/空对象），避免导航栏点击后全屏报错。
        if (o.code === 403) {
          if (import.meta.env.DEV) {
            console.warn(
              `[api] 业务 403 on ${response.config.url ?? '?'} — ${o.message ?? '权限不足'}，已静默降级为空数据。`,
              o,
            );
          }
          // 根据常见响应结构返回空数据，避免组件因 data 为 null 而崩溃
          response.data = { code: 0, message: 'success', data: [], total: 0, page: 1, page_size: 20 };
          return response;
        }
        const bizMsg = typeof o.message === 'string' ? o.message : undefined;
        return Promise.reject(makeBusinessApiError(response.config, o, o.code, bizMsg));
      }
      response.data = normalizeApiSuccessBody(o as Record<string, unknown>);
    }
    return response;
  },
  async (error: unknown) => {
    if (!axios.isAxiosError(error)) return Promise.reject(error);
    const status = error.response?.status;
    const path = window.location.pathname;

    if (status === 403) {
      if (path === '/login' || path === '/access-denied') {
        return Promise.reject(error);
      }
      // FIX: 403 不再整页跳转 /access-denied，改为静默 reject + 控制台日志。
      // 调用方可通过 catch 自行处理（如展示局部 error 提示），避免导航栏点击后全屏报错。
      // 若调用方显式设置 skip403Redirect: false，则恢复旧行为（整页跳转）。
      const cfg = error.config as Record<string, unknown> | undefined;
      if (cfg?.skip403Redirect === false) {
        const full = `${path}${window.location.search || ''}`;
        navigateApiForbidden(full, error.config);
        return Promise.reject(error);
      }
      if (import.meta.env.DEV) {
        console.warn(
          `[api] HTTP 403 on ${error.config?.url ?? '?'} (from ${path}) — 拒绝访问，已静默忽略。`,
          error.response?.data,
        );
      }
      return Promise.reject(error);
    }

    if (status === 401) {
      if (path === '/login') return Promise.reject(error);
      const cfg = error.config;
      if (!cfg || cfg.skipAuthRefresh || cfg.softAuthFailure) {
        return Promise.reject(error);
      }

      const reqUrl = joinRequestUrl(cfg);
      if (/\/auth\/refresh\b/.test(reqUrl) || /\/auth\/login\b/.test(reqUrl)) {
        await hardLogout401();
        return Promise.reject(error);
      }
      if (cfg._authRetry) {
        await hardLogout401();
        return Promise.reject(error);
      }
      const ok = await performSilentTokenRefresh();
      if (!ok) {
        await hardLogout401();
        return Promise.reject(error);
      }
      cfg._authRetry = true;
      // 与 auth store 保持一致：优先 sessionStorage，回退 localStorage
      const newTok = (typeof sessionStorage !== 'undefined' ? sessionStorage.getItem('admin_token') : null)
        ?? localStorage.getItem('admin_token');
      if (newTok) {
        cfg.headers = (cfg.headers ?? {}) as import('axios').AxiosRequestHeaders;
        (cfg.headers as Record<string, string>).Authorization = `Bearer ${newTok}`;
      }
      return api.request(cfg);
    }

    return Promise.reject(error);
  }
);

export const productsAPI = {
  list: (params?: Record<string, any>) => api.get('/products', { params }),
  get: (id: string) => api.get(`/products/${id}`),
  create: (data: any) => api.post('/products', data),
  update: (id: string, data: any) => api.put(`/products/${id}`, data),
  delete: (id: string) => api.delete(`/products/${id}`),
  exportCsv: (params?: Record<string, unknown>) =>
    api.get('/products/export', { params, responseType: 'blob' }),
  importCsv: (formData: FormData) =>
    api.post('/products/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  categories: () => api.get('/products/categories'),
  categoriesTree: () => api.get('/products/categories/tree'),
  createCategory: (data: any) => api.post('/products/categories', data),
  updateCategory: (id: string, data: any) => api.put(`/products/categories/${id}`, data),
  deleteCategory: (id: string) => api.delete(`/products/categories/${id}`),
};

export const seoAPI = {
  dashboard: (params?: { range?: string }) =>
    api.get('/seo/dashboard', { params, softAuthFailure: true }),
  seoPagesSummary: () => api.get('/seo/seo-pages-summary'),
  generateLLMSTxt: (data: any) => api.post('/seo/llms-txt/generate', data),
  validateLLMSTxt: (data: { content: string }) => api.post('/seo/llms-txt/validate', data),
  optimizeContent: (data: any) => api.post('/seo/content-optimizer/optimize', data),
  audit: (data: any) => api.post('/seo/site-audit', data),
  getAudit: (id: string) => api.get(`/seo/site-audit/${id}`),
  pages: (params?: Record<string, any>) => api.get('/seo/pages', { params }),
  updatePage: (id: string, data: any) => api.put(`/seo/pages/${id}`, data),
  optimizePage: (id: string, data: any) => api.post(`/seo/pages/${id}/optimize`, data),
  schemaGenerate: (data: any) => api.post('/seo/schema-markup/generate', data),
  schemaValidate: (data: any) => api.post('/seo/schema-markup/validate', data),
  schemaList: () => api.get('/seo/schema-markup'),
  schemaExport: (id: string) => api.get(`/seo/schema-markup/export/${id}`),
  schemaGet: (id: string) => api.get(`/seo/schema-markup/${id}`),
  schemaTypes: () => api.get('/seo/schema-markup/types'),
  schemaDelete: (id: string) => api.delete(`/seo/schema-markup/${id}`),
  schemaSave: (data: Record<string, unknown>) => api.post('/seo/schema-markup', data),
  authors: () => api.get('/seo/eeat/authors'),
  authorCreate: (data: any) => api.post('/seo/eeat/authors', data),
  authorUpdate: (id: string, data: any) => api.put(`/seo/eeat/authors/${id}`, data),
  authorDelete: (id: string) => api.delete(`/seo/eeat/authors/${id}`),
  trustSignals: () => api.get('/seo/eeat/trust-signals'),
  score: (data: any) => api.post('/seo/eeat/score', data),
  auditLogs: (params?: Record<string, any>) => api.get('/system/audit/logs', { params }),
  deleteAuditLog: (id: string) => api.delete(`/system/audit/logs/${id}`),
  clearAuditLogs: () => api.delete('/system/audit/logs'),
  // 鎵归噺SEO
  batchApplyRule: (data: any) => api.post('/seo/batch-seo/seo-batch-apply-rule', data),
  extractParams: (data: any) => api.post('/seo/batch-seo/extract-params', data),
};

export const contentAPI = {
  list: (params?: Record<string, any>) => api.get('/content/pages', { params }),
  get: (id: string) => api.get(`/content/pages/${id}`),
  create: (data: any) => api.post('/content/pages', data),
  update: (id: string, data: any) => api.put(`/content/pages/${id}`, data),
  delete: (id: string) => api.delete(`/content/pages/${id}`),
  seo: (data: any) => api.post('/content/seo', data),
  seoPage: (id: string) => api.get(`/content/seo/page/${id}`),
  seoProduct: (id: string) => api.get(`/content/seo/product/${id}`),
  aiGenerate: (data: Record<string, unknown>) => api.post('/ai/product/generate', data),
  aiPolish: (data: Record<string, unknown>) => api.post('/ai/product/polish', data),
};

// TODO: Backend case_studies API returns __dict__-serialized objects (including
// SQLAlchemy internal fields like _sa_instance_state). The backend should switch
// to Pydantic response_model or schema-based serialization. Until then, consumers
// should guard against unexpected keys in the response payload.
export const casesAPI = {
  list: (params?: Record<string, any>) => api.get('/case-studies', { params }),
  get: (id: string) => api.get(`/case-studies/${id}`),
  create: (data: any) => api.post('/case-studies', data),
  update: (id: string, data: any) => api.put(`/case-studies/${id}`, data),
  delete: (id: string) => api.delete(`/case-studies/${id}`),
};

export const inquiriesAPI = {
  list: (params?: Record<string, any>) => api.get('/inquiries', { params }),
  get: (id: string) => api.get(`/inquiries/${id}`),
  update: (id: string, data: any) => api.put(`/inquiries/${id}`, data),
  delete: (id: string) => api.delete(`/inquiries/${id}`),
};

export const systemAPI = {
  login: (data: any) => api.post('/auth/login', data, { skipAuthRefresh: true }),
  contact: (data: any) => api.post('/inquiries', data),
  auditLogs: (params?: Record<string, any>) => api.get('/system/audit/logs', { params }),
  deleteAuditLog: (id: string) => api.delete(`/system/audit/logs/${id}`),
  clearAuditLogs: () => api.delete('/system/audit/logs'),
};

export const usersAPI = {
  list: (params?: Record<string, any>) => api.get('/users', { params }),
  create: (data: any) => api.post('/users', data),
  update: (id: string, data: any) => api.put(`/users/${id}`, data),
  delete: (id: string) => api.delete(`/users/${id}`),
};

/** SEO 鐭╅樀 `/api/v1/seo-matrix/*`锛屼笌 FastAPI `seo_matrix.py` 瀵归綈 */
export const seoMatrixAPI = {
  getSettings: () => api.get('/seo-matrix/settings'),
  updateSettings: (data: Record<string, unknown>) => api.put('/seo-matrix/settings', data),

  getProvinces: () => api.get('/seo-matrix/provinces'),
  getCities: (provinceId: string) => api.get(`/seo-matrix/provinces/${provinceId}/cities`),
  getDistricts: (cityId: string) => api.get(`/seo-matrix/cities/${cityId}/districts`),
  getKeywordGroups: () => api.get('/seo-matrix/keyword-groups'),
  getKeywords: (params?: Record<string, unknown>) =>
    api.get('/seo-matrix/region-keywords', { params }),
  createKeyword: (data: Record<string, unknown>) => api.post('/seo-matrix/region-keywords', data),
  updateKeyword: (id: string, data: Record<string, unknown>) =>
    api.put(`/seo-matrix/region-keywords/${id}`, data),
  deleteKeyword: (id: string) => api.delete(`/seo-matrix/region-keywords/${id}`),
  importKeywords: (formData: FormData) =>
    api.post('/seo-matrix/region-keywords/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  getCombinatorialRules: () => api.get('/seo-matrix/combinatorial-rules'),
  createRule: (form: Record<string, unknown>) =>
    api.post('/seo-matrix/combinatorial-rules', {
      name: form.name,
      template: form.pattern,
      description: form.remark,
      priority: form.priority ?? 10,
    }),
  updateRule: (id: string, form: Record<string, unknown>) =>
    api.put(`/seo-matrix/combinatorial-rules/${id}`, {
      name: form.name,
      template: form.pattern,
      description: form.remark,
      priority: form.priority ?? 10,
    }),
  generateKeywords: (body: Record<string, unknown>) =>
    api.post('/seo-matrix/generate-keywords', {
      rule_id: body.rule_id,
      rule_ids: body.rule_id ? [body.rule_id] : undefined,
      count: body.count,
      region_scope: body.region_scope,
    }),
  getGeneratedKeywords: (params?: Record<string, unknown>) =>
    api.get('/seo-matrix/generated-keywords', {
      params: { ...params, valid_only: false },
    }),
  deleteGeneratedKeyword: (id: string) => api.delete(`/seo-matrix/generated-keywords/${id}`),
  batchDeleteKeywords: (ids: string[]) =>
    api.post('/seo-matrix/generated-keywords/batch-delete', { ids }),
  regenerateKeywords: (ruleId: string) =>
    api.post(`/seo-matrix/combinatorial-rules/${ruleId}/regenerate`),

  getContentTemplates: (params?: Record<string, unknown>) =>
    api.get('/seo-matrix/content-templates', { params }),
  createTemplate: (form: Record<string, unknown>) =>
    api.post('/seo-matrix/content-templates', {
      name: form.name,
      content: form.content,
      description: form.remark,
      template_type: form.category || 'product',
      variables: [],
      priority: 10,
    }),
  updateTemplate: (id: string, form: Record<string, unknown>) =>
    api.put(`/seo-matrix/content-templates/${id}`, {
      name: form.name,
      content: form.content,
      remark: form.remark,
      category: form.category,
    }),
  getGeneratedContents: (params?: Record<string, unknown>) =>
    api.get('/seo-matrix/generated-contents', { params }),
  generateContent: (body: Record<string, unknown>) =>
    api.post('/seo-matrix/generate-content', body),
  publishContent: (id: string) => api.post(`/seo-matrix/generated-contents/${id}/publish`),
  deleteContent: (id: string) => api.delete(`/seo-matrix/generated-contents/${id}`),

  getPlatforms: () => api.get('/seo-matrix/platforms'),
  getPlatformAccounts: (params?: Record<string, unknown>) =>
    api.get('/seo-matrix/platform-accounts', { params }),
  createPlatformAccount: (data: Record<string, unknown>) =>
    api.post('/seo-matrix/platform-accounts', {
      platform_id: data.platform_id ?? data.platform,
      account_name: data.account_name ?? data.name,
      username: data.username,
      email: data.email,
    }),
  updatePlatformAccount: (id: string, data: Record<string, unknown>) =>
    api.put(`/seo-matrix/platform-accounts/${id}`, {
      platform_id: data.platform_id ?? data.platform,
      account_name: data.account_name ?? data.name,
      username: data.username,
      email: data.email,
      is_active: data.is_active,
    }),

  getPublishTasks: (params?: Record<string, unknown>) => {
    const p = { ...params };
    if (p.platform && !p.platform_id) {
      p.platform_id = p.platform;
      delete p.platform;
    }
    return api.get('/seo-matrix/publish-tasks', { params: p });
  },
  createPublishTask: (body: Record<string, unknown>) => {
    const st = body.scheduled_time as { toISOString?: () => string } | string | null | undefined;
    const scheduled =
      st && typeof st === 'object' && typeof st.toISOString === 'function'
        ? st.toISOString()
        : (st as string | undefined);
    return api.post('/seo-matrix/publish', {
      content_ids: body.content_ids,
      platform_id: body.platform_id,
      account_id: body.account_id,
      publish_type: body.publish_time_type === 'scheduled' ? 'scheduled' : 'immediate',
      scheduled_time: scheduled,
    });
  },
  retryPublishTask: (id: string) => api.post(`/seo-matrix/publish-tasks/${id}/retry`),
  deletePublishTask: (id: string) => api.delete(`/seo-matrix/publish-tasks/${id}`),

  dashboard: () => api.get('/seo-matrix/dashboard'),

  getInclusionStatus: (params?: Record<string, unknown>) =>
    api.get('/seo-matrix/inclusion-status', { params }),
  getInclusionProbeConfig: () => api.get('/seo-matrix/inclusion-probe-config'),
  seedIndustryKeywords: (data?: { belt_id?: string; include_ranking?: boolean }) =>
    api.post('/seo-matrix/seed-industry-keywords', data ?? {}),
  checkInclusion: (taskIds?: string[]) => api.post('/seo-matrix/check-inclusion', taskIds ?? []),
  recheckInclusion: (rowId: string) => api.post(`/seo-matrix/inclusion-status/${rowId}/recheck`),
  saveInclusionSettings: (data: Record<string, unknown>) =>
    api.put('/seo-matrix/inclusion-settings', data),
};

/** 增长内置工具 `/api/v1/growth-tools/*` */
export const growthToolsAPI = {
  getHotKeywords: () => api.get('/growth-tools/keywords/hot'),
  getKeywordLibrary: (params?: { word_class?: string }) =>
    api.get('/growth-tools/keywords/library', { params }),
  addKeyword: (data: Record<string, unknown>) => api.post('/growth-tools/keywords/library', data),
  deleteKeyword: (id: string) => api.delete(`/growth-tools/keywords/library/${id}`),
  inspectContent: (data: { title?: string; body: string; keywords?: string[] }) =>
    api.post('/growth-tools/content-quality/inspect', data),
  getAiTrafficOverview: () => api.get('/growth-tools/ai-traffic/overview'),
  runBaiduProbe: (data: { keyword: string; site?: string }) =>
    api.post('/growth-tools/ai-traffic/baidu-probe', data),
  runConversionProbe: (data?: { site?: string; start_date?: string; end_date?: string }) =>
    api.post('/growth-tools/ai-traffic/conversion-probe', data || {}),
  getDashboard: () => api.get('/growth-tools/dashboard'),
  getAgentPresets: () => api.get('/growth-tools/agent/presets'),
  listAgentRuns: (params?: { limit?: number }) =>
    api.get('/growth-tools/agent/runs', { params }),
  startAgentRun: (data: {
    goal?: string;
    preset_id?: string;
    mode?: string;
    focus_keyword?: string;
    content_title?: string;
    content_body?: string;
    extra_keywords?: string[];
    save_focus_keyword?: boolean;
  }) => api.post('/growth-tools/agent/runs', data),
  getAgentRun: (runId: string) => api.get(`/growth-tools/agent/runs/${runId}`),
};

/** 鏂伴椈 `/api/v1/news`锛堣 docs/4-API鎺ュ彛瀹氫箟.md 搂6锛?*/
export const newsAPI = {
  list: (params?: Record<string, unknown>) => api.get('/news', { params }),
  get: (id: string) => api.get(`/news/${id}`),
  create: (data: Record<string, unknown>) => api.post('/news', data),
  update: (id: string, data: Record<string, unknown>) => api.put(`/news/${id}`, data),
  remove: (id: string) => api.delete(`/news/${id}`),
};

/** 鍏ㄥ眬鍚堣 `/api/v1/compliance`锛埪?3锛屼笌 SEO 鍐呭悎瑙勬壂鎻忓尯鍒嗭級 */
export const complianceHubAPI = {
  overview: () => api.get('/compliance'),
  audit: () => api.get('/compliance/audit'),
  issues: (params?: Record<string, unknown>) => api.get('/compliance/issues', { params }),
  resolveIssue: (issueId: string, body?: Record<string, unknown>) =>
    api.put(`/compliance/issues/${issueId}/resolve`, body ?? {}),
  report: (params?: { format?: string }) => api.get('/compliance/report', { params }),
};

/** AI 閰嶇疆 `/api/v1/ai-config`锛埪?1锛?*/
export const aiConfigAPI = {
  get: () => api.get('/ai-config'),
  update: (data: Record<string, unknown>) => api.put('/ai-config', data),
  toggleProvider: (providerId: string, body?: Record<string, unknown>) =>
    api.post(`/ai-config/provider/${providerId}/toggle`, body ?? {}),
  stats: () => api.get('/ai-config/stats'),
};

/** A/B 娴嬭瘯 `/api/v1/ab-test`锛埪?2锛?*/
export const abTestAPI = {
  list: (params?: Record<string, unknown>) => api.get('/ab-test', { params }),
  get: (id: string) => api.get(`/ab-test/${id}`),
  create: (data: Record<string, unknown>) => api.post('/ab-test', data),
  update: (id: string, data: Record<string, unknown>) => api.put(`/ab-test/${id}`, data),
  remove: (id: string) => api.delete(`/ab-test/${id}`),
  start: (id: string) => api.post(`/ab-test/${id}/start`),
  stop: (id: string) => api.post(`/ab-test/${id}/stop`),
};

/** 椋炰功 `/api/v1/feishu`锛埪?5锛?*/
export const feishuAPI = {
  getBind: () => api.get('/feishu/bind'),
  bind: (data: Record<string, unknown>) => api.post('/feishu/bind', data),
  unbind: (data: Record<string, unknown>) => api.post('/feishu/unbind', data),
  logs: (params?: Record<string, unknown>) => api.get('/feishu/logs', { params }),
  dailyReport: () => api.get('/feishu/report/daily'),
};

/** 鏁版嵁鍒嗘瀽 `/api/v1/analytics`锛埪?锛?*/
export const dataAnalyticsAPI = {
  list: (params?: Record<string, unknown>) => api.get('/analytics', { params }),
  dashboard: () => api.get('/analytics/dashboard'),
  traffic: (params?: Record<string, unknown>) => api.get('/analytics/traffic', { params }),
  products: (params?: Record<string, unknown>) => api.get('/analytics/products', { params }),
  exportData: (params?: Record<string, unknown>) => api.get('/analytics/export', { params }),
};

/** 绔欑偣璁剧疆 `/api/v1/settings`锛埪?0锛?*/
export const siteSettingsAPI = {
  get: () => api.get('/settings'),
  updateSite: (data: Record<string, unknown>) => api.put('/settings/site', data),
  updateSeo: (data: Record<string, unknown>) => api.put('/settings/seo', data),
  updateSystem: (data: Record<string, unknown>) => api.put('/settings/system', data),
};

export default api;

// ========== 鏂板妯″潡 API 瀹㈡埛绔?==========

/** 鏅鸿兘浣撳崗鍚?`/api/v1/agent-hub/*` */
export const agentHubAPI = {
  overview: () => api.get('/agent-hub'),
  mcpBridgeStatus: () => api.get('/agent-hub/mcp-bridge'),
  mcpTools: () => api.get('/agent-hub/mcp-bridge/tools'),
  taskOrchestrator: () => api.get('/agent-hub/task-orchestrator'),
  executionReview: (params?: Record<string, unknown>) =>
    api.get('/agent-hub/execution-review', { params }),
};

/** 澶氬獟浣撳伐鍘?`/api/v1/media-factory/*` */
export const mediaFactoryAPI = {
  overview: () => api.get('/media-factory'),
  ttsStatus: () => api.get('/media-factory/tts'),
  chartsStatus: () => api.get('/media-factory/charts'),
  renderQueue: (params?: Record<string, unknown>) =>
    api.get('/media-factory/render-queue', { params }),
};

/** 鍏ㄧ悆鍖栧璇█ `/api/v1/globalization/*` */
export const globalizationAPI = {
  overview: () => api.get('/globalization'),
  glossary: (params?: Record<string, unknown>) => api.get('/globalization/glossary', { params }),
  translatorStatus: () => api.get('/globalization/translator'),
  cultureAdaptStatus: () => api.get('/globalization/culture-adapt'),
};

/** 鏅鸿兘鐗╂祦瀹氫环 `/api/v1/logistics/*` */
export const logisticsAPI = {
  overview: () => api.get('/logistics'),
  lbsRouting: (params?: Record<string, unknown>) => api.get('/logistics/lbs-routing', { params }),
  freightCalc: (params?: Record<string, unknown>) => api.get('/logistics/freight-calc', { params }),
  quotations: (params?: Record<string, unknown>) => api.get('/logistics/quotation', { params }),
  createQuotation: (data: Record<string, unknown>) => api.post('/logistics/quotation', data),
};

/** 绯荤粺鍋ュ悍鍘嬫祴 `/api/v1/system-health/*` */
export const systemHealthAPI = {
  overview: () => api.get('/system-health'),
  stressTestStatus: () => api.get('/system-health/stress-test'),
  runStressTest: (data: Record<string, unknown>) => api.post('/system-health/stress-test', data),
  resourceMonitor: () => api.get('/system-health/resource-monitor'),
  backupStatus: () => api.get('/system-health/backup'),
  triggerBackup: () => api.post('/system-health/backup'),
  restoreBackup: (data: Record<string, unknown>) => api.post('/system-health/backup/restore', data),
};

/** AI娣卞害瀛︿範 `/api/v1/ai-learning/*` */
export const aiLearningAPI = {
  overview: () => api.get('/ai-learning'),
  behaviorAnalysis: () => api.get('/ai-learning/behavior'),
  conversionFunnel: () => api.get('/ai-learning/conversion-funnel'),
  autoABTestStatus: () => api.get('/ai-learning/auto-ab-test'),
  createAutoABTest: (data: Record<string, unknown>) => api.post('/ai-learning/auto-ab-test', data),
};

/** SaaS绉熸埛 `/api/v1/tenants/*` */
export const tenantsAPI = {
  overview: () => api.get('/tenants'),
  plans: () => api.get('/tenants/plans'),
  updatePlans: (data: Record<string, unknown>) => api.put('/tenants/plans', data),
  billing: (params?: Record<string, unknown>) => api.get('/tenants/billing', { params }),
  whiteLabel: () => api.get('/tenants/white-label'),
};

/** 璁ょ煡鏅鸿兘 `/api/v1/cognitive/*` */
export const cognitiveAPI = {
  overview: () => api.get('/cognitive'),
  qaEngine: () => api.get('/cognitive/qa-engine'),
  expertSystem: () => api.get('/cognitive/expert-system'),
  semanticIndex: () => api.get('/cognitive/semantic-index'),
};

/** 杈圭紭璁＄畻CDN `/api/v1/edge-cdn/*` */
export const edgeCDNAPI = {
  overview: () => api.get('/edge-cdn'),
  nodes: (params?: Record<string, unknown>) => api.get('/edge-cdn/nodes', { params }),
  deployNode: (data: Record<string, unknown>) => api.post('/edge-cdn/nodes', data),
  preheatStatus: () => api.get('/edge-cdn/preheat'),
  triggerPreheat: (data: Record<string, unknown>) => api.post('/edge-cdn/preheat', data),
  protocolStatus: () => api.get('/edge-cdn/protocol'),
};

/** 文件管理 `/api/v1/files/*` */
export const filesAPI = {
  upload: (file: File, opts?: { tenant_id?: string; storage_region?: string }) => {
    const formData = new FormData();
    formData.append('file', file);
    if (opts?.tenant_id) formData.append('tenant_id', opts.tenant_id);
    if (opts?.storage_region) formData.append('storage_region', opts.storage_region);
    return api.post('/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  uploadMulti: (files: File[], opts?: { tenant_id?: string; storage_region?: string }) => {
    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));
    if (opts?.tenant_id) formData.append('tenant_id', opts.tenant_id);
    if (opts?.storage_region) formData.append('storage_region', opts.storage_region);
    return api.post('/files/upload-multi', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  list: (params?: Record<string, unknown>) => api.get('/files', { params }),
  delete: (id: string) => api.delete(`/files/${id}`),
  stats: (params?: Record<string, unknown>) => api.get('/files/stats', { params }),
  storageProfile: (params?: Record<string, unknown>) =>
    api.get('/files/storage-profile', { params }),
};

/** 寮€鍙戣€呯敓鎬?`/api/v1/developer/*` */
export const developerAPI = {
  overview: () => api.get('/developer'),
  sdkList: () => api.get('/developer/sdk'),
  lowCodeStatus: () => api.get('/developer/low-code'),
  plugins: (params?: Record<string, unknown>) => api.get('/developer/plugins', { params }),
};

/** AI 生成 `/api/v1/ai/*` */
export const aiGenerateAPI = {
  generate: (data: Record<string, unknown>) => api.post('/ai/generate', data),
  optimize: (data: Record<string, unknown>) => api.post('/ai/optimize', data),
};

/** V2Ray 订阅 `/api/v1/super-admin/v2ray/*` */
export const v2rayAPI = {
  listSubscriptions: () => api.get('/super-admin/v2ray/subscriptions'),
  createSubscription: (data: Record<string, unknown>) =>
    api.post('/super-admin/v2ray/subscriptions', data),
  updateSubscription: (id: string | number) =>
    api.post(`/super-admin/v2ray/subscriptions/${id}/refresh`),
  deleteSubscription: (id: string | number) =>
    api.delete(`/super-admin/v2ray/subscriptions/${id}`),
};

export * from './ubrain/conversation';
export * from './ubrain/skill';
export * from './ubrain/task';
export * from './ubrain/invitation';
export * from './ubrain/sales';
export * from './founderOps';
export * from './oauthBindings';
export * from './oauth';
export * from './emailAuth';
export * from './authRefresh';
export * from './authPaths';
