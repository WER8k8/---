/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * LOGIN-LOCK-01 · 平台超管唯一登录入口
 *
 * 硬锁契约：../../.project/login-entry-lock.json
 * 角色壳隔离：../../.project/role-shell-lock.json → roleShellLock.ts
 * 说明文档：../../docs/product/LOGIN-SINGLE-ENTRY-CHARTER.md
 *
 * 禁止：四门户 ?portal=、多门户预填凭据表、client/login.vue、多套 login/*.vue
 * 改本文件或 router 登录路由前请跑：npm run cert:login-lock
 */

/** 平台超管登录页文案（唯一登录入口 /login） */

export interface LoginPortalFeature {
  icon: string;
  title: string;
  desc: string;
}

export interface LoginPortalCopy {
  welcomeTitle: string;
  welcomeDesc: string;
  brandTitle: [string, string];
  brandLead: string;
  features: LoginPortalFeature[];
  foot: string;
  submitLabel: string;
}

export const PLATFORM_LOGIN_COPY: LoginPortalCopy = {
  welcomeTitle: '辛苦了，欢迎回家',
  welcomeDesc: '登录后进入平台控制台',
  brandTitle: ['优丁平台', '运营控制台'],
  brandLead: '平台运营与租户治理，从这里开始。',
  features: [
    { icon: '租', title: '租户', desc: '开通、套餐、用量与续费治理' },
    { icon: '系', title: '系统', desc: '角色权限、审计与全局配置' },
    { icon: '数', title: '数据', desc: '平台指标、渠道与业务总览' },
  ],
  foot: '内部运营 · 租户与系统治理',
  submitLabel: '进入控制台',
};

/**
 * 本地开发账号仅存放在仓库外/契约文件，禁止写入登录页 UI 或前端源码：
 * `.project/dev-login-accounts.json` · `scripts/start-dev-admin.ps1`
 */

export const LOGIN_PATH = '/login';

export function loginPortalPath(): string {
  return LOGIN_PATH;
}

export {
  homePathForRole,
  isTenantLoginIntent,
  resolveLoginTarget,
} from '@/constants/roleShellLock';
