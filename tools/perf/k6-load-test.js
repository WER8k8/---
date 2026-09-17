/**
 * k6 性能基准测试脚本
 *
 * 测试维度：
 * 1. 负载测试 — 100 并发持续 5 分钟
 * 2. 压力测试 — 逐步加压至系统极限
 * 3. 尖峰测试 — 瞬时 500 并发
 * 4. 浸泡测试 — 50 并发持续 30 分钟
 *
 * 运行方式：k6 run tools/perf/k6-load-test.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8001';
const TEST_MODE = __ENV.TEST_MODE || 'load';

const errorRate = new Rate('errors');
const apiLatency = new Trend('api_latency');

const thresholds = {
  http_req_duration: ['p(95)<500', 'p(99)<1000'],
  errors: ['rate<0.01'],
  api_latency: ['avg<300', 'p(95)<500'],
};

const scenarios = {
  load: {
    executor: 'constant-vus',
    vus: 100,
    duration: '5m',
  },
  stress: {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '2m', target: 50 },
      { duration: '5m', target: 200 },
      { duration: '2m', target: 500 },
      { duration: '5m', target: 500 },
      { duration: '2m', target: 0 },
    ],
  },
  spike: {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '30s', target: 500 },
      { duration: '1m', target: 500 },
      { duration: '30s', target: 0 },
    ],
  },
  soak: {
    executor: 'constant-vus',
    vus: 50,
    duration: '30m',
  },
};

export const options = {
  scenarios: { [TEST_MODE]: scenarios[TEST_MODE] },
  thresholds,
};

function login() {
  const res = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
    username: 'admin',
    password: 'admin123',
  }), {
    headers: { 'Content-Type': 'application/json' },
  });

  const success = check(res, {
    'login status 200': (r) => r.status === 200,
    'login has token': (r) => {
      try { return !!JSON.parse(r.body).access_token; }
      catch { return false; }
    },
  });
  errorRate.add(!success);

  if (success) {
    try { return JSON.parse(res.body).access_token; }
    catch { return null; }
  }
  return null;
}

export default function () {
  const token = login();
  if (!token) { sleep(1); return; }

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };

  group('核心 API 链路', () => {
    let res;

    res = http.get(`${BASE_URL}/api/v1/dashboard/stats`, { headers });
    apiLatency.add(res.timings.duration);
    check(res, { 'dashboard 200': (r) => r.status === 200 });

    sleep(0.5);

    res = http.get(`${BASE_URL}/api/v1/products?page=1&page_size=20`, { headers });
    apiLatency.add(res.timings.duration);
    check(res, { 'products list 200': (r) => r.status === 200 });

    sleep(0.5);

    res = http.get(`${BASE_URL}/api/v1/inquiries?page=1&page_size=20`, { headers });
    apiLatency.add(res.timings.duration);
    check(res, { 'inquiries list 200': (r) => r.status === 200 });

    sleep(1);
  });
}
