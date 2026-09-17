/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="conversation-list">
    <div class="conversation-header">
      <h3 class="title">对话列表</h3>
      <a-button type="primary" :icon="h(PlusOutlined)" @click="createConversation">
        新建对话
      </a-button>
    </div>
    
    <div class="search-box">
      <a-input-search
        v-model:value="searchQuery"
        placeholder="搜索对话..."
        allow-clear
        @search="handleSearch"
      />
    </div>
    
    <div class="conversation-items" ref="listRef">
      <template v-if="loading">
        <SkeletonCard variant="text" />
      </template>
      <template v-else>
        <div
          v-for="conversation in filteredConversations"
          :key="conversation.id"
          :class="['conversation-item', { active: conversation.id === currentConversationId }]"
          @click="selectConversation(conversation.id)"
        >
          <div class="conversation-info">
            <div class="conversation-title">{{ conversation.title }}</div>
            <div class="conversation-preview">
              {{ conversation.lastMessage?.content || '暂无消息' }}
            </div>
          </div>
          <div class="conversation-meta">
            <div class="conversation-time">
              {{ formatTime(conversation.updatedAt) }}
            </div>
            <div class="conversation-count" v-if="conversation.messageCount">
              {{ conversation.messageCount }}条消息
            </div>
          </div>
          <div class="conversation-actions">
            <a-dropdown>
              <a-button type="text" :icon="h(MoreOutlined)" @click.stop />
              <template #overlay>
                <a-menu @click="({ key }) => handleAction(String(key), conversation.id)">
                  <a-menu-item key="rename">
                    <EditOutlined />
                    <span>重命名</span>
                  </a-menu-item>
                  <a-menu-item key="delete">
                    <DeleteOutlined />
                    <span>删除</span>
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </div>
        </div>
        
        <a-empty v-if="filteredConversations.length === 0" description="暂无对话" />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue';
import SkeletonCard from '@/components/common/SkeletonCard.vue';
import { useConversationStore } from '@/stores/conversation';
import { formatDate } from '@/utils/index';
import { message } from 'ant-design-vue';
import {
  PlusOutlined,
  MoreOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue';

const conversationStore = useConversationStore();

const searchQuery = ref('');
const loading = ref(false);
const listRef = ref<HTMLElement>();

const currentConversationId = computed(() => conversationStore.currentConversationId);

const filteredConversations = computed(() => {
  if (!searchQuery.value) {
    return conversationStore.sortedConversations;
  }
  const query = searchQuery.value.toLowerCase();
  return conversationStore.sortedConversations.filter(
    conversation =>
      conversation.title.toLowerCase().includes(query) ||
      conversation.lastMessage?.content?.toLowerCase().includes(query)
  );
});

function formatTime(date: Date) {
  const now = new Date();
  const diff = now.getTime() - new Date(date).getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  
  if (days === 0) {
    return formatDate(date, 'HH:mm');
  } else if (days === 1) {
    return '昨天';
  } else if (days < 7) {
    return `${days}天前`;
  } else {
    return formatDate(date, 'MM-DD');
  }
}

function createConversation() {
  conversationStore.createNewConversation();
}

function selectConversation(id: string) {
  conversationStore.setCurrentConversation(id);
}

function handleSearch(value: string) {
  // 搜索逻辑已在computed中处理
}

async function handleAction(key: string, conversationId: string) {
  switch (key) {
    case 'rename':
      try {
        const newTitle = prompt('请输入新名称:');
        if (!newTitle) return;
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || '/api'}/v1/conversations/${conversationId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: newTitle }),
        });
        if (!response.ok) throw new Error(`API error: ${response.status}`);
        conversationStore.updateConversation(conversationId, { title: newTitle } as any);
        message.success('对话已重命名');
      } catch (error) {
        console.error('重命名对话失败:', error);
        message.error('重命名对话失败');
      }
      break;
    case 'delete':
      conversationStore.removeConversation(conversationId);
      break;
  }
}
</script>

<style scoped>
.conversation-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  border-right: 1px solid #f0f0f0;
}

.conversation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.search-box {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.conversation-items {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.3s;
  position: relative;
}

.conversation-item:hover {
  background-color: #f5f5f5;
}

.conversation-item.active {
  background-color: #e6f7ff;
  border-right: 3px solid #1890ff;
}

.conversation-info {
  flex: 1;
  min-width: 0;
}

.conversation-title {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-preview {
  font-size: 12px;
  color: #8c8c8c;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-meta {
  text-align: right;
  margin-left: 8px;
}

.conversation-time {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 4px;
}

.conversation-count {
  font-size: 11px;
  color: #bfbfbf;
}

.conversation-actions {
  margin-left: 8px;
  opacity: 0;
  transition: opacity 0.3s;
}

.conversation-item:hover .conversation-actions {
  opacity: 1;
}
</style>