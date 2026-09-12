import { describe, expect, it, beforeEach } from 'vitest'
import {
  SESSION_KICKED_FLAG,
  SESSION_KICKED_MESSAGE,
  consumeSessionKickedMessage,
  isSessionReplacedPayload,
  markSessionKicked,
} from './sessionKick'

describe('sessionKick', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  it('detects FastAPI detail.error_code', () => {
    expect(
      isSessionReplacedPayload({
        detail: { message: 'x', error_code: 'SESSION_REPLACED' },
      }),
    ).toBe(true)
  })

  it('detects top-level error_code from refresh', () => {
    expect(
      isSessionReplacedPayload({
        code: 401,
        message: '账号已在其他设备登录，请重新登录',
        error_code: 'SESSION_REPLACED',
        data: null,
      }),
    ).toBe(true)
  })

  it('detects SESSION_REPLACED embedded in message string', () => {
    expect(
      isSessionReplacedPayload({
        code: 401,
        message: "{'message': '账号已在其他设备登录', 'error_code': 'SESSION_REPLACED'}",
        data: null,
      }),
    ).toBe(true)
  })

  it('ignores unrelated 401 bodies', () => {
    expect(isSessionReplacedPayload({ detail: '令牌已失效，请重新登录' })).toBe(false)
    expect(isSessionReplacedPayload({ code: 401, message: '无效的刷新令牌' })).toBe(false)
  })

  it('consumes kick flag once', () => {
    markSessionKicked()
    expect(sessionStorage.getItem(SESSION_KICKED_FLAG)).toBe('1')
    expect(consumeSessionKickedMessage()).toBe(SESSION_KICKED_MESSAGE)
    expect(consumeSessionKickedMessage()).toBeNull()
  })
})
