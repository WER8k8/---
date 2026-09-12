#!/usr/bin/env node
/** 合并 batch-wire 产生的重复 vue import */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const viewsDir = path.join(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..'), 'src/views')

function walk(dir, out = []) {
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name)
    if (fs.statSync(p).isDirectory()) walk(p, out)
    else if (name.endsWith('.vue')) out.push(p)
  }
  return out
}

let fixed = 0
for (const file of walk(viewsDir)) {
  let src = fs.readFileSync(file, 'utf8')
  if (!src.includes("import { onMounted } from 'vue'")) continue
  if (!src.match(/import \{[^}]+\} from 'vue'/g)?.length) continue

  src = src.replace(/import \{ onMounted \} from 'vue'\n/, '')
  src = src.replace(/import \{([^}]+)\} from 'vue'/, (m, inner) => {
    const parts = inner.split(',').map((s) => s.trim()).filter(Boolean)
    if (!parts.includes('onMounted')) parts.push('onMounted')
    return `import { ${parts.join(', ')} } from 'vue'`
  })
  fs.writeFileSync(file, src)
  fixed++
}
console.log({ fixed })
