const fs = require('fs');
const content = fs.readFileSync('C:/Users/97907/Desktop/上线网站/frontend/admin/src/views/login/index.vue', 'utf8');
// Search for tenant-related UI logic
const lines = content.split('\n');
for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes('tenantLoginIntent') || lines[i].includes('TENANT') || lines[i].includes('tenant_demo') || lines[i].includes('租户演示')) {
    console.log((i+1) + ': ' + lines[i].trim());
  }
}