const fs = require('fs');
const lines = fs.readFileSync('C:/Users/97907/Desktop/上线网站/frontend/admin/src/router/index.ts', 'utf8').split('\n');
// Show lines 300-340 to see parent route
for (let i = 299; i < Math.min(340, lines.length); i++) {
  console.log((i+1) + ': ' + lines[i]);
}