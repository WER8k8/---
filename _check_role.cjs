const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222").catch(() => null);
  if (!browser) { console.log("Cannot connect to browser CDP"); return; }
  const contexts = browser.contexts();
  for (const ctx of contexts) {
    for (const page of ctx.pages()) {
      const url = page.url();
      if (url.includes("5173")) {
        console.log("Page URL:", url);
        const role = await page.evaluate(() => {
          const store = JSON.parse(sessionStorage.getItem("admin_token") || "null");
          return { token: store ? "exists" : "null", currentUrl: window.location.href };
        });
        console.log("Token:", role.token);
        console.log("Full URL:", role.currentUrl);
        // Check if there's admin sidebar content
        const hasAdminMenu = await page.evaluate(() => {
          const el = document.querySelector(".admin-layout, .ant-layout-sider, [data-layout=admin]");
          return el ? "yes" : "no";
        });
        console.log("Has admin layout:", hasAdminMenu);
        // Check page title/heading
        const heading = await page.evaluate(() => {
          const h = document.querySelector("h1, h2, .page-title, .ant-page-header-heading-title");
          return h ? h.textContent.trim() : "none";
        });
        console.log("Heading:", heading);
      }
    }
  }
  await browser.close();
})();
