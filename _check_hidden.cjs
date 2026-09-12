const fs = require('fs');
const content = fs.readFileSync('C:/Users/97907/Desktop/上线网站/frontend/admin/src/constants/stubVisibility.ts', 'utf8');
// Search for copilot related entries
const lines = content.split('\n');
for (let i = 0; i < lines.length; i++) {
  if (lines[i].toLowerCase().includes('copilot') || lines[i].toLowerCase().includes('sell-flywheel') || lines[i].toLowerCase().includes('卖货飞轮')) {
    console.log((i+1) + ': ' + lines[i].trim());
  }
}
// Also check isClientPathHidden function
for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes('isClientPathHidden')) {
    console.log((i+1) + ': ' + lines[i].trim());
  }
}