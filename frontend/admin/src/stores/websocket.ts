/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { WebSocketConnectionStatus, WebSocketMessage } from '@/types/websocket';

export const useWebSocketStore = defineStore('websocket', () => {
  // 状态
  const connectionStatus = ref<WebSocketConnectionStatus>('disconnected');
  const lastMessage = ref<WebSocketMessage | null>(null);
  const reconnectAttempts = ref(0);
  const maxReconnectAttempts = ref(5);
  const reconnectInterval = ref(3000);
  const error = ref<string | null>(null);
  const messageQueue = ref<WebSocketMessage[]>([]);
  /** @deprecated 请使用 `connectionStatus` 替代。`isConnected` 是 `connectionStatus` 的布尔派生值，保留仅用于向后兼容。 */
  const isConnected = ref(false);

  // 计算属性
  const statusText = computed(() => {
    const statusMap: Record<WebSocketConnectionStatus, string> = {
      connected: '已连接',
      disconnected: '已断开',
      connecting: '连接中...',
      reconnecting: '重连中...',
      error: '连接错误',
    };
    return statusMap[connectionStatus.value];
  });

  const canReconnect = computed(() => {
    return reconnectAttempts.value < maxReconnectAttempts.value;
  });

  const hasQueuedMessages = computed(() => {
    return messageQueue.value.length > 0;
  });

  // 方法
  function setConnectionStatus(status: WebSocketConnectionStatus) {
    connectionStatus.value = status;
    isConnected.value = status === 'connected';
    
    if (status === 'connected') {
      error.value = null;
      reconnectAttempts.value = 0;
    }
  }

  function setLastMessage(message: WebSocketMessage | null) {
    lastMessage.value = message;
  }

  function setError(errorMessage: string | null) {
    error.value = errorMessage;
    if (errorMessage) {
      connectionStatus.value = 'error';
    }
  }

  function incrementReconnectAttempts() {
    reconnectAttempts.value++;
  }

  function resetReconnectAttempts() {
    reconnectAttempts.value = 0;
  }

  function setMaxReconnectAttempts(attempts: number) {
    maxReconnectAttempts.value = attempts;
  }

  function setReconnectInterval(interval: number) {
    reconnectInterval.value = interval;
  }

  function queueMessage(message: WebSocketMessage) {
    messageQueue.value.push(message);
  }

  function clearMessageQueue() {
    messageQueue.value = [];
  }

  function processQueuedMessages(callback: (message: WebSocketMessage) => void) {
    while (messageQueue.value.length > 0) {
      const message = messageQueue.value.shift();
      if (message) {
        callback(message);
      }
    }
  }

  function handleConnectionError(errorMessage: string) {
    setError(errorMessage);
    connectionStatus.value = 'error';
  }

  function handleReconnecting() {
    connectionStatus.value = 'reconnecting';
    incrementReconnectAttempts();
  }

  function handleConnected() {
    setConnectionStatus('connected');
    resetReconnectAttempts();
  }

  function handleDisconnected() {
    setConnectionStatus('disconnected');
  }

  return {
    // 状态
    connectionStatus,
    lastMessage,
    reconnectAttempts,
    maxReconnectAttempts,
    reconnectInterval,
    error,
    messageQueue,
    isConnected,
    // 计算属性
    statusText,
    canReconnect,
    hasQueuedMessages,
    // 方法
    setConnectionStatus,
    setLastMessage,
    setError,
    incrementReconnectAttempts,
    resetReconnectAttempts,
    setMaxReconnectAttempts,
    setReconnectInterval,
    queueMessage,
    clearMessageQueue,
    processQueuedMessages,
    handleConnectionError,
    handleReconnecting,
    handleConnected,
    handleDisconnected,
  };
});