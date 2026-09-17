/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * 任务相关类型定义
 */

export interface Task {
  id: string;
  skillId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  startTime: Date;
  endTime?: Date;
  result?: TaskResult;
  error?: string;
}

export interface TaskResult {
  type: 'customer_list' | 'email_draft' | 'research_report' | 'analysis';
  data: any;
  summary?: string;
}

export interface TaskStatusResponse {
  task: Task;
}

export interface TaskResultResponse {
  result: TaskResult;
}

export interface TaskListResponse {
  tasks: Task[];
  total: number;
  page: number;
  limit: number;
}

export interface CancelTaskResponse {
  success: boolean;
  message?: string;
}

export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface TaskProgressUpdate {
  taskId: string;
  status: TaskStatus;
  progress: number;
  message?: string;
  estimatedTime?: number;
}

export interface TaskCompleteUpdate {
  taskId: string;
  status: 'completed';
  result: TaskResult;
  executionTime: number;
}