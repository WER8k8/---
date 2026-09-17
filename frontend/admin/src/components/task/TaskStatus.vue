/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="task-status">
    <div class="status-header">
      <div class="status-icon" :class="statusClass">
        <component :is="statusIcon" />
      </div>
      <div class="status-info">
        <h3 class="status-title">{{ statusTitle }}</h3>
        <div class="status-meta">
          <span class="task-id">任务ID: {{ taskId }}</span>
          <span class="task-time">{{ formatTime(startTime) }}</span>
        </div>
      </div>
    </div>
    
    <div class="status-progress" v-if="status === 'running' || status === 'pending'">
      <TaskProgress
        :progress="progress"
        :status="status"
        :message="message"
        :estimated-time="estimatedTime"
        @cancel="handleCancel"
      />
    </div>
    
    <div class="status-result" v-if="status === 'completed' && result">
      <h4>执行结果</h4>
      <div class="result-summary">
        {{ result.summary || '任务已完成' }}
      </div>
      <a-button type="link" @click="viewDetails">
        查看详情
        <RightOutlined />
      </a-button>
    </div>
    
    <div class="status-error" v-if="status === 'failed' && error">
      <h4>执行失败</h4>
      <div class="error-message">
        {{ error }}
      </div>
      <a-button type="primary" @click="handleRetry">
        <ReloadOutlined />
        重试任务
      </a-button>
    </div>
    
    <div class="status-actions">
      <a-button 
        v-if="status === 'running'"
        type="default"
        danger
        @click="handleCancel"
      >
        取消任务
      </a-button>
      <a-button 
        v-if="status === 'completed'"
        type="primary"
        @click="viewDetails"
      >
        查看结果
      </a-button>
      <a-button 
        v-if="status === 'failed'"
        type="primary"
        @click="handleRetry"
      >
        重试
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h } from 'vue';
import { formatDate } from '@/utils/index';
import TaskProgress from './TaskProgress.vue';
import {
  ClockCircleOutlined,
  SyncOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  RightOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';
import type { TaskResult } from '@/types/task';

const props = defineProps<{
  taskId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  message?: string;
  estimatedTime?: number;
  startTime: Date;
  endTime?: Date;
  result?: TaskResult;
  error?: string;
}>();

const emit = defineEmits<{
  (e: 'cancel'): void;
  (e: 'retry'): void;
  (e: 'view-details'): void;
}>();

const statusIcon = computed(() => {
  const iconMap: Record<string, any> = {
    pending: ClockCircleOutlined,
    running: SyncOutlined,
    completed: CheckCircleOutlined,
    failed: CloseCircleOutlined,
  };
  return iconMap[props.status] || ClockCircleOutlined;
});

const statusClass = computed(() => props.status);

const statusTitle = computed(() => {
  const titleMap: Record<string, string> = {
    pending: '任务等待中',
    running: '任务执行中',
    completed: '任务已完成',
    failed: '任务执行失败',
  };
  return titleMap[props.status] || '未知状态';
});

function formatTime(date: Date) {
  return formatDate(date, 'YYYY-MM-DD HH:mm:ss');
}

function handleCancel() {
  emit('cancel');
}

function handleRetry() {
  emit('retry');
}

function viewDetails() {
  emit('view-details');
}
</script>

<style scoped>
.task-status {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}

.status-header {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.status-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.status-icon.pending {
  background: #f5f5f5;
  color: #8c8c8c;
}

.status-icon.running {
  background: #e6f7ff;
  color: #1890ff;
  animation: spin 2s linear infinite;
}

.status-icon.completed {
  background: #f6ffed;
  color: #52c41a;
}

.status-icon.failed {
  background: #fff2f0;
  color: #ff4d4f;
}

.status-info {
  flex: 1;
}

.status-title {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.status-meta {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #8c8c8c;
}

.task-id {
  font-family: monospace;
}

.status-result h4,
.status-error h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.result-summary {
  font-size: 14px;
  color: #52c41a;
  line-height: 1.6;
  margin-bottom: 12px;
}

.error-message {
  font-size: 14px;
  color: #ff4d4f;
  line-height: 1.6;
  margin-bottom: 12px;
  padding: 12px;
  background: #fff2f0;
  border-radius: 4px;
  border: 1px solid #ffccc7;
}

.status-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>