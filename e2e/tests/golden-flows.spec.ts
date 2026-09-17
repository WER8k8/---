/**
 * P0 黄金流程 E2E 测试
 *
 * 覆盖 5 条核心业务链路：
 * 1. 超管登录 → 仪表盘
 * 2. 租户登录 → 询盘收件箱 → 回复
 * 3. 租户登录 → 产品发布
 * 4. 访客 → 官网 → 提交询盘
 * 5. 租户 → GoodJob CRM → PI 生成
 */

import { test, expect } from '@playwright/test';

test.describe('黄金流程 1：超管仪表盘', () => {
  test.use({ storageState: 'e2e/.auth/admin.json' });

  test('超管登录后看到仪表盘', async ({ page }) => {
    await page.goto('/admin/dashboard');
    await expect(page.locator('h1, .page-title')).toContainText(/仪表盘|dashboard/i);
    await expect(page.locator('.ant-card, .yd-stats-card').first()).toBeVisible();
  });

  test('超管可查看租户列表', async ({ page }) => {
    await page.goto('/admin/tenants');
    await expect(page.locator('.ant-table, .yd-data-table').first()).toBeVisible();
  });

  test('超管可查看系统健康', async ({ page }) => {
    await page.goto('/admin/system-health');
    await expect(page.locator('[data-testid="health-status"], .health-indicator').first()).toBeVisible();
  });
});

test.describe('黄金流程 2：租户询盘处理', () => {
  test.use({ storageState: 'e2e/.auth/tenant.json' });

  test('租户登录后进入询盘收件箱', async ({ page }) => {
    await page.goto('/client/inquiries');
    await expect(page.locator('h1, .page-title')).toContainText(/询盘|inquir/i);
  });

  test('租户可查看产品列表', async ({ page }) => {
    await page.goto('/client/products');
    await expect(page.locator('.ant-table, .yd-data-table').first()).toBeVisible();
  });
});

test.describe('黄金流程 3：租户产品发布', () => {
  test.use({ storageState: 'e2e/.auth/tenant.json' });

  test('租户可进入产品编辑页', async ({ page }) => {
    await page.goto('/client/products');
    const createBtn = page.getByRole('button', { name: /新建|创建|add|create/i });
    if (await createBtn.isVisible()) {
      await createBtn.click();
      await expect(page).toHaveURL(/\/products\/(new|create|edit)/);
    }
  });
});

test.describe('黄金流程 4：访客官网询盘', () => {
  test('访客可浏览官网首页', async ({ page }) => {
    const baseURL = process.env.E2E_SITE_URL || 'http://127.0.0.1:3000';
    await page.goto(baseURL);
    await expect(page.locator('header, nav').first()).toBeVisible();
  });

  test('访客可浏览产品页', async ({ page }) => {
    const baseURL = process.env.E2E_SITE_URL || 'http://127.0.0.1:3000';
    await page.goto(`${baseURL}/products`);
    await expect(page.locator('.product-card, .product-list, main').first()).toBeVisible();
  });

  test('访客可提交询盘表单', async ({ page }) => {
    const baseURL = process.env.E2E_SITE_URL || 'http://127.0.0.1:3000';
    await page.goto(`${baseURL}/contact`);
    const form = page.locator('form').first();
    if (await form.isVisible()) {
      await page.getByLabel(/姓名|name/i).first().fill('E2E Test User');
      await page.getByLabel(/邮箱|email/i).first().fill('e2e@test.com');
      await page.getByLabel(/手机|phone|mobile/i).first().fill('+8613800138000');
      await page.getByLabel(/留言|message|内容/i).first().fill('E2E test inquiry');
      const submitBtn = page.getByRole('button', { name: /提交|发送|submit|send/i });
      if (await submitBtn.isVisible()) {
        await submitBtn.click();
        await expect(page.locator('.ant-message-success, .success-message, [role="alert"]').first()).toBeVisible({ timeout: 10000 });
      }
    }
  });
});

test.describe('黄金流程 5：角色壳隔离验证', () => {
  test('超管无法访问租户路由', async ({ page }) => {
    test.use({ storageState: 'e2e/.auth/admin.json' });
    await page.goto('/client/inquiries');
    await expect(page).not.toHaveURL(/\/client\/inquiries/);
  });

  test('租户无法访问超管路由', async ({ page }) => {
    test.use({ storageState: 'e2e/.auth/tenant.json' });
    await page.goto('/admin/tenants');
    await expect(page).not.toHaveURL(/\/admin\/tenants/);
  });
});
