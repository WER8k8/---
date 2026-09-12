const fs = require('fs');
const lines = fs.readFileSync('C:/Users/97907/Desktop/上线网站/frontend/admin/src/router/index.ts', 'utf8').split('\n');
// Show lines 220-300 to see the top-level wrapper route
for (let i = 219; i < Math.min(300, lines.length); i++) {
  console.log((i+1) + ': ' + lines[i]);
}