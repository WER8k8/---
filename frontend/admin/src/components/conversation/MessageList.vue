/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="message-list" ref="containerRef">
    <div class="message-container" ref="listRef">
      <div
        v-for="{ data, index } in virtualList"
        :key="data.id"
        :style="{ height: `${itemHeight}px` }"
      >
        <MessageItem
          :message="data"
          :is-last="index === messages.length - 1"
          @retry="handleRetry"
          @copy="handleCopy"
        />
      </div>
    </div>
    
    <div v-if="loading" class="loading-indicator">
      <a-spin tip="加载中..." />
    </div>
    
    <div v-if="!loading && messages.length === 0" class="empty-state">
      <a-empty description="暂无消息，开始对话吧！">
        <template #image>
          <MessageOutlined style="font-size: 48px; color: #bfbfbf" />
        </template>
      </a-empty>
    </div>
    
    <div ref="scrollAnchor" class="scroll-anchor" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue';
import { useVirtualList } from '@vueuse/core';
import { useConversationStore } from '@/stores/conversation';
import MessageItem from './MessageItem.vue';
import { MessageOutlined } from '@ant-design/icons-vue';

const props = defineProps<{
  conversationId?: string;
}>();

const emit = defineEmits<{
  (e: 'retry', messageId: string): void;
  (e: 'copy', content: string): void;
}>();

const conversationStore = useConversationStore();
const containerRef = ref<HTMLElement>();
const listRef = ref<HTMLElement>();
const scrollAnchor = ref<HTMLElement>();
const loading = ref(false);

const itemHeight = 80; // 消息项高度

const messages = computed(() => {
  if (props.conversationId) {
    return conversationStore.messages.get(props.conversationId) || [];
  }
  return conversationStore.currentMessages;
});

const { list: virtualList, scrollTo } = useVirtualList(
  messages as any,
  {
    itemHeight,
    overscan: 5,
  }
);

// 自动滚动到底部
watch(
  () => messages.value.length,
  async () => {
    await nextTick();
    if (messages.value.length > 0) {
      scrollTo(messages.value.length - 1);
    }
  }
);

// 初始加载时滚动到底部
onMounted(() => {
  if (messages.value.length > 0) {
    setTimeout(() => {
      scrollTo(messages.value.length - 1);
    }, 100);
  }
});

function handleRetry(messageId: string) {
  emit('retry', messageId);
}

function handleCopy(content: string) {
  emit('copy', content);
  navigator.clipboard.writeText(content);
}
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #fafafa;
  position: relative;
}

.message-container {
  min-height: 100%;
}

.loading-indicator {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 300px;
}

.scroll-anchor {
  height: 1px;
  width: 100%;
}

@media (max-width: 768px) {
  .message-list {
    padding: 12px;
  }
}
</style>