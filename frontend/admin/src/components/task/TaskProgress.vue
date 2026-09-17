/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="task-progress">
    <div class="progress-header">
      <div class="progress-status">
        <a-badge :status="statusType" :text="statusText" />
      </div>
      <div class="progress-percentage">{{ progress }}%</div>
    </div>
    
    <a-progress
      :percent="progress"
      :status="progressStatus"
      :show-info="false"
      :stroke-color="strokeColor"
      :trail-color="trailColor"
    />
    
    <div class="progress-info">
      <div class="progress-message" v-if="message">
        {{ message }}
      </div>
      <div class="progress-time" v-if="estimatedTime">
        预计剩余时间: {{ formatTime(estimatedTime) }}
      </div>
    </div>
    
    <div class="progress-actions" v-if="showActions">
      <a-button 
        v-if="status === 'running'"
        type="text" 
        danger 
        size="small"
        @click="handleCancel"
      >
        取消任务
      </a-button>
      <a-button 
        v-if="status === 'failed'"
        type="text" 
        size="small"
        @click="handleRetry"
      >
        重试
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(defineProps<{
  progress: number;
  status?: 'pending' | 'running' | 'completed' | 'failed';
  message?: string;
  estimatedTime?: number;
  showActions?: boolean;
}>(), {
  status: 'pending',
  message: '',
  estimatedTime: 0,
  showActions: true,
});

const emit = defineEmits<{
  (e: 'cancel'): void;
  (e: 'retry'): void;
}>();

const statusType = computed((): 'default' | 'processing' | 'success' | 'error' => {
  const typeMap: Record<string, 'default' | 'processing' | 'success' | 'error'> = {
    pending: 'default',
    running: 'processing',
    completed: 'success',
    failed: 'error',
  };
  return typeMap[props.status] || 'default';
});

const statusText = computed(() => {
  const textMap: Record<string, string> = {
    pending: '等待中',
    running: '执行中',
    completed: '已完成',
    failed: '执行失败',
  };
  return textMap[props.status] || '未知状态';
});

const progressStatus = computed((): 'normal' | 'active' | 'success' | 'exception' => {
  const statusMap: Record<string, 'normal' | 'active' | 'success' | 'exception'> = {
    pending: 'normal',
    running: 'active',
    completed: 'success',
    failed: 'exception',
  };
  return statusMap[props.status] || 'normal';
});

const strokeColor = computed(() => {
  const colorMap: Record<string, string> = {
    pending: '#d9d9d9',
    running: '#1890ff',
    completed: '#52c41a',
    failed: '#ff4d4f',
  };
  return colorMap[props.status] || '#d9d9d9';
});

const trailColor = computed(() => {
  return '#f5f5f5';
});

function formatTime(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}秒`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}分${remainingSeconds}秒`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}小时${minutes}分钟`;
  }
}

function handleCancel() {
  emit('cancel');
}

function handleRetry() {
  emit('retry');
}
</script>

<style scoped>
.task-progress {
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}

.progress-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.progress-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-percentage {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
}

.progress-info {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-message {
  font-size: 12px;
  color: #8c8c8c;
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.progress-time {
  font-size: 12px;
  color: #8c8c8c;
  flex-shrink: 0;
  margin-left: 16px;
}

.progress-actions {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 768px) {
  .progress-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .progress-time {
    margin-left: 0;
  }
}
</style>