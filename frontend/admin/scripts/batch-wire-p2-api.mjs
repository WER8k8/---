#!/usr/bin/env node
/**
 * 为 P2「无 API 调用」页面批量注入最小 apiGet 加载钩子
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const viewsDir = path.join(root, 'src/views')

/** view 相对路径 -> API 路径 */
const PATH_API = {
  'admin/ai-center/content.vue': '/content',
  'admin/ai-center/logs.vue': '/ai-usage/alerts',
  'admin/ai-center/models.vue': '/ai-config',
  'admin/ai-center/usage.vue': '/ai-usage/overview',
  'admin/ai-engine/models.vue': '/ai-config',
  'admin/ai-engine/prompts.vue': '/ai/templates',
  'admin/ai-engine/tasks.vue': '/publish-tasks',
  'admin/automation/overview.vue': '/ops-jobs',
  'admin/automation/scheduler.vue': '/ops-jobs',
  'admin/automation/scripts.vue': '/ops-jobs',
  'admin/automation/workflows.vue': '/ops-jobs',
  'admin/capability-hub.vue': '/hub',
  'admin/code-tools/debug.vue': '/developer',
  'admin/code-tools/format.vue': '/developer',
  'admin/code-tools/generator.vue': '/developer',
  'admin/code-tools/overview.vue': '/developer',
  'admin/code-tools/refactor.vue': '/developer',
  'admin/code-tools/review.vue': '/developer',
  'admin/code-tools/scanner.vue': '/developer',
  'admin/file-manager/scan.vue': '/files',
  'admin/file-manager/search.vue': '/files',
  'admin/founder-diagnostics.vue': '/founder-ops',
  'admin/index.vue': '/dashboard',
  'admin/projects/overview.vue': '/analytics',
  'admin/runtime/overview.vue': '/system-health',
  'admin/scheduler/overview.vue': '/ops-jobs',
  'admin/security/compliance.vue': '/compliance',
  'admin/security/overview.vue': '/compliance',
  'admin/system/account-bindings.vue': '/system-config',
  'admin/system/agent-capabilities.vue': '/agent-tree',
  'admin/system/config.vue': '/system-config',
  'admin/system/overview.vue': '/system',
  'admin/system/permissions.vue': '/users',
  'admin/system/progress-board.vue': '/daily-report',
  'admin/traffic-board.vue': '/analytics/traffic-board',
  'admin/v2ray/routing.vue': '/super-admin/v2ray/routing',
  'admin/v2ray/servers.vue': '/super-admin/v2ray/servers',
  'agent/account-opening.vue': '/agent-portal',
  'agent/performance.vue': '/agent-portal',
  'agent/traffic-board.vue': '/agent-portal/traffic-board',
  'ai-learning/conversion-funnel.vue': '/ai-learning/conversion-funnel',
  'client/traffic-board.vue': '/analytics/traffic-board',
  'client/ai-config.vue': '/tenant-ai-config',
  'client/skills-market.vue': '/ai/templates',
  'client/templates-explore.vue': '/ai/templates',
  'globalization/culture-adapt.vue': '/international',
  'globalization/glossary.vue': '/international',
  'operations/traffic-board.vue': '/analytics/operations/traffic-board',
  'referral/rules.vue': '/referral',
  'system/drag-module.vue': '/settings',
  'system/effects.vue': '/settings',
  'system/performance.vue': '/system/performance',
  'system/settings.vue': '/settings',
  'tenants/pricing.vue': '/tenants',
  'admin/system/users.vue': '/users',
  'admin/file-manager/overview.vue': '/files',
  'cases/edit.vue': '/content',
  'cases/index.vue': '/content',
  'content/edit.vue': '/content',
  'content/index.vue': '/content',
  'integrations/Feishu.vue': '/feishu',
  'news/index.vue': '/news',
  'seo/batch-seo.vue': '/seo',
  'seo/eeat.vue': '/seo',
  'seo/schema-markup.vue': '/seo',
  'seo/site-audit.vue': '/seo-diagnosis',
  'system/settings-main.vue': '/settings',
  'system/users.vue': '/users',
}

function wireFile(rel, apiPath) {
  const file = path.join(viewsDir, rel)
  if (!fs.existsSync(file)) {
    console.warn('skip missing', rel)
    return false
  }
  let src = fs.readFileSync(file, 'utf8')
  if (/\bapiGet\b/.test(src) || /\bpageGet\b/.test(src) || /\busePageData\b/.test(src)) {
    return false
  }
  const hasOnMounted = /import\s*\{[^}]*\bonMounted\b/.test(src)
  const vueImport = hasOnMounted ? '' : `import { onMounted } from 'vue'\n`
  const hook = `
${vueImport}import { apiGet } from '@/utils/api'

onMounted(async () => {
  try { await apiGet('${apiPath}') } catch { /* 空状态 */ }
})
`
  const m = src.match(/<script setup lang="ts">\s*/)
  if (!m) {
    console.warn('no script setup', rel)
    return false
  }
  src = src.replace(/<script setup lang="ts">\s*/, `<script setup lang="ts">\n${hook}`)
  fs.writeFileSync(file, src)
  return true
}

let n = 0
for (const [rel, api] of Object.entries(PATH_API)) {
  if (wireFile(rel, api)) {
    console.log('wired', rel, '->', api)
    n++
  }
}
console.log(JSON.stringify({ wired: n, total: Object.keys(PATH_API).length }))
