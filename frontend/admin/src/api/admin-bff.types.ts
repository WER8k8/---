/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * UAC 类型 — 与 backend/app/api/v1/admin_bff/schemas 对齐
 */

export interface UacTenantBrief {
  id: string;
  name: string;
  code: string;
}

export interface UacOnboardingStep {
  id: string;
  title: string;
  route: string;
  order: number;
  done: boolean;
}

export interface UacPlanUsage {
  plan_code?: string;
  plan_name?: string;
  ai_quota_used?: number;
  ai_quota_max?: number;
  ai_quota_pct?: number;
  status?: string;
  expires_at?: string | null;
}

export interface UacUserInfo {
  id: string;
  userId: string;
  username: string;
  nickname?: string;
  realName?: string;
  shell: string;
  homePath: string;
  roles: string[];
  tenant?: UacTenantBrief | null;
  onboarding_steps: UacOnboardingStep[];
  plan_usage: UacPlanUsage;
}

export interface UacMenuRoute {
  name: string;
  path: string;
  component?: string;
  redirect?: string;
  meta?: Record<string, unknown>;
  children?: UacMenuRoute[];
}

export interface UacPermissionBundle {
  shell: string;
  roles: string[];
  codes: string[];
  homePath: string;
}

export interface UacLoginResult {
  accessToken: string;
  refreshToken?: string;
}

export interface UacTenantSearchHit {
  tenantId: string;
  tenantCode: string;
  tenantName: string;
}

/** BFF 基址 — 与 Vben 一致，独立于 legacy /api/v1 CRUD */
export const BFF_BASE_URL = '/api/v1/admin-bff';
