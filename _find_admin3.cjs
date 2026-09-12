const fs = require('fs');
const content = fs.readFileSync('C:/Users/97907/Desktop/上线网站/frontend/admin/src/router/index.ts', 'utf8');
const lines = content.split('\n');
console.log("Total lines:", lines.length);
// Search for admin layout
for (let i = 0; i < lines.length; i++) {
  const line = lines[i].trim();
  if (line.includes('admin') && (line.includes('path') || line.includes('Layout') || line.includes('component'))) {
    console.log((i+1) + ': ' + line);
  }
}