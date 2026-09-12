<template>
  <YdPage title="工作流说明" subtitle="用步骤文本描述编排，本地草稿" surface="elevated">
    <template #actions>
      <router-link to="/admin/scheduler-hub">
        <a-button type="primary">调度中心</a-button>
      </router-link>
    </template>
  <div class="page p-6 space-y-4">
    <a-card
      title="新建 / 编辑"
      size="small"
    >
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
        <a-button
          type="primary"
          @click="save"
        >
          {{ editingId ? '更新' : '保存' }}
        </a-button>
        <a-button
          v-if="editingId"
          @click="reset"
        >
          取消
        </a-button>
      </a-space>
    </a-card>

    <a-table
      :columns="cols"
      :data-source="state.workflows"
      row-key="id"
      size="small"
      :pagination="false"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'steps'">
          <span class="pre">{{ record.steps }}</span>
        </template>
        <template v-else-if="column.key === 'actions'">
          <a-button
            type="link"
            size="small"
            @click="edit(record)"
          >
            编辑
          </a-button>
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
const steps = ref('');
const editingId = ref<string | null>(null);

const cols: TableColumnsType = [
  { title: '名称', dataIndex: 'name', key: 'name', width: 180, ellipsis: true },
  { title: '步骤', dataIndex: 'steps', key: 'steps', ellipsis: true },
  { title: '更新', dataIndex: 'updatedAt', key: 'updatedAt', width: 180 },
  { title: '操作', key: 'actions', width: 140 },
];

function save() {
  const n = name.value.trim();
  if (!n || !steps.value.trim()) {
    message.warning('请填写名称与步骤');
    return;
  }
  const now = new Date().toISOString();
  if (editingId.value) {
    const w = state.value.workflows.find((x) => x.id === editingId.value);
    if (w) {
      w.name = n;
      w.steps = steps.value;
      w.updatedAt = now;
      message.success('已更新');
    }
  } else {
    state.value.workflows.unshift({ id: genId(), name: n, steps: steps.value, updatedAt: now });
    message.success('已保存');
  }
  reset();
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

function remove(id: string) {
  state.value.workflows = state.value.workflows.filter((w) => w.id !== id);
}
</script>

<style scoped>
.pre {
  white-space: pre-wrap;
  font-size: 12px;
  color: #475569;
}
</style>
