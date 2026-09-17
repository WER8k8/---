/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

// Mock auth store so we can control currentRole / username
let mockRole: string | undefined;
let mockUsername: string | null = null;

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    get currentRole() { return mockRole; },
    get username() { return mockUsername; },
  }),
}));

vi.mock('@/stores/agentCapabilities', () => ({
  useAgentCapabilitiesStore: () => ({
    applyJwtRoleToSessionLevel: vi.fn(),
    resetSessionLevelFromJwt: vi.fn(),
  }),
}));

vi.mock('@/api/authPaths', () => ({ authLoginUrl: () => '/api/v1/auth/login' }));
vi.mock('@/api/emailAuth', () => ({ loginByEmail: vi.fn() }));
vi.mock('@/api/oauth', () => ({ exchangeThirdPartyLogin: vi.fn() }));
vi.mock('@/api/authRefresh', () => ({ performSilentTokenRefresh: vi.fn().mockResolvedValue(false) }));

import { useEffectivePlatformRole } from '../useEffectivePlatformRole';

describe('useEffectivePlatformRole', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    sessionStorage.clear();
    localStorage.clear();
    mockRole = undefined;
    mockUsername = null;
  });

  it('returns super_admin for dev admin username in dev mode', () => {
    mockRole = 'admin';
    mockUsername = 'admin';

    const { role } = useEffectivePlatformRole();
    expect(role.value).toBe('super_admin');
  });

  it('returns JWT role for non-admin username', () => {
    mockRole = 'editor';
    mockUsername = 'editor_user';

    const { role } = useEffectivePlatformRole();
    expect(role.value).toBe('editor');
  });

  it('returns undefined when role and username are both null', () => {
    mockRole = undefined;
    mockUsername = null;

    const { role } = useEffectivePlatformRole();
    expect(role.value).toBeUndefined();
  });

  it('roleLabel maps super_admin to 平台超管', () => {
    mockRole = 'super_admin';
    mockUsername = 'super_user';

    const { roleLabel } = useEffectivePlatformRole();
    expect(roleLabel.value).toBe('平台超管');
  });

  it('roleLabel maps admin to 运营管理员', () => {
    mockRole = 'admin';
    mockUsername = 'ops_user';

    const { roleLabel } = useEffectivePlatformRole();
    expect(roleLabel.value).toBe('运营管理员');
  });

  it('workbenchTitle reflects role', () => {
    mockRole = 'super_admin';
    mockUsername = 'super_user';

    const { workbenchTitle } = useEffectivePlatformRole();
    expect(workbenchTitle.value).toBe('平台超管工作台');
  });

  it('needsDevRelogin is true for admin/admin in dev', () => {
    mockRole = 'admin';
    mockUsername = 'admin';

    const { needsDevRelogin } = useEffectivePlatformRole();
    expect(needsDevRelogin.value).toBe(true);
  });

  it('needsDevRelogin is false for non-admin username', () => {
    mockRole = 'admin';
    mockUsername = 'ops_user';

    const { needsDevRelogin } = useEffectivePlatformRole();
    expect(needsDevRelogin.value).toBe(false);
  });
});
