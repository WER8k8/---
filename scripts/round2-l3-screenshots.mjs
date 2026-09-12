#!/usr/bin/env node
/**
 * 第二轮 L3 截图（headless）
 * 需 backend :8001 + admin :5173
 *   node scripts/round2-l3-screenshots.mjs
 */
import { chromium } from 'playwright'
import { mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
const OUT = path.join(ROOT, 'docs', '出海计', 'screenshots', 'round2')
const API = process.env.ADMIN_API_URL || 'http://127.0.0.1:8001/api/v1/auth/login'
const ORIGIN = process.env.ADMIN_DEV_ORIGIN || 'http://127.0.0.1:5173'
const USER = process.env.ADMIN_USERNAME || 'admin'
const PASS = process.env.ADMIN_PASSWORD || 'admin123'

const shots = [
  { name: '01-login', path: '/login', auth: false },
  { name: '02-inquiries', path: '/inquiries', auth: true },
  { name: '03-publish-unified', path: '/publish/unified', auth: true },
  { name: '04-copilot', path: '/client/copilot', auth: true },
  { name: '05-founder-diagnostics', path: '/admin/founder-diagnostics', auth: true },
  { name: '06-inquiries-export', path: '/inquiries', auth: true, note: 'export-ui' },
]

async function loginToken() {
  const res = await fetch(API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username_or_email: USER, password: PASS }),
  })
  const raw = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(`Login HTTP ${res.status}: ${JSON.stringify(raw).slice(0, 300)}`)
  const token = raw?.data?.access_token || raw?.access_token
  if (!token) throw new Error('No access_token')
  return token
}

await mkdir(OUT, { recursive: true })
const token = await loginToken()

let browser
try {
  browser = await chromium.launch({ headless: true, channel: 'msedge' })
} catch {
  browser = await chromium.launch({ headless: true })
}

const context = await browser.newContext({ baseURL: ORIGIN, viewport: { width: 1440, height: 900 } })
const page = await context.newPage()
const results = []

for (const s of shots) {
  const file = path.join(OUT, `${s.name}.png`)
  try {
    if (s.auth) {
      await page.addInitScript(
        ([t, u]) => {
          localStorage.setItem('admin_token', t)
          localStorage.setItem('admin_username', u)
        },
        [token, USER]
      )
    }
    await page.goto(s.path, { waitUntil: 'networkidle', timeout: 60000 })
    await page.waitForTimeout(1500)
    await page.screenshot({ path: file, fullPage: false })
    results.push({ name: s.name, ok: true, file: path.relative(ROOT, file) })
    console.log('OK', s.name)
  } catch (e) {
    results.push({ name: s.name, ok: false, error: String(e.message || e) })
    console.error('FAIL', s.name, e.message || e)
  }
}

await browser.close()
const manifest = { generated_at: new Date().toISOString(), origin: ORIGIN, api: API, results }
await writeFile(path.join(OUT, 'manifest.json'), JSON.stringify(manifest, null, 2))
const allOk = results.every((r) => r.ok)
process.exit(allOk ? 0 : 1)
