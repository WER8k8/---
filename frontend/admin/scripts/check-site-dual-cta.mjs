#!/usr/bin/env node
/**
 * P2-11 · 生成站双 CTA + 24h 承诺抽检
 * Usage: node scripts/check-site-dual-cta.mjs [path/to/site_content.json]
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const adminRoot = path.resolve(__dirname, '..')
const repoRoot = path.resolve(adminRoot, '../..')
const defaultFixture = path.join(
  repoRoot,
  'backend/tests/fixtures/site_content_ecc_sample.json',
)

const MARKERS_24H = ['24 hour', '24 hours', '24h', 'within 24', '24 小时', '24小时内']

function audit(site) {
  const issues = []
  const home = site?.pages?.home || {}
  const contact = site?.pages?.contact || {}
  for (const key of ['ctaPrimary', 'ctaSecondary', 'inquiryHook']) {
    if (!String(home[key] || '').trim()) issues.push(`home.${key} 缺失`)
  }
  const p = String(home.ctaPrimary || '').trim()
  const s = String(home.ctaSecondary || '').trim()
  if (p && s && p.toLowerCase() === s.toLowerCase()) {
    issues.push('home.ctaPrimary 与 ctaSecondary 不应相同')
  }
  const blob = [
    home.inquiryHook,
    contact.inquiryPrompt,
    String(home.description || '').slice(0, 400),
  ]
    .join(' ')
    .toLowerCase()
  if (!MARKERS_24H.some((m) => blob.includes(m))) {
    issues.push('缺少 24h 回复承诺')
  }
  return { ok: issues.length === 0, issues }
}

function loadJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'))
}

function buildSampleFromPipeline() {
  return {
    pages: {
      home: {
        ctaPrimary: 'Request Quotation',
        ctaSecondary: 'WhatsApp Us',
        inquiryHook:
          'Share your project specs — our export team replies within 24 hours with datasheet.',
        description: 'Manufacturer',
      },
      contact: { inquiryPrompt: 'Free sample available; reply within 24 hours.' },
    },
  }
}

const argPath = process.argv[2]
const samples = []

if (argPath && fs.existsSync(argPath)) {
  samples.push({ label: argPath, site: loadJson(argPath) })
} else if (fs.existsSync(defaultFixture)) {
  samples.push({ label: defaultFixture, site: loadJson(defaultFixture) })
}
samples.push({ label: 'pipeline-default', site: buildSampleFromPipeline() })

const results = samples.map(({ label, site }) => ({ label, ...audit(site) }))
const ok = results.every((r) => r.ok)

console.log(
  JSON.stringify(
    {
      ok,
      spec: 'western-inquiry-conversion',
      checked: results.length,
      results,
    },
    null,
    2,
  ),
)
process.exit(ok ? 0 : 1)
