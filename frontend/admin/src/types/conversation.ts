/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * 对话相关类型定义
 */

export interface Conversation {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  lastMessage?: Message;
}

export interface Message {
  id: string;
  conversationId: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  type: 'text' | 'skill_card' | 'task_progress' | 'result_card';
  timestamp: Date;
  metadata?: MessageMetadata;
}

export interface MessageMetadata {
  skillId?: string;
  taskId?: string;
  progress?: number;
  result?: any;
}

export interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
  page: number;
  limit: number;
}

export interface MessageListResponse {
  messages: Message[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

export interface CreateConversationRequest {
  title?: string;
}

export interface SendMessageRequest {
  content: string;
  type?: 'text' | 'skill_card' | 'task_progress' | 'result_card';
  metadata?: MessageMetadata;
}