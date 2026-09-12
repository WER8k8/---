const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'domcontentloaded', timeout: 20000 });
  await page.waitForTimeout(1500);
  const inputs = await page.$$('input');
  if (inputs.length > 0) await inputs[0].fill('tenant_demo');
  const pw = await page.$('input[type="password"]');
  if (pw) await pw.fill('TenantDemo@2026!');
  const btn = await page.$('button[type="submit"], button.ant-btn-primary');
  if (btn) await btn.click();
  await page.waitForTimeout(5000);
  console.log('锛氭槦涓枃*還', page.url());
  await page.goto('http://127.0.0.1:5173/client/onboarding', { waitUntil: 'domcontentloaded', timeout: 25000 });
  await page.waitForTimeout(4000);
  console.log('鏈€缁呈縩l', page.url());
  await page.screenshot({ path: 'C:/Users/97907/Desktop/上线网站/_tenant_onboarding.png', fullPage: true });
  const html = await page.content();
  console.log('onboarding-page:', html.includes('onboarding-page'));
  console.log('onb-step-rail:', html.includes('onb-step-rail'));
  console.log('onb-card:', html.includes('onb-card'));
  await browser.close();
  console.log('瀹屾垚');
})();

