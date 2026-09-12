const fs = require('fs');
const lines = fs.readFileSync('C:/Users/97907/Desktop/上线网站/frontend/admin/src/router/index.ts', 'utf8').split('\n');
// Show lines 330-345 to see the admin layout route
for (let i = 329; i < Math.min(350, lines.length); i++) {
  console.log((i+1) + ': ' + lines[i]);
}