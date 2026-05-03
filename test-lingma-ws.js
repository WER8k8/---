const WebSocket = require('ws');

const ws = new WebSocket('ws://127.0.0.1:36510');

ws.on('open', () => {
  console.log('Connected to Lingma WebSocket');
  
  const initMessage = JSON.stringify({
    jsonrpc: '2.0',
    id: 1,
    method: 'initialize',
    params: {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: { name: 'trae-test', version: '1.0.0' }
    }
  });
  
  ws.send(initMessage);
  console.log('Sent initialize message');
  
  setTimeout(() => {
    const chatMessage = JSON.stringify({
      jsonrpc: '2.0',
      id: 2,
      method: 'tools/call',
      params: {
        name: 'lingma_chat',
        arguments: { message: '你好，灵码！请回复一下测试连通性' }
      }
    });
    
    ws.send(chatMessage);
    console.log('Sent chat message');
  }, 2000);
});

ws.on('message', (data) => {
  const message = data.toString();
  console.log('Received:', message.substring(0, 500));
});

ws.on('error', (err) => {
  console.error('WebSocket error:', err.message);
});

ws.on('close', () => {
  console.log('WebSocket closed');
  process.exit(0);
});

setTimeout(() => {
  console.log('Timeout, closing connection');
  ws.close();
}, 10000);
