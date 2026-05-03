const net = require('net');
const crypto = require('crypto');

const LINGMA_WS_PORT = 36510;

function createWebSocketFrame(message) {
  const payload = Buffer.from(message, 'utf8');
  const maskKey = crypto.randomBytes(4);
  
  const maskedPayload = Buffer.alloc(payload.length);
  for (let i = 0; i < payload.length; i++) {
    maskedPayload[i] = payload[i] ^ maskKey[i % 4];
  }
  
  const frame = Buffer.alloc(2 + 4 + payload.length);
  frame[0] = 0x81;
  frame[1] = 0x80 | payload.length;
  maskKey.copy(frame, 2);
  maskedPayload.copy(frame, 6);
  
  return frame;
}

const socket = net.createConnection(LINGMA_WS_PORT, '127.0.0.1', () => {
  console.log('Connected to Lingma WebSocket');
  
  const upgradeRequest = [
    'GET / HTTP/1.1',
    'Host: 127.0.0.1:' + LINGMA_WS_PORT,
    'Upgrade: websocket',
    'Connection: Upgrade',
    'Sec-WebSocket-Key: ' + crypto.randomBytes(16).toString('base64'),
    'Sec-WebSocket-Version: 13',
    '',
    ''
  ].join('\r\n');
  
  socket.write(upgradeRequest);
  
  setTimeout(() => {
    const message = JSON.stringify({
      jsonrpc: '2.0',
      id: 1,
      method: 'chat',
      params: {
        message: '你好，灵码！请回复一下测试连通性'
      }
    });
    
    const frame = createWebSocketFrame(message);
    socket.write(frame);
    console.log('Sent chat message to Lingma');
    
    setTimeout(() => {
      socket.end();
      console.log('Connection closed');
    }, 5000);
  }, 2000);
});

socket.on('data', (data) => {
  console.log('Received from Lingma:', data.toString('utf8').substring(0, 500));
});

socket.on('error', (err) => {
  console.error('Error:', err.message);
});

socket.on('close', () => {
  console.log('Connection closed');
  process.exit(0);
});
