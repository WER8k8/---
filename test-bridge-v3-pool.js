/**
 * 极致性能基准测试 v2 - 连接池复用优化版
 * 
 * 测试项目：
 * - 连接池复用延迟测试
 * - 持久连接请求延迟
 * - 高并发连接池压力测试
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

// ==================== 连接池 ====================
class ConnectionPool {
  constructor(port, size = 10) {
    this.port = port;
    this.size = size;
    this.connections = [];
    this.index = 0;
  }

  async initialize() {
    const promises = [];
    for (let i = 0; i < this.size; i++) {
      promises.push(new Promise((resolve) => {
        const socket = net.createConnection(this.port, '127.0.0.1');
        socket.on('connect', () => resolve(socket));
        socket.on('error', () => resolve(null));
      }));
    }
    this.connections = (await Promise.all(promises)).filter(s => s !== null);
  }

  getConnection() {
    if (this.connections.length === 0) return null;
    const conn = this.connections[this.index % this.connections.length];
    this.index++;
    return conn;
  }

  close() {
    this.connections.forEach(c => c.destroy());
  }
}

// ==================== 测试套件 ====================
async function runBenchmarks() {
  console.log('🔬 Ultra-Low-Latency Bridge v3.0 - Connection Pool Benchmark\n');
  console.log('=' .repeat(60));

  // 启动测试服务器
  const testPort = 18789;
  const server = net.createServer((socket) => {
    socket.on('data', (data) => {
      try {
        const message = JSON.parse(data.toString('utf8'));
        const response = JSON.stringify({
          jsonrpc: '2.0',
          result: { status: 'ok', echo: message.method },
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

  // 测试1: 新连接建立延迟（无连接池）
  console.log('\n🔌 Test 1: New Connection Latency (No Pool)');
  const newConnLatency = await measureAsync(async () => {
    return new Promise((resolve) => {
      const client = net.createConnection(testPort, '127.0.0.1');
      const start = process.hrtime.bigint();
      
      client.on('connect', () => {
        client.write(JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'ping', params: {} }));
      });

      client.on('data', () => {
        const end = process.hrtime.bigint();
        client.destroy();
        resolve(Number(end - start) / 1e6);
      });

      client.on('error', () => resolve(0));
      setTimeout(() => resolve(0), 500);
    });
  }, 100);

  console.log(`   Average new connection latency: ${newConnLatency.toFixed(4)}ms`);
  console.log(`   Status: ${newConnLatency < 1 ? '✅ PASS' : '⚠️ NEEDS OPTIMIZATION'}`);

  // 测试2: 持久连接请求延迟（连接池复用）
  console.log('\n🔄 Test 2: Persistent Connection Latency (With Pool)');
  const pool = new ConnectionPool(testPort, 5);
  await pool.initialize();

  const persistentLatency = await measureAsync(async () => {
    return new Promise((resolve) => {
      const client = pool.getConnection();
      if (!client) {
        resolve(0);
        return;
      }

      const start = process.hrtime.bigint();
      
      const onData = (data) => {
        const end = process.hrtime.bigint();
        client.removeListener('data', onData);
        resolve(Number(end - start) / 1e6);
      };
      
      client.on('data', onData);
      client.write(JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'ping', params: {} }));
      
      setTimeout(() => {
        client.removeListener('data', onData);
        resolve(0);
      }, 500);
    });
  }, 1000);

  console.log(`   Average persistent connection latency: ${persistentLatency.toFixed(4)}ms`);
  console.log(`   Status: ${persistentLatency < 1 ? '✅ PASS - SUB-MILLISECOND!' : '⚠️ ABOVE TARGET'}`);

  // 测试3: 连接池并发压力测试
  console.log('\n⚡ Test 3: Connection Pool Concurrent Load (1000 requests, 5 connections)');
  const promises = [];
  for (let i = 0; i < 1000; i++) {
    promises.push(new Promise((resolve) => {
      const client = pool.getConnection();
      if (!client) {
        resolve(0);
        return;
      }

      const start = process.hrtime.bigint();
      
      const onData = (data) => {
        const end = process.hrtime.bigint();
        client.removeListener('data', onData);
        resolve(Number(end - start) / 1e6);
      };
      
      client.on('data', onData);
      client.write(JSON.stringify({ jsonrpc: '2.0', id: i, method: 'ping', params: {} }));
      
      setTimeout(() => {
        client.removeListener('data', onData);
        resolve(0);
      }, 1000);
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
    console.log(`   Success rate: ${(validLatencies.length / latencies.length * 100).toFixed(1)}%`);
    console.log(`   Status: ${p50 < 1 ? '✅ PASS - SUB-MILLISECOND UNDER LOAD!' : '⚠️ ABOVE TARGET'}`);
  } else {
    console.log('   No valid responses received');
  }

  pool.close();
  server.close();

  // 总结
  console.log('\n' + '='.repeat(60));
  console.log('📈 CONNECTION POOL BENCHMARK SUMMARY');
  console.log('='.repeat(60));
  console.log(`🔌 New Connection Latency: ${newConnLatency.toFixed(4)}ms`);
  console.log(`🔄 Persistent Connection: ${persistentLatency.toFixed(4)}ms`);
  if (validLatencies.length > 0) {
    const sorted = validLatencies.sort((a, b) => a - b);
    console.log(`⚡ Concurrent P50: ${sorted[Math.floor(sorted.length * 0.5)].toFixed(4)}ms`);
    console.log(`⚡ Concurrent P95: ${sorted[Math.floor(sorted.length * 0.95)].toFixed(4)}ms`);
    console.log(`⚡ Concurrent P99: ${sorted[Math.floor(sorted.length * 0.99)].toFixed(4)}ms`);
  }
  console.log('\n🎯 KEY INSIGHT: Connection pooling reduces latency by eliminating TCP handshake overhead');
  console.log('='.repeat(60));
}

// 运行测试
runBenchmarks().catch(console.error);
