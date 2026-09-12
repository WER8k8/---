import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// 自定义指标
const errorRate = new Rate('errors');

// 测试配置
export const options = {
  stages: [
    { duration: '30s', target: 20 },   // 热身：20用户
    { duration: '1m', target: 50 },    // 负载：50用户
    { duration: '2m', target: 100 },   // 压力：100用户
    { duration: '1m', target: 200 },   // 峰值：200用户
    { duration: '30s', target: 0 },    // 冷却
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95%请求<500ms
    http_req_failed: ['rate<0.01'],    // 错误率<1%
    errors: ['rate<0.1'],              // 自定义错误率<10%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// 测试数据
const testCredentials = {
  username: 'admin',
  password: 'Admin@123456'
};

let authToken = '';

export function setup() {
  // 登录获取token
  const loginRes = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify(testCredentials), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  check(loginRes, {
    'login successful': (r) => r.status === 200,
  });
  
  if (loginRes.status === 200) {
    authToken = loginRes.json('access_token');
  }
  
  return { authToken };
}

export default function(data) {
  const token = data.authToken;
  
  // 测试1: 健康检查
  const healthRes = http.get(`${BASE_URL}/api/v1/health`);
  check(healthRes, {
    'health check ok': (r) => r.status === 200,
  }) || errorRate.add(1);
  
  // 测试2: 获取产品列表
  const productsRes = http.get(`${BASE_URL}/api/v1/products`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  check(productsRes, {
    'products list ok': (r) => r.status === 200,
    'products is array': (r) => Array.isArray(r.json()),
  }) || errorRate.add(1);
  
  // 测试3: 获取内容页面
  const contentRes = http.get(`${BASE_URL}/api/v1/content/about`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  check(contentRes, {
    'content page ok': (r) => r.status === 200 || r.status === 404,
  }) || errorRate.add(1);
  
  // 测试4: 获取案例列表
  const casesRes = http.get(`${BASE_URL}/api/v1/cases`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  check(casesRes, {
    'cases list ok': (r) => r.status === 200,
  }) || errorRate.add(1);
  
  // 测试5: 提交询盘
  const inquiryPayload = JSON.stringify({
    name: `测试用户_${__VU}_${__ITER}`,
    phone: '13800138000',
    email: 'test@example.com',
    message: '这是一条测试询盘',
  });
  
  const inquiryRes = http.post(`${BASE_URL}/api/v1/inquiries`, inquiryPayload, {
    headers: { 'Content-Type': 'application/json' },
  });
  check(inquiryRes, {
    'inquiry created': (r) => r.status === 200 || r.status === 201,
  }) || errorRate.add(1);
  
  // 测试6: 获取分析数据
  const analyticsRes = http.get(`${BASE_URL}/api/v1/analytics/dashboard`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  check(analyticsRes, {
    'analytics ok': (r) => r.status === 200,
  }) || errorRate.add(1);
  
  sleep(1);
}

export function handleSummary(data) {
  return {
    'summary.json': JSON.stringify(data),
    stdout: textSummary(data),
  };
}

function textSummary(data) {
  return `
📊 压力测试报告
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 总请求数: ${data.metrics.http_reqs.values.count}
⏱️ 平均响应时间: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms
📈 P95响应时间: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms
📉 P99响应时间: ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms
❌ 错误率: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%
🔄 吞吐量: ${data.metrics.http_reqs.values.rate.toFixed(2)} req/s
━━━━━━━━━━━━━━━━━━━━━━━━
`;
}
