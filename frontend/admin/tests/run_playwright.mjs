import { chromium } from 'playwright';

const url = 'http://127.0.0.1:5173/client/email-campaigns';
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  // 注入一个简单的非过期伪 JWT（仅供前端路由/显示逻辑使用，不用于真实鉴权）
  const fakeJwt = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.' +
    'eyJleHAiOjMwMDAwMDAwMDAsInJvbGVzIjpbInRlbmFudCJdfQ.' +
    'signature';
  await page.addInitScript((token) => {
    try { sessionStorage.setItem('admin_token', token); sessionStorage.setItem('admin_username','tenant'); } catch {}
  }, fakeJwt);
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