const http = require('http');

const options = {
  hostname: '127.0.0.1',
  port: 8787,
  path: '/',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  }
};

const req = http.request(options, (res) => {
  let data = '';
  res.on('data', (chunk) => {
    data += chunk;
  });
  res.on('end', () => {
    console.log('Response:', data);
  });
});

req.on('error', (err) => {
  console.error('Error:', err.message);
});

const message = JSON.stringify({
  jsonrpc: '2.0',
  id: 1,
  method: 'tools/call',
  params: {
    name: 'lingma_chat',
    arguments: { message: '你好，灵码！请回复一下测试连通性' }
  }
});

req.write(message);
req.end();
