#!/usr/bin/env node
/**
 * COMM-QA-03 · 送检截图（仅非 blocked 模块）
 * 需 backend :8001 + admin :5173
 *   node scripts/capture-cert-screenshots-comm-qa-03.mjs
 */
import { chromium } from 'playwright';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const ASSIGNMENTS = path.join(ROOT, '.project', 'cert-screenshot-assignments-COMM-QA-03.json');
const DEV_ACCOUNTS = path.join(ROOT, '.project', 'dev-login-accounts.json');
const ARCHIVE = path.join(ROOT, 'docs', 'mod-04-rehearsal');
const API = process.env.ADMIN_API_URL || 'http://127.0.0.1:8001/api/v1/auth/login';
const ORIGIN = process.env.ADMIN_DEV_ORIGIN || 'http://127.0.0.1:5173';

async function loadAccounts() {
  try {
    const raw = JSON.parse(await readFile(DEV_ACCOUNTS, 'utf8'));
    const map = {};
    for (const a of raw.accounts || []) {
      map[a.role] = a;
    }
    return map;
  } catch {
    return {
      super_admin: { username: 'admin', password: 'ChangeMe@2026!' },
      tenant_admin: { username: 'tenant', password: 'tenant123' },
    };
  }
}

async function loginToken(username, password) {
  const res = await fetch(API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username_or_email: username, password }),
  });
  const raw = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(`Login HTTP ${res.status}: ${JSON.stringify(raw).slice(0, 300)}`);
  const token = raw?.data?.access_token || raw?.access_token;
  if (!token) throw new Error(`No access_token for ${username}`);
  return token;
}

const assignments = JSON.parse(await readFile(ASSIGNMENTS, 'utf8'));
const accounts = await loadAccounts();
const targets = (assignments.modules || []).filter((m) => m.status === 'pending' && m.route?.startsWith('/'));

await mkdir(ARCHIVE, { recursive: true });

let browser;
try {
  browser = await chromium.launch({ headless: true, channel: 'msedge' });
} catch {
  browser = await chromium.launch({ headless: true });
}

const results = [];
for (const mod of targets) {
  const acc = accounts[mod.role] || accounts.super_admin;
  const token = await loginToken(acc.username, acc.password);
  const outDir = path.join(ARCHIVE, path.dirname(mod.file));
  await mkdir(outDir, { recursive: true });
  const outFile = path.join(ARCHIVE, mod.file);

  const context = await browser.newContext({ baseURL: ORIGIN, viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  await page.addInitScript(
    ([t, u]) => {
      localStorage.setItem('admin_token', t);
      localStorage.setItem('admin_username', u);
      localStorage.setItem('admin_cert_mode', '0');
      localStorage.setItem('admin_lab_enabled', '0');
    },
    [token, acc.username],
  );

  try {
    await page.goto(mod.route, { waitUntil: 'networkidle', timeout: 90000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: outFile, fullPage: false });
    mod.status = 'captured';
    mod.captured_at = new Date().toISOString();
    results.push({ id: mod.id, ok: true, file: mod.file });
    console.log('OK', mod.id, mod.file);
  } catch (e) {
    mod.status = 'failed';
    mod.error = String(e.message || e);
    results.push({ id: mod.id, ok: false, error: mod.error });
    console.error('FAIL', mod.id, mod.error);
  } finally {
    await context.close();
  }
}

await browser.close();

assignments.summary = {
  total: assignments.modules.length,
  pending: assignments.modules.filter((m) => m.status === 'pending').length,
  blocked: assignments.modules.filter((m) => m.status === 'blocked').length,
  captured: assignments.modules.filter((m) => m.status === 'captured').length,
  failed: assignments.modules.filter((m) => m.status === 'failed').length,
};
assignments.last_capture_run = new Date().toISOString();

await writeFile(ASSIGNMENTS, `${JSON.stringify(assignments, null, 2)}\n`, 'utf8');
const manifest = {
  generated_at: new Date().toISOString(),
  origin: ORIGIN,
  results,
  summary: assignments.summary,
};
await writeFile(path.join(ARCHIVE, 'cert-capture-manifest-latest.json'), `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
console.log(JSON.stringify(manifest, null, 2));
