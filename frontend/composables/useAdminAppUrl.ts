/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * Admin SPA 外链（注册 / 登录 / 完整 Landing 镜像）
 * 生产通过 NUXT_PUBLIC_UNIFIED_ADMIN_LOGIN_URL 注入；本地默认 :5173
 */
export function useAdminAppUrl() {
  const config = useRuntimeConfig();

  const base = computed(() => {
    const loginUrl = (config.public.unifiedAdminLoginUrl as string) || '';
    if (loginUrl) {
      return loginUrl.replace(/\/login(\?.*)?$/, '');
    }
    if (import.meta.dev) {
      return 'http://127.0.0.1:5173';
    }
    return '';
  });

  function login(_portal?: 'tenant' | 'agent' | 'partner' | 'platform') {
    // LOGIN-LOCK-01：唯一登录页固定平台门面（data-portal="platform"），admin 端不解析
    // ?portal= 多门户参数 —— 历史遗留的生成端已拆除（2026-10-01 审计残留清理），
    // 保留形参以兼容既有调用方（pages/platform/index.vue 的 admin.login(...)）。
    const root = base.value || '/';
    return `${root}/login`;
  }

  return {
    base,
    login,
    register: computed(() => `${base.value}/tenants/register`),
    pricing: computed(() => `${base.value}/tenants/pricing`),
    landingMirror: computed(() => `${base.value}/landing`),
  };
}
