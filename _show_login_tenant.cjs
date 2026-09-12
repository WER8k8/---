const fs = require('fs');
const content = fs.readFileSync('C:/Users/97907/Desktop/上线网站/frontend/admin/src/views/login/index.vue', 'utf8');
const lines = content.split('\n');
// Show lines 225-245 to see tenant login intent logic
for (let i = 224; i < Math.min(245, lines.length); i++) {
  console.log((i+1) + ': ' + lines[i]);
}