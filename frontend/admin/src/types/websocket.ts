/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * WebSocket消息类型定义
 */

export interface WebSocketMessage {
  type: 'conversation' | 'task_update' | 'system' | 'heartbeat' | 'auth' | 'task_complete';
  payload: any;
  timestamp: Date;
  messageId?: string;
}

export interface WebSocketAuthMessage {
  type: 'auth';
  payload: {
    token: string;
  };
}

export interface WebSocketConversationMessage {
  type: 'conversation';
  payload: {
    conversationId: string;
    message: {
      id: string;
      role: 'user' | 'assistant' | 'system';
      content: string;
      type: 'text' | 'skill_card' | 'task_progress' | 'result_card';
      timestamp: string;
    };
  };
}

export interface WebSocketTaskUpdateMessage {
  type: 'task_update';
  payload: {
    taskId: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    progress: number;
    message?: string;
    estimatedTime?: number;
  };
}

export interface WebSocketTaskCompleteMessage {
  type: 'task_complete';
  payload: {
    taskId: string;
    status: 'completed';
    result: {
      type: 'customer_list' | 'email_draft' | 'research_report' | 'analysis';
      data: any;
      summary?: string;
    };
  };
}

export interface WebSocketHeartbeatMessage {
  type: 'heartbeat';
  payload: {
    timestamp: string;
  };
}

export interface WebSocketSystemMessage {
  type: 'system';
  payload: {
    level: 'info' | 'warning' | 'error';
    message: string;
    code?: string;
  };
}

export type WebSocketConnectionStatus = 'connected' | 'disconnected' | 'connecting' | 'reconnecting' | 'error';

export interface WebSocketConfig {
  url: string;
  reconnectAttempts: number;
  reconnectInterval: number;
  heartbeatInterval: number;
  timeout: number;
}