<template>
  <YdPage title="AI 任务看板" subtitle="跟踪 AI 相关待办（本地），与调度中心生产任务分工" surface="elevated">
    <template #actions>
      <router-link to="/admin/scheduler-hub">
        <a-button type="primary">调度中心</a-button>
      </router-link>
      <router-link to="/admin/ai-engine">
        <a-button>AI 引擎概览</a-button>
      </router-link>
    </template>
  <div class="page p-6 space-y-4">
    <a-card
      title="新建任务"
      size="small"
    >
      <a-space
        wrap
        style="margin-bottom: 12px"
      >
        <a-input
          v-model:value="title"
          placeholder="任务标题"
          style="width: 240px"
          allow-clear
        />
        <a-select
          v-model:value="status"
          style="width: 120px"
        >
          <a-select-option value="pending">
            待处理
          </a-select-option>
          <a-select-option value="running">
            进行中
          </a-select-option>
          <a-select-option value="done">
            完成
          </a-select-option>
        </a-select>
        <a-button
          type="primary"
          @click="add"
        >
          添加
        </a-button>
      </a-space>
      <a-input
        v-model:value="note"
        placeholder="备注（可选）"
        allow-clear
      />
    </a-card>

    <a-table
      :columns="cols"
      :data-source="state.aiTasks"
      row-key="id"
      size="small"
      :pagination="false"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tag :color="tagColor(record.status)">
            {{ statusLabel(record.status) }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'actions'">
          <a-button
            type="link"
            size="small"
            @click="cycle(record)"
          >
            推进状态
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
  try { await apiGet('/publish-tasks'); } catch { /* 空状态 */ }
});

const { state, genId } = useAdminWorkspace();
const title = ref('');
const note = ref('');
const status = ref<'pending' | 'running' | 'done'>('pending');

const cols: TableColumnsType = [
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '状态', key: 'status', width: 110 },
  { title: '备注', dataIndex: 'note', key: 'note', ellipsis: true },
  { title: '更新', dataIndex: 'updatedAt', key: 'updatedAt', width: 170 },
  { title: '操作', key: 'actions', width: 160 },
];

function tagColor(s: string) {
  if (s === 'done') return 'green';
  if (s === 'running') return 'blue';
  return 'default';
}

function statusLabel(s: string) {
  if (s === 'done') return '完成';
  if (s === 'running') return '进行中';
  return '待处理';
}

function add() {
  const t = title.value.trim();
  if (!t) {
    message.warning('请输入标题');
    return;
  }
  state.value.aiTasks.unshift({
    id: genId(),
    title: t,
    status: status.value,
    note: note.value.trim(),
    updatedAt: new Date().toISOString(),
  });
  title.value = '';
  note.value = '';
  message.success('已保存');
}

const order: Array<'pending' | 'running' | 'done'> = ['pending', 'running', 'done'];

function cycle(row: Record<string, unknown>) {
  const x = state.value.aiTasks.find((t) => t.id === String(row.id));
  if (!x) return;
  const i = order.indexOf(x.status as any);
  x.status = order[(i + 1) % order.length];
  x.updatedAt = new Date().toISOString();
}

function remove(id: string) {
  state.value.aiTasks = state.value.aiTasks.filter((t) => t.id !== id);
}
</script>
