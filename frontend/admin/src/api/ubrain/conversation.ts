import axios from 'axios';
import type { 
  Conversation, 
  ConversationListResponse, 
  Message, 
  MessageListResponse,
  CreateConversationRequest,
  SendMessageRequest
} from '@/types/conversation';

const API_BASE = '/api/conversations';

/**
 * 获取对话列表
 */
export async function getConversations(): Promise<ConversationListResponse> {
  const response = await axios.get(API_BASE);
  return response.data;
}

/**
 * 获取单个对话详情
 */
export async function getConversation(id: string): Promise<{ conversation: Conversation; messages: Message[] }> {
  const response = await axios.get(`${API_BASE}/${id}`);
  return response.data;
}

/**
 * 创建新对话
 */
export async function createConversation(data?: CreateConversationRequest): Promise<{ conversation: Conversation }> {
  const response = await axios.post(API_BASE, data);
  return response.data;
}

/**
 * 更新对话
 */
export async function updateConversation(id: string, data: Partial<Conversation>): Promise<{ conversation: Conversation }> {
  const response = await axios.put(`${API_BASE}/${id}`, data);
  return response.data;
}

/**
 * 删除对话
 */
export async function deleteConversation(id: string): Promise<{ success: boolean }> {
  const response = await axios.delete(`${API_BASE}/${id}`);
  return response.data;
}

/**
 * 获取对话消息列表
 */
export async function getMessages(conversationId: string, page: number = 1, limit: number = 50): Promise<MessageListResponse> {
  const response = await axios.get(`${API_BASE}/${conversationId}/messages`, {
    params: { page, limit }
  });
  return response.data;
}

/**
 * 发送消息
 */
export async function sendMessage(conversationId: string, data: SendMessageRequest): Promise<{ message: Message }> {
  const response = await axios.post(`${API_BASE}/${conversationId}/messages`, data);
  return response.data;
}

/**
 * 删除消息
 */
export async function deleteMessage(conversationId: string, messageId: string): Promise<{ success: boolean }> {
  const response = await axios.delete(`${API_BASE}/${conversationId}/messages/${messageId}`);
  return response.data;
}

/**
 * 搜索对话
 */
export async function searchConversations(query: string): Promise<ConversationListResponse> {
  const response = await axios.get(`${API_BASE}/search`, {
    params: { q: query }
  });
  return response.data;
}

/**
 * 清空对话消息
 */
export async function clearConversationMessages(conversationId: string): Promise<{ success: boolean }> {
  const response = await axios.delete(`${API_BASE}/${conversationId}/messages`);
  return response.data;
}