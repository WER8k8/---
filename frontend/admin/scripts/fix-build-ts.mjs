/**
 * 批量修复常见 vue-tsc 构建错误
 */
import { readFileSync, writeFileSync, readdirSync, statSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..', 'src')

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name)
    if (statSync(p).isDirectory()) walk(p, out)
    else if (p.endsWith('.vue') || p.endsWith('.ts')) out.push(p)
  }
  return out
}

let changed = 0

for (const file of walk(root)) {
  let src = readFileSync(file, 'utf8')
  const orig = src

  // value-style="color:#hex" -> :value-style="{ color: '#hex' }"
  src = src.replace(
    /value-style="color:([^"]+)"/g,
    (_, color) => `:value-style="{ color: '${color}' }"`
  )

  // fixed: 'right' in column defs -> fixed: 'right' as const (inside script)
  if (file.endsWith('.vue') && src.includes("fixed: 'right'")) {
    src = src.replace(/fixed: 'right'/g, "fixed: 'right' as const")
    src = src.replace(/fixed: 'left'/g, "fixed: 'left' as const")
  }

  // apiGet(url, { params }) -> apiGet(url, params)
  if (file.endsWith('.ts')) {
    src = src.replace(/apiGet\(([^,]+),\s*\{\s*params\s*\}\)/g, 'apiGet($1, params as any)')
  }

  if (src !== orig) {
    writeFileSync(file, src, 'utf8')
    changed++
    console.log('fixed:', file.replace(root, ''))
  }
}

console.log(`\nDone. ${changed} files updated.`)
