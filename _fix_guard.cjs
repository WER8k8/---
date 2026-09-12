const fs = require('fs');
const filePath = 'C:/Users/97907/Desktop/上线网站/frontend/admin/src/router/index.ts';
let content = fs.readFileSync(filePath, 'utf8');

// Fix: tenant_admin accessing /admin should redirect to /client/today WITHOUT logging out
// Change the block that does auth.logout() on /admin to just redirect silently

const oldCode = `      if (loc.startsWith('/admin')) {
        auth.logout();
        next({
          path: LOGIN_PATH,
          query: { redirect: to.fullPath },
          replace: true,
        });
        return;
      }`;

const newCode = `      if (loc.startsWith('/admin')) {
        next({ path: '/client/today', replace: true });
        return;
      }`;

if (content.includes(oldCode)) {
  content = content.replace(oldCode, newCode);
  fs.writeFileSync(filePath, content, 'utf8');
  console.log('FIXED: tenant_admin /admin redirect no longer logs out');
} else {
  console.log('ERROR: Could not find the exact code block to replace');
  // Show surrounding context
  const idx = content.indexOf("if (loc.startsWith('/admin'))");
  if (idx > -1) {
    console.log('Found at index:', idx);
    console.log('Context:', content.substring(idx - 50, idx + 300));
  }
}