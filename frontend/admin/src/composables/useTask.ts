/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { ref, computed } from 'vue';
import { useTaskStore } from '@/stores/task';
import * as taskAPI from '@/api/ubrain/task';
import type { Task, TaskResult, TaskStatus } from '@/types/task';

export function useTask() {
  const taskStore = useTaskStore();
  const loading = ref(false);
  const error = ref<string | null>(null);

  // 计算属性
  const tasks = computed(() => taskStore.tasks);
  const currentTask = computed(() => taskStore.currentTask);
  const pendingTasks = computed(() => taskStore.pendingTasks);
  const runningTasks = computed(() => taskStore.runningTasks);
  const completedTasks = computed(() => taskStore.completedTasks);
  const failedTasks = computed(() => taskStore.failedTasks);
  const activeTasks = computed(() => taskStore.activeTasks);
  const taskStats = computed(() => taskStore.taskStats);

  // 方法
  async function loadTasks(page: number = 1, limit: number = 20, status?: string) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await taskAPI.getTasks(page, limit, status);
      taskStore.setTasks(response.tasks);
      return response;
    } catch (err) {
      error.value = '加载任务列表失败';
      console.error('加载任务列表失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function loadTaskStatus(taskId: string) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await taskAPI.getTaskStatus(taskId);
      taskStore.updateTask(taskId, response.task);
      return response.task;
    } catch (err) {
      error.value = '获取任务状态失败';
      console.error('获取任务状态失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function loadTaskResult(taskId: string) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await taskAPI.getTaskResult(taskId);
      taskStore.setTaskResult(taskId, response.result);
      return response.result;
    } catch (err) {
      error.value = '获取任务结果失败';
      console.error('获取任务结果失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function cancelTask(taskId: string) {
    loading.value = true;
    error.value = null;
    
    try {
      await taskAPI.cancelTask(taskId);
      taskStore.cancelTask(taskId);
    } catch (err) {
      error.value = '取消任务失败';
      console.error('取消任务失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function retryTask(taskId: string) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await taskAPI.retryTask(taskId);
      // 可以在这里更新任务状态
      return response;
    } catch (err) {
      error.value = '重试任务失败';
      console.error('重试任务失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function deleteTask(taskId: string) {
    loading.value = true;
    error.value = null;
    
    try {
      await taskAPI.deleteTask(taskId);
      taskStore.removeTask(taskId);
    } catch (err) {
      error.value = '删除任务失败';
      console.error('删除任务失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function clearCompletedTasks() {
    loading.value = true;
    error.value = null;
    
    try {
      await taskAPI.clearCompletedTasks();
      taskStore.clearCompletedTasks();
    } catch (err) {
      error.value = '清理已完成任务失败';
      console.error('清理已完成任务失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function loadTaskStats() {
    loading.value = true;
    error.value = null;
    
    try {
      const stats = await taskAPI.getTaskStats();
      return stats;
    } catch (err) {
      error.value = '获取任务统计失败';
      console.error('获取任务统计失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  function selectTask(taskId: string) {
    taskStore.setCurrentTask(taskId);
  }

  function getTaskById(taskId: string) {
    return taskStore.getTaskById(taskId);
  }

  function updateTaskProgress(taskId: string, progress: number, message?: string) {
    taskStore.updateTaskProgress(taskId, progress, message);
  }

  function updateTaskStatus(taskId: string, status: TaskStatus, progress?: number) {
    taskStore.updateTaskStatus(taskId, status, progress);
  }

  function setTaskResult(taskId: string, result: TaskResult) {
    taskStore.setTaskResult(taskId, result);
  }

  function setTaskError(taskId: string, error: string) {
    taskStore.setTaskError(taskId, error);
  }

  function addTask(task: Task) {
    taskStore.addTask(task);
  }

  return {
    // 状态
    loading,
    error,
    tasks,
    currentTask,
    pendingTasks,
    runningTasks,
    completedTasks,
    failedTasks,
    activeTasks,
    taskStats,
    
    // 方法
    loadTasks,
    loadTaskStatus,
    loadTaskResult,
    cancelTask,
    retryTask,
    deleteTask,
    clearCompletedTasks,
    loadTaskStats,
    selectTask,
    getTaskById,
    updateTaskProgress,
    updateTaskStatus,
    setTaskResult,
    setTaskError,
    addTask,
  };
}