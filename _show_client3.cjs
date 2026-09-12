const fs = require('fs');
const lines = fs.readFileSync('C:/Users/97907/Desktop/上线网站/frontend/admin/src/router/index.ts', 'utf8').split('\n');
// Show lines 75-92 to see /client route start
for (let i = 74; i < Math.min(95, lines.length); i++) {
  console.log((i+1) + ': ' + lines[i]);
}