#!/usr/bin/env node
/**
 * S0-12 / UX-08 · 送检 12 截图自动采集
 *
 * 用法:
 *   node scripts/capture-cert-screenshots.mjs
 *   node scripts/capture-cert-screenshots.mjs --base http://127.0.0.1:5173 --api http://127.0.0.1:8001
 *
 * 环境变量: QA_ADMIN_USER / QA_ADMIN_PASSWORD（默认 admin / admin123）
 * 输出: docs/cert-screenshots/cert-*.png
 */
import { spawnSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const adminRoot = path.resolve(__dirname, '..')
const repoRoot = path.resolve(adminRoot, '../..')
const outDir = path.join(repoRoot, 'docs', 'cert-screenshots')

const args = process.argv.slice(2)
function arg(name, fallback) {
  const i = args.indexOf(name)
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback
}

const BASE = arg('--base', 'http://127.0.0.1:5173')
const API = arg('--api', 'http://127.0.0.1:8001')
const USER = process.env.QA_ADMIN_USER || 'admin'
const PASS = process.env.QA_ADMIN_PASSWORD || 'admin123'

/** 鉴定面 12 项 — 对齐 cert-screenshots-checklist.md */
const SHOTS = [
  { file: 'cert-01-login.png', path: '/login', auth: false },
  { file: 'cert-02-tenants.png', path: '/admin/tenants', auth: true },
  { file: 'cert-03-hierarchy.png', path: '/admin/hierarchy', auth: true },
  { file: 'cert-04-aggregation.png', path: '/admin/aggregation', auth: true },
  { file: 'cert-05-health.png', path: '/system-health/dashboard', auth: true },
  { file: 'cert-06-finance.png', path: '/admin/finance', auth: true },
  { file: 'cert-07-products.png', path: '/products', auth: true },
  { file: 'cert-08-categories.png', path: '/products/categories', auth: true },
  { file: 'cert-09-inquiries.png', path: '/international/inquiries', auth: true },
  { file: 'cert-10-seo.png', path: '/seo-matrix/publish', auth: true },
  { file: 'cert-11-ai-content.png', path: '/admin/ai-center/content', auth: true },
  { file: 'cert-12-trade-intel.png', path: '/admin/ai-engine/trade-intel', auth: true },
]

/** 三壳对比（UX-07 附加） */
const SHELL_SHOTS = [
  { file: 'ux-07-client-dashboard.png', path: '/client/dashboard', auth: true, user: 'editor', pass: 'editor123' },
  { file: 'ux-07-agent-performance.png', path: '/agent/performance', auth: true, user: 'sales', pass: 'sales123' },
  { file: 'ux-07-platform-dashboard.png', path: '/admin/dashboard', auth: true, user: USER, pass: PASS },
]

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

function ensurePlaywright() {
  const check = spawnSync('npx', ['playwright', '--version'], { shell: true, encoding: 'utf8' })
  if (check.status !== 0) {
    console.error('Playwright 未安装，正在 install chromium …')
    spawnSync('npx', ['playwright', 'install', 'chromium'], { shell: true, stdio: 'inherit' })
  }
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true })
  ensurePlaywright()

  const { chromium } = await import('playwright')

  let ok = 0
  let fail = 0

  async function capture(entry) {
    const browser = await chromium.launch({ headless: true })
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } })
    const page = await context.newPage()

    try {
      if (entry.auth) {
        const u = entry.user || USER
        const p = entry.pass || PASS
        const token = await apiLogin(u, p)
        if (!token) {
          console.log(`[SKIP] ${entry.file} — login failed (${u})`)
          fail++
          return
        }
        await page.goto(`${BASE}/login`, { waitUntil: 'domcontentloaded', timeout: 30000 })
        await page.evaluate((tok) => {
          localStorage.setItem('admin_token', tok)
          localStorage.setItem('admin_username', 'qa-screenshot')
        }, token)
      }

      const url = `${BASE}${entry.path}`
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 })
      await page.waitForTimeout(1500)
      const outPath = path.join(outDir, entry.file)
      await page.screenshot({ path: outPath, fullPage: false })
      console.log(`[OK] ${entry.file}`)
      ok++
    } catch (e) {
      console.log(`[FAIL] ${entry.file}: ${e.message}`)
      fail++
    } finally {
      await browser.close()
    }
  }

  for (const s of SHOTS) await capture(s)
  for (const s of SHELL_SHOTS) await capture(s)

  const manifest = {
    capturedAt: new Date().toISOString(),
    base: BASE,
    api: API,
    ok,
    fail,
    files: fs.readdirSync(outDir).filter((f) => f.endsWith('.png')),
  }
  fs.writeFileSync(path.join(outDir, 'manifest.json'), JSON.stringify(manifest, null, 2))
  console.log(`\nDone: ${ok} ok, ${fail} fail → ${outDir}`)
  process.exit(fail > 0 ? 1 : 0)
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
