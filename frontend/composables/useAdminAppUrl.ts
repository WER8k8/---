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

  function login(portal?: 'tenant' | 'agent' | 'partner' | 'platform') {
    const root = base.value || '/';
    if (!portal) return `${root}/login`;
    return `${root}/login?portal=${portal}`;
  }

  return {
    base,
    login,
    register: computed(() => `${base.value}/tenants/register`),
    pricing: computed(() => `${base.value}/tenants/pricing`),
    landingMirror: computed(() => `${base.value}/landing`),
  };
}
