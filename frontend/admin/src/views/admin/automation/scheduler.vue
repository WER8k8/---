/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="任务调度备忘" subtitle="记录 Cron 表达式与说明，已接后端 /ops-automations" surface="elevated">
    <template #actions>
      <router-link to="/admin/scheduler-hub">
        <a-button type="primary">打开调度中心</a-button>
      </router-link>
    </template>
    <div class="page p-6 space-y-4">
      <a-card title="新增计划" size="small">
        <a-space wrap style="margin-bottom: 12px">
          <a-input v-model:value="name" placeholder="任务名" style="width: 200px" />
          <a-input v-model:value="cron" placeholder="Cron，如 0 3 * * *" style="width: 200px" />
        </a-space>
        <a-input v-model:value="note" placeholder="说明" allow-clear />
        <a-button type="primary" style="margin-top: 12px" :loading="saving" @click="add">
          添加
        </a-button>
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
          <template v-if="column.key === 'actions'">
            <a-popconfirm title="确认删除该计划？" @confirm="remove(String(record.id))">
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
import { apiGet, apiPost, apiDelete } from '@/utils/api';
import { YdPage } from '@/components/youding';
import type { TableColumnsType } from 'ant-design-vue';

interface SlotRow {
  id: string;
  name: string;
  cron: string;
  note: string;
  updatedAt: string;
}

const name = ref('');
const cron = ref('');
const note = ref('');
const rows = ref<SlotRow[]>([]);
const loading = ref(false);
const saving = ref(false);
const deletingId = ref<string | null>(null);

const cols: TableColumnsType = [
  { title: '任务', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: 'Cron', dataIndex: 'cron', key: 'cron', width: 140 },
  { title: '说明', dataIndex: 'note', key: 'note', ellipsis: true },
  { title: '更新', dataIndex: 'updatedAt', key: 'updatedAt', width: 180 },
  { title: '操作', key: 'actions', width: 90 },
];

function mapItem(raw: any): SlotRow {
  return {
    id: String(raw.id),
    name: String(raw.name ?? ''),
    cron: String(raw.cron ?? ''),
    note: String(raw.payload?.note ?? raw.note ?? ''),
    updatedAt: String(raw.updated_at ?? raw.updatedAt ?? '').slice(0, 19).replace('T', ' ') || '-',
  };
}

async function load() {
  loading.value = true;
  try {
    const res = await apiGet<any>('/ops-automations', { kind: 'schedule_slot' });
    const items = res?.items ?? res?.data?.items ?? (Array.isArray(res) ? res : []);
    rows.value = items.map(mapItem);
  } catch (e: any) {
    message.error(e?.message || '调度槽加载失败');
    rows.value = [];
  } finally {
    loading.value = false;
  }
}

async function add() {
  const n = name.value.trim();
  const c = cron.value.trim();
  if (!n || !c) {
    message.warning('请填写任务名与 Cron');
    return;
  }
  saving.value = true;
  try {
    await apiPost('/ops-automations', {
      kind: 'schedule_slot',
      name: n,
      cron: c,
      payload: { note: note.value.trim() },
    });
    name.value = '';
    cron.value = '';
    note.value = '';
    message.success('已保存');
    await load();
  } catch (e: any) {
    message.error(e?.message || '保存失败');
  } finally {
    saving.value = false;
  }
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
