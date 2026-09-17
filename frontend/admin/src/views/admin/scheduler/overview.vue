/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="任务调度" subtitle="定时任务管理与自动化调度" surface="elevated">
  <div class="scheduler-overview">
    <div class="stats-row">
      <div
        class="stat-card"
        v-for="stat in schedulerStats"
        :key="stat.title"
      >
        <div
          class="stat-icon"
          :class="stat.iconBg"
        >
          <component :is="stat.icon" />
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ stat.value }}</span>
          <span class="stat-label">{{ stat.title }}</span>
        </div>
      </div>
    </div>

    <div class="task-section">
      <div class="section-header">
        <h3 class="section-title">
          任务列表
        </h3>
        <button
          class="add-btn"
          @click="() => { resetTaskForm(); showAddModal = true; }"
        >
          <PlusOutlined />
          添加任务
        </button>
      </div>
      <a-table
        :columns="columns"
        :data-source="tasks"
        :pagination="{ pageSize: 8 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-badge
              :status="
                record.status === 'running'
                  ? 'processing'
                  : record.status === 'completed'
                    ? 'success'
                    : 'warning'
              "
              :text="getStatusText(record.status)"
            />
          </template>
          <template v-else-if="column.key === 'cron'">
            <span class="cron-text">{{ record.cron }}</span>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-button
                size="small"
                @click="editTask(record as Task)"
              >
                编辑
              </a-button>
              <a-button
                size="small"
                @click="toggleTask(record as Task)"
              >
                {{
                  record.status === 'running' ? '暂停' : '启动'
                }}
              </a-button>
              <a-button
                size="small"
                danger
                @click="removeTask(record as Task)"
              >
                删除
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>

    <div class="recent-jobs">
      <h3 class="section-title">
        最近执行记录
      </h3>
      <div class="jobs-list">
        <div
          class="job-item"
          v-for="job in recentJobs"
          :key="job.id"
        >
          <div
            class="job-status"
            :class="job.status"
          >
            <component
              :is="job.status === 'success' ? CheckCircleOutlined : ExclamationCircleOutlined"
            />
          </div>
          <div class="job-info">
            <h4 class="job-name">
              {{ job.taskName }}
            </h4>
            <span class="job-time">{{ job.time }}</span>
          </div>
          <div class="job-duration">
            {{ job.duration }}
          </div>
        </div>
      </div>
    </div>

    <a-modal
      v-model:open="showAddModal"
      :title="editingTask ? '编辑定时任务' : '添加定时任务'"
      :footer="null"
    >
      <a-form
        :model="taskForm"
        ref="taskFormRef"
      >
        <a-form-item
          label="任务名称"
          name="name"
        >
          <a-input
            v-model:value="taskForm.name"
            placeholder="请输入任务名称"
          />
        </a-form-item>
        <a-form-item
          label="任务类型"
          name="type"
        >
          <a-select v-model:value="taskForm.type">
            <a-select-option value="cleanup">
              清理任务
            </a-select-option>
            <a-select-option value="backup">
              备份任务
            </a-select-option>
            <a-select-option value="sync">
              同步任务
            </a-select-option>
            <a-select-option value="report">
              报表任务
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item
          label="Cron表达式"
          name="cron"
        >
          <a-input
            v-model:value="taskForm.cron"
            placeholder="如: 0 0 * * *"
          />
          <p class="cron-hint">
            格式: 秒 分 时 日 月 周
          </p>
        </a-form-item>
        <a-form-item
          label="任务描述"
          name="description"
        >
          <a-textarea
            v-model:value="taskForm.description"
            placeholder="请输入任务描述"
            :rows="3"
          />
        </a-form-item>
        <div class="modal-footer">
          <a-button @click="showAddModal = false">
            取消
          </a-button>
          <a-button
            type="primary"
            @click="saveTask"
          >
            {{ editingTask ? '保存' : '添加任务' }}
          </a-button>
        </div>
      </a-form>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { message, Modal as AModal } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import {
  ClockCircleOutlined,
  PlusOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons-vue';
import type { TableColumnsType } from 'ant-design-vue';
import { apiGet } from '@/utils/api';

interface Task {
  id: number;
  name: string;
  type: string;
  cron: string;
  status: string;
  lastRun: string;
}

interface Job {
  id: number;
  taskName: string;
  time: string;
  duration: string;
  status: string;
}

const showAddModal = ref(false);
const editingTask = ref<Task | null>(null);

const taskForm = reactive({
  name: '',
  type: 'cleanup',
  cron: '',
  description: '',
});

const schedulerStats = ref<any[]>([]);

const columns: TableColumnsType<Task> = [
  { title: '任务名称', dataIndex: 'name', key: 'name' },
  { title: '类型', dataIndex: 'type', key: 'type' },
  { title: 'Cron表达式', key: 'cron' },
  { title: '状态', key: 'status' },
  { title: '上次运行', dataIndex: 'lastRun', key: 'lastRun' },
  { title: '操作', key: 'actions' },
];

const tasks = ref<Task[]>([
  {
    id: 1,
    name: '日志清理任务',
    type: 'cleanup',
    cron: '0 0 * * *',
    status: 'running',
    lastRun: '2024-01-15 00:00:00',
  },
  {
    id: 2,
    name: '数据库备份',
    type: 'backup',
    cron: '0 3 * * *',
    status: 'running',
    lastRun: '2024-01-15 03:00:00',
  },
  {
    id: 3,
    name: '数据同步',
    type: 'sync',
    cron: '*/30 * * * *',
    status: 'running',
    lastRun: '2024-01-15 10:30:00',
  },
  {
    id: 4,
    name: '日报生成',
    type: 'report',
    cron: '0 8 * * *',
    status: 'completed',
    lastRun: '2024-01-15 08:00:00',
  },
]);

const recentJobs = ref<Job[]>([
  {
    id: 1,
    taskName: '日志清理任务',
    time: '2024-01-15 00:00:00',
    duration: '2.3s',
    status: 'success',
  },
  {
    id: 2,
    taskName: '数据库备份',
    time: '2024-01-15 03:00:00',
    duration: '15.8s',
    status: 'success',
  },
  { id: 3, taskName: '数据同步', time: '2024-01-15 10:30:00', duration: '1.2s', status: 'success' },
  {
    id: 4,
    taskName: '日报生成',
    time: '2024-01-15 08:00:00',
    duration: '45.6s',
    status: 'success',
  },
]);

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    running: '运行中',
    completed: '已完成',
    paused: '已暂停',
    failed: '失败',
  };
  return map[status] || status;
};

const editTask = (task: Task) => {
  editingTask.value = task;
  taskForm.name = task.name;
  taskForm.type = task.type;
  taskForm.cron = task.cron;
  taskForm.description = '';
  showAddModal.value = true;
};

const toggleTask = (task: Task) => {
  task.status = task.status === 'running' ? 'paused' : 'running';
  message.success(task.status === 'running' ? '任务已启动' : '任务已暂停');
};

const removeTask = (task: Task) => {
  AModal.confirm({
    title: '确认删除',
    content: `确定删除任务「${task.name}」？`,
    okType: 'danger',
    onOk() {
      tasks.value = tasks.value.filter((t) => t.id !== task.id);
      message.success('任务已删除');
    },
  });
};

function resetTaskForm() {
  taskForm.name = '';
  taskForm.type = 'cleanup';
  taskForm.cron = '';
  taskForm.description = '';
  editingTask.value = null;
}

const saveTask = () => {
  if (!taskForm.name.trim()) {
    message.warning('请输入任务名称');
    return;
  }
  if (!taskForm.cron.trim()) {
    message.warning('请输入 Cron 表达式');
    return;
  }
  if (editingTask.value) {
    editingTask.value.name = taskForm.name.trim();
    editingTask.value.type = taskForm.type;
    editingTask.value.cron = taskForm.cron.trim();
    message.success('任务已更新');
  } else {
    const nextId = Math.max(0, ...tasks.value.map((t) => t.id)) + 1;
    tasks.value.unshift({
      id: nextId,
      name: taskForm.name.trim(),
      type: taskForm.type,
      cron: taskForm.cron.trim(),
      status: 'paused',
      lastRun: '-',
    });
    message.success('任务已添加');
  }
  showAddModal.value = false;
  resetTaskForm();
};

onMounted(async () => {
  try {
    await apiGet('/ops-jobs');
  } catch { /* 空状态 */ }
});
</script>

<style scoped lang="scss">
.scheduler-overview {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;

  .page-title {
    font-size: 24px;
    font-weight: 600;
    color: #1f2937;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .page-desc {
    font-size: 14px;
    color: #6b7280;
    margin-top: 4px;
  }
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;

  .stat-card {
    background: #fff;
    border-radius: 12px;
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

    .stat-icon {
      width: 44px;
      height: 44px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      color: #fff;

      &.bg-blue {
        background: linear-gradient(135deg, #4a9b8c 0%, #2a6b60 100%);
      }
      &.bg-green {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      }
      &.bg-purple {
        background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
      }
      &.bg-red {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      }
    }

    .stat-content {
      .stat-value {
        font-size: 24px;
        font-weight: 600;
        color: #1f2937;
        display: block;
      }

      .stat-label {
        font-size: 12px;
        color: #6b7280;
      }
    }
  }
}

.task-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  margin-bottom: 24px;

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .section-title {
      font-size: 16px;
      font-weight: 600;
      color: #1f2937;
      margin: 0;
    }

    .add-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      background: #4a9b8c;
      color: #fff;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 13px;
    }
  }

  .cron-text {
    font-family: monospace;
    font-size: 12px;
    color: #4a9b8c;
    background: #eef2ff;
    padding: 4px 8px;
    border-radius: 4px;
  }
}

.recent-jobs {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #f3f4f6;
  }

  .jobs-list {
    .job-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 0;
      border-bottom: 1px solid #f3f4f6;

      &:last-child {
        border-bottom: none;
      }

      .job-status {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        color: #fff;
        flex-shrink: 0;

        &.success {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        }
        &.failed {
          background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        }
      }

      .job-info {
        flex: 1;

        .job-name {
          font-size: 14px;
          font-weight: 500;
          color: #1f2937;
          margin: 0;
          margin-bottom: 2px;
        }

        .job-time {
          font-size: 12px;
          color: #9ca3af;
        }
      }

      .job-duration {
        font-size: 13px;
        color: #4a9b8c;
        font-weight: 500;
      }
    }
  }
}

.cron-hint {
  font-size: 12px;
  color: #9ca3af;
  margin: 4px 0 0 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

@media (max-width: 1024px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
}
</style>
