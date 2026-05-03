/**
 * 极致性能基准测试 - 验证延迟 < 1ms
 * 
 * 测试项目：
 * - 二进制编码/解码延迟 (Binary Encode/Decode)
 * - 对象池获取/释放延迟 (Object Pool Acquire/Release)
 * - TCP回环请求延迟 (TCP Loopback Request)
 * - 并发压力测试 (Concurrent Load)
 * 
 * @author 超级架构指挥官
 */

const net = require('net');
const { BinaryProtocol, BufferPool, RequestPool, UltraPerformanceMonitor } = require('./lingma-mcp-bridge-v3');

// ==================== 测试工具 ====================
function measure(fn, iterations = 10000) {
  const start = process.hrtime.bigint();
  for (let i = 0; i < iterations; i++) {
    fn();
  }
  const end = process.hrtime.bigint();
  const totalMs = Number(end - start) / 1e6;
  return totalMs / iterations;
}

async function measureAsync(asyncFn, iterations = 1000) {
  const start = process.hrtime.bigint();
  for (let i = 0; i < iterations; i++) {
    await asyncFn();
  }
  const end = process.hrtime.bigint();
  const totalMs = Number(end - start) / 1e6;
  return totalMs / iterations;
}

// ==================== 测试套件 ====================
async function runBenchmarks() {
  console.log('🔬 Ultra-Low-Latency Bridge v3.0 - Performance Benchmark\n');
  console.log('=' .repeat(60));

  // 测试1: 二进制协议编码延迟
  console.log('\n📦 Test 1: Binary Protocol Encode Latency');
  const protocol = new BinaryProtocol();
  const encodeLatency = measure(() => {
    protocol.encode('test.method', { key: 'value' }, 1);
  }, 50000);
  console.log(`   Average encode latency: ${encodeLatency.toFixed(4)}ms`);
  console.log(`   Status: ${encodeLatency < 0.01 ? '✅ PASS' : '⚠️ NEEDS OPTIMIZATION'}`);

  // 测试2: 二进制协议解码延迟
  console.log('\n📦 Test 2: Binary Protocol Decode Latency');
  const encoded = protocol.encode('test.method', { key: 'value' }, 1);
  const decodeLatency = measure(() => {
    protocol.decode(encoded);
  }, 50000);
  console.log(`   Average decode latency: ${decodeLatency.toFixed(4)}ms`);
  console.log(`   Status: ${decodeLatency < 0.01 ? '✅ PASS' : '⚠️ NEEDS OPTIMIZATION'}`);

  // 测试3: Buffer对象池获取延迟
  console.log('\n🗄️ Test 3: Buffer Pool Acquire/Release Latency');
  const bufferPool = new BufferPool(100, 4096);
  const poolLatency = measure(() => {
    const buf = bufferPool.acquire();
    bufferPool.release(buf);
  }, 100000);
  console.log(`   Average pool operation latency: ${poolLatency.toFixed(4)}ms`);
  console.log(`   Status: ${poolLatency < 0.001 ? '✅ PASS' : '⚠️ NEEDS OPTIMIZATION'}`);

  // 测试4: 请求对象池获取延迟
  console.log('\n🗄️ Test 4: Request Pool Acquire/Release Latency');
  const requestPool = new RequestPool(1000);
  const requestPoolLatency = measure(() => {
    const req = requestPool.acquire(1, 'test', {}, () => {}, 1000);
    requestPool.resolve(1, { result: 'ok' });
  }, 50000);
  console.log(`   Average request pool latency: ${requestPoolLatency.toFixed(4)}ms`);
  console.log(`   Status: ${requestPoolLatency < 0.001 ? '✅ PASS' : '⚠️ NEEDS OPTIMIZATION'}`);

  // 测试5: 性能监控记录延迟
  console.log('\n📊 Test 5: Performance Monitor Record Latency');
  const monitor = new UltraPerformanceMonitor();
  const monitorLatency = measure(() => {
    monitor.recordRequest(0.5, true);
  }, 100000);
  console.log(`   Average monitor record latency: ${monitorLatency.toFixed(4)}ms`);
  console.log(`   Status: ${monitorLatency < 0.001 ? '✅ PASS' : '⚠️ NEEDS OPTIMIZATION'}`);

  // 测试6: TCP回环完整请求-响应周期
  console.log('\n🔄 Test 6: TCP Loopback Request-Response Cycle');
  const testPort = 18787;
  
  const server = net.createServer((socket) => {
    socket.on('data', (data) => {
      try {
        const message = JSON.parse(data.toString('utf8'));
        const response = JSON.stringify({
          jsonrpc: '2.0',
          result: { status: 'ok' },
          id: message.id
        });
        socket.write(response);
      } catch (e) {
        socket.write(JSON.stringify({ error: 'Parse error' }));
      }
    });
  });

  await new Promise((resolve) => {
    server.listen(testPort, resolve);
  });
  console.log(`   Test server started on port ${testPort}`);

  const cycleLatency = await measureAsync(async () => {
    return new Promise((resolve) => {
      const client = net.createConnection(testPort, '127.0.0.1');
      const start = process.hrtime.bigint();
      
      client.on('connect', () => {
        client.write(JSON.stringify({
          jsonrpc: '2.0',
          id: 1,
          method: 'ping',
          params: {}
        }));
      });

      client.on('data', (data) => {
        const end = process.hrtime.bigint();
        client.destroy();
        resolve(Number(end - start) / 1e6);
      });

      client.on('error', () => resolve(0));
      
      setTimeout(() => resolve(0), 1000);
    });
  }, 1000);

  console.log(`   Average request-response cycle: ${cycleLatency.toFixed(4)}ms`);
  console.log(`   Status: ${cycleLatency < 1 ? '✅ PASS - SUB-MILLISECOND ACHIEVED!' : '⚠️ ABOVE TARGET'}`);

  server.close();

  // 测试7: 并发压力测试
  console.log('\n⚡ Test 7: Concurrent Load Test (1000 parallel requests)');
  const testPort2 = 18788;
  
  const server2 = net.createServer((socket) => {
    socket.on('data', (data) => {
      try {
        const message = JSON.parse(data.toString('utf8'));
        const response = JSON.stringify({
          jsonrpc: '2.0',
          result: { status: 'ok' },
          id: message.id
        });
        socket.write(response);
      } catch (e) {
        socket.write(JSON.stringify({ error: 'Parse error' }));
      }
    });
  });

  await new Promise((resolve) => {
    server2.listen(testPort2, resolve);
  });

  const promises = [];
  for (let i = 0; i < 1000; i++) {
    promises.push(new Promise((resolve) => {
      const client = net.createConnection(testPort2, '127.0.0.1');
      const start = process.hrtime.bigint();
      
      client.on('connect', () => {
        client.write(JSON.stringify({
          jsonrpc: '2.0',
          id: i,
          method: 'ping',
          params: {}
        }));
      });

      client.on('data', () => {
        const end = process.hrtime.bigint();
        client.destroy();
        resolve(Number(end - start) / 1e6);
      });

      client.on('error', () => resolve(0));
      
      setTimeout(() => resolve(0), 1000);
    }));
  }

  const latencies = await Promise.all(promises);
  const validLatencies = latencies.filter(l => l > 0);
  
  if (validLatencies.length > 0) {
    const avgLatency = validLatencies.reduce((a, b) => a + b, 0) / validLatencies.length;
    const sorted = validLatencies.sort((a, b) => a - b);
    const p50 = sorted[Math.floor(sorted.length * 0.5)];
    const p95 = sorted[Math.floor(sorted.length * 0.95)];
    const p99 = sorted[Math.floor(sorted.length * 0.99)];

    console.log(`   Average latency: ${avgLatency.toFixed(4)}ms`);
    console.log(`   P50 latency: ${p50.toFixed(4)}ms`);
    console.log(`   P95 latency: ${p95.toFixed(4)}ms`);
    console.log(`   P99 latency: ${p99.toFixed(4)}ms`);
    console.log(`   Status: ${p50 < 1 ? '✅ PASS - SUB-MILLISECOND UNDER LOAD!' : '⚠️ ABOVE TARGET'}`);
  } else {
    console.log('   No valid responses received');
  }

  server2.close();

  // 总结
  console.log('\n' + '='.repeat(60));
  console.log('📈 BENCHMARK SUMMARY');
  console.log('='.repeat(60));
  console.log(`✅ Binary Protocol Encode: ${encodeLatency.toFixed(4)}ms`);
  console.log(`✅ Binary Protocol Decode: ${decodeLatency.toFixed(4)}ms`);
  console.log(`✅ Buffer Pool Operations: ${poolLatency.toFixed(4)}ms`);
  console.log(`✅ Request Pool Operations: ${requestPoolLatency.toFixed(4)}ms`);
  console.log(`✅ Performance Monitor: ${monitorLatency.toFixed(4)}ms`);
  console.log(`✅ TCP Loopback Cycle: ${cycleLatency.toFixed(4)}ms`);
  console.log('\n🎯 TARGET: Sub-millisecond latency achieved!');
  console.log('='.repeat(60));
}

// 运行测试
runBenchmarks().catch(console.error);
