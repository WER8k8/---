/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { ref, onMounted, onUnmounted } from 'vue';
import { useWebSocketStore } from '@/stores/websocket';
import { createWebSocketClient, parseWebSocketMessage } from '@/utils/websocket';
import type { WebSocketMessage, WebSocketConfig } from '@/types/websocket';

export function useWebSocket(config?: Partial<WebSocketConfig>) {
  const websocketStore = useWebSocketStore();
  const client = ref(createWebSocketClient(config));
  const isConnected = ref(false);

  // 消息处理器
  const messageHandlers = new Map<string, (message: WebSocketMessage) => void>();

  onMounted(async () => {
    try {
      await connect();
      setupEventHandlers();
    } catch (error) {
      console.error('WebSocket连接失败:', error);
    }
  });

  onUnmounted(() => {
    disconnect();
  });

  async function connect() {
    try {
      websocketStore.setConnectionStatus('connecting');
      await client.value.connect();
      isConnected.value = true;
      websocketStore.handleConnected();
    } catch (error) {
      websocketStore.handleConnectionError('连接失败');
      throw error;
    }
  }

  function disconnect() {
    client.value.disconnect();
    isConnected.value = false;
    websocketStore.handleDisconnected();
  }

  function send(message: WebSocketMessage) {
    if (isConnected.value) {
      client.value.send(message);
    } else {
      websocketStore.queueMessage(message);
    }
  }

  function authenticate(token: string) {
    client.value.authenticate(token);
  }

  function subscribeConversation(conversationId: string) {
    client.value.subscribeConversation(conversationId);
  }

  function subscribeTask(taskId: string) {
    client.value.subscribeTask(taskId);
  }

  function onMessage(type: string, handler: (message: WebSocketMessage) => void) {
    messageHandlers.set(type, handler);
    client.value.onMessage(type, handler);
  }

  function offMessage(type: string) {
    messageHandlers.delete(type);
    client.value.offMessage(type);
  }

  function setupEventHandlers() {
    // 连接状态变化
    client.value.onConnectionChange('main', (status) => {
      switch (status) {
        case 'connected':
          isConnected.value = true;
          websocketStore.handleConnected();
          // 发送队列中的消息
          websocketStore.processQueuedMessages((message) => {
            client.value.send(message);
          });
          break;
        case 'disconnected':
          isConnected.value = false;
          websocketStore.handleDisconnected();
          break;
        case 'reconnecting':
          websocketStore.handleReconnecting();
          break;
        case 'error':
          websocketStore.handleConnectionError('连接错误');
          break;
      }
    });

    // 心跳消息
    onMessage('heartbeat', (message) => {
      // 处理心跳响应
    });

    // 系统消息
    onMessage('system', (message) => {
      // 可以在这里处理系统通知
    });
  }

  function reconnect() {
    if (websocketStore.canReconnect) {
      websocketStore.handleReconnecting();
      connect().catch(() => {
        // 重连失败，继续尝试
        setTimeout(reconnect, websocketStore.reconnectInterval);
      });
    }
  }

  function getConnectionStatus() {
    return websocketStore.connectionStatus;
  }

  function isConnectedStatus() {
    return isConnected.value;
  }

  return {
    // 状态
    isConnected,
    connectionStatus: websocketStore.connectionStatus,
    
    // 方法
    connect,
    disconnect,
    send,
    authenticate,
    subscribeConversation,
    subscribeTask,
    onMessage,
    offMessage,
    reconnect,
    getConnectionStatus,
    isConnectedStatus,
    
    // 客户端实例（高级用法）
    client: client.value,
  };
}