import { test, expect } from '@playwright/test';

test('email campaigns page shows tenant-restricted banner when backend unavailable', async ({ page }) => {
  await page.goto('http://127.0.0.1:5173/client/email-campaigns', { waitUntil: 'networkidle' });
  // wait a short while for client JS to run and API probes to fail
  await page.waitForTimeout(3000);
  // Look for alert text
  const banner = await page.locator('text=邮件功能受限').first();
  const visible = await banner.isVisible().catch(() => false);
  if (visible) {
    await page.screenshot({ path: 'tests/email_campaign_banner.png', fullPage: true });
  } else {
    await page.screenshot({ path: 'tests/email_campaign_no_banner.png', fullPage: true });
  }
  expect(visible).toBeTruthy();
});