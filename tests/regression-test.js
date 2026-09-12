/**
 * GB/T 25000.51-2016 回归测试套件
 * 用法: node tests/regression-test.js
 */

const http = require('http');

const BASE_URL = 'http://localhost:5173';
const API_URL = 'http://localhost:8001';

const tests = [];

function test(name, fn) {
  tests.push({ name, fn });
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

function assertStatus(res, expected) {
  if (res.statusCode !== expected) {
    throw new Error(`Expected status ${expected}, got ${res.statusCode}`);
  }
}

// 测试1: 前端页面可访问
test('前端页面HTTP 200', (resolve, reject) => {
  http.get(BASE_URL + '/', (res) => {
    try {
      assertStatus(res, 200);
      console.log('  ✅ 前端页面可访问');
      resolve();
    } catch (e) {
      reject(e);
    }
  }).on('error', reject);
});

// 测试2: 租户API需要认证（验证安全配置）
test('租户API需要认证', (resolve, reject) => {
  http.get(API_URL + '/api/v1/tenants/', (res) => {
    try {
      assertStatus(res, 401);
      console.log('  ✅ 租户API正确要求认证');
      resolve();
    } catch (e) {
      reject(e);
    }
  }).on('error', reject);
});

// 测试3: 超级管理员告警API可访问
test('超级管理员API可访问', (resolve, reject) => {
  http.get(API_URL + '/api/v1/super-admin/alerts/summary', (res) => {
    try {
      assert([200, 401].includes(res.statusCode), `Unexpected status: ${res.statusCode}`);
      console.log('  ✅ 超级管理员API正常响应');
      resolve();
    } catch (e) {
      reject(e);
    }
  }).on('error', reject);
});

// 测试4: 根路径API响应
test('API根路径正常', (resolve, reject) => {
  http.get(API_URL + '/', (res) => {
    try {
      assert([200, 404, 307].includes(res.statusCode), `Unexpected status: ${res.statusCode}`);
      console.log('  ✅ API根路径正常响应');
      resolve();
    } catch (e) {
      reject(e);
    }
  }).on('error', reject);
});

// 执行测试
async function runTests() {
  console.log('\n🧪 GB/T 25000.51-2016 回归测试套件');
  console.log('====================================\n');

  let passed = 0;
  let failed = 0;

  for (const { name, fn } of tests) {
    console.log(`测试: ${name}`);
    try {
      await new Promise(fn);
      passed++;
    } catch (e) {
      console.log(`  ❌ 失败: ${e.message}`);
      failed++;
    }
  }

  console.log('\n====================================');
  console.log(`结果: ${passed} 通过, ${failed} 失败`);
  console.log('====================================\n');

  process.exit(failed > 0 ? 1 : 0);
}

runTests();
