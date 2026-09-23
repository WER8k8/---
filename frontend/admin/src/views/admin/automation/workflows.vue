/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="工作流说明" subtitle="用步骤文本描述编排，已接后端 /ops-automations" surface="elevated">
    <template #actions>
      <router-link to="/admin/scheduler-hub">
        <a-button type="primary">调度中心</a-button>
      </router-link>
    </template>
    <div class="page p-6 space-y-4">
      <a-card title="新建 / 编辑" size="small">
        <a-input
          v-model:value="name"
          placeholder="流程名称"
          style="margin-bottom: 8px"
          allow-clear
        />
        <a-textarea
          v-model:value="steps"
          :rows="8"
          placeholder="每行一步，例如：拉取数据 -> 校验 -> 写库"
        />
        <a-space style="margin-top: 12px">
          <a-button type="primary" :loading="saving" @click="save">
            {{ editingId ? '更新' : '保存' }}
          </a-button>
          <a-button v-if="editingId" @click="reset">取消</a-button>
        </a-space>
      </a-card>

      <a-table
        :columns="cols"
        :data-source="rows"
        row-key="id"
        size="small"
        :loading="loading"
        :pagination="false"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'steps'">
            <span class="pre">{{ record.steps }}</span>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-button type="link" size="small" @click="edit(record)">编辑</a-button>
            <a-popconfirm title="确认删除该工作流？" @confirm="remove(String(record.id))">
              <a-button type="link" danger size="small" :loading="deletingId === record.id">
                删除
              </a-button>
            </a-popconfirm>
          </template>
        </template>
      </a-table>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { apiGet, apiPost, apiPut, apiDelete } from '@/utils/api';
import { YdPage } from '@/components/youding';
import type { TableColumnsType } from 'ant-design-vue';

interface WorkflowRow {
  id: string;
  name: string;
  steps: string;
  updatedAt: string;
}

const name = ref('');
const steps = ref('');
const editingId = ref<string | null>(null);
const rows = ref<WorkflowRow[]>([]);
const loading = ref(false);
const saving = ref(false);
const deletingId = ref<string | null>(null);

const cols: TableColumnsType = [
  { title: '名称', dataIndex: 'name', key: 'name', width: 180, ellipsis: true },
  { title: '步骤', dataIndex: 'steps', key: 'steps', ellipsis: true },
  { title: '更新', dataIndex: 'updatedAt', key: 'updatedAt', width: 180 },
  { title: '操作', key: 'actions', width: 140 },
];

function mapItem(raw: any): WorkflowRow {
  return {
    id: String(raw.id),
    name: String(raw.name ?? ''),
    steps: String(raw.steps ?? ''),
    updatedAt: String(raw.updated_at ?? raw.updatedAt ?? '').slice(0, 19).replace('T', ' ') || '-',
  };
}

async function load() {
  loading.value = true;
  try {
    const res = await apiGet<any>('/ops-automations', { kind: 'workflow' });
    const items = res?.items ?? res?.data?.items ?? (Array.isArray(res) ? res : []);
    rows.value = items.map(mapItem);
  } catch (e: any) {
    message.error(e?.message || '工作流加载失败');
    rows.value = [];
  } finally {
    loading.value = false;
  }
}

async function save() {
  const n = name.value.trim();
  if (!n || !steps.value.trim()) {
    message.warning('请填写名称与步骤');
    return;
  }
  saving.value = true;
  try {
    if (editingId.value) {
      await apiPut(`/ops-automations/${editingId.value}`, {
        name: n,
        steps: steps.value,
      });
      message.success('已更新');
    } else {
      await apiPost('/ops-automations', {
        kind: 'workflow',
        name: n,
        steps: steps.value,
      });
      message.success('已保存');
    }
    reset();
    await load();
  } catch (e: any) {
    message.error(e?.message || '保存失败');
  } finally {
    saving.value = false;
  }
}

function edit(row: Record<string, unknown>) {
  editingId.value = String(row.id);
  name.value = String(row.name ?? '');
  steps.value = String(row.steps ?? '');
}

function reset() {
  editingId.value = null;
  name.value = '';
  steps.value = '';
}

async function remove(id: string) {
  deletingId.value = id;
  try {
    await apiDelete(`/ops-automations/${id}`);
    message.success('已删除');
    await load();
  } catch (e: any) {
    message.error(e?.message || '删除失败');
  } finally {
    deletingId.value = null;
  }
}

onMounted(() => {
  void load();
});
</script>

<style scoped>
.pre {
  white-space: pre-wrap;
  font-size: 12px;
  color: #475569;
}
</style>
