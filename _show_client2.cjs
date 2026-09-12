const fs = require('fs');
const lines = fs.readFileSync('C:/Users/97907/Desktop/上线网站/frontend/admin/src/router/index.ts', 'utf8').split('\n');
// Show lines 90-130 to see client layout start
for (let i = 88; i < Math.min(130, lines.length); i++) {
  console.log((i+1) + ': ' + lines[i]);
}