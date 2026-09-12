import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { bffLogin, bffLogout, bffUserInfo } from '@/api/admin-bff';
import { loginByEmail } from '@/api/emailAuth';
import { exchangeThirdPartyLogin, type OAuthProvider } from '@/api/oauth';
import { decodeJwtPayload, isJwtExpired, jwtRoleFromPayload } from '@/utils/jwtPayload';
import {
  canRestoreSession,
  hasValidAccessToken,
  readStoredAccessToken,
  readStoredRefreshToken,
} from '@/utils/sessionAuth';
import { performSilentTokenRefresh } from '@/api/authRefresh';
import { useAgentCapabilitiesStore } from '@/stores/agentCapabilities';

const LS_REFRESH = 'admin_refresh_token';
let authInitPromise: Promise<void> | null = null;
let authInitResolved = false;
let authInitGeneration = 0;

function invalidateAuthInit() {
  authInitPromise = null;
  authInitResolved = false;
  authInitGeneration += 1;
}

// FIX-22: 不再使用 sessionStorage 存储 Token（迁移到 HttpOnly Cookie）
// 保留 sessionStorage 仅用于 username 记忆（非敏感信息）
const tokenStore = typeof sessionStorage !== 'undefined' ? sessionStorage : (typeof localStorage !== 'undefined' ? localStorage : null);

/** SECURITY: uj_user_info Cookie 已改为 HttpOnly，前端无法直接读取
 * 前端通过 bffUserInfo API 获取用户信息 */
function readUserInfoCookie(): null {
  return null;
}

export const useAuthStore = defineStore('auth', () => {
  // SECURITY: uj_user_info Cookie 已改为 HttpOnly，初始状态从 sessionStorage 记忆或 API 获取
  const token = ref<string | null>(null);
  const refreshToken = ref<string | null>(null);
  const username = ref<string | null>(tokenStore?.getItem('admin_username') ?? null);
  const lastJwtSyncedForCapabilities = ref<string | null>(null);
  /** FIX-23: Cookie 认证模式下从 bffUserInfo 保存角色，避免 decodeJwtPayload('cookie') 失败 */
  const cookieAuthRole = ref<string | undefined>(undefined);

  /** 登录/OAuth 刚写入 token 后标记就绪，避免路由守卫重复走续期链 */
  function markAuthSessionReady(access: string) {
    authInitPromise = null;
    authInitResolved = true;
    lastJwtSyncedForCapabilities.value = access;
  }

  /** SECURITY: 认证状态从内存 Token 或 sessionStorage 判断（Cookie 已 HttpOnly） */
  const isAuthenticated = computed(() => {
    if (token.value) return true;
    return canRestoreSession();
  });

  /** SECURITY: 角色从 JWT 解析（Cookie 已 HttpOnly，通过 ensureAuthInitialized 同步） */
  const currentRole = computed<string | undefined>(() => {
    /** FIX-23: Cookie 认证模式下直接从 bffUserInfo 缓存读取角色 */
    if (cookieAuthRole.value) return cookieAuthRole.value;
    const t = token.value;
    if (!t || t === 'cookie') return undefined;
    return jwtRoleFromPayload(decodeJwtPayload(t)) as string | undefined;
  });

  function applyTokenPair(access: string, refresh?: string) {
    invalidateAuthInit();
    token.value = access;
    refreshToken.value = refresh || null;
    // 写入 sessionStorage 供 legacy api 客户端读取（BFF 客户端走 Cookie）
    tokenStore?.setItem('admin_token', access);
    if (refresh) {
      tokenStore?.setItem('admin_refresh_token', refresh);
    } else {
      // Cookie 模式轮换不回传新 rt：旧 rt 已被后端 revoke，残留会让下一次
      // refresh 带 body 旧值而 401 → hardLogout。清掉，刷新走最新 Cookie。
      tokenStore?.removeItem('admin_refresh_token');
    }
    useAgentCapabilitiesStore().applyJwtRoleToSessionLevel(
      jwtRoleFromPayload(decodeJwtPayload(access))
    );
    markAuthSessionReady(access);
  }

  async function login(usernameValue: string, password: string) {
    try {
      // FIX-21: BFF 层真正落地 — 登录走 BFF 统一接入契约
      const result = await bffLogin(usernameValue, password);
      const accessToken = result.accessToken;
      if (!accessToken) {
        throw new Error('登录失败，请稍后再试');
      }
      token.value = accessToken;
      username.value = usernameValue;
      // 写入 sessionStorage 供 legacy api 客户端读取（BFF 客户端走 Cookie）
      tokenStore?.setItem('admin_token', accessToken);
      tokenStore?.setItem('admin_username', usernameValue);
      if (typeof result.refreshToken === 'string' && result.refreshToken.length > 0) {
        refreshToken.value = result.refreshToken;
        tokenStore?.setItem('admin_refresh_token', result.refreshToken);
      } else {
        refreshToken.value = null;
      }

      useAgentCapabilitiesStore().resetSessionLevelFromJwt(accessToken);
      markAuthSessionReady(accessToken);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      if (msg.includes('Failed to fetch') || msg.includes('Network Error'))
        throw new Error('无法连接后端 API，请先启动 backend（127.0.0.1:8001）并确认管理端由 Vite 提供（npm run dev）');
      // BFF 层已处理 HTTP 状态码 → Error message 映射
      throw e;
    }
  }

  async function loginWithEmail(email: string, code: string) {
    const data = await loginByEmail(email, code);
    const refresh =
      typeof data.refresh_token === 'string' && data.refresh_token.length > 0
        ? data.refresh_token
        : '';
    if (refresh) {
      applyTokenPair(data.access_token, refresh);
    } else {
      token.value = data.access_token;
      tokenStore?.setItem('admin_token', data.access_token);
      useAgentCapabilitiesStore().resetSessionLevelFromJwt(data.access_token);
      markAuthSessionReady(data.access_token);
    }
    username.value = email;
    tokenStore?.setItem('admin_username', email);
  }

  async function loginWithOAuth(provider: OAuthProvider, code: string, state?: string) {
    const data = await exchangeThirdPartyLogin(provider, code, state);
    const refresh =
      typeof data.refresh_token === 'string' && data.refresh_token.length > 0
        ? data.refresh_token
        : '';
    if (refresh) {
      applyTokenPair(data.access_token, refresh);
    } else {
      token.value = data.access_token;
      tokenStore?.setItem('admin_token', data.access_token);
      useAgentCapabilitiesStore().resetSessionLevelFromJwt(data.access_token);
      markAuthSessionReady(data.access_token);
    }
    const name = data.user?.username || provider;
    username.value = name;
    tokenStore?.setItem('admin_username', name);
  }

  async function logout() {
    token.value = null;
    refreshToken.value = null;
    username.value = null;
    lastJwtSyncedForCapabilities.value = null;
    cookieAuthRole.value = undefined;
    invalidateAuthInit();
    tokenStore?.removeItem('admin_token');
    tokenStore?.removeItem('admin_refresh_token');
    tokenStore?.removeItem('admin_username');
    useAgentCapabilitiesStore().resetSessionLevelFromJwt(null);
    // FIX-22: 调用 BFF logout 清除 HttpOnly Cookies
    // 调用方必须 await 本函数后再导航：cookie 清除完成前放行导航，
    // ensureAuthInitialized 会用残留 cookie 调 bffUserInfo 重新水合会话，
    // 导致"退出后弹回工作台"竞态
    await bffLogout().catch(() => {});
  }

  async function ensureAuthInitialized() {
    if (typeof window === 'undefined') return;

    const access = token.value ?? readStoredAccessToken();
    /** FIX-23: 区分 Cookie 认证模式与 JWT 模式，避免 isJwtExpired('cookie') 误报过期 */
    const isCookieAuth = access === 'cookie';
    if (
      authInitResolved &&
      access &&
      (isCookieAuth || !isJwtExpired(access)) &&
      lastJwtSyncedForCapabilities.value === access
    ) {
      if (token.value !== access) token.value = access;
      return;
    }

    if (access && !isCookieAuth && isJwtExpired(access)) {
      invalidateAuthInit();
    }

    if (authInitPromise) {
      await authInitPromise;
      return;
    }
    const generationAtStart = authInitGeneration;
    authInitPromise = (async () => {
      // SECURITY: 通过 BFF API 获取用户信息（Cookie 已 HttpOnly）
      try {
        const info = await bffUserInfo();
        if (info) {
          token.value = 'cookie' as any;
          /** FIX-23: UacUserInfo 使用 roles 数组，取首个作为主角色 */
          const primaryRole = info.roles?.[0] || (info as any).role || info.shell;
          cookieAuthRole.value = primaryRole;
          username.value = info.username || username.value;
          lastJwtSyncedForCapabilities.value = token.value;
          useAgentCapabilitiesStore().applyJwtRoleToSessionLevel(primaryRole as any);
          return;
        }
      } catch {
        // Cookie 过期或无效
        cookieAuthRole.value = undefined;
      }

      if (token.value == null) token.value = readStoredAccessToken();
      if (refreshToken.value == null) refreshToken.value = readStoredRefreshToken();
      if (username.value == null) username.value = tokenStore?.getItem('admin_username') ?? null;

      const currentAccess = token.value;
      if (!currentAccess && !canRestoreSession()) {
        lastJwtSyncedForCapabilities.value = null;
        return;
      }
      if (!currentAccess || isJwtExpired(currentAccess)) {
        if (canRestoreSession()) {
          const ok = await performSilentTokenRefresh();
          if (ok) {
            token.value = readStoredAccessToken();
            refreshToken.value = readStoredRefreshToken();
          }
        }
      }
      if (!token.value) {
        lastJwtSyncedForCapabilities.value = null;
        return;
      }
      if (lastJwtSyncedForCapabilities.value === token.value) return;
      lastJwtSyncedForCapabilities.value = token.value;
      useAgentCapabilitiesStore().applyJwtRoleToSessionLevel(
        jwtRoleFromPayload(decodeJwtPayload(token.value)),
      );
    })();
    try {
      await authInitPromise;
    } finally {
      if (generationAtStart === authInitGeneration) {
        authInitResolved = true;
      }
    }
  }

  return {
    token,
    refreshToken,
    username,
    isAuthenticated,
    currentRole,
    login,
    loginWithEmail,
    loginWithOAuth,
    logout,
    ensureAuthInitialized,
    applyTokenPair,
  };
});
