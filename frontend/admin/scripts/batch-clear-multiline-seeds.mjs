#!/usr/bin/env node
/** 清零 multiline ref([{...}]) 种子数组 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const viewsDir = path.join(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..'), 'src/views')

const TARGETS = [
  'admin/ai-center/usage.vue',
  'admin/ai-engine/templates.vue',
  'admin/ai-engine/token.vue',
  'admin/code-tools/overview.vue',
  'admin/projects/overview.vue',
  'admin/runtime/overview.vue',
  'admin/scheduler/overview.vue',
  'admin/security/overview.vue',
  'admin/system/overview.vue',
  'admin/system/permissions.vue',
  'agent-hub/dashboard.vue',
  'edge-cdn/dashboard.vue',
  'globalization/dashboard.vue',
  'international/inquiries.vue',
  'seo/performance.vue',
]

/** const x = ref([ ... ]) 含换行 */
const MULTI_SEED = /const\s+(\w+)\s*=\s*ref\(\[\s*[\s\S]*?\]\)/g

let total = 0
for (const rel of TARGETS) {
  const file = path.join(viewsDir, rel)
  if (!fs.existsSync(file)) continue
  let src = fs.readFileSync(file, 'utf8')
  let n = 0
  src = src.replace(MULTI_SEED, (_, name) => {
    n++
    return `const ${name} = ref<any[]>([])`
  })
  if (n) {
    fs.writeFileSync(file, src)
    total += n
    console.log(rel, n)
  }
}
console.log(JSON.stringify({ arraysCleared: total }))
