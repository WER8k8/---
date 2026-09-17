/**
 * E2E 认证设置 — 登录并保存认证状态
 */

import { test as setup, expect } from '@playwright/test';

const ADMIN_AUTH_FILE = 'e2e/.auth/admin.json';
const TENANT_AUTH_FILE = 'e2e/.auth/tenant.json';
const AGENT_AUTH_FILE = 'e2e/.auth/agent.json';

setup('authenticate as admin', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel(/用户名|账号|username/i).fill('admin');
  await page.getByLabel(/密码|password/i).fill('admin123');
  await page.getByRole('button', { name: /登录|sign in/i }).click();
  await page.waitForURL('**/admin/**');
  await expect(page).toHaveURL(/\/admin/);
  await page.context().storageState({ path: ADMIN_AUTH_FILE });
});

setup('authenticate as tenant', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel(/用户名|账号|username/i).fill('tenant');
  await page.getByLabel(/密码|password/i).fill('tenant123');
  await page.getByRole('button', { name: /登录|sign in/i }).click();
  await page.waitForURL('**/client/**');
  await expect(page).toHaveURL(/\/client/);
  await page.context().storageState({ path: TENANT_AUTH_FILE });
});

setup('authenticate as agent', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel(/用户名|账号|username/i).fill('agent');
  await page.getByLabel(/密码|password/i).fill('agent123');
  await page.getByRole('button', { name: /登录|sign in/i }).click();
  await page.waitForURL('**/agent/**');
  await expect(page).toHaveURL(/\/agent/);
  await page.context().storageState({ path: AGENT_AUTH_FILE });
});
