#!/usr/bin/env node
/**
 * MOD-04 · 七步录屏路由静态彩排截图（vite preview，无需 HTTPS）
 * Usage: cd frontend/admin && node scripts/mod-04-rehearsal-screenshots.mjs
 */
import { chromium } from 'playwright'
import { mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '../../..')
const OUT = path.join(ROOT, 'docs', 'compliance', 'mod-04-recordings', 'rehearsal')
const ORIGIN = process.env.MOD04_BASE_URL || 'http://127.0.0.1:4173'

const shots = [
  { file: 'mod04-01-login.png', path: '/login' },
  { file: 'mod04-02-pillars.png', path: '/client/dashboard' },
  { file: 'mod04-03-inquiry-queue.png', path: '/client/queues/inquiries' },
  { file: 'mod04-04-plan-gate.png', path: '/client/plan-gate' },
  { file: 'mod04-05-platform.png', path: '/admin/tenants' },
  { file: 'mod04-06-agent.png', path: '/agent/performance' },
]

await mkdir(OUT, { recursive: true })

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
  const file = path.join(OUT, s.file)
  try {
    await page.goto(s.path, { waitUntil: 'domcontentloaded', timeout: 25000 })
    await page.waitForTimeout(1200)
    await page.screenshot({ path: file, fullPage: false })
    results.push({ path: s.path, file: s.file, ok: true })
  } catch (e) {
    results.push({ path: s.path, file: s.file, ok: false, error: String(e.message || e) })
  }
}

await browser.close()

const report = {
  ok: results.every((r) => r.ok),
  task: 'MOD-04-rehearsal-screenshots',
  base_url: ORIGIN,
  output_dir: path.relative(ROOT, OUT).replace(/\\/g, '/'),
  shots: results,
  human_pending: 'HTTPS 域就绪后替换为正式录屏 mp4',
}
await writeFile(path.join(ROOT, 'docs/mod-04-rehearsal-screenshots-latest.json'), JSON.stringify(report, null, 2))
console.log(JSON.stringify(report, null, 2))
process.exit(report.ok ? 0 : 1)
