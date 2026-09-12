const fs = require('fs');
const lines = fs.readFileSync('C:/Users/97907/Desktop/上线网站/frontend/admin/src/router/index.ts', 'utf8').split('\n');
for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes("/admin") && lines[i].includes("AdminLayout")) {
    for (let j = i; j < Math.min(i + 30, lines.length); j++) {
      console.log((j + 1) + ': ' + lines[j]);
    }
    break;
  }
}
// Also search for 'AdminLayout' anywhere
for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes("AdminLayout")) {
    console.log("AdminLayout found at line " + (i+1) + ": " + lines[i].trim());
  }
}