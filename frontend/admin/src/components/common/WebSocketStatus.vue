/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="websocket-status">
    <a-tooltip :title="statusText">
      <div class="status-indicator" :class="statusClass">
        <div class="status-dot" :aria-label="statusText" role="status" />
        <span class="status-text">{{ statusText }}</span>
      </div>
    </a-tooltip>
    
    <a-dropdown v-if="showDetails">
      <a-button type="text" size="small" :icon="h(InfoCircleOutlined)" />
      <template #overlay>
        <a-menu>
          <a-menu-item key="status">
            <span>状态: {{ statusText }}</span>
          </a-menu-item>
          <a-menu-item key="reconnect">
            <span>重连次数: {{ reconnectAttempts }}/{{ maxReconnectAttempts }}</span>
          </a-menu-item>
          <a-menu-item v-if="error" key="error">
            <span>错误: {{ error }}</span>
          </a-menu-item>
          <a-menu-divider />
          <a-menu-item key="reconnect-now" @click="handleReconnect">
            <ReloadOutlined />
            <span>立即重连</span>
          </a-menu-item>
        </a-menu>
      </template>
    </a-dropdown>
  </div>
</template>

<script setup lang="ts">
import { computed, h } from 'vue';
import { useWebSocketStore } from '@/stores/websocket';
import { InfoCircleOutlined, ReloadOutlined } from '@ant-design/icons-vue';

const props = withDefaults(defineProps<{
  showDetails?: boolean;
}>(), {
  showDetails: true,
});

const websocketStore = useWebSocketStore();

const statusText = computed(() => websocketStore.statusText);
const statusClass = computed(() => websocketStore.connectionStatus);
const reconnectAttempts = computed(() => websocketStore.reconnectAttempts);
const maxReconnectAttempts = computed(() => websocketStore.maxReconnectAttempts);
const error = computed(() => websocketStore.error);

function handleReconnect() {
  websocketStore.resetReconnectAttempts();
  websocketStore.handleConnected();
}
</script>

<style scoped>
.websocket-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 4px;
  background: #f5f5f5;
  cursor: pointer;
  transition: all 0.3s;
}

.status-indicator:hover {
  background: #e8e8e8;
}

.status-indicator:focus-visible {
  outline: 2px solid #1890ff;
  outline-offset: 2px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d9d9d9;
}

.status-indicator.connected .status-dot {
  background: #52c41a;
  box-shadow: 0 0 4px rgba(82, 196, 26, 0.5);
}

.status-indicator.disconnected .status-dot {
  background: #ff4d4f;
}

.status-indicator.connecting .status-dot,
.status-indicator.reconnecting .status-dot {
  background: #faad14;
  animation: pulse 1.5s infinite;
}

.status-indicator.error .status-dot {
  background: #ff4d4f;
}

.status-text {
  font-size: 12px;
  color: #8c8c8c;
}

.status-indicator.connected .status-text {
  color: #52c41a;
}

.status-indicator.disconnected .status-text,
.status-indicator.error .status-text {
  color: #ff4d4f;
}

.status-indicator.connecting .status-text,
.status-indicator.reconnecting .status-text {
  color: #faad14;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}
</style>