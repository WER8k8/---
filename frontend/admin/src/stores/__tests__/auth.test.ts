/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

// Mock API modules before importing the store
vi.mock('@/api/authPaths', () => ({
  authLoginUrl: () => '/api/v1/auth/login',
}));

vi.mock('@/api/emailAuth', () => ({
  loginByEmail: vi.fn(),
}));

vi.mock('@/api/oauth', () => ({
  exchangeThirdPartyLogin: vi.fn(),
}));

vi.mock('@/api/authRefresh', () => ({
  performSilentTokenRefresh: vi.fn().mockResolvedValue(false),
}));

vi.mock('@/api/admin-bff', () => ({
  bffLogin: vi.fn(),
  bffLogout: vi.fn(),
  bffUserInfo: vi.fn(),
}));

vi.mock('@/stores/agentCapabilities', () => ({
  useAgentCapabilitiesStore: () => ({
    applyJwtRoleToSessionLevel: vi.fn(),
    resetSessionLevelFromJwt: vi.fn(),
  }),
}));

import { bffLogin, bffLogout } from '@/api/admin-bff';
import { useAuthStore } from '../auth';

/** Build a minimal JWT with base64url payload */
function makeJwt(payload: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const body = btoa(JSON.stringify(payload)).replace(/=/g, '');
  return `${header}.${body}.sig`;
}

function makeNonExpiringJwt(role: string, extra: Record<string, unknown> = {}): string {
  return makeJwt({ role, exp: Math.floor(Date.now() / 1000) + 3600, ...extra });
}

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    sessionStorage.clear();
    localStorage.clear();
  });

  describe('initial state', () => {
    it('starts with null token and not authenticated', () => {
      const auth = useAuthStore();
      expect(auth.token).toBeNull();
      expect(auth.username).toBeNull();
      expect(auth.isAuthenticated).toBe(false);
    });
  });

  describe('login', () => {
    it('stores token and username on successful login', async () => {
      const access = makeNonExpiringJwt('admin');
      vi.mocked(bffLogin).mockResolvedValue({
        accessToken: access,
        refreshToken: 'refresh-abc',
      });

      const auth = useAuthStore();
      await auth.login('admin', 'pass123');

      expect(auth.token).toBe(access);
      expect(auth.username).toBe('admin');
      expect(sessionStorage.getItem('admin_token')).toBe(access);
      expect(sessionStorage.getItem('admin_username')).toBe('admin');
      expect(sessionStorage.getItem('admin_refresh_token')).toBe('refresh-abc');
    });

    it('throws on wrong password (non-ok response)', async () => {
      vi.mocked(bffLogin).mockRejectedValue(new Error('账号或密码错误'));

      const auth = useAuthStore();
      await expect(auth.login('admin', 'wrong')).rejects.toThrow('账号或密码错误');
      expect(auth.token).toBeNull();
    });

    it('throws on rate limit (429)', async () => {
      vi.mocked(bffLogin).mockRejectedValue(new Error('Too many requests'));

      const auth = useAuthStore();
      await expect(auth.login('admin', 'pass')).rejects.toThrow('Too many requests');
    });
  });

  describe('logout', () => {
    it('clears all tokens and storage', async () => {
      const access = makeNonExpiringJwt('admin');
      vi.mocked(bffLogin).mockResolvedValue({ accessToken: access });
      vi.mocked(bffLogout).mockResolvedValue();

      const auth = useAuthStore();
      await auth.login('admin', 'pass');
      expect(auth.token).not.toBeNull();

      await auth.logout();
      expect(auth.token).toBeNull();
      expect(auth.refreshToken).toBeNull();
      expect(auth.username).toBeNull();
      expect(sessionStorage.getItem('admin_token')).toBeNull();
      expect(sessionStorage.getItem('admin_username')).toBeNull();
    });
  });

  describe('currentRole', () => {
    it('extracts role from JWT payload', () => {
      const access = makeNonExpiringJwt('super_admin');
      const auth = useAuthStore();
      auth.applyTokenPair(access, 'refresh');
      expect(auth.currentRole).toBe('super_admin');
    });

    it('returns undefined when no token', () => {
      const auth = useAuthStore();
      expect(auth.currentRole).toBeUndefined();
    });
  });

  describe('applyTokenPair', () => {
    it('sets both access and refresh tokens', () => {
      const access = makeNonExpiringJwt('editor');
      const auth = useAuthStore();
      auth.applyTokenPair(access, 'refresh-xyz');
      expect(auth.token).toBe(access);
      expect(auth.refreshToken).toBe('refresh-xyz');
      expect(sessionStorage.getItem('admin_token')).toBe(access);
      expect(sessionStorage.getItem('admin_refresh_token')).toBe('refresh-xyz');
    });
  });
});
