const fs = require('fs');
const lines = fs.readFileSync('C:/Users/97907/Desktop/上线网站/frontend/admin/src/router/index.ts', 'utf8').split('\n');
// Show lines around the fix
for (let i = 1750; i < Math.min(1770, lines.length); i++) {
  console.log((i+1) + ': ' + lines[i]);
}