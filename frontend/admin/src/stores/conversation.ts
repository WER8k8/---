import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Conversation, Message, MessageMetadata } from '@/types/conversation';

export const useConversationStore = defineStore('conversation', () => {
  // 状态
  const conversations = ref<Conversation[]>([]);
  const currentConversationId = ref<string | null>(null);
  const messages = ref<Map<string, Message[]>>(new Map());
  const loading = ref(false);
  const error = ref<string | null>(null);

  // 计算属性
  const currentConversation = computed(() => {
    if (!currentConversationId.value) return null;
    return conversations.value.find(c => c.id === currentConversationId.value) || null;
  });

  const currentMessages = computed(() => {
    if (!currentConversationId.value) return [];
    return messages.value.get(currentConversationId.value) || [];
  });

  const sortedConversations = computed(() => {
    return [...conversations.value].sort((a, b) => 
      new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    );
  });

  // 方法
  function setConversations(newConversations: Conversation[]) {
    conversations.value = newConversations;
  }

  function addConversation(conversation: Conversation) {
    conversations.value.unshift(conversation);
  }

  function updateConversation(id: string, updates: Partial<Conversation>) {
    const index = conversations.value.findIndex(c => c.id === id);
    if (index !== -1) {
      conversations.value[index] = { ...conversations.value[index], ...updates };
    }
  }

  function removeConversation(id: string) {
    conversations.value = conversations.value.filter(c => c.id !== id);
    messages.value.delete(id);
    if (currentConversationId.value === id) {
      currentConversationId.value = conversations.value[0]?.id || null;
    }
  }

  function setCurrentConversation(id: string | null) {
    currentConversationId.value = id;
  }

  function setMessages(conversationId: string, messageList: Message[]) {
    messages.value.set(conversationId, messageList);
  }

  function addMessage(conversationId: string, message: Message) {
    const conversationMessages = messages.value.get(conversationId) || [];
    conversationMessages.push(message);
    messages.value.set(conversationId, conversationMessages);
    
    // 更新对话的最后消息
    const conversation = conversations.value.find(c => c.id === conversationId);
    if (conversation) {
      conversation.lastMessage = message;
      conversation.messageCount = conversationMessages.length;
      conversation.updatedAt = new Date();
    }
  }

  function updateMessage(conversationId: string, messageId: string, updates: Partial<Message>) {
    const conversationMessages = messages.value.get(conversationId);
    if (conversationMessages) {
      const index = conversationMessages.findIndex(m => m.id === messageId);
      if (index !== -1) {
        conversationMessages[index] = { ...conversationMessages[index], ...updates };
      }
    }
  }

  function clearMessages(conversationId: string) {
    messages.value.delete(conversationId);
  }

  function setLoading(value: boolean) {
    loading.value = value;
  }

  function setError(value: string | null) {
    error.value = value;
  }

  function createNewConversation(title?: string): Conversation {
    const id = `conv_${Date.now()}`;
    const now = new Date();
    const newConversation: Conversation = {
      id,
      title: title || `对话 ${conversations.value.length + 1}`,
      createdAt: now,
      updatedAt: now,
      messageCount: 0,
    };
    addConversation(newConversation);
    setCurrentConversation(id);
    return newConversation;
  }

  function sendMessage(content: string, type: 'text' = 'text', metadata?: MessageMetadata): Message {
    if (!currentConversationId.value) {
      throw new Error('没有选中的对话');
    }
    
    const message: Message = {
      id: `msg_${Date.now()}`,
      conversationId: currentConversationId.value,
      role: 'user',
      content,
      type,
      timestamp: new Date(),
      metadata,
    };
    
    addMessage(currentConversationId.value, message);
    return message;
  }

  return {
    // 状态
    conversations,
    currentConversationId,
    messages,
    loading,
    error,
    // 计算属性
    currentConversation,
    currentMessages,
    sortedConversations,
    // 方法
    setConversations,
    addConversation,
    updateConversation,
    removeConversation,
    setCurrentConversation,
    setMessages,
    addMessage,
    updateMessage,
    clearMessages,
    setLoading,
    setError,
    createNewConversation,
    sendMessage,
  };
});