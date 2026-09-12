import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const adminRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const prodRoot = 'C:/Users/97907/Desktop/上线网站/frontend/admin/src'

const roots = [
  path.join(adminRoot, 'src'),
  prodRoot,
].filter((r) => fs.existsSync(r))

const bad = []

function walk(dir) {
  for (const name of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, name.name)
    if (name.isDirectory()) walk(p)
    else if (name.name.endsWith('.vue')) {
      const t = fs.readFileSync(p, 'utf8')
      if (
        t.includes('\uFFFD')
        || /tab="[^"]*\?\s*\/>/.test(t)
        || /tab='[^']*\?\s*\/>/.test(t)
      ) {
        bad.push(p.replace(/\\/g, '/'))
      }
    }
  }
}

for (const root of roots) {
  console.log('---', root)
  walk(root)
}
console.log(JSON.stringify({ corrupt: bad.length, files: bad }, null, 2))
process.exit(bad.length > 0 ? 1 : 0)
