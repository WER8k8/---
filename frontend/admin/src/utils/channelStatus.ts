/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * 获客渠道可用状态 —— 前端统一四态：live / mock / degraded / blocked
 *
 * 背景与口径：
 * 后端真源 `backend/app/services/ubrain/channel_status.py` 目前只产出
 * `real / mock / coming_soon`（见 `backend/app/api/v1/routes/acquisition.py`
 * 的 GET /acquisition/channels）。本模块负责把它归一化到前端统一四态，
 * 并同时兼容后端未来直接下发 live / degraded / blocked 的情况，避免两端
 * 取值域不一致时前端静默失败。
 *
 * 四态语义（务必与运营口径一致）：
 *   live     真实可用：已配置真实 API 凭证，产出为真实线索
 *   mock     演示数据：未配置凭证，返回演示数据 —— 不可当作真实商机
 *   degraded 降级可用：部分可用 / 间接测量，结果仅供参考
 *   blocked  不可用：尚未开发或已被禁用，无法获取线索
 *
 * 注意：四态在 UI 上都同时用「图标 + 文案 + 颜色」三重要素表达，
 * 不允许只靠颜色区分（色盲可访问性）。
 */

export type ChannelState = 'live' | 'mock' | 'degraded' | 'blocked'

/** 后端取值 → 前端四态。未识别的取值一律按 blocked 处理（诚实优先）。 */
const STATE_ALIASES: Record<string, ChannelState> = {
  // 已对齐四态
  live: 'live',
  mock: 'mock',
  degraded: 'degraded',
  blocked: 'blocked',
  // 后端当前取值别名
  real: 'live',
  coming_soon: 'blocked',
  comingsoon: 'blocked',
  // 常见同义词兜底
  ok: 'live',
  healthy: 'live',
  ready: 'live',
  demo: 'mock',
  fake: 'mock',
  stub: 'mock',
  partial: 'degraded',
  indirect: 'degraded',
  disabled: 'blocked',
  offline: 'blocked',
  error: 'blocked',
  unavailable: 'blocked',
}

export interface ChannelStateMeta {
  /** 归一化状态 */
  state: ChannelState
  /** 中文短文案（徽标内展示） */
  label: string
  /** 语义色（取自设计 token，随主题变化） */
  color: string
  /** 浅底色（同一 token 家族） */
  background: string
  /** 是否可以当作真实商机使用 */
  trustworthy: boolean
  /** 悬停说明 */
  description: string
}

export const CHANNEL_STATE_META: Record<ChannelState, ChannelStateMeta> = {
  live: {
    state: 'live',
    label: '可用',
    color: 'var(--uj-success, #16a34a)',
    background: 'color-mix(in srgb, var(--uj-success, #16a34a) 12%, transparent)',
    trustworthy: true,
    description: '已配置真实 API，产出为真实线索。',
  },
  mock: {
    state: 'mock',
    label: '演示数据',
    color: 'var(--uj-warning, #d97706)',
    background: 'color-mix(in srgb, var(--uj-warning, #d97706) 14%, transparent)',
    trustworthy: false,
    description: '未配置凭证，当前返回演示数据，不可当作真实商机。',
  },
  degraded: {
    state: 'degraded',
    label: '降级中',
    color: 'var(--uj-info-strong, #2b6295)',
    background: 'color-mix(in srgb, var(--uj-info-strong, #2b6295) 12%, transparent)',
    trustworthy: false,
    description: '部分可用或为间接测量，结果仅供参考，需人工复核。',
  },
  blocked: {
    state: 'blocked',
    label: '不可用',
    color: 'var(--uj-danger, #dc2626)',
    background: 'color-mix(in srgb, var(--uj-danger, #dc2626) 12%, transparent)',
    trustworthy: false,
    description: '尚未开发或已被禁用，无法获取线索。',
  },
}

/** 把任意后端取值归一化到前端四态 */
export function normalizeChannelState(raw?: string | null): ChannelState {
  if (!raw) return 'blocked'
  const key = String(raw).trim().toLowerCase()
  return STATE_ALIASES[key] ?? 'blocked'
}

export function getChannelStateMeta(raw?: string | null): ChannelStateMeta {
  return CHANNEL_STATE_META[normalizeChannelState(raw)]
}

/** 短文案，例如「可用」「演示数据」 */
export function channelStateLabel(raw?: string | null): string {
  return getChannelStateMeta(raw).label
}

/** 下拉选项后缀：live 返回空串，其余返回「（演示数据）」 */
export function channelStateSuffix(raw?: string | null): string {
  const meta = getChannelStateMeta(raw)
  return meta.state === 'live' ? '' : `（${meta.label}）`
}

/** 是否可当作真实商机 */
export function isChannelTrustworthy(raw?: string | null): boolean {
  return getChannelStateMeta(raw).trustworthy
}

/** 四态固定顺序，供图例渲染 */
export const CHANNEL_STATE_ORDER: ChannelState[] = ['live', 'mock', 'degraded', 'blocked']
