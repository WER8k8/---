#!/usr/bin/env node
/**
 * 系统全面测试脚本
 * 覆盖认证、租户管理、文件管理、视频发布、SEO等核心模块
 */

const API_BASE = 'http://127.0.0.1:8001';
const USERNAME = 'admin';
const PASSWORD = 'admin123';

let token = null;
let tenantId = null;

const testResults = {
  passed: [],
  failed: [],
  skipped: []
};

function logResult(testName, status, message = '') {
  const result = { testName, status, message };
  if (status === 'PASS') {
    testResults.passed.push(result);
    console.log(`✅ PASS: ${testName} ${message ? '- ' + message : ''}`);
  } else if (status === 'FAIL') {
    testResults.failed.push(result);
    console.log(`❌ FAIL: ${testName} - ${message}`);
  } else {
    testResults.skipped.push(result);
    console.log(`⚠️ SKIP: ${testName} - ${message}`);
  }
}

async function fetchWithAuth(url, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return fetch(url, { ...options, headers });
}

async function testAuth() {
  console.log('\n=== 认证模块测试 ===');
  
  // 测试登录
  const loginRes = await fetchWithAuth(`${API_BASE}/api/v1/auth/login`, {
    method: 'POST',
    body: JSON.stringify({ username_or_email: USERNAME, password: PASSWORD })
  });
  
  if (loginRes.status === 200) {
    const data = await loginRes.json();
    token = data.data?.access_token;
    logResult('用户登录', 'PASS', `Token获取成功`);
  } else {
    logResult('用户登录', 'FAIL', `HTTP ${loginRes.status}`);
    return false;
  }
  
  // 测试获取当前用户
  const userRes = await fetchWithAuth(`${API_BASE}/api/v1/users/me`);
  if (userRes.status === 200) {
    const data = await userRes.json();
    logResult('获取当前用户', 'PASS', `用户: ${data.data?.username}`);
  } else {
    logResult('获取当前用户', 'FAIL', `HTTP ${userRes.status}`);
  }
  
  return true;
}

async function testTenants() {
  console.log('\n=== 租户管理模块测试 ===');
  
  // 获取租户列表
  const listRes = await fetchWithAuth(`${API_BASE}/api/v1/tenants/`);
  if (listRes.status === 200) {
    const data = await listRes.json();
    tenantId = data.data?.recent_tenants?.[0]?.id;
    logResult('获取租户列表', 'PASS', `找到 ${data.data?.recent_tenants?.length || 0} 个租户`);
  } else {
    logResult('获取租户列表', 'FAIL', `HTTP ${listRes.status}`);
  }
  
  // 获取当前租户
  const currentRes = await fetchWithAuth(`${API_BASE}/api/v1/tenants/current`);
  if (currentRes.status === 200) {
    logResult('获取当前租户', 'PASS');
  } else {
    logResult('获取当前租户', 'FAIL', `HTTP ${currentRes.status}`);
  }
}

async function testFiles() {
  console.log('\n=== 文件管理模块测试 ===');
  
  // 获取文件列表
  const listRes = await fetchWithAuth(`${API_BASE}/api/v1/files/`);
  if (listRes.status === 200) {
    logResult('获取文件列表', 'PASS');
  } else {
    logResult('获取文件列表', 'FAIL', `HTTP ${listRes.status}`);
  }
  
  // 获取文件统计
  const statsRes = await fetchWithAuth(`${API_BASE}/api/v1/files/stats`);
  if (statsRes.status === 200) {
    logResult('获取文件统计', 'PASS');
  } else {
    logResult('获取文件统计', 'FAIL', `HTTP ${statsRes.status}`);
  }
  
  // 测试asset-proxy（未认证）
  const proxyUrl = 'https://hb-bkt.clouddn.com/test.jpg';
  const proxyRes = await fetch(`${API_BASE}/api/v1/files/asset-proxy?url=${encodeURIComponent(proxyUrl)}`);
  if (proxyRes.status === 200 || proxyRes.status === 404) { // 404是因为文件不存在，不是认证错误
    logResult('asset-proxy未认证访问', 'PASS', `HTTP ${proxyRes.status}`);
  } else {
    logResult('asset-proxy未认证访问', 'FAIL', `HTTP ${proxyRes.status}`);
  }
  
  // 测试asset-proxy（已认证）
  const proxyAuthRes = await fetchWithAuth(`${API_BASE}/api/v1/files/asset-proxy?url=${encodeURIComponent(proxyUrl)}`);
  if (proxyAuthRes.status === 200 || proxyAuthRes.status === 404) {
    logResult('asset-proxy已认证访问', 'PASS', `HTTP ${proxyAuthRes.status}`);
  } else {
    logResult('asset-proxy已认证访问', 'FAIL', `HTTP ${proxyAuthRes.status}`);
  }
}

async function testVideoPublish() {
  console.log('\n=== 视频发布模块测试 ===');
  
  // 获取视频发布任务列表
  const tasksRes = await fetchWithAuth(`${API_BASE}/api/v1/publish-tasks`);
  if (tasksRes.status === 200) {
    logResult('获取发布任务列表', 'PASS');
  } else {
    logResult('获取发布任务列表', 'FAIL', `HTTP ${tasksRes.status}`);
  }
  
  // 获取视频绑定列表
  const bindRes = await fetchWithAuth(`${API_BASE}/api/v1/publish/video/bind-hub`);
  if (bindRes.status === 200) {
    logResult('获取平台绑定列表', 'PASS');
  } else {
    logResult('获取平台绑定列表', 'FAIL', `HTTP ${bindRes.status}`);
  }
}

async function testCrossPlatform() {
  console.log('\n=== 跨平台数据模块测试 ===');
  
  const dashRes = await fetchWithAuth(`${API_BASE}/api/v1/cross-platform-dashboard/summary`);
  if (dashRes.status === 200) {
    logResult('获取跨平台数据汇总', 'PASS');
  } else {
    logResult('获取跨平台数据汇总', 'FAIL', `HTTP ${dashRes.status}`);
  }
}

async function testSEO() {
  console.log('\n=== SEO模块测试 ===');
  
  // 获取SEO矩阵关键词
  const keywordsRes = await fetchWithAuth(`${API_BASE}/api/v1/seo-matrix/generated-keywords`);
  if (keywordsRes.status === 200) {
    logResult('获取SEO矩阵关键词', 'PASS');
  } else {
    logResult('获取SEO矩阵关键词', 'FAIL', `HTTP ${keywordsRes.status}`);
  }
  
  // 获取SEO诊断（POST方法）
  const diagRes = await fetchWithAuth(`${API_BASE}/api/v1/seo-diagnosis`, {
    method: 'POST',
    body: JSON.stringify({ name: '测试用户', phone: '13800138000' })
  });
  if (diagRes.status === 200) {
    logResult('SEO诊断检查', 'PASS', `HTTP ${diagRes.status}`);
  } else {
    logResult('SEO诊断检查', 'FAIL', `HTTP ${diagRes.status}`);
  }
}

async function testInquiries() {
  console.log('\n=== 询盘模块测试 ===');
  
  const inquiriesRes = await fetchWithAuth(`${API_BASE}/api/v1/inquiries/unified`);
  if (inquiriesRes.status === 200) {
    logResult('获取询盘列表', 'PASS');
  } else {
    logResult('获取询盘列表', 'FAIL', `HTTP ${inquiriesRes.status}`);
  }
}

async function testSystem() {
  console.log('\n=== 系统模块测试 ===');
  
  // 健康检查
  const healthRes = await fetch(`${API_BASE}/api/v1/health`);
  if (healthRes.status === 200) {
    logResult('健康检查', 'PASS');
  } else {
    logResult('健康检查', 'FAIL', `HTTP ${healthRes.status}`);
  }
  
  // 获取系统信息
  const configRes = await fetchWithAuth(`${API_BASE}/api/v1/system/info`);
  if (configRes.status === 200) {
    logResult('获取系统信息', 'PASS');
  } else {
    logResult('获取系统信息', 'FAIL', `HTTP ${configRes.status}`);
  }
}

async function testEdgeCDN() {
  console.log('\n=== Edge CDN模块测试 ===');
  
  const endpointsRes = await fetchWithAuth(`${API_BASE}/api/v1/egress/endpoints`);
  if (endpointsRes.status === 200) {
    logResult('获取出口端点', 'PASS');
  } else {
    logResult('获取出口端点', 'FAIL', `HTTP ${endpointsRes.status}`);
  }
}

async function generateReport() {
  console.log('\n' + '='.repeat(60));
  console.log('                    系统全面测试报告');
  console.log('='.repeat(60));
  
  const total = testResults.passed.length + testResults.failed.length + testResults.skipped.length;
  const passRate = total > 0 ? ((testResults.passed.length / total) * 100).toFixed(1) : 0;
  
  console.log(`\n📊 测试统计:`);
  console.log(`   总测试数: ${total}`);
  console.log(`   ✅ 通过: ${testResults.passed.length}`);
  console.log(`   ❌ 失败: ${testResults.failed.length}`);
  console.log(`   ⚠️ 跳过: ${testResults.skipped.length}`);
  console.log(`   📈 通过率: ${passRate}%`);
  
  if (testResults.failed.length > 0) {
    console.log(`\n❌ 失败测试详情:`);
    testResults.failed.forEach((item, index) => {
      console.log(`   ${index + 1}. ${item.testName}: ${item.message}`);
    });
  }
  
  console.log(`\n${passRate >= 90 ? '🎉 测试通过！系统状态良好。' : '⚠️ 部分测试失败，请检查相关模块。'}`);
}

async function main() {
  console.log('🚀 开始系统全面测试...');
  
  // 先测试认证，认证失败则停止
  const authSuccess = await testAuth();
  if (!authSuccess) {
    console.log('\n❌ 认证失败，无法继续测试');
    return;
  }
  
  // 并行执行其他测试模块
  await Promise.all([
    testTenants(),
    testFiles(),
    testVideoPublish(),
    testCrossPlatform(),
    testSEO(),
    testInquiries(),
    testSystem(),
    testEdgeCDN()
  ]);
  
  // 生成报告
  await generateReport();
}

main().catch(err => {
  console.error('❌ 测试执行异常:', err);
});
