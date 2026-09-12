import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Task, TaskResult, TaskStatus } from '@/types/task';

export const useTaskStore = defineStore('task', () => {
  // 状态
  const tasks = ref<Task[]>([]);
  const currentTaskId = ref<string | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // 计算属性
  const currentTask = computed(() => {
    if (!currentTaskId.value) return null;
    return tasks.value.find(t => t.id === currentTaskId.value) || null;
  });

  const pendingTasks = computed(() => {
    return tasks.value.filter(t => t.status === 'pending');
  });

  const runningTasks = computed(() => {
    return tasks.value.filter(t => t.status === 'running');
  });

  const completedTasks = computed(() => {
    return tasks.value.filter(t => t.status === 'completed');
  });

  const failedTasks = computed(() => {
    return tasks.value.filter(t => t.status === 'failed');
  });

  const activeTasks = computed(() => {
    return tasks.value.filter(t => t.status === 'pending' || t.status === 'running');
  });

  const taskStats = computed(() => {
    return {
      total: tasks.value.length,
      pending: pendingTasks.value.length,
      running: runningTasks.value.length,
      completed: completedTasks.value.length,
      failed: failedTasks.value.length,
    };
  });

  // 方法
  function setTasks(newTasks: Task[]) {
    tasks.value = newTasks;
  }

  function addTask(task: Task) {
    tasks.value.push(task);
  }

  function updateTask(id: string, updates: Partial<Task>) {
    const index = tasks.value.findIndex(t => t.id === id);
    if (index !== -1) {
      tasks.value[index] = { ...tasks.value[index], ...updates };
    }
  }

  function removeTask(id: string) {
    tasks.value = tasks.value.filter(t => t.id !== id);
    if (currentTaskId.value === id) {
      currentTaskId.value = null;
    }
  }

  function setCurrentTask(id: string | null) {
    currentTaskId.value = id;
  }

  function setLoading(value: boolean) {
    loading.value = value;
  }

  function setError(value: string | null) {
    error.value = value;
  }

  function updateTaskStatus(id: string, status: TaskStatus, progress?: number) {
    const task = tasks.value.find(t => t.id === id);
    if (task) {
      task.status = status;
      if (progress !== undefined) {
        task.progress = progress;
      }
      if (status === 'completed' || status === 'failed') {
        task.endTime = new Date();
      }
    }
  }

  function updateTaskProgress(id: string, progress: number, message?: string) {
    const task = tasks.value.find(t => t.id === id);
    if (task) {
      task.progress = progress;
      if (message && task.result) {
        task.result.summary = message;
      }
    }
  }

  function setTaskResult(id: string, result: TaskResult) {
    const task = tasks.value.find(t => t.id === id);
    if (task) {
      task.result = result;
      task.status = 'completed';
      task.progress = 100;
      task.endTime = new Date();
    }
  }

  function setTaskError(id: string, error: string) {
    const task = tasks.value.find(t => t.id === id);
    if (task) {
      task.error = error;
      task.status = 'failed';
      task.endTime = new Date();
    }
  }

  function getTaskById(id: string): Task | undefined {
    return tasks.value.find(t => t.id === id);
  }

  function clearCompletedTasks() {
    tasks.value = tasks.value.filter(t => t.status !== 'completed');
  }

  function clearFailedTasks() {
    tasks.value = tasks.value.filter(t => t.status !== 'failed');
  }

  function cancelTask(id: string) {
    const task = tasks.value.find(t => t.id === id);
    if (task && (task.status === 'pending' || task.status === 'running')) {
      task.status = 'failed';
      task.error = '任务已取消';
      task.endTime = new Date();
    }
  }

  return {
    // 状态
    tasks,
    currentTaskId,
    loading,
    error,
    // 计算属性
    currentTask,
    pendingTasks,
    runningTasks,
    completedTasks,
    failedTasks,
    activeTasks,
    taskStats,
    // 方法
    setTasks,
    addTask,
    updateTask,
    removeTask,
    setCurrentTask,
    setLoading,
    setError,
    updateTaskStatus,
    updateTaskProgress,
    setTaskResult,
    setTaskError,
    getTaskById,
    clearCompletedTasks,
    clearFailedTasks,
    cancelTask,
  };
});