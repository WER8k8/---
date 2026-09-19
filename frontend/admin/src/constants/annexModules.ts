/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * 功能域模块注册表（原 annex）· 标签与嵌入地址的单一真源
 *
 * 主理人裁定（2026-09-19）：GoodJob / TradeAI 是优丁**功能域菜单**，**并无特权**。
 * - 菜单与页头使用业务功能名，禁止「附属执行台 / 附属一 / 附属二」特权叙事
 * - 权限与其它业务模块同级，走 UJ RBAC，无第二套超管壳
 * - 技术上仍可经 iframe/票据挂引擎诊断（非主产品路径）
 * 约束：embed 地址必须 VITE_ 前缀才能进 import.meta.env。
 */

export interface AnnexModuleMeta {
  /** 菜单与页头展示名（业务功能域，无特权措辞） */
  label: string;
  /** 嵌入地址所在的 Vite 环境变量键 */
  envKey: string;
  /** 一句话定位（副标题） */
  desc: string;
  /** 超管壳入口 */
  adminPath: string;
  /** 租户壳入口 */
  clientPath: string;
  /** 所属功能域菜单分组（与其它业务模块同级） */
  domain: string;
  /** 是否特权入口：恒 false（功能域菜单无特权） */
  privileged: false;
}

export const ANNEX_MODULES: Record<string, AnnexModuleMeta> = {
  'trade-ai': {
    label: '社媒拓客',
    envKey: 'VITE_TRADEAI_EMBED_URL',
    desc: '获客转化 · 社媒挖掘与智能触达',
    adminPath: '/admin/annex/trade-ai',
    clientPath: '/client/annex/trade-ai',
    domain: '获客转化',
    privileged: false,
  },
  goodjob: {
    label: '外贸履约',
    envKey: 'VITE_GOODJOB_EMBED_URL',
    desc: '履约与账户 · 外贸单证与客户跟进',
    adminPath: '/admin/annex/goodjob',
    clientPath: '/client/annex/goodjob',
    domain: '履约与账户',
    privileged: false,
  },
};

export function annexMeta(key: string): AnnexModuleMeta | null {
  return ANNEX_MODULES[key] ?? null;
}

/** 从 Vite env 读取某个功能域引擎的嵌入地址；未配置返回空串 */
export function resolveAnnexEmbedUrl(
  key: string,
  env: Record<string, string | undefined> = import.meta.env as Record<string, string | undefined>,
): string {
  const meta = annexMeta(key);
  if (!meta) return '';
  return String(env[meta.envKey] || '').trim();
}

/** 外贸履约功能域子模块（挂载于 /client/annex/goodjob/<module>） */
export interface GoodJobModuleMeta {
  key: 'tickets' | 'customers';
  label: string;
  desc: string;
  view: string;
}

export const GOODJOB_MODULES: GoodJobModuleMeta[] = [
  {
    key: 'tickets',
    label: '外贸单证',
    desc: 'PI/CI/PL/CO 套打 · 报关资料',
    view: 'documents',
  },
  {
    key: 'customers',
    label: '客户档案',
    desc: '客户池 · 商机 · 跟进与线索',
    view: 'customers',
  },
];

export function goodjobModuleMeta(key: string): GoodJobModuleMeta | undefined {
  return GOODJOB_MODULES.find((m) => m.key === key);
}

/** 功能域菜单是否无特权（门禁用） */
export function annexDomainsHaveNoPrivilege(): boolean {
  return Object.values(ANNEX_MODULES).every((m) => m.privileged === false);
}