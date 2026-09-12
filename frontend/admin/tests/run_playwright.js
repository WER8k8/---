(async () => {
  const { chromium } = require('playwright');
  const url = 'http://127.0.0.1:5173/client/email-campaigns';
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  try {
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);
    const banner = await page.locator('text=邮件功能受限').first();
    const visible = await banner.isVisible().catch(() => false);
    if (visible) {
      console.log('BANNER: visible');
      await page.screenshot({ path: 'tests/email_campaign_banner.png', fullPage: true });
    } else {
      console.log('BANNER: not visible');
      await page.screenshot({ path: 'tests/email_campaign_no_banner.png', fullPage: true });
    }
    await browser.close();
    process.exit(visible ? 0 : 2);
  } catch (e) {
    console.error('ERROR:', e.message);
    await page.screenshot({ path: 'tests/email_campaign_error.png', fullPage: true }).catch(()=>{});
    await browser.close();
    process.exit(3);
  }
})();