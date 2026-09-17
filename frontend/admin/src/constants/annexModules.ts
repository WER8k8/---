/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * 附属执行台（annex）模块注册表 · 标签与嵌入地址的单一真源
 *
 * 背景：annex 页通过 iframe 挂载 _external 下的附属应用，握手走 POST /annex/ticket。
 * 关键约束：Vite 默认 envPrefix = 'VITE_'，**非 VITE_ 前缀的环境变量不会进入 import.meta.env**，
 * 因此 embed 地址必须写成 VITE_XXX_EMBED_URL（历史实现用 GOODJOB_EMBED_URL 导致永远读不到）。
 */

export interface AnnexModuleMeta {
  /** 菜单与页头展示名 */
  label: string;
  /** 嵌入地址所在的 Vite 环境变量键 */
  envKey: string;
  /** 一句话定位（副标题） */
  desc: string;
  /** 超管壳入口 */
  adminPath: string;
  /** 租户壳入口 */
  clientPath: string;
}

export const ANNEX_MODULES: Record<string, AnnexModuleMeta> = {
  'trade-ai': {
    label: 'TradeAI 执行台',
    envKey: 'VITE_TRADEAI_EMBED_URL',
    desc: '附属一 · AI 营销执行台',
    adminPath: '/admin/annex/trade-ai',
    clientPath: '/client/annex/trade-ai',
  },
  goodjob: {
    label: 'GoodJob 执行台',
    envKey: 'VITE_GOODJOB_EMBED_URL',
    desc: '附属二 · 外贸 CRM 执行台',
    adminPath: '/admin/annex/goodjob',
    clientPath: '/client/annex/goodjob',
  },
};

export function annexMeta(key: string): AnnexModuleMeta | null {
  return ANNEX_MODULES[key] ?? null;
}

/** 从 Vite env 读取某个附属的嵌入地址；未配置返回空串 */
export function resolveAnnexEmbedUrl(
  key: string,
  env: Record<string, string | undefined> = import.meta.env as Record<string, string | undefined>,
): string {
  const meta = annexMeta(key);
  if (!meta) return '';
  return String(env[meta.envKey] || '').trim();
}

/** GoodJob CRM 附属模块（挂载于 /client/annex/goodjob/<module>） */
export interface GoodJobModuleMeta {
  /** 路由段与 annexModule meta 值 */
  key: 'tickets' | 'customers';
  /** 菜单与页头展示名 */
  label: string;
  /** 页面副标题 */
  desc: string;
  /** GoodJob 内部 data-view id，用作最佳努力直达参数 gj_view */
  view: string;
}

/** 独立、清晰可访问的 GoodJob CRM 功能模块清单 */
export const GOODJOB_MODULES: GoodJobModuleMeta[] = [
  {
    key: 'tickets',
    label: '票据中心管理',
    desc: '外贸单证 · PI/CI/PL/CO 套打 · 报关资料平台',
    view: 'documents',
  },
  {
    key: 'customers',
    label: '客户管理',
    desc: '客户池 · 商机 · 跟进与线索管理',
    view: 'customers',
  },
];

/** 按模块 key 查表 */
export function goodjobModuleMeta(key: string): GoodJobModuleMeta | undefined {
  return GOODJOB_MODULES.find((m) => m.key === key);
}
