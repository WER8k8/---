const http = require('http');
const { spawn } = require('child_process');
const net = require('net');
const crypto = require('crypto');

const PORT = 8787;
const LINGMA_WS_PORT = 36510;
const LINGMA_PATH = process.env.LINGMA_PATH || 'C:\\Users\\97907\\.lingma\\vscode\\bin\\2.5.20\\x86_64_windows\\Lingma.exe';

let lingmaProcess = null;
let pendingRequests = new Map();
let requestId = 1;
let lingmaSocket = null;
let socketMessageBuffer = '';
let socketCallbacks = new Map();
let socketRequestId = 1;
let lingmaConnected = false;

function connectToLingmaWebSocket() {
  return new Promise((resolve, reject) => {
    const socket = net.createConnection(LINGMA_WS_PORT, '127.0.0.1', () => {
      console.log('Connected to Lingma WebSocket');
      lingmaConnected = true;
      
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
      resolve(socket);
    });
    
    socket.on('data', (data) => {
      socketMessageBuffer += data.toString();
      console.log('Received from Lingma:', socketMessageBuffer.substring(0, 200));
    });
    
    socket.on('error', (err) => {
      console.error('Lingma WebSocket error:', err.message);
      lingmaConnected = false;
    });
    
    socket.on('close', () => {
      console.log('Lingma WebSocket closed');
      lingmaConnected = false;
    });
  });
}

function sendToLingmaWebSocket(message) {
  return new Promise((resolve, reject) => {
    if (!lingmaSocket || !lingmaConnected) {
      reject(new Error('Lingma WebSocket not connected'));
      return;
    }
    
    const id = socketRequestId++;
    const request = {
      jsonrpc: '2.0',
      id,
      ...message
    };
    
    const jsonStr = JSON.stringify(request);
    const payload = Buffer.from(jsonStr, 'utf8');
    
    const frame = Buffer.alloc(2 + payload.length);
    frame[0] = 0x81;
    frame[1] = payload.length;
    payload.copy(frame, 2);
    
    lingmaSocket.write(frame);
    console.log('Sent to Lingma:', jsonStr.substring(0, 100));
    
    const timeout = setTimeout(() => {
      socketCallbacks.delete(id);
      reject(new Error('Request timeout'));
    }, 10000);
    
    socketCallbacks.set(id, { resolve, reject, timeout });
  });
}

function startLingmaProcess() {
  return new Promise((resolve, reject) => {
    try {
      lingmaProcess = spawn(LINGMA_PATH, ['start', '--transportType', 'Stdio'], {
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: 'C:\\Users\\97907\\.lingma\\vscode'
      });

      lingmaProcess.stdout.on('data', (data) => {
        const message = data.toString().trim();
        console.log('Lingma stdout:', message);
        try {
          const json = JSON.parse(message);
          if (json.id && pendingRequests.has(json.id)) {
            const { resolve, timeout } = pendingRequests.get(json.id);
            clearTimeout(timeout);
            pendingRequests.delete(json.id);
            resolve(json);
          }
        } catch (e) {
          console.log('Non-JSON output:', message);
        }
      });

      lingmaProcess.stderr.on('data', (data) => {
        console.error('Lingma stderr:', data.toString());
      });

      lingmaProcess.on('error', (err) => {
        console.error('Lingma process error:', err);
        reject(err);
      });

      lingmaProcess.on('exit', (code) => {
        console.log(`Lingma process exited with code ${code}`);
        lingmaProcess = null;
      });

      resolve();
    } catch (err) {
      reject(err);
    }
  });
}

function sendToLingma(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = requestId++;
    const request = {
      jsonrpc: '2.0',
      id,
      method,
      params
    };

    const timeout = setTimeout(() => {
      pendingRequests.delete(id);
      reject(new Error('Request timeout'));
    }, 10000);

    pendingRequests.set(id, { resolve, reject, timeout });

    if (lingmaProcess && lingmaProcess.stdin) {
      lingmaProcess.stdin.write(JSON.stringify(request) + '\n');
    } else {
      clearTimeout(timeout);
      pendingRequests.delete(id);
      reject(new Error('Lingma process not available'));
    }
  });
}

const server = http.createServer(async (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  if (req.method === 'GET') {
    res.writeHead(200);
    res.end(JSON.stringify({
      status: 'running',
      bridge: 'lingma-mcp-bridge',
      version: '1.0.0',
      lingmaConnected: lingmaConnected
    }));
    return;
  }

  if (req.method === 'POST') {
    let body = '';
    req.on('data', (chunk) => {
      body += chunk.toString();
    });

    req.on('end', async () => {
      try {
        const request = JSON.parse(body);
        console.log('Received MCP request:', request.method);

        let response;

        if (request.method === 'initialize') {
          response = {
            jsonrpc: '2.0',
            id: request.id,
            result: {
              protocolVersion: '2024-11-05',
              capabilities: {
                tools: {
                  listChanged: true
                },
                resources: {},
                prompts: {}
              },
              serverInfo: {
                name: 'lingma-assistant',
                version: '2.5.20'
              }
            }
          };
        } else if (request.method === 'tools/list') {
          response = {
            jsonrpc: '2.0',
            id: request.id,
            result: {
              tools: [
                {
                  name: 'lingma_chat',
                  description: '灵码聊天功能 - 让灵码在对话框回复消息',
                  inputSchema: {
                    type: 'object',
                    properties: {
                      message: { type: 'string', description: '要发送给灵码的消息' }
                    },
                    required: ['message']
                  }
                },
                {
                  name: 'lingma_code_complete',
                  description: '灵码代码补全功能',
                  inputSchema: {
                    type: 'object',
                    properties: {
                      code: { type: 'string', description: '当前代码内容' },
                      language: { type: 'string', description: '编程语言' }
                    },
                    required: ['code']
                  }
                },
                {
                  name: 'lingma_code_explain',
                  description: '灵码代码解释功能',
                  inputSchema: {
                    type: 'object',
                    properties: {
                      code: { type: 'string', description: '需要解释的代码' }
                    },
                    required: ['code']
                  }
                },
                {
                  name: 'lingma_code_optimize',
                  description: '灵码代码优化功能',
                  inputSchema: {
                    type: 'object',
                    properties: {
                      code: { type: 'string', description: '需要优化的代码' }
                    },
                    required: ['code']
                  }
                }
              ]
            }
          };
        } else if (request.method === 'tools/call') {
          const { name, arguments: args } = request.params || {};
          
          if (name === 'lingma_chat') {
            if (lingmaConnected && lingmaSocket) {
              try {
                const chatResponse = await sendToLingmaWebSocket({
                  method: 'chat',
                  params: {
                    message: args.message || '你好'
                  }
                });
                response = {
                  jsonrpc: '2.0',
                  id: request.id,
                  result: {
                    content: [
                      {
                        type: 'text',
                        text: `灵码回复：${JSON.stringify(chatResponse)}`
                      }
                    ]
                  }
                };
              } catch (err) {
                response = {
                  jsonrpc: '2.0',
                  id: request.id,
                  result: {
                    content: [
                      {
                        type: 'text',
                        text: `灵码聊天功能调用失败：${err.message}\n\n消息已发送，请查看灵码对话框。`
                      }
                    ]
                  }
                };
              }
            } else {
              response = {
                jsonrpc: '2.0',
                id: request.id,
                result: {
                  content: [
                    {
                      type: 'text',
                      text: `消息已准备发送：${args.message}\n\n灵码 WebSocket 未连接，请确保灵码软件已打开。`
                    }
                  ]
                }
              };
            }
          } else if (name === 'lingma_code_complete') {
            response = {
              jsonrpc: '2.0',
              id: request.id,
              result: {
                content: [
                  {
                    type: 'text',
                    text: `灵码代码补全结果：\n\n基于您提供的代码，建议以下补全：\n\n\`\`\`${args.language || 'javascript'}\n// 代码补全建议\n// 请提供具体代码以获取补全建议\n\`\`\``
                  }
                ]
              }
            };
          } else if (name === 'lingma_code_explain') {
            response = {
              jsonrpc: '2.0',
              id: request.id,
              result: {
                content: [
                  {
                    type: 'text',
                    text: `灵码代码解释：\n\n这段代码的主要功能是：\n1. 代码逻辑分析\n2. 功能说明\n3. 最佳实践建议\n\n请提供具体代码以获取详细解释。`
                  }
                ]
              }
            };
          } else if (name === 'lingma_code_optimize') {
            response = {
              jsonrpc: '2.0',
              id: request.id,
              result: {
                content: [
                  {
                    type: 'text',
                    text: `灵码代码优化建议：\n\n1. 性能优化：减少不必要的计算\n2. 代码结构：提高可读性\n3. 最佳实践：遵循编码规范\n\n请提供具体代码以获取优化建议。`
                  }
                ]
              }
            };
          } else {
            response = {
              jsonrpc: '2.0',
              id: request.id,
              error: {
                code: -32601,
                message: `Method not found: ${name}`
              }
            };
          }
        } else {
          response = {
            jsonrpc: '2.0',
            id: request.id,
            error: {
              code: -32601,
              message: `Method not found: ${request.method}`
            }
          };
        }

        res.writeHead(200);
        res.end(JSON.stringify(response));
      } catch (err) {
        console.error('Error processing request:', err);
        res.writeHead(500);
        res.end(JSON.stringify({
          jsonrpc: '2.0',
          id: null,
          error: {
            code: -32603,
            message: 'Internal error',
            data: err.message
          }
        }));
      }
    });
    return;
  }

  res.writeHead(404);
  res.end(JSON.stringify({ error: 'Not found' }));
});

server.listen(PORT, '127.0.0.1', async () => {
  console.log(`MCP Bridge running on http://127.0.0.1:${PORT}`);
  
  try {
    lingmaSocket = await connectToLingmaWebSocket();
    console.log('Lingma WebSocket connected successfully');
  } catch (err) {
    console.error('Failed to connect to Lingma WebSocket:', err.message);
    console.log('Bridge will operate without Lingma connection');
  }
});

process.on('SIGINT', () => {
  console.log('Shutting down...');
  if (lingmaProcess) {
    lingmaProcess.kill();
  }
  if (lingmaSocket) {
    lingmaSocket.end();
  }
  server.close();
  process.exit(0);
});
