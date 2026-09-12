import { ref, computed } from 'vue';
import { useConversationStore } from '@/stores/conversation';
import * as conversationAPI from '@/api/ubrain/conversation';
import type { Conversation, Message, SendMessageRequest } from '@/types/conversation';

export function useConversation() {
  const conversationStore = useConversationStore();
  const loading = ref(false);
  const error = ref<string | null>(null);

  // 计算属性
  const conversations = computed(() => conversationStore.conversations);
  const currentConversation = computed(() => conversationStore.currentConversation);
  const currentMessages = computed(() => conversationStore.currentMessages);
  const currentConversationId = computed(() => conversationStore.currentConversationId);

  // 方法
  async function loadConversations() {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await conversationAPI.getConversations();
      conversationStore.setConversations(response.conversations);
    } catch (err) {
      error.value = '加载对话列表失败';
      console.error('加载对话列表失败:', err);
    } finally {
      loading.value = false;
    }
  }

  async function loadConversation(id: string) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await conversationAPI.getConversation(id);
      conversationStore.setCurrentConversation(id);
      conversationStore.setMessages(id, response.messages);
    } catch (err) {
      error.value = '加载对话详情失败';
      console.error('加载对话详情失败:', err);
    } finally {
      loading.value = false;
    }
  }

  async function createConversation(title?: string) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await conversationAPI.createConversation({ title });
      conversationStore.addConversation(response.conversation);
      conversationStore.setCurrentConversation(response.conversation.id);
      return response.conversation;
    } catch (err) {
      error.value = '创建对话失败';
      console.error('创建对话失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function deleteConversation(id: string) {
    loading.value = true;
    error.value = null;
    
    try {
      await conversationAPI.deleteConversation(id);
      conversationStore.removeConversation(id);
    } catch (err) {
      error.value = '删除对话失败';
      console.error('删除对话失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function sendMessage(content: string, type: 'text' = 'text', metadata?: any) {
    if (!currentConversationId.value) {
      throw new Error('没有选中的对话');
    }
    
    loading.value = true;
    error.value = null;
    
    try {
      // 先添加用户消息到本地
      const userMessage = conversationStore.sendMessage(content, type, metadata);
      
      // 发送到服务器
      const request: SendMessageRequest = {
        content,
        type,
        metadata,
      };
      
      await conversationAPI.sendMessage(currentConversationId.value, request);
      
      return userMessage;
    } catch (err) {
      error.value = '发送消息失败';
      console.error('发送消息失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function loadMessages(conversationId: string, page: number = 1) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await conversationAPI.getMessages(conversationId, page);
      conversationStore.setMessages(conversationId, response.messages);
      return response;
    } catch (err) {
      error.value = '加载消息失败';
      console.error('加载消息失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  function selectConversation(id: string) {
    conversationStore.setCurrentConversation(id);
  }

  function clearConversationMessages(conversationId: string) {
    conversationStore.clearMessages(conversationId);
  }

  function addMessage(conversationId: string, message: Message) {
    conversationStore.addMessage(conversationId, message);
  }

  function updateMessage(conversationId: string, messageId: string, updates: Partial<Message>) {
    conversationStore.updateMessage(conversationId, messageId, updates);
  }

  return {
    // 状态
    loading,
    error,
    conversations,
    currentConversation,
    currentMessages,
    currentConversationId,
    
    // 方法
    loadConversations,
    loadConversation,
    createConversation,
    deleteConversation,
    sendMessage,
    loadMessages,
    selectConversation,
    clearConversationMessages,
    addMessage,
    updateMessage,
  };
}