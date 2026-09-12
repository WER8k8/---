#!/usr/bin/env node
/**
 * W6 · 90 秒送检路径截图 — LOCKED §10 七步
 * Usage:
 *   npm run build && npm run preview &
 *   node scripts/capture-90s-rehearsal.mjs --base http://127.0.0.1:4173
 */
import { spawnSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const adminRoot = path.resolve(__dirname, '..')
const repoRoot = path.resolve(adminRoot, '../..')
const outDir = path.join(repoRoot, 'docs', 'compliance', '90s-rehearsal')

const args = process.argv.slice(2)
function arg(name, fallback) {
  const i = args.indexOf(name)
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback
}

const BASE = arg('--base', 'http://127.0.0.1:4173')
const API = arg('--api', 'http://127.0.0.1:8001')
const USER = process.env.QA_ADMIN_USER || 'admin'
const PASS = process.env.QA_ADMIN_PASSWORD || 'admin123'

const SHOTS = [
  { file: '90s-01-login-brand-hero.png', path: '/login', auth: false, note: '0–15s' },
  { file: '90s-02-dashboard-kpi.png', path: '/admin/dashboard', auth: true, note: '15–30s' },
  { file: '90s-03-tenants-table.png', path: '/admin/tenants', auth: true, note: '30–50s' },
  { file: '90s-04-inquiries-table.png', path: '/inquiries', auth: true, note: '30–50s' },
  { file: '90s-05-theme-dark.png', path: '/admin/dashboard', auth: true, themeDark: true, note: '50–70s' },
  { file: '90s-06-client-shell.png', path: '/client/dashboard', auth: true, user: 'editor', pass: 'editor123', note: '70–90s' },
  { file: '90s-07-agent-shell.png', path: '/agent/performance', auth: true, user: 'sales', pass: 'sales123', note: '70–90s' },
]

function ensurePlaywright() {
  const check = spawnSync('npx', ['playwright', '--version'], { shell: true, encoding: 'utf8' })
  if (check.status !== 0) {
    spawnSync('npx', ['playwright', 'install', 'chromium'], { shell: true, stdio: 'inherit' })
  }
}

async function apiLogin(username, password) {
  const res = await fetch(`${API}/api/v1/admin-bff/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  const body = await res.json()
  if (body.code !== 0) return null
  return body.data?.accessToken || null
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true })
  ensurePlaywright()
  const { chromium } = await import('playwright')

  const results = []
  for (const s of SHOTS) {
    const browser = await chromium.launch({ headless: true })
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } })
    const page = await context.newPage()
    const outPath = path.join(outDir, s.file)
    try {
      if (s.auth) {
        const u = s.user || USER
        const p = s.pass || PASS
        const token = await apiLogin(u, p)
        if (!token) throw new Error(`login failed (${u})`)
        await page.goto(`${BASE}/login`, { waitUntil: 'domcontentloaded', timeout: 30000 })
        await page.evaluate((tok) => {
          localStorage.setItem('admin_token', tok)
          localStorage.setItem('admin_username', 'qa-rehearsal')
          localStorage.setItem('admin_cert_mode', '1')
        }, token)
      }
      if (s.themeDark) {
        await page.goto(`${BASE}${s.path}`, { waitUntil: 'domcontentloaded', timeout: 60000 })
        await page.evaluate(() => {
          const raw = localStorage.getItem('uj-ui-preferences-v1')
          const prefs = raw ? JSON.parse(raw) : {}
          prefs.theme = 'dark'
          prefs.accentRole = 'platform'
          prefs.primaryColor = prefs.primaryColor || '#7c3aed'
          localStorage.setItem('uj-ui-preferences-v1', JSON.stringify(prefs))
          document.documentElement.dataset.ujTheme = 'dark'
        })
        await page.reload({ waitUntil: 'domcontentloaded' })
        const themeBtn = page.locator('button[title="主题与布局"]')
        if (await themeBtn.count()) await themeBtn.click()
        await page.waitForTimeout(800)
      } else {
        await page.goto(`${BASE}${s.path}`, { waitUntil: 'domcontentloaded', timeout: 60000 })
        await page.waitForTimeout(1200)
      }
      await page.screenshot({ path: outPath, fullPage: false })
      results.push({ ...s, ok: true, file: s.file })
      console.log(`[OK] ${s.note} ${s.file}`)
    } catch (e) {
      results.push({ ...s, ok: false, error: String(e.message || e) })
      console.log(`[FAIL] ${s.file}: ${e.message}`)
    } finally {
      await browser.close()
    }
  }

  const report = {
    capturedAt: new Date().toISOString(),
    base: BASE,
    ok: results.every((r) => r.ok),
    output_dir: path.relative(repoRoot, outDir).replace(/\\/g, '/'),
    shots: results,
    human_pending: '正式送检可替换为 mp4 录屏；需 HTTPS 域与真实账号',
  }
  fs.writeFileSync(path.join(repoRoot, 'docs/90s-rehearsal-screenshots-latest.json'), JSON.stringify(report, null, 2))
  console.log(JSON.stringify({ ok: report.ok, dir: report.output_dir }, null, 2))
  process.exit(report.ok ? 0 : 1)
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
