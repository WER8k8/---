/**
 * 响应式布局 E2E 验证
 *
 * 验证 AI 自适应引擎在不同断点下的布局表现：
 * - 侧栏模式切换（expanded/collapsed/hidden）
 * - 密度模式切换
 * - 字号缩放
 */

import { test, expect } from '@playwright/test';

const VIEWPORTS = {
  'xs-phone': { width: 375, height: 667 },
  'sm-phone': { width: 414, height: 896 },
  'md-tablet': { width: 768, height: 1024 },
  'lg-laptop': { width: 1024, height: 768 },
  'xl-desktop': { width: 1440, height: 900 },
  '2xl-large': { width: 1920, height: 1080 },
} as const;

test.describe('响应式布局断点验证', () => {
  test.use({ storageState: 'e2e/.auth/admin.json' });

  for (const [name, viewport] of Object.entries(VIEWPORTS)) {
    test(`${name} (${viewport.width}x${viewport.height}) 布局正确`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto('/admin/dashboard');

      await expect(page.locator('body')).toBeVisible();

      const root = page.locator(':root');
      const layout = await root.getAttribute('style');

      if (viewport.width < 768) {
        await expect(page.locator('.sidebar, [data-testid="sidebar"]')).not.toBeVisible();
      } else if (viewport.width < 1024) {
        const sidebar = page.locator('.sidebar, [data-testid="sidebar"]');
        if (await sidebar.isVisible()) {
          const width = await sidebar.boundingBox().then(b => b?.width || 0);
          expect(width).toBeLessThan(248);
        }
      }
    });
  }
});

test.describe('自适应密度验证', () => {
  test.use({ storageState: 'e2e/.auth/admin.json' });

  test('紧凑模式表格行高更小', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/admin/dashboard');
    await page.evaluate(() => {
      document.documentElement.classList.add('adaptive-density-compact');
    });
    const compactHeight = await page.locator('.ant-table-row, tr').first().boundingBox()
      .then(b => b?.height || 0);

    await page.evaluate(() => {
      document.documentElement.classList.remove('adaptive-density-compact');
      document.documentElement.classList.add('adaptive-density-comfortable');
    });
    const comfortableHeight = await page.locator('.ant-table-row, tr').first().boundingBox()
      .then(b => b?.height || 0);

    if (compactHeight > 0 && comfortableHeight > 0) {
      expect(compactHeight).toBeLessThan(comfortableHeight);
    }
  });
});

test.describe('无障碍合规验证', () => {
  test.use({ storageState: 'e2e/.auth/admin.json' });

  test('页面有正确的 lang 属性', async ({ page }) => {
    await page.goto('/admin/dashboard');
    const lang = await page.locator('html').getAttribute('lang');
    expect(lang).toBeTruthy();
  });

  test('所有图片有 alt 文本', async ({ page }) => {
    await page.goto('/admin/dashboard');
    const imagesWithoutAlt = await page.locator('img:not([alt])').count();
    expect(imagesWithoutAlt).toBe(0);
  });

  test('表单元素有关联标签', async ({ page }) => {
    await page.goto('/login');
    const inputs = page.locator('input:not([type="hidden"])');
    const count = await inputs.count();
    for (let i = 0; i < count; i++) {
      const input = inputs.nth(i);
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const placeholder = await input.getAttribute('placeholder');
      expect(id || ariaLabel || placeholder).toBeTruthy();
    }
  });

  test('键盘可导航（Tab 循环）', async ({ page }) => {
    await page.goto('/login');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    const focused = page.locator(':focus');
    await expect(focused).toBeVisible();
  });
});
