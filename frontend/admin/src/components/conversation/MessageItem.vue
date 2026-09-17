/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div :class="['message-item', message.role, message.type]">
    <div class="message-avatar">
      <a-avatar v-if="message.role === 'user'" :src="userAvatar" :size="36">
        <template #icon>
          <UserOutlined />
        </template>
      </a-avatar>
      <a-avatar v-else-if="message.role === 'assistant'" :size="36" style="background-color: #1890ff">
        <template #icon>
          <RobotOutlined />
        </template>
      </a-avatar>
      <a-avatar v-else :size="36" style="background-color: #52c41a">
        <template #icon>
          <InfoCircleOutlined />
        </template>
      </a-avatar>
    </div>
    
    <div class="message-content">
      <div class="message-header">
        <span class="message-role">
          {{ message.role === 'user' ? '我' : message.role === 'assistant' ? '卖货助手' : '系统' }}
        </span>
        <span class="message-time">{{ formatTime(message.timestamp) }}</span>
      </div>
      
      <div class="message-body">
        <!-- 文本消息 -->
        <div v-if="message.type === 'text'" class="text-content" v-html="sanitizeHtml(renderContent(message.content))" />
        
        <!-- 技能卡片 -->
        <div v-else-if="message.type === 'skill_card'" class="skill-card">
          <SkillCard :skill="(message.metadata?.skillId ? { id: message.metadata.skillId } : null) as any" />
        </div>
        
        <!-- 任务进度 -->
        <div v-else-if="message.type === 'task_progress'" class="task-progress">
          <TaskProgress :progress="message.metadata?.progress || 0" :status="(message.metadata as any)?.status" />
        </div>
        
        <!-- 结果卡片 -->
        <div v-else-if="message.type === 'result_card'" class="result-card">
          <TaskResult :result="message.metadata?.result" />
        </div>
        
        <!-- 默认文本 -->
        <div v-else class="text-content">{{ message.content }}</div>
      </div>
      
      <div class="message-actions">
        <a-tooltip title="复制">
          <a-button type="text" size="small" :icon="h(CopyOutlined)" @click="handleCopy" />
        </a-tooltip>
        <a-tooltip v-if="message.role === 'assistant'" title="重新生成">
          <a-button type="text" size="small" :icon="h(RedoOutlined)" @click="handleRetry" />
        </a-tooltip>
        <a-tooltip title="更多">
          <a-dropdown>
            <a-button type="text" size="small" :icon="h(MoreOutlined)" />
            <template #overlay>
              <a-menu @click="handleMenuClick">
                <a-menu-item key="delete">
                  <DeleteOutlined />
                  <span>删除</span>
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </a-tooltip>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { h, computed } from 'vue';
import { message as antdMessage } from 'ant-design-vue';
import { useUserStore } from '@/stores/user';
import { formatDate } from '@/utils/index';
import SkillCard from '@/components/skill/SkillCard.vue';
import TaskProgress from '@/components/task/TaskProgress.vue';
import TaskResult from '@/components/task/TaskResult.vue';
import {
  UserOutlined,
  RobotOutlined,
  InfoCircleOutlined,
  CopyOutlined,
  RedoOutlined,
  MoreOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue';
import type { MenuInfo } from 'ant-design-vue/es/menu/src/interface';
import { useSanitize } from '@/composables/useSanitize';
import type { Message } from '@/types/conversation';

const { sanitizeHtml } = useSanitize();

const props = defineProps<{
  message: Message;
  isLast?: boolean;
}>();

const emit = defineEmits<{
  (e: 'retry', messageId: string): void;
  (e: 'copy', content: string): void;
}>();

const userStore = useUserStore();

const userAvatar = computed(() => userStore.userAvatar);

function formatTime(timestamp: Date) {
  return formatDate(timestamp, 'HH:mm');
}

function renderContent(content: string) {
  // 简单的Markdown渲染
  let rendered = content;
  
  // 处理代码块
  rendered = rendered.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>');
  
  // 处理行内代码
  rendered = rendered.replace(/`([^`]+)`/g, '<code>$1</code>');
  
  // 处理粗体
  rendered = rendered.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  
  // 处理斜体
  rendered = rendered.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  
  // 处理链接
  rendered = rendered.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
  
  // 处理换行
  rendered = rendered.replace(/\n/g, '<br>');
  
  return rendered;
}

function handleCopy() {
  emit('copy', props.message.content);
}

function handleRetry() {
  emit('retry', props.message.id);
}

async function handleMenuClick({ key }: MenuInfo) {
  if (String(key) === 'delete') {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || '/api'}/v1/conversations/${props.message.conversationId}/messages/${props.message.id}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error(`API error: ${response.status}`);
      antdMessage.success('消息已删除');
    } catch (error) {
      console.error('删除消息失败:', error);
      antdMessage.error('删除消息失败');
    }
  }
}
</script>

<style scoped>
.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  padding: 8px;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.message-item:hover {
  background-color: rgba(0, 0, 0, 0.02);
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-item.user .message-content {
  align-items: flex-end;
}

.message-item.user .message-header {
  flex-direction: row-reverse;
}

.message-item.user .message-body {
  background: #1890ff;
  color: white;
  border-radius: 18px 18px 4px 18px;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  display: flex;
  flex-direction: column;
  max-width: 70%;
  min-width: 120px;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.message-role {
  font-size: 12px;
  font-weight: 500;
  color: #1a1a1a;
}

.message-time {
  font-size: 11px;
  color: #8c8c8c;
}

.message-body {
  background: #fff;
  padding: 12px 16px;
  border-radius: 18px 18px 18px 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  position: relative;
}

.text-content {
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.text-content :deep(pre) {
  background: #f5f5f5;
  border-radius: 4px;
  padding: 12px;
  overflow-x: auto;
  margin: 8px 0;
}

.text-content :deep(code) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
}

.text-content :deep(a) {
  color: #1890ff;
  text-decoration: none;
}

.text-content :deep(a:hover) {
  text-decoration: underline;
}

.message-item.user .text-content :deep(a) {
  color: #fff;
}

.skill-card,
.task-progress,
.result-card {
  min-width: 280px;
}

.message-actions {
  display: flex;
  gap: 4px;
  margin-top: 4px;
  opacity: 0;
  transition: opacity 0.3s;
}

.message-item:hover .message-actions {
  opacity: 1;
}

@media (max-width: 768px) {
  .message-content {
    max-width: 85%;
  }
  
  .message-body {
    padding: 10px 14px;
  }
}
</style>