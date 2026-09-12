/**
 * 超级管理员认证中间件（基于 ECC 安全规范重构）
 *
 * 变更：
 *   - 公开路径由规则数组定义，新增路由只需追加模式无需改判断逻辑
 *   - 完全移除 localStorage 依赖，统一使用 Cookie 管理 token
 *   - 静态资源路径 /api/ 和资源文件自动放行
 */

/** 公开路径精确匹配列表 */
const PUBLIC_EXACT: string[] = [
  '/admin/login',
  '/',
  '/products',
  '/cases',
  '/news',
  '/about',
  '/contact',
  '/terms',
  '/privacy',
  '/sitemap.xml',
  '/tenant',
  '/error',
];

/** 公开路径前缀匹配列表（支持动态路由如 /news/slug） */
const PUBLIC_PREFIXES: string[] = [
  '/products/',
  '/cases/',
  '/news/',
  '/tenant/',
  '/tenant',
];

/** 无需认证的资源前缀 */
const STATIC_PREFIXES: string[] = [
  '/_nuxt/',
  '/__nuxt',
  '/api/',
  '/images/',
  '/fonts/',
  '/favicon.',
  '/.well-known/',
];

function isPublicPath(path: string): boolean {
  if (PUBLIC_EXACT.includes(path)) return true;
  if (PUBLIC_PREFIXES.some((p) => path.startsWith(p))) return true;
  if (STATIC_PREFIXES.some((p) => path.startsWith(p))) return true;
  return false;
}

export default defineNuxtRouteMiddleware((to) => {
  // 公开路径直接放行
  if (isPublicPath(to.path)) return;

  // /admin/* 需要认证
  if (to.path.startsWith('/admin')) {
    if (import.meta.client) {
      const token = useCookie('admin_token').value;
      if (!token) {
        return navigateTo('/admin/login');
      }
    }
  }
});
