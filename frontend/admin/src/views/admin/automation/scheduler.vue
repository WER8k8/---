<template>
  <YdPage title="任务调度备忘" subtitle="记录 Cron 表达式与说明（本地草案）" surface="elevated">
    <template #actions>
      <router-link to="/admin/scheduler-hub">
        <a-button type="primary">打开调度中心</a-button>
      </router-link>
    </template>
  <div class="page p-6 space-y-4">
    <a-card
      title="新增计划"
      size="small"
    >
      <a-space
        wrap
        style="margin-bottom: 12px"
      >
        <a-input
          v-model:value="name"
          placeholder="任务名"
          style="width: 200px"
        />
        <a-input
          v-model:value="cron"
          placeholder="Cron，如 0 3 * * *"
          style="width: 200px"
        />
      </a-space>
      <a-input
        v-model:value="note"
        placeholder="说明"
        allow-clear
      />
      <a-button
        type="primary"
        style="margin-top: 12px"
        @click="add"
      >
        添加
      </a-button>
    </a-card>

    <a-table
      :columns="cols"
      :data-source="state.schedulerSlots"
      row-key="id"
      size="small"
      :pagination="false"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'actions'">
          <a-button
            type="link"
            danger
            size="small"
            @click="remove(record.id)"
          >
            删除
          </a-button>
        </template>
      </template>
    </a-table>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { apiGet } from '@/utils/api';
import { YdPage } from '@/components/youding';
import type { TableColumnsType } from 'ant-design-vue';
import { useAdminWorkspace } from '@/composables/useAdminWorkspace';

onMounted(async () => {
  try { await apiGet('/ops-jobs'); } catch { /* 空状态 */ }
});

const { state, genId } = useAdminWorkspace();
const name = ref('');
const cron = ref('');
const note = ref('');

const cols: TableColumnsType = [
  { title: '任务', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: 'Cron', dataIndex: 'cron', key: 'cron', width: 140 },
  { title: '说明', dataIndex: 'note', key: 'note', ellipsis: true },
  { title: '更新', dataIndex: 'updatedAt', key: 'updatedAt', width: 180 },
  { title: '操作', key: 'actions', width: 90 },
];

function add() {
  const n = name.value.trim();
  const c = cron.value.trim();
  if (!n || !c) {
    message.warning('请填写任务名与 Cron');
    return;
  }
  state.value.schedulerSlots.unshift({
    id: genId(),
    name: n,
    cron: c,
    note: note.value.trim(),
    updatedAt: new Date().toISOString(),
  });
  name.value = '';
  cron.value = '';
  note.value = '';
  message.success('已保存到本地');
}

function remove(id: string) {
  state.value.schedulerSlots = state.value.schedulerSlots.filter((s) => s.id !== id);
}
</script>
