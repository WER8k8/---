/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="error-message" :class="[type, { bordered }]">
    <div class="error-icon">
      <component :is="iconComponent" />
    </div>
    
    <div class="error-content">
      <div class="error-title" v-if="title">{{ title }}</div>
      <div class="error-description">{{ message }}</div>
      
      <div class="error-details" v-if="details && showDetails">
        <a-collapse :bordered="false">
          <a-collapse-panel key="details" header="查看详情">
            <pre class="error-details-content">{{ details }}</pre>
          </a-collapse-panel>
        </a-collapse>
      </div>
    </div>
    
    <div class="error-actions">
      <a-button v-if="showRetry" type="primary" size="small" @click="handleRetry">
        <ReloadOutlined />
        重试
      </a-button>
      <a-button v-if="showDismiss" type="text" size="small" @click="handleDismiss">
        忽略
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h } from 'vue';
import {
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';

const props = withDefaults(defineProps<{
  type?: 'error' | 'warning' | 'info';
  title?: string;
  message: string;
  details?: string;
  showDetails?: boolean;
  showRetry?: boolean;
  showDismiss?: boolean;
  bordered?: boolean;
}>(), {
  type: 'error',
  title: '',
  details: '',
  showDetails: false,
  showRetry: true,
  showDismiss: true,
  bordered: true,
});

const emit = defineEmits<{
  (e: 'retry'): void;
  (e: 'dismiss'): void;
}>();

const iconComponent = computed(() => {
  const iconMap: Record<string, any> = {
    error: CloseCircleOutlined,
    warning: ExclamationCircleOutlined,
    info: InfoCircleOutlined,
  };
  return iconMap[props.type] || WarningOutlined;
});

function handleRetry() {
  emit('retry');
}

function handleDismiss() {
  emit('dismiss');
}
</script>

<style scoped>
.error-message {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  background: #fff2f0;
}

.error-message.bordered {
  border: 1px solid #ffccc7;
}

.error-message.error {
  background: #fff2f0;
}

.error-message.error.bordered {
  border-color: #ffccc7;
}

.error-message.warning {
  background: #fffbe6;
}

.error-message.warning.bordered {
  border-color: #fff1b8;
}

.error-message.info {
  background: #e6f7ff;
}

.error-message.info.bordered {
  border-color: #91d5ff;
}

.error-icon {
  flex-shrink: 0;
  font-size: 20px;
}

.error-message.error .error-icon {
  color: #ff4d4f;
}

.error-message.warning .error-icon {
  color: #faad14;
}

.error-message.info .error-icon {
  color: #1890ff;
}

.error-content {
  flex: 1;
  min-width: 0;
}

.error-title {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.error-description {
  font-size: 14px;
  color: #8c8c8c;
  line-height: 1.5;
}

.error-details {
  margin-top: 12px;
}

.error-details-content {
  font-size: 12px;
  background: #fafafa;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.error-actions {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

@media (max-width: 768px) {
  .error-message {
    flex-direction: column;
    gap: 8px;
  }
  
  .error-actions {
    flex-direction: row;
    justify-content: flex-end;
  }
}
</style>