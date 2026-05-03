const http = require('http');

const BASE_URL = 'http://127.0.0.1:8787';

function makeRequest(path = '/', method = 'GET', body = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: '127.0.0.1',
      port: 8787,
      path,
      method,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(data) });
        } catch (e) {
          resolve({ status: res.statusCode, data: data });
        }
      });
    });

    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function runTests() {
  console.log('=== 高性能 MCP Bridge v2.0 性能测试 ===\n');

  // 测试1：基础连通性
  console.log('📡 测试1：基础连通性...');
  const start1 = Date.now();
  const res1 = await makeRequest();
  const latency1 = Date.now() - start1;
  console.log(`   状态: ${res1.status === 200 ? '✅ 通过' : '❌ 失败'}`);
  console.log(`   延迟: ${latency1}ms`);
  console.log(`   响应: ${JSON.stringify(res1.data).substring(0, 100)}...\n`);

  // 测试2：MCP 初始化
  console.log('🔧 测试2：MCP 初始化...');
  const start2 = Date.now();
  const res2 = await makeRequest('/', 'POST', {
    jsonrpc: '2.0',
    id: 1,
    method: 'initialize',
    params: {}
  });
  const latency2 = Date.now() - start2;
  console.log(`   状态: ${res2.status === 200 ? '✅ 通过' : '❌ 失败'}`);
  console.log(`   延迟: ${latency2}ms\n`);

  // 测试3：工具列表
  console.log('📋 测试3：工具列表获取...');
  const start3 = Date.now();
  const res3 = await makeRequest('/', 'POST', {
    jsonrpc: '2.0',
    id: 2,
    method: 'tools/list',
    params: {}
  });
  const latency3 = Date.now() - start3;
  const toolCount = res3.data?.result?.tools?.length || 0;
  console.log(`   状态: ${res3.status === 200 ? '✅ 通过' : '❌ 失败'}`);
  console.log(`   延迟: ${latency3}ms`);
  console.log(`   工具数: ${toolCount}\n`);

  // 测试4：聊天工具调用
  console.log('💬 测试4：聊天工具调用...');
  const start4 = Date.now();
  const res4 = await makeRequest('/', 'POST', {
    jsonrpc: '2.0',
    id: 3,
    method: 'tools/call',
    params: {
      name: 'lingma_chat',
      arguments: { message: '你好，测试连通性' }
    }
  });
  const latency4 = Date.now() - start4;
  console.log(`   状态: ${res4.status === 200 ? '✅ 通过' : '❌ 失败'}`);
  console.log(`   延迟: ${latency4}ms\n`);

  // 测试5：性能指标
  console.log('📊 测试5：性能指标获取...');
  const start5 = Date.now();
  const res5 = await makeRequest('/metrics');
  const latency5 = Date.now() - start5;
  console.log(`   状态: ${res5.status === 200 ? '✅ 通过' : '❌ 失败'}`);
  console.log(`   延迟: ${latency5}ms`);
  if (res5.data) {
    console.log(`   总请求: ${res5.data.totalRequests || 0}`);
    console.log(`   成功率: ${res5.data.successRate || 'N/A'}`);
    console.log(`   P50延迟: ${res5.data.p50Latency || 0}ms`);
    console.log(`   P95延迟: ${res5.data.p95Latency || 0}ms`);
  }
  console.log('');

  // 测试6：并发请求
  console.log('⚡ 测试6：并发请求测试 (10个)...');
  const start6 = Date.now();
  const promises = [];
  for (let i = 0; i < 10; i++) {
    promises.push(makeRequest('/', 'POST', {
      jsonrpc: '2.0',
      id: 100 + i,
      method: 'tools/list',
      params: {}
    }));
  }
  const results = await Promise.all(promises);
  const latency6 = Date.now() - start6;
  const successCount = results.filter(r => r.status === 200).length;
  console.log(`   总耗时: ${latency6}ms`);
  console.log(`   成功: ${successCount}/10`);
  console.log(`   平均: ${(latency6 / 10).toFixed(1)}ms/请求\n`);

  // 总结
  console.log('=== 性能总结 ===');
  console.log(`基础连通性: ${latency1}ms`);
  console.log(`MCP 初始化: ${latency2}ms`);
  console.log(`工具列表: ${latency3}ms`);
  console.log(`聊天调用: ${latency4}ms`);
  console.log(`性能指标: ${latency5}ms`);
  console.log(`并发测试: ${latency6}ms (10请求)`);
  console.log('\n✅ 性能测试完成！');
}

runTests().catch(console.error);
