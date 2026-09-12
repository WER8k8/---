#!/usr/bin/env node
/**
 * 清零 interactive-stubs：去掉硬编码 ref([{...}]) 种子，合并重复 onMounted
 */
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
  'admin/v2ray/routing.vue',
  'admin/v2ray/servers.vue',
  'agent-hub/dashboard.vue',
  'cognitive/dashboard.vue',
  'developer/dashboard.vue',
  'edge-cdn/dashboard.vue',
  'globalization/dashboard.vue',
  'international/inquiries.vue',
  'seo/performance.vue',
]

/** 单行 const x = ref([{...}]) 或 const x=ref([{...}]) */
const SEED_LINE = /const\s+(\w+)\s*=\s*ref\(\[\{[^\]]+\]\)/g

function stripBatchWireHook(src) {
  return src.replace(
    /\nimport \{ apiGet \} from '@\/utils\/api'\n\nonMounted\(async \(\) => \{\n {2}try \{ await apiGet\('[^']+'\) \} catch \{ \/\* 空状态 \*\/ \}\n\}\)\n/g,
    '',
  )
}

function mergeApiGetImport(src) {
  if (!src.includes("from '@/utils/api'") && src.includes('apiGet(')) {
    src = src.replace(
      /(<script setup lang="ts">\n)/,
      "$1import { apiGet } from '@/utils/api'\n",
    )
  }
  return src
}

function clearSeeds(src) {
  let n = 0
  const out = src.replace(SEED_LINE, (_, name) => {
    n++
    return `const ${name} = ref<any[]>([])`
  })
  return { src: out, n }
}

let files = 0
let seeds = 0
for (const rel of TARGETS) {
  const file = path.join(viewsDir, rel)
  if (!fs.existsSync(file)) continue
  let src = fs.readFileSync(file, 'utf8')
  src = stripBatchWireHook(src)
  const { src: cleared, n } = clearSeeds(src)
  src = mergeApiGetImport(cleared)
  if (n > 0 || stripBatchWireHook) {
    fs.writeFileSync(file, src)
    files++
    seeds += n
  }
}
console.log(JSON.stringify({ files, seedsCleared: seeds }))
