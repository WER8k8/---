const fs = require('fs');
const lines = fs.readFileSync(String.raw`C:\Users\97907\Desktop\上线网站\frontend\admin\src\router\index.ts`, 'utf8').split('\n');
for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes("path: '/admin'") && lines[i].includes('AdminLayout')) {
    for (let j = i; j < Math.min(i + 30, lines.length); j++) {
      console.log((j + 1) + ': ' + lines[j]);
    }
    break;
  }
}