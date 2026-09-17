/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { describe, expect, it } from 'vitest'
import { buildPlatformAccountBody } from '@/api'

/**
 * PC-01 回归锁：旧版 createPlatformAccount / updatePlatformAccount 只发 5 个字段，
 * 把 cookie 与 token 整个丢掉，导致凭证面板填了也存不下来。
 */
describe('buildPlatformAccountBody', () => {
  it('透传 cookie_data / token_data / configs', () => {
    const body = buildPlatformAccountBody({
      platform_id: 'p1',
      account_name: 'alibaba-main',
      cookie_data: 'sess=abc',
      token_data: { alibaba_access_token: 't' },
      configs: { nurture_daily_posts: '3' },
    })
    expect(body.cookie_data).toBe('sess=abc')
    expect(body.token_data).toEqual({ alibaba_access_token: 't' })
    expect(body.configs).toEqual({ nurture_daily_posts: '3' })
  })

  it('保留指引登记的平铺凭证字段', () => {
    const body = buildPlatformAccountBody({
      platform: 'p2',
      name: 'mic',
      mic_access_token: 'tok-1',
      alibaba_member_id: 'member-1',
    })
    expect(body.platform_id).toBe('p2')
    expect(body.account_name).toBe('mic')
    expect(body.mic_access_token).toBe('tok-1')
    expect(body.alibaba_member_id).toBe('member-1')
  })

  it('不把前端 alias 与空值发给后端', () => {
    const body = buildPlatformAccountBody({
      id: 'a1',
      platform_id: 'p3',
      account_name: 'zhihu',
      tenant_id: 't9',
      cookie_data: '',
      token_data: null,
    })
    expect(body).not.toHaveProperty('id')
    expect(body).not.toHaveProperty('platform')
    expect(body).not.toHaveProperty('name')
    // 展示字段与后端不认的键不转发，空凭证也不覆盖原值
    expect(body).not.toHaveProperty('tenant_id')
    expect(body).not.toHaveProperty('cookie_data')
    expect(body).not.toHaveProperty('token_data')
    expect(body.platform_id).toBe('p3')
    expect(body.account_name).toBe('zhihu')
  })

  it('login_status 可透传（重绑后改回 logged_in 要用）', () => {
    const body = buildPlatformAccountBody({ platform_id: 'p4', login_status: 'logged_in' })
    expect(body.login_status).toBe('logged_in')
  })
})
