const fs = require('fs');
const lines = fs.readFileSync('C:/Users/97907/Desktop/上线网站/frontend/admin/src/router/index.ts', 'utf8').split('\n');
// Show lines 1756-1780 (the tenant_admin guard)
for (let i = 1755; i < Math.min(1785, lines.length); i++) {
  console.log((i+1) + ': ' + lines[i]);
}