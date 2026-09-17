/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { io, Socket } from 'socket.io-client';
import type { WebSocketConfig, WebSocketMessage } from '@/types/websocket';

export class WebSocketClient {
  private socket: Socket | null = null;
  private config: WebSocketConfig;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private messageHandlers: Map<string, (message: WebSocketMessage) => void> = new Map();
  private connectionHandlers: Map<string, (status: string) => void> = new Map();

  constructor(config: WebSocketConfig) {
    this.config = config;
  }

  /**
   * 连接WebSocket服务器
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.socket = io(this.config.url, {
          transports: ['websocket', 'polling'],
          timeout: this.config.timeout,
          reconnection: true,
          reconnectionAttempts: this.config.reconnectAttempts,
          reconnectionDelay: this.config.reconnectInterval,
          autoConnect: true,
        });

        this.setupEventHandlers();

        this.socket.on('connect', () => {
          this.notifyConnectionHandlers('connected');
          this.startHeartbeat();
          resolve();
        });

        this.socket.on('connect_error', (error: Error) => {
          this.notifyConnectionHandlers('error');
          reject(error);
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.stopHeartbeat();
    this.stopReconnectTimer();
    this.notifyConnectionHandlers('disconnected');
  }

  /**
   * 发送消息
   */
  send(message: WebSocketMessage): void {
    if (this.socket && this.socket.connected) {
      this.socket.emit('message', message);
    } else {
      console.warn('WebSocket未连接，消息将被丢弃');
    }
  }

  /**
   * 发送认证消息
   */
  authenticate(token: string): void {
    const authMessage: WebSocketMessage = {
      type: 'auth',
      payload: { token },
      timestamp: new Date(),
    };
    this.send(authMessage);
  }

  /**
   * 订阅对话消息
   */
  subscribeConversation(conversationId: string): void {
    const subscribeMessage: WebSocketMessage = {
      type: 'conversation',
      payload: { action: 'subscribe', conversationId },
      timestamp: new Date(),
    };
    this.send(subscribeMessage);
  }

  /**
   * 订阅任务更新
   */
  subscribeTask(taskId: string): void {
    const subscribeMessage: WebSocketMessage = {
      type: 'task_update',
      payload: { action: 'subscribe', taskId },
      timestamp: new Date(),
    };
    this.send(subscribeMessage);
  }

  /**
   * 注册消息处理器
   */
  onMessage(type: string, handler: (message: WebSocketMessage) => void): void {
    this.messageHandlers.set(type, handler);
  }

  /**
   * 移除消息处理器
   */
  offMessage(type: string): void {
    this.messageHandlers.delete(type);
  }

  /**
   * 注册连接状态处理器
   */
  onConnectionChange(id: string, handler: (status: string) => void): void {
    this.connectionHandlers.set(id, handler);
  }

  /**
   * 移除连接状态处理器
   */
  offConnectionChange(id: string): void {
    this.connectionHandlers.delete(id);
  }

  /**
   * 获取连接状态
   */
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  /**
   * 设置事件处理器
   */
  private setupEventHandlers(): void {
    if (!this.socket) return;

    this.socket.on('message', (data: WebSocketMessage) => {
      this.notifyMessageHandlers(data);
    });

    this.socket.on('disconnect', (reason: string) => {
      this.stopHeartbeat();
      this.notifyConnectionHandlers('disconnected');
      
      if (reason === 'io server disconnect') {
        // 服务器主动断开，尝试重连
        this.scheduleReconnect();
      }
    });

    this.socket.on('reconnect', () => {
      this.notifyConnectionHandlers('connected');
      this.startHeartbeat();
    });

    this.socket.on('reconnect_attempt', () => {
      this.notifyConnectionHandlers('reconnecting');
    });

    this.socket.on('reconnect_failed', () => {
      this.notifyConnectionHandlers('error');
    });
  }

  /**
   * 通知消息处理器
   */
  private notifyMessageHandlers(message: WebSocketMessage): void {
    const handler = this.messageHandlers.get(message.type);
    if (handler) {
      handler(message);
    }
    
    // 通用处理器
    const allHandler = this.messageHandlers.get('*');
    if (allHandler) {
      allHandler(message);
    }
  }

  /**
   * 通知连接状态处理器
   */
  private notifyConnectionHandlers(status: string): void {
    this.connectionHandlers.forEach(handler => {
      handler(status);
    });
  }

  /**
   * 开始心跳检测
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.socket?.connected) {
        const heartbeat: WebSocketMessage = {
          type: 'heartbeat',
          payload: { timestamp: new Date().toISOString() },
          timestamp: new Date(),
        };
        this.send(heartbeat);
      }
    }, this.config.heartbeatInterval);
  }

  /**
   * 停止心跳检测
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * 安排重连
   */
  private scheduleReconnect(): void {
    this.stopReconnectTimer();
    this.reconnectTimer = setTimeout(() => {
      this.notifyConnectionHandlers('reconnecting');
      this.connect().catch(() => {
        // 重连失败，继续尝试
        this.scheduleReconnect();
      });
    }, this.config.reconnectInterval);
  }

  /**
   * 停止重连定时器
   */
  private stopReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}

/**
 * 创建WebSocket客户端实例
 */
export function createWebSocketClient(config?: Partial<WebSocketConfig>): WebSocketClient {
  const defaultUrl =
    import.meta.env.VITE_WS_URL ||
    (typeof window !== 'undefined'
      ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`
      : 'ws://127.0.0.1:8001/ws');
  const defaultConfig: WebSocketConfig = {
    url: defaultUrl,
    reconnectAttempts: 5,
    reconnectInterval: 3000,
    heartbeatInterval: 30000,
    timeout: 10000,
  };

  return new WebSocketClient({ ...defaultConfig, ...config });
}

/**
 * 解析WebSocket消息
 */
export function parseWebSocketMessage(data: any): WebSocketMessage | null {
  try {
    if (typeof data === 'string') {
      return JSON.parse(data);
    }
    return data as WebSocketMessage;
  } catch (error) {
    console.error('解析WebSocket消息失败:', error);
    return null;
  }
}

/**
 * 序列化WebSocket消息
 */
export function serializeWebSocketMessage(message: WebSocketMessage): string {
  return JSON.stringify(message);
}