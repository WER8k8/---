const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  
  await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(1000);
  
  const inputs = await page.$$('input');
  if (inputs.length > 0) await inputs[0].fill('admin');
  const pw = await page.$('input[type="password"]');
  if (pw) await pw.fill('admin123');
  const btn = await page.$('button[type="submit"], button.ant-btn-primary');
  if (btn) await btn.click();
  await page.waitForTimeout(3000);
  
  await page.goto('http://127.0.0.1:5173/client/onboarding', { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(2000);
  
  await page.screenshot({ path: 'C:/Users/97907/Desktop/上线网站/_onb_preview.png', fullPage: true });
  console.log('Screenshot saved');
  
  await browser.close();
})();
