const fs = require('fs');
const lines = fs.readFileSync('C:/Users/97907/Desktop/上线网站/frontend/admin/src/router/index.ts', 'utf8').split('\n');
// Show the client layout route (around line 128-200)
for (let i = 125; i < Math.min(200, lines.length); i++) {
  console.log((i+1) + ': ' + lines[i]);
}