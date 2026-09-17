/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import axios from 'axios';
import type { 
  Task, 
  TaskStatusResponse, 
  TaskResultResponse,
  TaskListResponse,
  CancelTaskResponse
} from '@/types/task';

const API_BASE = '/api/tasks';

/**
 * 获取任务状态
 */
export async function getTaskStatus(id: string): Promise<TaskStatusResponse> {
  const response = await axios.get(`${API_BASE}/${id}`);
  return response.data;
}

/**
 * 取消任务
 */
export async function cancelTask(id: string): Promise<CancelTaskResponse> {
  const response = await axios.post(`${API_BASE}/${id}/cancel`);
  return response.data;
}

/**
 * 获取任务结果
 */
export async function getTaskResult(id: string): Promise<TaskResultResponse> {
  const response = await axios.get(`${API_BASE}/${id}/result`);
  return response.data;
}

/**
 * 获取任务列表
 */
export async function getTasks(page: number = 1, limit: number = 20, status?: string): Promise<TaskListResponse> {
  const response = await axios.get(API_BASE, {
    params: { page, limit, status }
  });
  return response.data;
}

/**
 * 获取正在运行的任务
 */
export async function getRunningTasks(): Promise<TaskListResponse> {
  const response = await axios.get(`${API_BASE}/running`);
  return response.data;
}

/**
 * 获取已完成的任务
 */
export async function getCompletedTasks(page: number = 1, limit: number = 20): Promise<TaskListResponse> {
  const response = await axios.get(`${API_BASE}/completed`, {
    params: { page, limit }
  });
  return response.data;
}

/**
 * 获取失败的任务
 */
export async function getFailedTasks(page: number = 1, limit: number = 20): Promise<TaskListResponse> {
  const response = await axios.get(`${API_BASE}/failed`, {
    params: { page, limit }
  });
  return response.data;
}

/**
 * 重试失败的任务
 */
export async function retryTask(id: string): Promise<{ taskId: string }> {
  const response = await axios.post(`${API_BASE}/${id}/retry`);
  return response.data;
}

/**
 * 删除任务
 */
export async function deleteTask(id: string): Promise<{ success: boolean }> {
  const response = await axios.delete(`${API_BASE}/${id}`);
  return response.data;
}

/**
 * 清理已完成的任务
 */
export async function clearCompletedTasks(): Promise<{ success: boolean; count: number }> {
  const response = await axios.delete(`${API_BASE}/completed`);
  return response.data;
}

/**
 * 获取任务统计
 */
export async function getTaskStats(): Promise<{
  total: number;
  pending: number;
  running: number;
  completed: number;
  failed: number;
}> {
  const response = await axios.get(`${API_BASE}/stats`);
  return response.data;
}