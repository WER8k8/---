/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="任务调度" subtitle="定时任务管理与自动化调度 · 已接后端 /ops-scheduler-tasks" surface="elevated">
    <div class="scheduler-overview">
      <div class="stats-row">
        <div class="stat-card" v-for="stat in schedulerStats" :key="stat.title">
          <div class="stat-icon" :class="stat.iconBg">
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
          <h3 class="section-title">任务列表</h3>
          <button class="add-btn" @click="() => { resetTaskForm(); showAddModal = true; }">
            <PlusOutlined />
            添加任务
          </button>
        </div>
        <a-table
          :columns="columns"
          :data-source="tasks"
          row-key="id"
          :loading="loading"
          :pagination="{ pageSize: 8 }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-badge
                :status="record.enabled ? 'processing' : 'default'"
                :text="record.enabled ? '已启用' : '已停用'"
              />
            </template>
            <template v-else-if="column.key === 'cron'">
              <span class="cron-text">{{ record.cron }}</span>
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-space>
                <a-button size="small" @click="editTask(record as TaskRow)">编辑</a-button>
                <a-button size="small" :loading="togglingId === record.id" @click="toggleTask(record as TaskRow)">
                  {{ record.enabled ? '停用' : '启用' }}
                </a-button>
                <a-button size="small" danger :loading="deletingId === record.id" @click="removeTask(record as TaskRow)">
                  删除
                </a-button>
              </a-space>
            </template>
          </template>
        </a-table>
      </div>

      <a-modal
        v-model:open="showAddModal"
        :title="editingTask ? '编辑定时任务' : '添加定时任务'"
        :footer="null"
      >
        <a-form :model="taskForm" ref="taskFormRef">
          <a-form-item label="任务名称" name="name">
            <a-input v-model:value="taskForm.name" placeholder="请输入任务名称" />
          </a-form-item>
          <a-form-item label="任务类型" name="type">
            <a-select v-model:value="taskForm.type">
              <a-select-option value="cleanup">清理任务</a-select-option>
              <a-select-option value="backup">备份任务</a-select-option>
              <a-select-option value="sync">同步任务</a-select-option>
              <a-select-option value="report">报表任务</a-select-option>
              <a-select-option value="custom">自定义</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="Cron表达式" name="cron">
            <a-input v-model:value="taskForm.cron" placeholder="如: 0 0 * * *" />
            <p class="cron-hint">格式: 分 时 日 月 周</p>
          </a-form-item>
          <a-form-item label="任务描述" name="description">
            <a-textarea v-model:value="taskForm.description" placeholder="请输入任务描述" :rows="3" />
          </a-form-item>
          <div class="modal-footer">
            <a-button @click="showAddModal = false">取消</a-button>
            <a-button type="primary" :loading="saving" @click="saveTask">
              {{ editingTask ? '保存' : '添加任务' }}
            </a-button>
          </div>
        </a-form>
      </a-modal>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import {
  ClockCircleOutlined,
  PlusOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons-vue';
import type { TableColumnsType } from 'ant-design-vue';
import { apiGet, apiPost, apiPut, apiPatch, apiDelete } from '@/utils/api';

interface TaskRow {
  id: string;
  name: string;
  type: string;
  cron: string;
  description: string;
  enabled: boolean;
  updated_at: string;
}

const showAddModal = ref(false);
const editingTask = ref<TaskRow | null>(null);
const loading = ref(false);
const saving = ref(false);
const togglingId = ref<string | null>(null);
const deletingId = ref<string | null>(null);

const taskForm = reactive({
  name: '',
  type: 'cleanup',
  cron: '',
  description: '',
});

const tasks = ref<TaskRow[]>([]);

const enabledCount = computed(() => tasks.value.filter((t) => t.enabled).length);
const disabledCount = computed(() => tasks.value.length - enabledCount.value);

const schedulerStats = computed(() => [
  { title: '任务总数', value: tasks.value.length, icon: ClockCircleOutlined, iconBg: 'bg-blue' },
  { title: '已启用', value: enabledCount.value, icon: CheckCircleOutlined, iconBg: 'bg-green' },
  { title: '已停用', value: disabledCount.value, icon: ExclamationCircleOutlined, iconBg: 'bg-red' },
]);

const columns: TableColumnsType<TaskRow> = [
  { title: '任务名称', dataIndex: 'name', key: 'name' },
  { title: '类型', dataIndex: 'type', key: 'type' },
  { title: 'Cron表达式', key: 'cron' },
  { title: '状态', key: 'status' },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '操作', key: 'actions' },
];

function mapItem(raw: any): TaskRow {
  return {
    id: String(raw.id),
    name: String(raw.name ?? ''),
    type: String(raw.type ?? 'custom'),
    cron: String(raw.cron ?? ''),
    description: String(raw.description ?? ''),
    enabled: raw.enabled !== false,
    updated_at: String(raw.updated_at ?? ''),
  };
}

async function load() {
  loading.value = true;
  try {
    const res = await apiGet<any>('/ops-scheduler-tasks');
    const items = res?.items ?? res?.data?.items ?? (Array.isArray(res) ? res : []);
    tasks.value = items.map(mapItem);
  } catch (e: any) {
    message.error(e?.message || '调度任务加载失败');
    tasks.value = [];
  } finally {
    loading.value = false;
  }
}

const editTask = (task: TaskRow) => {
  editingTask.value = task;
  taskForm.name = task.name;
  taskForm.type = task.type || 'custom';
  taskForm.cron = task.cron;
  taskForm.description = task.description || '';
  showAddModal.value = true;
};

const toggleTask = async (task: TaskRow) => {
  togglingId.value = task.id;
  try {
    await apiPatch(`/ops-scheduler-tasks/${task.id}/enabled`, { enabled: !task.enabled });
    message.success(task.enabled ? '已停用' : '已启用');
    await load();
  } catch (e: any) {
    message.error(e?.message || '启停失败');
  } finally {
    togglingId.value = null;
  }
};

const removeTask = async (task: TaskRow) => {
  deletingId.value = task.id;
  try {
    await apiDelete(`/ops-scheduler-tasks/${task.id}`);
    message.success('已删除');
    await load();
  } catch (e: any) {
    message.error(e?.message || '删除失败');
  } finally {
    deletingId.value = null;
  }
};

function resetTaskForm() {
  taskForm.name = '';
  taskForm.type = 'cleanup';
  taskForm.cron = '';
  taskForm.description = '';
  editingTask.value = null;
}

const saveTask = async () => {
  if (!taskForm.name.trim()) {
    message.warning('请输入任务名称');
    return;
  }
  if (!taskForm.cron.trim()) {
    message.warning('请输入 Cron 表达式');
    return;
  }
  saving.value = true;
  try {
    const payload = {
      name: taskForm.name.trim(),
      cron: taskForm.cron.trim(),
      description: taskForm.description.trim(),
      type: taskForm.type,
    };
    if (editingTask.value) {
      await apiPut(`/ops-scheduler-tasks/${editingTask.value.id}`, payload);
      message.success('任务已保存');
    } else {
      await apiPost('/ops-scheduler-tasks', { ...payload, enabled: true });
      message.success('任务已添加');
    }
    showAddModal.value = false;
    resetTaskForm();
    await load();
  } catch (e: any) {
    message.error(e?.message || '保存失败');
  } finally {
    saving.value = false;
  }
};

onMounted(() => {
  void load();
});
</script>

<style scoped lang="scss">
.scheduler-overview {
  padding: 24px;
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
        font-weight: 500;
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
      font-weight: 500;
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
