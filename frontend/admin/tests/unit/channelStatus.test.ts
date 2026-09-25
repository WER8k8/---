/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { describe, it, expect } from 'vitest'
import {
  normalizeChannelState,
  channelStateLabel,
  channelStateSuffix,
  isChannelTrustworthy,
  getChannelStateMeta,
  CHANNEL_STATE_ORDER,
} from '@/utils/channelStatus'

describe('channelStatus 四态归一化', () => {
  it('后端现有取值 real/mock/coming_soon 正确映射到四态', () => {
    expect(normalizeChannelState('real')).toBe('live')
    expect(normalizeChannelState('mock')).toBe('mock')
    expect(normalizeChannelState('coming_soon')).toBe('blocked')
  })

  it('已对齐的四态原样保留', () => {
    expect(normalizeChannelState('live')).toBe('live')
    expect(normalizeChannelState('mock')).toBe('mock')
    expect(normalizeChannelState('degraded')).toBe('degraded')
    expect(normalizeChannelState('blocked')).toBe('blocked')
  })

  it('大小写与空白容错', () => {
    expect(normalizeChannelState('  REAL ')).toBe('live')
    expect(normalizeChannelState('Coming_Soon')).toBe('blocked')
  })

  it('未知 / 空值一律按 blocked 处理（诚实优先，不误判为可用）', () => {
    expect(normalizeChannelState('')).toBe('blocked')
    expect(normalizeChannelState(undefined)).toBe('blocked')
    expect(normalizeChannelState(null)).toBe('blocked')
    expect(normalizeChannelState('some_new_state')).toBe('blocked')
  })

  it('只有 live 可标记为可信商机', () => {
    expect(isChannelTrustworthy('real')).toBe(true)
    expect(isChannelTrustworthy('mock')).toBe(false)
    expect(isChannelTrustworthy('degraded')).toBe(false)
    expect(isChannelTrustworthy('coming_soon')).toBe(false)
  })

  it('下拉后缀：live 无后缀，其余带中文标注', () => {
    expect(channelStateSuffix('real')).toBe('')
    expect(channelStateSuffix('mock')).toBe('（演示数据）')
    expect(channelStateSuffix('coming_soon')).toBe('（不可用）')
    expect(channelStateSuffix('degraded')).toBe('（降级中）')
  })

  it('四态文案与顺序稳定，供图例渲染', () => {
    expect(CHANNEL_STATE_ORDER).toEqual(['live', 'mock', 'degraded', 'blocked'])
    expect(channelStateLabel('real')).toBe('可用')
    expect(channelStateLabel('mock')).toBe('演示数据')
    expect(getChannelStateMeta('degraded').state).toBe('degraded')
  })

  it('四态颜色互不相同（避免仅靠颜色也要保证四态可区分）', () => {
    const colors = new Set(CHANNEL_STATE_ORDER.map((s) => getChannelStateMeta(s).color))
    expect(colors.size).toBe(4)
  })
})
