#!/usr/bin/env node
/**
 * 调后端登录 → 往本机管理端域名写入 localStorage → 打开已登录后台（需已运行 backend:8000 与 admin Vite:5173）
 *   node scripts/admin-open-logged-in.mjs
 *   node scripts/admin-open-logged-in.mjs --password=YourPass
 */
import { chromium } from 'playwright'

const API = process.env.ADMIN_API_URL || 'http://127.0.0.1:8000/api/v1/auth/login'
const ORIGIN = process.env.ADMIN_DEV_ORIGIN || 'http://127.0.0.1:5173'
const USER = process.env.ADMIN_USERNAME || 'admin'

let password = process.env.ADMIN_PASSWORD || '123456'
const pwArg = process.argv.find((a) => a.startsWith('--password='))
if (pwArg) password = pwArg.slice('--password='.length)

const res = await fetch(API, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username_or_email: USER, password }),
})
const raw = await res.json().catch(() => ({}))
if (!res.ok) {
  console.error('Login HTTP', res.status, raw)
  process.exit(1)
}
const token =
  raw?.data?.access_token ||
  raw?.access_token ||
  (typeof raw?.data === 'object' && raw.data?.access_token)
if (!token) {
  console.error('No access_token in response:', JSON.stringify(raw).slice(0, 500))
  process.exit(1)
}

let browser
const channel = process.env.PW_CHANNEL || 'msedge'
try {
  browser = await chromium.launch({ headless: false, channel })
} catch (e) {
  console.warn(channel, '不可用，改用 Chromium（首次需 npx playwright install chromium）', e.message)
  browser = await chromium.launch({ headless: false })
}
const context = await browser.newContext({ baseURL: ORIGIN })
const page = await context.newPage()
await page.addInitScript(
  ([t, u]) => {
    localStorage.setItem('admin_token', t)
    localStorage.setItem('admin_username', u)
  },
  [token, USER]
)
await page.goto('/admin', { waitUntil: 'domcontentloaded' })
console.log('已打开', ORIGIN + '/admin')
console.log('按 Ctrl+C 可结束本脚本（会关闭本次打开的浏览器窗口）。')
await new Promise(() => {})
